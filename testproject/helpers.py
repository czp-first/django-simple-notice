# -*- coding: UTF-8 -*-
"""
@Summary : docstr
@Author  : Rey
@Time    : 2022-04-02 10:58:14
"""
from notice.helpers import BaseGetAllowedTypes


class ExampleGetAllowedViewTypes(BaseGetAllowedTypes):

    def judge(self):
        all_notice_types = self.get_all_notice_type_names()
        allowed_notice_type_ids = []

        self.done_notice_type.append('system')
        if self.receiver_id:
            allowed_notice_type_ids.append(all_notice_types['system'])

        self.done_notice_type.append('private')
        if self.receiver_id:
            allowed_notice_type_ids.append(all_notice_types['private'])

        if set(all_notice_types) - set(self.done_notice_type) != set():
            raise NotImplementedError(
                'not judge all existed notice types: to judge={}'.format(set(all_notice_types) - set(self.done_notice_type))
            )

        all_receiver_types = self.get_all_receiver_type_names()
        allowed_receiver_type_ids = []

        self.done_receiver_type.append('all')
        if self.receiver_id:
            allowed_receiver_type_ids.append(all_receiver_types['all'])

        self.done_receiver_type.append('part')
        if self.receiver_id:
            allowed_receiver_type_ids.append(all_receiver_types['part'])

        if set(all_receiver_types) - set(self.done_receiver_type) != set():
            raise NotImplementedError(
                'not judge all existed receiver types: to judge={}'.format(set(all_receiver_types) - set(self.done_receiver_type))
            )

        return allowed_notice_type_ids, allowed_receiver_type_ids
