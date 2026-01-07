from app_backend.services.base import BaseService
from common.models import Action


class ActionService(BaseService):
    model_class = Action
    is_collection_paginate = False
