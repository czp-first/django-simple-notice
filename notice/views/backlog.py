# -*- coding: UTF-8 -*-
"""
@Summary : backlog
@Author  : Rey
@Time    : 2022-04-27 13:25:25
"""
import math

from django.utils import timezone
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_http_methods

from notice.forms import BlockForm
from notice.models import Backlog
from notice.response import AuthFailed, ValidationFailed, ValidationFailedDetailEnum


# check if undo backlog exist: resp={'undo': false}
def undo_backlog(receiver):
    filter_params = {
        'is_done': False,
        "receiver": receiver
    }

    is_undo = Backlog.objects.filter(**filter_params).exists()
    return JsonResponse(data={'undo': is_undo})


# create a backlog:
def create_backlog(data: dict, creator_id: str):
    f = BlockForm(data)
    if not f.is_valid():
        return ValidationFailed(f.errors)

    data = f.cleaned_data
    data["creator"] = creator_id
    back_log = Backlog.objects.create(**data)
    return JsonResponse(data={'id': back_log.pk})


@require_http_methods(["GET", "POST"])
def backlog(request: HttpRequest):
    if not request.user.is_authenticated:
        return AuthFailed()

    if request.method == 'POST':
        data = request.POST.dict()
        return create_backlog(data, request.user.pk)

    receiver = request.GET.get("receiver")
    return undo_backlog(receiver)


# list backlog
def list_backlog(params: dict):
    backlog_info = Backlog.objects.filter().values().order_by("-id")
    page = params.get('page', '1')
    if not page.isdigit():
        return ValidationFailed(ValidationFailedDetailEnum.PAGE.value)
    page = int(page)

    size = params.get('size', '10')
    if not size.isdigit():
        return ValidationFailed(ValidationFailedDetailEnum.SIZE.value)
    size = int(size)

    total = Backlog.objects.all().count()
    max_page = math.ceil(total / size)
    resp = {
        'total': total,
        'max_page': max_page,
        'page': page,
        'items': list(backlog_info)[(page-1)*size: page*size]
    }
    return JsonResponse(data=resp)


@require_http_methods(["GET"])
def backlogs(request: HttpRequest):
    if not request.user.is_authenticated:
        return AuthFailed()
    param = request.GET

    return list_backlog(param)


# finish backlog
def finish_backlog(pk: int):
    Backlog.objects.filter(id=pk).update(is_done=True, done_at=timezone.now())

    return JsonResponse(data={})


@require_http_methods(["PUT"])
def f_backlog(request: HttpRequest, pk: int):
    if not request.user.is_authenticated:
        return AuthFailed()
    return finish_backlog(pk)
