# -*- coding: UTF-8 -*-
"""
@Summary : backlog
@Author  : Rey, wangliang
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
def create_backlog(data: dict, receivers: list, creator: str):

    if not isinstance(receivers, list):
        return ValidationFailed(ValidationFailedDetailEnum.RECEIVER_TYPE.value)

    f = BacklogForm(data)
    if not f.is_valid():
        return ValidationFailed(f.errors)
    clean_data = f.cleaned_data
    clean_data['creator'] = creator
    clean_data['data'] = data.get("data")
    clean_data.pop("receiver")
    clean_data["batch"] = uuid.uuid4()
    backlog_notices = [Backlog(**clean_data, receiver=receiver, ) for receiver in receivers]
    backlog_objs = Backlog.objects.bulk_create(backlog_notices)

    return JsonResponse(data={'id': [backlog_notice.id for backlog_notice in backlog_objs]})


# Gets the current user backlog number
def get_backlog(receiver: str):
    if not Backlog.objects.filter(receiver=receiver).exists():
        return NotFound()

    backlog_num = Backlog.objects.filter(receiver=receiver, is_done=False).count()
    processed_num = Backlog.objects.filter(receiver=receiver, is_done=True).count()
    initiator_num = Backlog.objects.filter(receiver=receiver, initiator=receiver).count()
    total = backlog_num + processed_num
    data = {
        "pending_num": backlog_num,
        "processed_num": processed_num,
        "initiator_num": initiator_num,
        "total": total
    }
    return JsonResponse(data)


@require_http_methods(["GET", "POST"])
def backlog(request: HttpRequest):
    if not request.user.is_authenticated:
        return AuthFailed()

    if request.method == "POST":
        data = json.loads(request.body)
        receivers = data.get("receiver")

        return create_backlog(data, receivers, str(request.user.pk))

    receiver = request.user.pk
    return get_backlog(receiver)


def check_params(params: dict):
    """参数校验"""

    backlog_type = params.get("backlog_type", "0")
    start = params.get("start")
    end = params.get("end")
    flow_status = params.get("flow_status")
    handle_status = params.get("handle_status")
    data_format = r'^\d{4}-\d{2}-\d{2}\s\d{1,2}:\d{1,2}:\d{1,2}$'

    if backlog_type not in ("0", "1", "2", "3", "4") or not backlog_type.isdigit():
        return False, ValidationFailed(ValidationFailedDetailEnum.BACKLOG_TYPE.value)

    if start:
        if not re.match(data_format, start):
            return False, ValidationFailed(ValidationFailedDetailEnum.TIME_TYPE.value)

    if end:
        if not re.match(data_format, end):
            return False, ValidationFailed(ValidationFailedDetailEnum.TIME_TYPE.value)
        if start and re.match(data_format, start):
            if end < start:
                return False, ValidationFailed(ValidationFailedDetailEnum.TIME_TYPE.value)

    if flow_status:
        if not flow_status.isdigit() or flow_status not in ("0", "1", "2", "3", "4"):
            return False, ValidationFailed(ValidationFailedDetailEnum.FLOW_TYPE.value)

    if handle_status:
        if handle_status not in ("0", "1", "2") or not handle_status.isdigit():
            return False, ValidationFailed(ValidationFailedDetailEnum.HANDLE_TYPE.value)

    return True, params


def filter_conditions(receiver: str, params: dict):
    """条件过滤器"""
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

    return con


#  The backlog message list
def list_backlog(page: int, size: int, params: dict, receiver: str):
    is_valid, params = check_params(params)
    if not is_valid:
        return params

    queryset = Backlog.objects.filter(receiver=receiver)
    con = filter_conditions(receiver, params)
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
                "initiator_name": item.initiator_name,
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

    if not page.isdigit():
        return ValidationFailed(ValidationFailedDetailEnum.PAGE.value)

    if not size.isdigit():
        return ValidationFailed(ValidationFailedDetailEnum.SIZE.value)

    is_valid, params = check_params(params)
    if not is_valid:
        return params

    return list_backlog(int(page), int(size), params, str(request.user.pk))


# The backlog message is set to read
def backlog_read(pk: int, receiver: str):
    if not Backlog.objects.filter(receiver=receiver).exists():
        return NotFound()
    if not Backlog.objects.filter(pk=pk).exists():
        return NotFound()
    Backlog.objects.filter(receiver=receiver, id=pk).update(is_read=True, read_at=timezone.now())
    return JsonResponse(data={})


@require_http_methods(["PUT"])
def read_backlog(request: HttpRequest, pk: int):
    if not request.user.is_authenticated:
        return AuthFailed()

    return backlog_read(pk, str(request.user.pk))


def handlers(receiver: str):
    backlog_obj: Backlog = Backlog.objects.filter(initiator=receiver).first()
    if not backlog_obj:
        return NotFound()
    handler_infos: Backlog = Backlog.objects.filter(initiator=receiver).values("candidates")
    handler_set = set()
    for handler in handler_infos:
        handler_set |= (set(handler.get("candidates")))
    return JsonResponse({"handler_list": list(handler_set)})


@require_http_methods(["GET"])
def handler_list(request: HttpRequest):
    if not request.user.is_authenticated:
        return AuthFailed()

    return handlers(str(request.user.pk))


# handle the current node backlog
def current_node_backlog(pk: int, node_handlers: list, receiver: str):
    if not Backlog.objects.filter(receiver=receiver, id=pk).exists():
        return NotFound()
    batch = Backlog.objects.get(id=pk).batch
    Backlog.objects.filter(batch=batch).update(
        is_done=True, done_at=timezone.now(),
        handler=node_handlers, candidates=node_handlers
    )

    return JsonResponse({})


@require_http_methods(["PUT"])
def handle_backlog(request: HttpRequest, pk: int):
    if not request.user.is_authenticated:
        return AuthFailed()
    node_handlers = json.loads(request.body).get("node_handlers")

    return current_node_backlog(pk, node_handlers, str(request.user.pk))
