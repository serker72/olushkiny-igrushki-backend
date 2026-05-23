from fastapi.security import HTTPBearer
from libre_fastapi_jwt import AuthJWTBearer

# security = HTTPBearer()
security = AuthJWTBearer()
