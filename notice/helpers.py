# -*- coding: UTF-8 -*-
"""
@Summary : docstr
@Author  : Rey
@Time    : 2022-04-02 10:58:14
"""
from abc import ABCMeta, abstractmethod

from django.apps import apps


class BaseGetAllowedTypes(metaclass=ABCMeta):
    """include receiver types and notice types"""
    def __init__(self, receiver_id) -> None:
        if not isinstance(receiver_id, int):
            raise TypeError('invalid type: receiver user id')
        self.receiver_id = receiver_id
        self.done_receiver_type = list()
        self.done_notice_type = list()

    @staticmethod
    def get_all_notice_type_names():
        return dict(apps.get_model('notice.NoticeType').objects.all().values_list('name', 'id'))

    @staticmethod
    def get_all_receiver_type_names():
        return dict(apps.get_model('notice.ReceiverType').objects.all().values_list('name', 'id'))

    @abstractmethod
    def judge(self):
        pass

