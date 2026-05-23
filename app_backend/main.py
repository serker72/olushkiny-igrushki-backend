import hashlib
import hmac
import random
import string
import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import Depends, FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBearer
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from libre_fastapi_jwt import AuthJWT, AuthJWTBearer
from libre_fastapi_jwt.exceptions import AuthJWTException
from loguru import logger
from pydantic import ValidationError
from starlette.middleware.sessions import SessionMiddleware
from starlette_wtf import CSRFProtectMiddleware

from app_backend.dependencies import security
from app_backend.routers import BaseRouter, BaseUIRouter
from app_backend.services.base import ServiceManager
from common.exceptions import (
    BackendException,
    ForbiddenException,
    ServerErrorException,
    UnauthorizedException,
    UnprocessableEntityException,
    pydantic_error_translator,
    translation_folders,
    translation_loaders,
)
from common.helpers import constants as c
from common.helpers import json
from common.helpers.database import (
    async_session_generator,
    get_request_sa_session,
    get_sa_async_engine,
    get_sa_async_session,
    has_uncommitted_changes,
)
from common.helpers.date_time import format_datetime
from common.helpers.exception import get_traceback
from common.helpers.log import logger_configure
from common.helpers.redis_async import get_async_redis, redis_async_connection_pool
from common.helpers.request import get_client_ip_from_fastapi_request, get_client_user_agent_from_fastapi_request
from common.schemas.models import UserModel
from common.schemas.models.settings import settings
from common.schemas.responses.base import CustomJSONResponse

app_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=7))
logger_configure(c.APPLICATION_CODE_BACKEND, app_id)

logger.debug(f"translation_folders: {repr(translation_folders)}")
logger.debug(f"translation_loaders: {repr(translation_loaders)}")

# Список публичных методов
public_endpoints = [
    "/docs",
    "/redoc",
    "/openapi.json",
    # f"{settings.backend_api_prefix}/docs",
    # f"{settings.backend_api_prefix}/redoc",
    # f"{settings.backend_api_prefix}/openapi.json",
]

# Список методов, требующих JWT refresh_token
refresh_token_endpoints = [
    f"{settings.backend_api_prefix}/auth/token-refresh",
]

# Список методов, не требующих кеширования
not_cached_endpoints = [
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
    # f"{settings.backend_api_prefix}/",
    # f"{settings.backend_api_prefix}/docs",
    # f"{settings.backend_api_prefix}/redoc",
    # f"{settings.backend_api_prefix}/openapi.json",
]

# Список методов, не требующих подключения к БД
without_database_endpoints = [
    "/",
    "/docs",
    "/redoc",
    "/openapi.json",
    # f"{settings.backend_api_prefix}/",
    # f"{settings.backend_api_prefix}/docs",
    # f"{settings.backend_api_prefix}/redoc",
    # f"{settings.backend_api_prefix}/openapi.json",
]


@AuthJWT.load_config
def get_config():
    return settings


@asynccontextmanager
async def app_lifespan(_: FastAPI):
    """Выполнение действий после старта и перед финишем приложения"""
    # app_id = "".join(random.choices(string.ascii_uppercase + string.digits, k=7))
    with logger.contextualize(app_id=app_id):
        logger.info("=== STARTUP ===")

        sa_engine = get_sa_async_engine()
        logger.info(f"sa_engine: {repr(sa_engine.pool)}")

        async with get_sa_async_session(sa_engine) as session:
            await service_manager.get_service(
                module_code=c.MODULE_CODE_USERS, request_id="app_lifespan", session=session
            ).save_user_list_to_cache()

        # auth_jwt = AuthJWTBearer()
        # logger.info(f"auth_jwt: {repr(auth_jwt.__dict__)}")

        # yield {"app_id": app_id, "sa_engine": sa_engine, "auth_jwt": auth_jwt}
        yield {"app_id": app_id, "sa_engine": sa_engine}

        await sa_engine.dispose()

        if redis_async_connection_pool:
            await redis_async_connection_pool.aclose()

        logger.info("=== SHUTDOWN ==")


auth_dep = AuthJWTBearer()

app = FastAPI(
    title="OlushkinyIgrushki",
    default_response_class=CustomJSONResponse,
    # root_path=settings.backend_api_prefix,
    lifespan=app_lifespan,
    docs_url=None,
    redoc_url=None,
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_allow_origin,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=settings.backend_secret_key, session_cookie="sess")
app.add_middleware(CSRFProtectMiddleware, csrf_secret=settings.backend_csrf_protec_secret_key)

