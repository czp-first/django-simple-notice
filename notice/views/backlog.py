# -*- coding: UTF-8 -*-
"""
@Summary : backlog
@Author  : Rey, wangliang
@Time    : 2022-04-27 13:25:25
"""

from datetime import datetime
import json
import math
import re
import uuid

from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse, HttpRequest
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from notice.forms import BacklogForm, HandleBacklogForm, HandleObjForm
from notice.models import Backlog
from notice.response import AuthFailed, NotFound, ValidationFailed, ValidationFailedDetailEnum
from notice.settings import NOTICE_DATETIME_FORMAT


def create_backlog(data: dict, creator: str):
    """batch create backlog

    :param dict data: data
    :param str creator: creator
    :return _type_: _description_
    """

    f = BacklogForm(data)
    if not f.is_valid():
        return ValidationFailed(f.errors)
    cleaned_data = f.cleaned_data
    cleaned_data['creator'] = creator
    cleaned_data['data'] = data.get('data')
    receivers = cleaned_data.pop('receivers')
    cleaned_data['batch'] = cleaned_data['batch'] if cleaned_data['batch'] else uuid.uuid4()
    backlog_notices = [Backlog(**cleaned_data, receiver=receiver) for receiver in receivers]
    backlog_objs = Backlog.objects.bulk_create(backlog_notices)

    return JsonResponse(data={'id': [backlog_notice.id for backlog_notice in backlog_objs]})


def get_backlogs_statistics(receiver: str):
    """backlogs statistics

    :param str receiver: _description_
    :return _type_: _description_
    """

    undo = Backlog.objects.filter(receiver=receiver, is_done=False).count()
    done = Backlog.objects.filter(receiver=receiver, is_done=True).count()
    total = undo + done
    data = {
        'undo': undo,
        'done': done,
        'total': total,
    }
    return JsonResponse(data)


@require_http_methods(['GET', 'POST'])
def backlog(request: HttpRequest):
    if not request.user.is_authenticated:
        return AuthFailed()
    if request.method == 'POST':
        data = json.loads(request.body)
        return create_backlog(data, str(request.user.pk))

    receiver = request.user.pk
    return get_backlogs_statistics(str(receiver))


def check_params(params: dict):
    """参数校验"""

    backlog_type = params.get('backlog_type', 'all')
    start = params.get('start')
    end = params.get('end')
    data_format = r'^\d{4}-\d{2}-\d{2}\s\d{1,2}:\d{1,2}:\d{1,2}$'

    if not backlog_type or backlog_type not in ('all', 'undo', 'done'):
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

    return True, params


def filter_conditions(params: dict):
    """条件过滤器"""
    # 首页列表待办（通过控制page、size控制页面展示多少条数据）
    con = Q()
    for key, value in params.items():
        if not value or not value.strip():
            continue
        q = Q()
        q.connector = 'OR'
        condition = []
        if key == 'keyword':
            condition = [
                ('obj_key__contains', value),
                ('obj_name__contains', value),
                ('initiator_name__contains', value)
            ]

        elif key == 'backlog_type':
            conditions = {
                'undo': ('is_done', False),
                'done': ('is_done', True),
            }
            if value not in conditions:
                continue
            condition = [
                conditions.get(value)
            ]

        elif key == 'start':
            value = datetime.strptime(value, NOTICE_DATETIME_FORMAT).replace(tzinfo=timezone.get_default_timezone())
            condition = [
                ('created_at__gte', value)
            ]

        elif key == 'end':
            value = datetime.strptime(value, NOTICE_DATETIME_FORMAT).replace(tzinfo=timezone.get_default_timezone())
            condition = [
                ('created_at__lte', value)
            ]

        elif key == 'obj_status':
            condition = [
                ('obj_status', value)
            ]

        q.children.extend(condition)
        con.add(q, 'AND')

    return con


