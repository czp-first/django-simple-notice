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
    def __init__(self) -> None:
        self.done_receiver_type = list()
        self.done_notice_type = list()
        self._all_notice_type_names = None
        self._all_receiver_type_names = None

    @property
    def all_notice_type_names(self):
        if not self._all_notice_type_names:
            self._all_notice_type_names = dict(apps.get_model('notice.NoticeType').objects.all().values_list('name', 'id'))
        return self._all_notice_type_names

    @property
    def all_receiver_type_names(self):
        if not self._all_receiver_type_names:
            self._all_receiver_type_names = dict(apps.get_model('notice.ReceiverType').objects.all().values_list('name', 'id'))
        return self._all_receiver_type_names

    @abstractmethod
    def judge_notice_receiver_types(self) -> list:
        pass

    @abstractmethod
    def judge_notice_types(self) -> list:
        pass

    def judge(self):
        if not (set(self.all_notice_type_names) - set(self.done_notice_type)):
            raise NotImplementedError(
                'not judge all existed notice types: to judge={}'.format(set(self.all_notice_type_names) - set(self.done_notice_type))
            )
        if not (set(self.all_receiver_type_names) - set(self.done_receiver_type)):
            raise NotImplementedError(
                'not judge all existed receiver types: to judge={}'.format(set(self.all_receiver_type_names) - set(self.done_receiver_type))
            )
        return self.judge_notice_types(), self.judge_notice_receiver_types()
