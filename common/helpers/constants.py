# Locales
LOCALE_DEFAULT = "ru_RU"

# Password composition
PASSWORD_COMPOSITION_ASCII_LOWERCASE = "ascii_lowercase"
PASSWORD_COMPOSITION_ASCII_UPPERCASE = "ascii_uppercase"
PASSWORD_COMPOSITION_DIGITS = "digits"
PASSWORD_COMPOSITION_PUNCTUATION = "punctuation"

# Module Codes
MODULE_CODE_FILES = "files"
MODULE_CODE_USERS = "users"
MODULE_CODE_USER_AUTHORIZATION_CODES = "user_authorization_codes"
MODULE_CODE_USER_REGISTRATION_CODES = "user_registration_codes"
MODULE_CODE_USER_DEVICES = "user_devices"
MODULE_CODE_DEVICES = "devices"
MODULE_CODE_MODULES = "modules"
MODULE_CODE_SYSTEMS = "systems"
MODULE_CODE_ROLES = "roles"
MODULE_CODE_ORGANIZATIONS = "organizations"

# Entity States
STATE_ANNULLED = "annulled"
STATE_APPROVED = "approved"
STATE_BLOCKED = "blocked"
STATE_CANCELLED = "cancelled"
STATE_COMPLETED = "completed"
STATE_DELETED = "deleted"
STATE_DRAFT = "draft"
STATE_EXPIRED = "expired"
STATE_PENDING = "pending"
STATE_REJECTED = "rejected"
STATE_UNCOMPLETED = "uncompleted"
STATE_UNVERIFIED = "unverified"
STATE_PUBLISHED = "published"
STATE_ARCHIVED = "archived"

# User wallet transaction types
TRANSACTION_TYPE_TASK_PAY = "task_pay"
TRANSACTION_TYPE_FINE = "fine"
TRANSACTION_TYPE_WITHDRAWAL = "withdrawal"

# SQLAlchemy
SA_FILTER_OPERATOR_AND = "and"
SA_FILTER_OPERATOR_OR = "or"
SA_SORT_ORDER_ASC = "ASC"
SA_SORT_ORDER_DESC = "DESC"

# Formats
FORMAT_DATE_TIME = "%d.%m.%Y %H:%M:%S"
FORMAT_DATE = "%d.%m.%Y"
FORMAT_LOG_DEFAULT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
FORMAT_LOG_APP = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<level>{extra[app_id]: <7}</level> | "
    "<level>{extra[request_id]: <32}</level> | "
    "<level>{extra[user_ip]: <15}</level> | "
    "<level>{extra[user_id]: <6}</level> | "
    "<level>{extra[user_agent]}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)
FORMAT_LOG_QUEUE_PROCESSING = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    "<level>{extra[p_id]: <40}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

# JWT
JWT_ACCESS_TOKEN = "access_token"
JWT_REFRESH_TOKEN = "refresh_token"
JWT_ACCESS_TOKEN_JTI = "access_token_jti"
JWT_ACCESS_TOKEN_TITLE = "доступа"
JWT_REFRESH_TOKEN_TITLE = "обновления"
JWT_ACCESS_TOKEN_TYPE = "access"
JWT_REFRESH_TOKEN_TYPE = "refresh"

# Actions
ACTION_APPROVAL = "approval"
ACTION_PUBLISHING = "publishing"
ACTION_ARCHIVING = "archiving"
ACTION_BLOCKING = "blocking"
ACTION_CHANGING_ROLES = "changing_roles"
ACTION_CREATE = "create"
ACTION_DEBITING_FINE_AMOUNT = "debiting_fine_amount"
ACTION_DEBITING_WITHDRAWAL_AMOUNT = "debiting_withdrawal_amount"
ACTION_DELETE = "delete"
ACTION_REJECTING = "rejecting"
ACTION_TRANSFER_TO_CANCELLED = "transfer_to_cancelled"
ACTION_TRANSFER_TO_COMPLETED = "transfer_to_completed"
ACTION_TRANSFER_TO_DEFERRED = "transfer_to_deferred"
ACTION_TRANSFER_TO_PARTIAL_COMPLETED = "transfer_to_partial_completed"
ACTION_TRANSFER_TO_REJECTED = "transfer_to_rejected"
ACTION_TRANSFER_TO_RESERVED = "transfer_to_reserved"
ACTION_TRANSFER_TO_VERIFICATION = "transfer_to_verification"
ACTION_TRANSFER_TO_WORK = "transfer_to_work"
ACTION_UNBLOCKING = "unblocking"
ACTION_UPDATE = "update"
ACTION_VERIFICATION = "verification"
ACTION_VIEW = "view"

# Redis keys
REDIS_KEY_SYSTEM_INFO = "system_info"
CACHE_PREFIX = "levelcraft-fastapi-cache"
REDIS_KEY_JWT_ACTIVELIST_HASH_PATTERN = "jwt:activelist:{user_id}:*"
REDIS_KEY_JWT_ACTIVELIST_HASH = "jwt:activelist:{user_id}:{user_device_id}"
REDIS_KEY_JWT_ACTIVELIST_KEY = "{type}:{jti}"
REDIS_KEY_JWT_BLACKLIST = "jwt:blacklist:{type}:{jti}"
REDIS_KEY_USER_LIST_HASH = "user:list"
REDIS_KEY_USER_LIST_KEY = "user:{user_id}"

# Time zones
USER_DEFAULT_TIME_ZONE = "Europe/Moscow"

# User Login Fields
USER_LOGIN_EMAIL = "email"
USER_LOGIN_PHONE = "phone"

# User Login Title Fields
USER_LOGIN_TITLE_EMAIL = "адрес email"
USER_LOGIN_TITLE_PHONE = "номер телефона"

# Application codes
APPLICATION_CODE_COMMON = "common"
APPLICATION_CODE_BACKEND = "backend"
APPLICATION_CODE_QUEUE_PROCESSING = "queue_processing"

# RabbitMQ Queue Names
RABBITMQ_QUEUE_EMAIL_MESSAGES = "email_messages"

# Form messages
FORM_FIELD_REQUIRED_MESSAGE = "Это поле является обязательным."
FORM_FIELD_JSON_SCHEMA_MISSING_MESSAGE = "Значение поля не соответствует схеме JSON."
FORM_FIELD_REGEXP_MISSING_MESSAGE = "Значение поля не соответствует регулярному выражению"
FORM_FIELD_MIN_LENGTH_MESSAGE = "Количество символов в значении поля - %(min)."
FORM_FIELD_MAX_LENGTH_MESSAGE = "Количество символов в значении поля - %(max)."
FORM_FIELD_MIN_AND_MAX_LENGTH_MESSAGE = "Количество символов в значении поля - от %(min) до %(max)."
FORM_FIELD_MIN_AND_MAX_MESSAGE = "Значение поля должно быть в интервале от %(min)s до %(max)s."