#  The backlog message list
def list_backlog(page: int, size: int, params: dict, receiver: str):
    is_valid, params = check_params(params)
    if not is_valid:
        return params

    queryset = Backlog.objects.filter(receiver=receiver)
    con = filter_conditions(params)
    queryset = queryset.filter(con)
    total = queryset.count()
    max_page = math.ceil(total / size)

    if page > max_page:
        items = []
    else:
        items = [
            {
                'id': item.id,
                'created_at': item.created_at.strftime(NOTICE_DATETIME_FORMAT),
                'is_done': item.is_done,
                'handlers': item.handlers if item.handlers else [],
                'initiator': item.initiator,
                'initiator_name': item.initiator_name,
                'initiated_at': item.initiated_at,
                'obj_name': item.obj_name,
                'obj_key': item.obj_key,
                'obj_status': item.obj_status,
                'data': {} if not item.data else item.data,
                'is_read': item.is_read,
                'candidates': item.candidates if item.candidates else [],
                'company': item.company,
                'company_type': item.company_type,
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


def backlog_read(pk: int, receiver: str):
    """set backlog read

    :param int pk: backlog id
    :param str receiver: backlog receiver
    :return _type_: _description_
    """
    if not Backlog.objects.filter(receiver=receiver, pk=pk).exists():
        return NotFound()
    Backlog.objects.filter(receiver=receiver, id=pk).update(is_read=True, read_at=timezone.now())
    return JsonResponse(data={})


@require_http_methods(['PUT'])
def read_backlog(request: HttpRequest, pk: int):
    if not request.user.is_authenticated:
        return AuthFailed()

    return backlog_read(pk, str(request.user.pk))


def batch_handle_backlog(body, data):
    f = HandleBacklogForm(body)
    if not f.is_valid():
        return ValidationFailed()

    if not isinstance(data, dict):
        return ValidationFailed()

    cleaned_data = f.cleaned_data
    with transaction.atomic():
        backlogs = Backlog.objects.filter(batch=cleaned_data['batch']).select_for_update()
        if not backlogs:
            return NotFound()

        item = backlogs[0]
        handlers = item.handlers if item.handlers else []
        handlers.append(cleaned_data['handler'])
        update_params = {'handlers': handlers}
        if data:
            item_data = item.data if item.data else {}
            item_data.update(data)
            update_params['data'] = item_data
        if not cleaned_data['is_done']:
            backlogs.update(**update_params)
        else:
            keep = []
            remove = []
            for i in backlogs:
                if i.receiver in handlers:
                    keep.append(i.pk)
                else:
                    remove.append(i.pk)
            update_params['is_done'] = True
            update_params['done_at'] = timezone.now()
            Backlog.objects.filter(pk__in=keep).update(**update_params)
            Backlog.objects.filter(pk__in=remove).update(**update_params, is_deleted=True)
    return JsonResponse({})


@require_http_methods(['POST'])
def handle_backlog(request: HttpRequest):
    body = json.loads(request.body)
    data = body.pop('data', {})
    return batch_handle_backlog(body, data)


def batch_handle_obj(body, data):
    f = HandleObjForm(body)
    if not f.is_valid():
        return ValidationFailed()

    if not isinstance(data, dict):
        return ValidationFailed()
    cleaned_data = f.cleaned_data
    with transaction.atomic():
        backlogs = Backlog.objects.filter(obj_key=cleaned_data['key']).select_for_update()
        if not backlogs:
            return NotFound()
        backlog = backlogs[0]
        update_params = {
            'obj_status': cleaned_data['status']
        }
        if data:
            item_data = backlog.data if backlog.data else {}
            item_data.update(data)
            update_params['data'] = item_data
        Backlog.objects.filter(obj_key=cleaned_data['key']).update(
            **update_params
        )
    return JsonResponse({})


@require_http_methods(['POST'])
def handle_obj(request):
    body = json.loads(request.body)
    data = body.pop('data', {})
    return batch_handle_obj(body, data)
