# -*- coding: UTF-8 -*-
"""
@Summary : app的配置
@Author  : Rey
@Time    : 2022-03-30 11:58:02
"""
from importlib import import_module

from django.conf import settings

from notice.helpers import BaseGetAllowedTypes


NOTICE_CREATOR_MODEL = getattr(settings, 'NOTICE_CREATOR_MODEL', settings.AUTH_USER_MODEL)
NOTICE_RECEIVER_MODEL = getattr(settings, 'NOTICE_RECEIVER_MODEL', settings.AUTH_USER_MODEL)
NOTICE_DATETIME_FORMAT = getattr(settings, 'NOTICE_DATETIME_FORMAT', '%Y-%m-%d %H:%M:%S')

def get_notice_allowed_types_cls():
    cls_conf = getattr(settings, 'NOTICE_ALLOWED_TYPED_CLASS')
    if not cls_conf or not isinstance(cls_conf, dict) or 'module' not in cls_conf or 'class' not in cls_conf:
        raise NotImplementedError('please conf notice allowed types class correctly!')
    module = import_module(cls_conf['module'])
    cls = getattr(module, cls_conf['class'])
    if not issubclass(cls, BaseGetAllowedTypes):
        raise NotImplementedError('please implement notice allowed types class correctly!')
    return cls

NOTICE_ALLOWED_TYPED_CLASS = get_notice_allowed_types_cls()
