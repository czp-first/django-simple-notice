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
def list_private(receiver: str, page: int, size: int, title: str):
    queryset = PrivateNotice.objects.filter(receiver=receiver)
    if title:
        queryset = queryset.filter(title__contains=title)

    total = queryset.count()
    max_page = math.ceil(total / size)

    if page > max_page:
        items = []
    else:
        items = list(queryset.order_by('-id')[(page - 1) * size: page * size].values(
            "id",
            "created_at",
            "title",
            "obj_key",
            "business_type",
            "node",
            "is_node_done",
            "data",
            "is_read"
        ))

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

    if not page.isdigit():
        return ValidationFailed(ValidationFailedDetailEnum.PAGE.value)

    if not size.isdigit():
        return ValidationFailed(ValidationFailedDetailEnum.SIZE.value)
    page = int(page)
    size = int(size)
    return list_private(str(request.user.pk), page, size, title)


# get a private notice detail
def private_detail(receiver: str, pk: int):
    private = PrivateNotice.objects.filter(pk=pk, receiver=receiver).values().first()
    if not private:
        return NotFound()

    resp = dict(private)
    return JsonResponse(data=resp)


@require_http_methods(["GET"])
def private_notice_detail(request: HttpRequest, pk: int):
    if not request.user.is_authenticated:
        return AuthFailed()

    return private_detail(str(request.user.pk), pk)


# finish private
def finish_private(receiver: str, pk: int):
    PrivateNotice.objects.filter(receiver=receiver, id=pk).update(is_read=True, read_at=timezone.now())
    return JsonResponse(data={})


@require_http_methods(["PUT"])
def f_private(request: HttpRequest, pk: int):
    if not request.user.is_authenticated:
        return AuthFailed()
    return finish_private(str(request.user.pk), pk)


# change node status
def change_node_status(receiver: str, params: dict):
    params["receiver"] = receiver
    PrivateNotice.objects.filter(**params).update(is_node_done=True, updated_at=timezone.now())
    return JsonResponse(data={})


@require_http_methods(["PUT"])
def alter_node_status(request: HttpRequest):
    # TODO:Change node state logic may change
    if not request.user.is_authenticated:
        return AuthFailed()

    params = json.loads(request.body)
    return change_node_status(str(request.user.pk), params)