app.mount("/static", StaticFiles(directory="app_backend/static"), name="static")

templates = Jinja2Templates(directory="templates")
templates.env.filters["format_datetime"] = format_datetime

service_manager = ServiceManager(settings=settings, templates=templates, jwt_auth=auth_dep())

"""
Механизм поиска и подключения классов представлений:
- файлы представлений необходимо размещать в каталоге `app/routers`
- базовый класс представления `BaseRouter` располагается в файле `app/routers/base.py` 
- все представления реализуются на базе класса:
  - наименование класса состоит из двух сегментов, `{module code}` и `Router`, к примеру `SystemRouter`
  - класс порождается от классов `BaseRouter, Routable`
- все классы представлений импортируются в файле `app/routers/__init__.py`
- все маршруты всех классов представлений, потомков класса `BaseRouter`, добавляются в список маршрутов приложения
- если свойство класса представления `is_security_dependency`: 
    - `True` - все маршруты будут требовать указание JWT токена
    - `False` - все маршруты, которые не указаны в `security_dependency_endpoints`, являются общедоступными
"""
for router_class in list(BaseRouter.__subclasses__() + BaseUIRouter.__subclasses__()):
    logger.debug(f"router_class: {repr(router_class.__name__)}")
    # logger.debug(f"router_class.__bases__: {repr(router_class.__bases__)}")
    logger.debug(f"router_class.__bases__ is BaseUIRouter: {repr(issubclass(router_class, BaseUIRouter))}")
    router_kwargs = {"settings": settings}
    if issubclass(router_class, BaseUIRouter):
        router_kwargs["templates"] = templates

    router = router_class(service_manager, **router_kwargs)

    # Добавление списка методов, не требующих кеширования
    if isinstance(router.not_cached_endpoints, list) and len(router.not_cached_endpoints) > 0:
        not_cached_endpoints.extend(
            [f"{settings.backend_api_prefix}{router.prefix}{url}" for url in router.not_cached_endpoints]
        )

    # Добавление списка методов, не требующих подключения к БД
    if isinstance(router.without_database_endpoints, list) and len(router.without_database_endpoints) > 0:
        without_database_endpoints.extend(
            [f"{settings.backend_api_prefix}{router.prefix}{url}" for url in router.without_database_endpoints]
        )

    for route in router.router.routes:
        if router.is_security_dependency or (
            isinstance(router.security_dependency_endpoints, list)
            and len(router.security_dependency_endpoints) > 0
            and f"/{route.path.split('/')[-1]}" in router.security_dependency_endpoints
        ):
            route.dependencies = [Depends(security)]

        # if not any([isinstance(dependency.dependency, HTTPBearer) for dependency in route.dependencies]) and (
        if not any([isinstance(dependency.dependency, AuthJWTBearer) for dependency in route.dependencies]) and (
            f"{'' if issubclass(router_class, BaseUIRouter) else settings.backend_api_prefix}{route.path}"
            not in refresh_token_endpoints
        ):
            public_endpoints.append(
                f"{'' if issubclass(router_class, BaseUIRouter) else settings.backend_api_prefix}{route.path}"
            )

        logger.debug(f"router_class: {repr(router_class.__name__)}, route.dependencies: {repr(route.dependencies)}")

    # Добавление маршрутов представления в список маршрутов приложения
    app.include_router(
        router.router,
        prefix="" if issubclass(router_class, BaseUIRouter) else settings.backend_api_prefix,
    )

logger.debug(f"public_endpoints={repr(public_endpoints)}")
logger.debug(f"not_cached_endpoints={repr(not_cached_endpoints)}")
logger.debug(f"without_database_endpoints={repr(without_database_endpoints)}")
logger.debug(f"app.routes={repr(app.routes)}")


