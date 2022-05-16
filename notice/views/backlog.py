# -*- coding: UTF-8 -*-
"""
@Summary : backlog
@Author  : Rey
@Time    : 2022-04-27 13:25:25
"""
import re
import json
import math
import uuid

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
    data["batch"] = uuid.uuid4()
    backlog_notices = [Backlog(**data, receiver=receiver, ) for receiver in receivers]
    backlog_objs = Backlog.objects.bulk_create(backlog_notices)

    return JsonResponse(data={'id': [backlog_notice.id for backlog_notice in backlog_objs]})


# Gets the current user backlog number
def get_backlog(receiver: str):
    if not Backlog.objects.filter(receiver=receiver).exists():
        return NotFound()
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
    # 全部待办 ：0
    # 1 待办--待处理 2 待办--已处理  3 待办--我发起的
    # 4 待办提醒 首页列表待办（通过控制page、size控制页面展示多少条数据）
    con = Q()
    if params:
        for key, value in params.items():
            q = Q()
            q.connector = 'OR'
            condition = []
            if key == "keyword":
                condition = [
                    ("obj_key__contains", value),
                    ("obj_name__contains", value),
                    ("initiator", value)
                ]

            if key == "backlog_type" and value != "0":
                conditions = {
                    "1": ("is_done", False),
                    "2": ("is_done", True),
                    "3": ("initiator", receiver),
                    "4": ("is_done", False)
                }
                condition = [
                    conditions.get(value)
                ]

            if key == "start":
                condition = [
                        ("created_at__gte", value)
                ]

            if key == "end":
                condition = [
                    ("created_at__lte", value)
                ]

            if key == "flow_status" and value != "0":
                flow_conditions = {
                    "1": "进行中",
                    "2": "通过",
                    "3": "驳回",
                    "4": "撤回"
                }
                condition = [
                    ("obj_status", flow_conditions.get(value))
                ]

            if key == "handle_status" and value != "0":
                handle_conditions = {
                    "1": False,
                    "2": True
                }
                condition = [
                    ("is_done", handle_conditions.get(value))
                ]

            if key == "handler" and value != "0":
                condition = [("candidates__contains", list(value))]

            q.children.extend(condition)
            con.add(q, "AND")

    queryset = queryset.filter(con)
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
                "is_read": item.is_read,
                "candidates": item.candidates
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
    if not request.user.is_authenticated:
        return AuthFailed()
    params = request.GET.dict()
    page = params.pop('page', "1")
    size = params.pop('size', "10")
    backlog_type = params.get("backlog_type", "0")
    start = params.get("start")
    end = params.get("end")
    flow_status = params.get("flow_status")
    handle_status = params.get("handle_status")
    data_format = r'^\d{4}-\d{2}-\d{2}\s\d{1,2}:\d{1,2}:\d{1,2}$'

    if backlog_type not in ("0", "1", "2", "3", "4") or not backlog_type.isdigit():
        return ValidationFailed(ValidationFailedDetailEnum.BACKLOG_TYPE.value)

    if not page.isdigit():
        return ValidationFailed(ValidationFailedDetailEnum.PAGE.value)

    if not size.isdigit():
        return ValidationFailed(ValidationFailedDetailEnum.SIZE.value)

    if start:
        if not re.match(data_format, start):
            return ValidationFailed(ValidationFailedDetailEnum.TIME_TYPE.value)

    if end:
        if not re.match(data_format, end):
            return ValidationFailed(ValidationFailedDetailEnum.TIME_TYPE.value)
        if start and re.match(data_format, start):
            if end < start:
                return ValidationFailed(ValidationFailedDetailEnum.TIME_TYPE.value)

    if flow_status:
        if not flow_status.isdigit() or flow_status not in ("0", "1", "2", "3", "4"):
            return ValidationFailed(ValidationFailedDetailEnum.BACKLOG_TYPE.value)

    if handle_status:
        if handle_status not in ("0", "1", "2") or not handle_status.isdigit():
            return ValidationFailed(ValidationFailedDetailEnum.BACKLOG_TYPE.value)

    return list_backlog(str(request.user.pk), int(page), int(size), params)


# The backlog message is set to read
def backlog_read(receiver: str, pk: int):
    Backlog.objects.filter(receiver=receiver, id=pk).update(is_read=True, read_at=timezone.now())
    return JsonResponse(data={})


@require_http_methods(["PUT"])
def read_backlog(request: HttpRequest, pk: int):
    if not request.user.is_authenticated:
        return AuthFailed()

    return backlog_read(str(request.user.pk), pk)


def handlers(receiver: str):
    backlog_obj: Backlog = Backlog.objects.filter(initiator=receiver).only("candidates").first()
    if not backlog_obj:
        return NotFound()
    return JsonResponse({"handler_list": backlog_obj.handler})


@require_http_methods(["GET"])
def handler_list(request: HttpRequest):
    if not request.user.is_authenticated:
        return AuthFailed()

    return handlers(str(request.user.pk))


# handle the current node backlog
def current_node_backlog(receiver: str, pk: int, node_handlers: list):
    if not Backlog.objects.filter(receiver=receiver, id=pk).exists():
        return NotFound()
    batch = Backlog.objects.get(id=pk).batch
    Backlog.objects.filter(batch=batch).update(
        is_done=True, done_at=timezone.now(),
        handler=node_handlers, candidates=node_handlers,
    )

    return JsonResponse({})


@require_http_methods(["PUT"])
def handle_backlog(request: HttpRequest, pk: int):
    if not request.user.is_authenticated:
        return AuthFailed()
    node_handlers = json.loads(request.body).get("node_handlers")

    return current_node_backlog(str(request.user.pk), pk, node_handlers)
