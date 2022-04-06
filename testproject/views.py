# -*- coding: UTF-8 -*-
"""
@Summary : views
@Author  : Rey
@Time    : 2022-04-02 18:18:19
"""
from rest_framework.views import APIView

from notice.views.admin import notice as notice_view


class ListNoticeView(APIView):
    def get(self, request, *args, **kwargs):
        return notice_view(request)