async def verify_token(
    request: Request, auth_jwt: AuthJWT, required_token_type: str, encoded_token: str = None
) -> tuple[UserModel, dict]:
    """Проверка JWT токена"""
    verified_token = auth_jwt.get_raw_jwt(encoded_token)
    logger.debug(f"verified_token: {repr(verified_token)}")

    if not verified_token or verified_token["type"] != required_token_type:
        raise ForbiddenException(code=f"jwt_{required_token_type}_required")

    user_ip = get_client_ip_from_fastapi_request(request)
    user_agent = get_client_user_agent_from_fastapi_request(request)
    user_device_id = f"{verified_token['device_id']}::{user_agent}"
    user_device_id_hash = hmac.new(
        settings.backend_password_secret_key.encode("utf-8"), user_device_id.encode("utf-8"), hashlib.sha3_512
    ).hexdigest()
    logger.info(f"user_ip: {user_ip}")
    logger.info(f"user_agent: {user_agent}")
    logger.info(f"user_device_id: {user_device_id}")
    logger.info(f"user_device_id_hash: {user_device_id_hash}")

    try:
        user_id = int(verified_token["sub"])
    except ValueError:
        raise UnauthorizedException(
            code=f"jwt_{verified_token['type']}_subject_is_invalid",
            message_context={"id": verified_token["sub"]},
            context={"id": verified_token["sub"]},
        )

    redis_connection = await get_async_redis()

    # Проверка статуса пользователя
    key = c.REDIS_KEY_USER_LIST_KEY.format(user_id=user_id)
    if not await redis_connection.hexists(c.REDIS_KEY_USER_LIST_HASH, key):
        raise UnauthorizedException(code="user_not_found_by_id", message_context={"field_value": user_id})

    user_data = await redis_connection.hget(c.REDIS_KEY_USER_LIST_HASH, key)
    logger.debug(f"user_data: {type(user_data)} {repr(user_data)}")
    if not user_data:
        raise UnauthorizedException(code="user_not_found_by_id", message_context={"field_value": user_id})

    user = UserModel.model_validate(json.loads(user_data))
    logger.debug(f"user: {repr(user.model_dump())}")

    if user.state.code == c.STATE_DELETED:
        raise UnauthorizedException(code="user_state_is_deleted", message_context={"id": user_id})
    elif user.state.code == c.STATE_BLOCKED:
        raise UnauthorizedException(code="user_state_is_blocked", message_context={"id": user_id})

    key = c.REDIS_KEY_JWT_BLACKLIST.format(type=verified_token["type"], jti=verified_token["jti"])
    entry = await redis_connection.get(key)
    if entry == "true":
        raise UnauthorizedException(code=f"jwt_{verified_token['type']}_is_revoked")

    hash_name = c.REDIS_KEY_JWT_ACTIVELIST_HASH.format(user_id=user_id, user_device_id=user_device_id_hash)
    key = c.REDIS_KEY_JWT_ACTIVELIST_KEY.format(type=verified_token["type"], jti=verified_token["jti"])
    logger.debug(f"hash_name: {hash_name}")
    logger.debug(f"key: {key}")
    # if not await redis_connection.hexists(hash_name, key):
    key_exists = await redis_connection.hexists(hash_name, key)
    logger.debug(f"key_exists: {repr(key_exists)}")
    if not key_exists:
        raise UnauthorizedException(code=f"jwt_{verified_token['type']}_not_found_in_active_list")

    return user, verified_token


@app.middleware("http")
async def db_async_session_middleware(request: Request, call_next):
    """Создание асинхронной сессии SQLAlchemy для каждого запроса"""
    url = f"{request.url.path}{f'?{request.url.query}' if request.url.query else ''}"

    if request.url.path in without_database_endpoints:
        logger.info(f"{request.method} {url}, is_without_database=1")
        return await call_next(request)

    async_session = async_session_generator(request.state.sa_engine)
    async with async_session() as request.state.sa_session:
        try:
            logger.info(f"{request.method} {url}, session={repr(request.state.sa_session)}")
            response = await call_next(request)

            logger.debug(f"response status_code={response.status_code}")
            if response.status_code not in {status.HTTP_200_OK, status.HTTP_201_CREATED}:
                await async_session.rollback()
            elif has_uncommitted_changes(request.state.sa_session):
                await async_session.commit()
                # logger.debug(
                #     f"commit session: {repr(async_session.__dict__)} {repr(request.state.sa_session.__dict__)}"
                # )
        except Exception as e:
            trace = get_traceback(e)
            logger.error(f"session: {get_request_sa_session(request)}, trace: \n{trace}")

            if (
                isinstance(e, BackendException)
                and e.is_session_commit is True
                and has_uncommitted_changes(request.state.sa_session)
            ):
                await async_session.commit()
                logger.debug(f"commit session: {get_request_sa_session(request)}")
            else:
                await async_session.rollback()
                logger.debug(f"rollback session: {get_request_sa_session(request)}")

            if isinstance(e, BackendException):
                response = CustomJSONResponse(content=e.get_content().model_dump(), status_code=e.status_code)
            else:
                response = CustomJSONResponse(
                    content=(
                        ServerErrorException(code="undefined", message_context={"error": str(e)})
                        .get_content()
                        .model_dump()
                    ),
                    status_code=ServerErrorException.status_code,
                )
        finally:
            await async_session.remove()

    return response


