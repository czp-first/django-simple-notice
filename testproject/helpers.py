# -*- coding: UTF-8 -*-
"""
@Summary : docstr
@Author  : Rey
@Time    : 2022-04-02 10:58:14
"""
from notice.helpers import BaseGetAllowedTypes


class ExampleGetAllowedViewTypes(BaseGetAllowedTypes):

    def __init__(self, receiver) -> None:
        super().__init__()
        self.receiver = receiver

    def judge_notice_types(self) -> list:
        allowed_notice_type_ids = []

        self.done_notice_type.append('system')
        if self.receiver:
            allowed_notice_type_ids.append(self.all_notice_type_names['system'])

        self.done_notice_type.append('private')
        if self.receiver:
            allowed_notice_type_ids.append(self.all_notice_type_names['private'])

        return allowed_notice_type_ids

    def judge_notice_receiver_types(self) -> list:
        allowed_receiver_type_ids = []

        self.done_receiver_type.append('all')
        if self.receiver:
            allowed_receiver_type_ids.append(self.all_receiver_type_names['all'])

        self.done_receiver_type.append('part')
        # if self.receiver_id:
        #     allowed_receiver_type_ids.append(all_receiver_types['part'])

        return allowed_receiver_type_ids
