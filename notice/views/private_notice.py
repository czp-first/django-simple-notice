# -*- coding: UTF-8 -*-
"""
@Summary : private notice
@Author  : Rey
@Time    : 2022-04-27 13:25:37
"""
import math

from django.utils import timezone
from django.http import JsonResponse, HttpRequest
from django.db.models import Q
from django.http.request import QueryDict
from django.views.decorators.http import require_http_methods

from notice.forms import PrivateForm
from notice.models import PrivateNotice
from notice.response import AuthFailed, NotFound, ValidationFailed, ValidationFailedDetailEnum


# check if exist unread private notice: resp={'undo': false}
def unread_private(receiver):
    filter_params = {
        'is_read': False,
        "receiver": receiver
    }

    is_read = PrivateNotice.objects.filter(**filter_params).exists()
    return JsonResponse(data={'undo': is_read})


# create private notice:
def create_private(data: dict, creator: str):
    f = PrivateForm(data)
    if not f.is_valid():
        return ValidationFailed(f.errors)

    data = f.cleaned_data
    data["creator"] = creator
    private_obj = PrivateNotice.objects.create(**data)
    return JsonResponse(data={'id': private_obj.pk})


@require_http_methods(["GET", "POST"])
def private(request: HttpRequest):
    if not request.user.is_authenticated:
        return AuthFailed()

    if request.method == 'POST':
        data = request.POST.dict()
        return create_private(data, request.user.pk)

    receiver = request.user.pk
    return unread_private(receiver)


# list private notice
def list_private(params: QueryDict, receiver: str):
    keyword = params.get("keyword")
    private_info = PrivateNotice.objects.filter(receiver=receiver).values().order_by("-id")
    if keyword:
        private_info = PrivateNotice.objects.filter(
            Q(title__contains=keyword) |
            Q(creator__contains=keyword)
        ).values().order_by("-id")

    page = params.get('page', '1')
    if not page.isdigit():
        return ValidationFailed(ValidationFailedDetailEnum.PAGE.value)
    page = int(page)

    size = params.get('size', '10')
    if not size.isdigit():
        return ValidationFailed(ValidationFailedDetailEnum.SIZE.value)
    size = int(size)

    total = private_info.count()
    max_page = math.ceil(total / size)
    resp = {
        'total': total,
        'max_page': max_page,
        'page': page,
        'items': list(private_info)[(page - 1) * size: page * size]
    }
    return JsonResponse(data=resp)


@require_http_methods(["GET"])
def privates(request: HttpRequest):
    if not request.user.is_authenticated:
        return AuthFailed()
    param = request.GET
    return list_private(param, request.user.pk)


# get a private notice detail
def private_detail(pk: int):
    private = PrivateNotice.objects.filter(pk=pk).values().first()
    if not private:
        return NotFound()

    resp = dict(private)
    return JsonResponse(data=resp)


@require_http_methods(["GET"])
def private_notice_detail(request: HttpRequest, pk: int):
    if not request.user.is_authenticated:
        return AuthFailed()

    return private_detail(pk)


# finish private
def finish_private(pk: int):
    PrivateNotice.objects.filter(id=pk).update(is_read=True, read_at=timezone.now())

    return JsonResponse(data={})


@require_http_methods(["PUT"])
def f_private(request: HttpRequest, pk: int):
    if not request.user.is_authenticated:
        return AuthFailed()
    return finish_private(pk)