# @app.middleware("http")
# async def response_cache_middleware(request: Request, call_next):
#     """Кеширование результатов обработки запроса"""
#     default_cache_control = f"max-age={settings.api_caching_time}"
#     cache_control = request.headers.get("Cache-Control", default_cache_control)
#
#     logger.info(f"cache_control={repr(cache_control)}, request_path={request.url.path}")
#
#     if cache_control == "no-cache" or request.url.path in not_cached_endpoints:
#         logger.info("no-cache")
#         return await call_next(request)
#
#     cache_key = ":".join(
#         [c.CACHE_PREFIX, request.method.lower(), request.url.path, repr(sorted(request.query_params.items()))]
#     ).replace(" ", "")
#     logger.debug(f"cache_key={repr(cache_key)}")
#
#     # async with aioredis.Redis(connection_pool=request.state.cache_pool) as cache_client:
#     #     logger.debug(f"cache_client.connection_pool: {repr(cache_client.connection_pool.__dict__)}")
#     cache_client = request.state.cache_client
#
#     try:
#         # async with cache_client.pipeline() as pipe:
#         #     ttl, cached = await pipe.ttl(cache_key).get(cache_key).execute()
#
#         if settings.api_cache_type == "memcached":
#             item = await cache_client.get(cache_key.encode())
#             if item is not None and getattr(item, "value", None):
#                 parts = item.value.decode("utf-8").split("::")
#                 ttl, cached = int(parts[1]) - int(time.time()), parts[0]
#             else:
#                 ttl, cached = 0, None
#         else:
#             cached = await cache_client.get(cache_key)
#             ttl = await cache_client.ttl(cache_key)
#
#         logger.debug("cache read")
#     except Exception as e:
#         trace = get_traceback(e)
#         logger.error(f"Error retrieving cache key '{cache_key}': {str(e)}\n{trace}")
#         ttl, cached = 0, None
#
#     logger.info(f"cache_key={repr(cache_key)}, is_cached={repr(cached is not None)}, ttl={repr(ttl)}")
#     request.state.is_cached = cached is not None
#
#     if cached is None:
#         response: Response = await call_next(request)
#         response_body = [chunk async for chunk in response.body_iterator]
#         response.body_iterator = iterate_in_threadpool(iter(response_body))
#
#         logger.debug(f"status_code: {repr(response.status_code)}")
#
#         if response.status_code == 200:
#             if cache_control == "no-store":
#                 return response
#
#             max_age = (
#                 int(cache_control.split("=")[1])
#                 if cache_control and "max-age" in cache_control
#                 else settings.api_caching_time
#             )
#             if settings.api_cache_type == "memcached":
#                 max_age = int(time.time()) + max_age
#
#             try:
#                 if settings.api_cache_type == "memcached":
#                     value = f"{response_body[0].decode()}::{max_age}".encode()
#                     # await cache_client.set(cache_key.encode(), response_body[0], exptime=max_age)
#                     await cache_client.set(cache_key.encode(), value, exptime=max_age)
#                 else:
#                     await cache_client.set(cache_key, response_body[0].decode(), max_age)
#
#                 logger.debug("cache save")
#                 logger.info(f"cache_key={repr(cache_key)}, is_saved=1")
#             except Exception as e:
#                 trace = get_traceback(e)
#                 logger.error(f"Error setting cache key '{cache_key}': {str(e)}\n{trace}")
#
#             response.headers.update(
#                 {
#                     "Cache-Control": default_cache_control,
#                     "ETag": f"W/{hash(response_body[0])}",
#                     "X-Cache": "MISS",
#                 }
#             )
#
#         return response
#     else:
#         etag = f"W/{hash(cached)}"
#
#         if request.headers.get("if-none-match") == etag:
#             logger.info(f"if-none-match: {etag}")
#             return Response(status_code=status.HTTP_304_NOT_MODIFIED, headers={"ETag": etag})
#
#         headers = {
#             "Cache-Control": f"max-age={ttl}",
#             "ETag": etag,
#             "X-Cache": "HIT",
#         }
#         json_data_str = cached.decode("utf-8") if not isinstance(cached, str) else cached
#         logger.debug("result prepared")
#         # return StreamingResponse(iter([cached]), media_type="application/json", headers=headers)
#         return StreamingResponse(iter([json_data_str]), media_type="application/json", headers=headers)


