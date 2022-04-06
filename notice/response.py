# -*- coding: UTF-8 -*-
"""
@Summary : response and error msg
@Author  : Rey
@Time    : 2022-04-03 11:09:46
"""
from enum import Enum

from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _


class BaseFailedJsonResponse(JsonResponse):
    status_code = 400
    default_detail = 'bad request'
    default_code = 'error'

    def __init__(self,
        detail=None,
        code=None,
        encoder=DjangoJSONEncoder,
        safe=True,
        json_dumps_params=None,
        **kwargs,):
        if detail is None:
            detail = self.default_detail
        if code is None:
            code = self.default_code
        super().__init__({'detail': detail, 'code': code}, encoder, safe, json_dumps_params, **kwargs)



class ValidationFailed(BaseFailedJsonResponse):
    status_code = 400
    default_detail = 'invalid input'
    default_code = 'invalid'


class AuthFailed(BaseFailedJsonResponse):
    status_code = 401
    default_detail = 'Auth Failed'
    default_code = 'authentication_failed'


class NotFound(BaseFailedJsonResponse):
    status_code = 404
    default_detail = 'Not Found'
    default_code = 'not_found'


class ValidationFailedDetailEnum(Enum):
    NOTICE_TYPE = _('Invalid Notice Type')
    RECEIVER_TYPE = _('Invalid Receiver Type')
    SEND_WAY = _('Invalid Send Way')
    PUBLISH_TIME = _('Invalid Publish Time')
    PAGE = _('Invalid Page')
    SIZE = _('Invalid Size')

    OUTDATE = _('Cant Set Time Which Is Out Of Date')
    CHANGE_NOT_DRAFT = _('Cant Change Notice Which Is Not Draft')
    CHANGE_DRAFT_TIMING = _('Cant Change Timing Which Is Draft')
    DELETE_DRAFT_TIMING = _('Cant Delete Timing Which Is Draft')
    DELETE_NOT_DRAFT = _('Cant Delete Notice Which Is Not Draft')
    CHANGE_PUBLISHED = _('Cant Change Notice Which Has Been published')
    DELETE_PUBLISHED = _('Cant Delete Notice Which Has Been published')
