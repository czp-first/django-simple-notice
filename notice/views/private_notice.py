# -*- coding: UTF-8 -*-
"""
@Summary : private notice
@Author  : Rey
@Time    : 2022-04-27 13:25:37
"""
import json
import math

from django.utils import timezone
from django.http import JsonResponse, HttpRequest
from django.views.decorators.http import require_http_methods

from notice.forms import PrivateForm
from notice.models import PrivateNotice
from notice.response import AuthFailed, NotFound, ValidationFailed, ValidationFailedDetailEnum
from notice.settings import NOTICE_DATETIME_FORMAT


# check if exist unread private notice: resp={'undo': false}
def unread_private(receiver: str):
    filter_params = {
        'is_read': False,
        'receiver': receiver
    }

    is_read = PrivateNotice.objects.filter(**filter_params).exists()
    return JsonResponse(data={'undo': is_read})


# create private notice:
def create_private(data: dict, creator: str, receivers: list):
    f = PrivateForm(data)
    if not f.is_valid():
        return ValidationFailed(f.errors)

    data = f.cleaned_data
    data['creator'] = creator
    data.pop("receiver")
    private_notices = [PrivateNotice(**data, receiver=receiver) for receiver in receivers]

    private_objs = PrivateNotice.objects.bulk_create(private_notices)
    return JsonResponse(data={'id': [private_notice.id for private_notice in private_objs]})


@require_http_methods(["GET", "POST"])
def private(request: HttpRequest):
    if not request.user.is_authenticated:
        return AuthFailed()

    if request.method == "POST":
        data = request.POST
        receivers = request.POST.get("receiver").split(",")
        return create_private(data, str(request.user.pk), receivers)

    receiver = request.user.pk
    return unread_private(receiver)


# list private notice
def list_private(receiver: str, page: int, size: int, title: str, is_index: bool):
    queryset = PrivateNotice.objects.filter(receiver=receiver)

    if is_index:
        queryset = queryset.filter(is_read=False)

    if title:
        queryset = queryset.filter(title__contains=title)

    total = queryset.count()
    max_page = math.ceil(total / size)

    if page > max_page:
        items = []
    else:
        items = [
            {
                "id": item.id,
                "created_at": item.created_at.strftime(NOTICE_DATETIME_FORMAT),
                "title": item.title,
                "data": item.data,
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
def privates(request: HttpRequest):
    if not request.user.is_authenticated:
        return AuthFailed()
    params = request.GET
    title = params.get('title')
    page = params.get('page', '1')
    size = params.get('size', '10')
    is_index = json.loads(params.get("is_index", 'false'))

    if not page.isdigit():
        return ValidationFailed(ValidationFailedDetailEnum.PAGE.value)

    if not size.isdigit():
        return ValidationFailed(ValidationFailedDetailEnum.SIZE.value)
    page = int(page)
    size = int(size)
    return list_private(str(request.user.pk), page, size, title, is_index)


# get a private notice detail
def private_detail(receiver: str, pk: int):
    private_obj: PrivateNotice = PrivateNotice.objects.filter(
        pk=pk,
        receiver=receiver
    ).only("id", "title", "content", "created_at", "data").first()
    if not private:
        return NotFound()

    resp = {
        "id": private_obj.id,
        "title": private_obj.title,
        "content": private_obj.content,
        "created_at": private_obj.created_at.strftime(NOTICE_DATETIME_FORMAT),
        "data": {} if not private_obj.data else private_obj.data
    }
    return JsonResponse(data=resp)


# finish private
def finish_private(receiver: str, pk: int):
    PrivateNotice.objects.filter(receiver=receiver, id=pk).update(is_read=True, read_at=timezone.now())
    return JsonResponse(data={})


@require_http_methods(["GET", "PUT"])
def private_notice_detail(request: HttpRequest, pk: int):
    if not request.user.is_authenticated:
        return AuthFailed()

    if request.method == "PUT":
        return finish_private(str(request.user.pk), pk)

    return private_detail(str(request.user.pk), pk)