@app.middleware("http")
async def jwt_token_middleware(request: Request, call_next):
    """Проверка JWT токена пользователя"""
    logger.info(f"request_path={request.url.path}, public_endpoints={repr(public_endpoints)}")

    if request.url.path in public_endpoints:
        logger.info("JWT: public endpoint")
        return await call_next(request)

    if request.method.lower() == "options":
        logger.info("JWT: OPTIONS method")
        return await call_next(request)

    try:
        if request.url.path in refresh_token_endpoints:
            auth_jwt = auth_dep()
            required_token_type = c.JWT_REFRESH_TOKEN_TYPE
            encoded_token = request.cookies.get(settings.authjwt_refresh_cookie_key)
        else:
            # auth_jwt = auth_dep(req=request)
            auth_jwt = auth_dep()
            required_token_type = c.JWT_ACCESS_TOKEN_TYPE
            # encoded_token = None
            encoded_token = request.cookies.get(settings.authjwt_access_cookie_key)

        user, verified_token = await verify_token(request, auth_jwt, required_token_type, encoded_token)
    except AuthJWTException as e:
        trace = get_traceback(e)
        logger.error(f"JWT: get token error {repr(e.__dict__)}\n{trace}")
        if not str(request.url).startswith(settings.backend_api_prefix):
            return RedirectResponse("/auth/sign-in")

        return CustomJSONResponse(
            status_code=UnauthorizedException.status_code,
            content=(
                UnauthorizedException(
                    code="jwt_authentication_error",
                    nested_code=e.message,
                    nested_translation_loader_key="libre_fastapi_jwt",
                )
                .get_content()
                .model_dump()
            ),
        )
    except Exception as e:
        trace = get_traceback(e)
        logger.error(f"JWT: undefined error {repr(e.__dict__)}\n{trace}")
        if not str(request.url).startswith(settings.backend_api_prefix):
            return RedirectResponse("/auth/sign-in")

        if isinstance(e, BackendException):
            return CustomJSONResponse(content=e.get_content().model_dump(), status_code=e.status_code)

        return CustomJSONResponse(
            status_code=UnauthorizedException.status_code,
            content=(
                UnauthorizedException(code="jwt_authentication_error", message_context={"error": str(e)})
                .get_content()
                .model_dump()
            ),
        )
    else:
        request.state.user_id = user.id
        request.state.user_time_zone = user.time_zone
        request.state.verified_token = verified_token
        with logger.contextualize(user_id=user.id):
            return await call_next(request)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Генерация уникального идентификатора и фиксация времени выполнения запроса"""
    request_id = request.headers.get("x-request-id") or uuid4().hex
    user_id = getattr(request.state, "user_id", "-")
    user_ip = get_client_ip_from_fastapi_request(request)
    user_agent = get_client_user_agent_from_fastapi_request(request)

    with logger.contextualize(
        app_id=request.state.app_id, request_id=request_id, user_id=user_id, user_ip=user_ip, user_agent=user_agent
    ):
        url = f"{request.url.path}{f'?{request.url.query}' if request.url.query else ''}"
        logger.info(f"BEGIN: {request.method} {url}")
        start_time = time.time()

        logger.info(f"request.headers: {repr(request.headers)}")
        logger.info(f"user_agent: {user_agent}")
        logger.info(f"user_ip::user_agent: {user_ip}::{user_agent}")

        request.state.request_id = request_id
        request.state.user_agent = user_agent

        response = await call_next(request)

        process_time = (time.time() - start_time) * 1000
        str_process_time = "{0:.2f}".format(process_time)
        logger.info(
            f"END: {request.method} {url}, completed_in={str_process_time} ms, status_code= {response.status_code}"
        )

        return response


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException) -> CustomJSONResponse:
    """Обработчик исключений класса AuthJWTException"""
    # return CustomJSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": exc.message})
    logger.info(f"exc: {repr(exc.__dict__)}")
    return CustomJSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(BackendException)
async def backend_exception_handler(request: Request, exc: BackendException) -> CustomJSONResponse:
    """Обработчик исключений класса BackendException и его потомков"""
    return CustomJSONResponse(status_code=exc.status_code, content=exc.get_content().model_dump())


@app.exception_handler(RequestValidationError)
@app.exception_handler(ValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError | ValidationError
) -> CustomJSONResponse:
    """Обработчик исключений классов RequestValidationError, ValidationError"""
    return CustomJSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=(
            UnprocessableEntityException(
                code="invalid_request_data_format",
                context={
                    "errors": pydantic_error_translator.translate(
                        errors=exc.errors(), locale=getattr(request.state, "locale", c.LOCALE_DEFAULT)
                    )
                },
            )
            .get_content()
            .model_dump()
        ),
    )


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    """Генерация документации Swagger UI с использованием статических файлов"""
    # return get_swagger_ui_html(
    #     openapi_url=f"{settings.backend_api_prefix}/openapi.json",
    #     title=app.title + " - Swagger UI",
    #     oauth2_redirect_url=f"{settings.backend_api_prefix}/docs/oauth2-redirect",
    #     swagger_js_url=f"{settings.backend_api_prefix}/static/js/swagger-ui-bundle.js",
    #     swagger_css_url=f"{settings.backend_api_prefix}/static/css/swagger-ui.css",
    #     swagger_favicon_url=f"{settings.backend_api_prefix}/static/images/fastapi-favicon.png",
    #     swagger_ui_parameters={"displayRequestDuration": True},
    # )
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=app.title + " - Swagger UI",
        oauth2_redirect_url="/docs/oauth2-redirect",
        swagger_js_url="/static/js/swagger-ui-bundle.js",
        swagger_css_url="/static/css/swagger-ui.css",
        swagger_favicon_url="/static/images/fastapi-favicon.png",
        swagger_ui_parameters={"displayRequestDuration": True},
    )


@app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
async def swagger_ui_redirect() -> HTMLResponse:
    """Выполнение OAuth2 редиректа для Swagger UI"""
    return get_swagger_ui_oauth2_redirect_html()


@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    """Генерация документации Redoc с использованием статических файлов"""
    # return get_redoc_html(
    #     openapi_url=f"{settings.backend_api_prefix}/openapi.json",
    #     title=app.title + " - ReDoc",
    #     redoc_js_url=f"{settings.backend_api_prefix}/static/js/redoc.standalone.js",
    #     redoc_favicon_url=f"{settings.backend_api_prefix}/static/images/fastapi-favicon.png",
    #     with_google_fonts=False,
    # )
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=app.title + " - ReDoc",
        redoc_js_url="/static/js/redoc.standalone.js",
        redoc_favicon_url="/static/images/fastapi-favicon.png",
        with_google_fonts=False,
    )


# def custom_openapi():
#     if app.openapi_schema:
#         return app.openapi_schema
#
#     openapi_schema = get_openapi(
#         title="Custom title",
#         version="2.5.0",
#         description="This is a very custom OpenAPI schema",
#         routes=app.routes,
#     )
#
#     # Custom documentation libre-fastapi-jwt
#     headers = {
#         "name": "Authorization",
#         "in": "header",
#         "required": True,
#         "schema": {"title": "Authorization", "type": "string"},
#     }
#
#     # Get routes from index 4 because before that fastapi define router for /openapi.json, /redoc, /docs, etc
#     # Get all router where operation_id is authorize
#     router_authorize = [route for route in app.routes[4:] if route.operation_id == "authorize"]
#
#     for route in router_authorize:
#         method = list(route.methods)[0].lower()
#         try:
#             # If the router has another parameter
#             openapi_schema["paths"][route.path][method]["parameters"].append(headers)
#         except Exception:
#             # If the router doesn't have a parameter
#             openapi_schema["paths"][route.path][method].update({"parameters": [headers]})
#
#     app.openapi_schema = openapi_schema
#     return app.openapi_schema
#
#
# app.openapi = custom_openapi
