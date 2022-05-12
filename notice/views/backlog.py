# -*- coding: UTF-8 -*-
"""
@Summary : backlog
@Author  : Rey
@Time    : 2022-04-27 13:25:25
"""
import json
import math

from django.utils import timezone
from django.http import JsonResponse, HttpRequest
from django.db.models import Q
from django.views.decorators.http import require_http_methods

from notice.forms import BacklogForm
from notice.models import Backlog
from notice.response import AuthFailed, NotFound, ValidationFailed, ValidationFailedDetailEnum
from notice.settings import NOTICE_DATETIME_FORMAT


# Add new backlog
def create_backlog(data: dict, creator: str, receivers: list):
    f = BacklogForm(data)
    if not f.is_valid():
        return ValidationFailed(f.errors)
    data = f.cleaned_data
    data['creator'] = creator
    data.pop("receiver")
    backlog_notices = [Backlog(**data, receiver=receiver) for receiver in receivers]
    backlog_objs = Backlog.objects.bulk_create(backlog_notices)

    return JsonResponse(data={'id': [backlog_notice.id for backlog_notice in backlog_objs]})


# Gets the current user backlog number
def get_backlog(receiver: str):
    num = Backlog.objects.filter(receiver=receiver, is_done=False).count()
    return JsonResponse({"num": num})


@require_http_methods(["GET", "POST"])
def backlog(request: HttpRequest):
    if not request.user.is_authenticated:
        return AuthFailed()

    if request.method == "POST":
        data = request.POST
        receivers = request.POST.get("receiver").split(",")
        return create_backlog(data, str(request.user.pk), receivers)

    receiver = request.user.pk
    return get_backlog(receiver)


#  The backlog message list
def list_backlog(receiver: str, page: int, size: int, params: dict):
    queryset = Backlog.objects.filter(receiver=receiver)
    # 全部待办：0 1 待办--待处理 2 待办--已处理  3 待办--我发起的
    # 4.待办提醒 5.首页列表待办（通过控制page、size控制页面展示多少条数据）
    if params:
        for key, value in params.items():
            if key == "backlog_type":
                backlog_type = params.get("backlog_type")
                if backlog_type in ("0", "4", "5"):
                    queryset = queryset

                elif backlog_type == "1":
                    queryset = queryset.filter(is_done=False)

                elif backlog_type == "2":
                    queryset = queryset.filter(is_done=True)

                elif backlog_type == "3":
                    queryset = queryset.filter(initiator=receiver)

                else:
                    raise ValidationFailed("backlog_type值错误")

            if key == "handle_status":
                handle_status = params.get("handle_status")
                queryset = queryset.filter(is_done=handle_status)

            if key == "keyword":
                keyword = params.get("keyword")
                queryset = queryset.filter(
                    Q(obj_name__contains=keyword) |
                    Q(obj_key__contains=keyword) |
                    Q(initiator__contains=keyword)
                )

            if key == "start":
                start = params.get("start")
                queryset = queryset.filter(created_at=start)

            if key == "end":
                end = params.get("end")
                queryset = queryset.filter(created_at=end)

            if key == "handler":
                handler = params.get("handler")
                queryset = queryset.filter(handler=handler)

            if key == "flow_status":
                flow_status = params.get("flow_status")
                queryset = queryset.filter(obj_status=flow_status)

    total = queryset.count()
    max_page = math.ceil(total / size)

    if page > max_page:
        items = []
    else:
        items = [
            {
                "id": item.id,
                "created_at": item.created_at.strftime(NOTICE_DATETIME_FORMAT),
                "is_done": item.is_done,
                "creator": item.creator,
                "handler": item.handler,
                "initiator": item.initiator,
                "obj_key": item.obj_key,
                "obj_name": item.obj_name,
                "obj_status": item.obj_status,
                "data": {} if not item.data else item.data,
                "is_read": item.is_read
            }
            for item in queryset.order_by('-id')[(page - 1) * size: page * size]
        ]

    resp = {
        'total': total,
        'max_page': max_page,
        'page': page,
        'items': items,
        "size": size
    }
    return JsonResponse(data=resp)


@require_http_methods(['GET'])
def backlogs(request: HttpRequest):
    # if not request.user.is_authenticated:
    #     return AuthFailed()
    params = request.GET
    page = params.get('page', '1')
    size = params.get('size', '10')

    if not page.isdigit():
        return ValidationFailed(ValidationFailedDetailEnum.PAGE.value)
    if not size.isdigit():
        return ValidationFailed(ValidationFailedDetailEnum.SIZE.value)

    page = int(page)
    size = int(size)
    # 写成动态的（根据前端传参动态改变）
    return list_backlog("1", page, size, params)
    #return list_backlog(str(request.user.pk), page, size, params)


# The backlog message is set to read
def backlog_read(receiver: str, pk: int):
    Backlog.objects.filter(receiver=receiver, id=pk).update(is_read=True, read_at=timezone.now())
    return JsonResponse(data={})


@require_http_methods(["PUT"])
def read_backlog(request: HttpRequest, pk: int):
    if not request.user.is_authenticated:
        return AuthFailed()

    return backlog_read(str(request.user.pk), pk)


# handle the current node backlog
def current_node_backlog():
    pass


@require_http_methods(["PUT"])
def handle_backlog():
    pass
