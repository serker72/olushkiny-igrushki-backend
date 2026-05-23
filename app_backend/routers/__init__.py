# isort: off
from .base import BaseRouter, BaseUIRouter

# isort: on
from .auth import AuthRouter, AuthUIRouter
from .categories import CategoryUIRouter
from .dashboard import DashboardUIRouter
from .files import FileRouter
from .modules import ModuleRouter
from .systems import SystemRouter
from .users import UserRouter

__all__ = [
    "AuthRouter",
    "AuthUIRouter",
    "BaseRouter",
    "CategoryUIRouter",
    "DashboardUIRouter",
    "FileRouter",
    "ModuleRouter",
    "SystemRouter",
    "UserRouter",
]
