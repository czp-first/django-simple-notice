# -*- coding: UTF-8 -*-
"""
@Summary : admin views
@Author  : Rey
@Time    : 2022-03-30 13:16:11
"""
import json
import math

from django.http import JsonResponse, HttpRequest
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from notice.forms import NoticeForm, ChangeTimingForm
from notice.models import NoticeStore, NoticeType, ReceiverType
from notice.response import AuthFailed, NotFound, ValidationFailed, ValidationFailedDetailEnum
from notice.settings import NOTICE_DATETIME_FORMAT


def list_all_notice_types(request):
    notice_types = NoticeType.objects.all().only('id', 'desc').order_by('id')
    data = [{'id': item.id, 'desc': item.desc} for item in notice_types]
    return JsonResponse(data=data, safe=False)


def list_all_receiver_types(request):
    receiver_types = ReceiverType.objects.all().only('id', 'desc').order_by('id')
    data = [{'id': item.id, 'desc': item.desc} for item in receiver_types]
    return JsonResponse(data=data, safe=False)


def create_notice(data: dict, creator_id: int):
    # TODO(Rey): if send way is now or timing, all fields are required.
    f = NoticeForm(data)
    if not f.is_valid():
        return ValidationFailed(f.errors)

    data = f.cleaned_data
    data.pop('send_way')
    data['notice_type_id'] = data.pop('type_id')
    data['creator_id'] = creator_id

    notice = NoticeStore.objects.create(**data)
    return JsonResponse(data={'id': notice.pk})


def list_notice(params: dict):
    page = params.get('page', '1')
    if not page.isdigit():
        return ValidationFailed(ValidationFailedDetailEnum.PAGE.value)
    page = int(page)

    size = params.get('size', '10')
    if not size.isdigit():
        return ValidationFailed(ValidationFailedDetailEnum.SIZE.value)
    size = int(size)

    total = NoticeStore.objects.all().count()
    max_page = math.ceil(total / size)

    items = [
        {
            'id': item.id,
            'title': item.title,
            'created_at': item.created_at.strftime(NOTICE_DATETIME_FORMAT),
            'publish_at': item.publish_at.strftime(NOTICE_DATETIME_FORMAT) if item.publish_at else None,
            'type': item.notice_type.desc,
            'status': NoticeStore.StatusLabel.get(item.status)
        }
        for item in NoticeStore.objects.all().select_related(
            'notice_type'
        ).order_by('-id')[(page-1)*size: page*size]
    ] if page <= max_page else []

    resp = {
        'total': total,
        'max_page': max_page,
        'page': page,
        'items': items
    }
    return JsonResponse(data=resp)


@require_http_methods(['GET', 'POST'])
def notice(request: HttpRequest):
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return AuthFailed()
        return create_notice(json.loads(request.body), request.user.pk)
    params = request.GET
    return list_notice(params)


def retrieve_notice(pk: int):
    notice = NoticeStore.objects.filter(pk=pk).only(
        'is_draft', 'publish_at', 'title', 'content'
    ).first()
    if not notice:
        return NotFound()

    resp = {
        'id': notice.id,
        'title': notice.title,
        'content': notice.content,
        'publish_at': notice.published_at,
    }
    return JsonResponse(data=resp)


def delete_notice(pk: int):
    if not NoticeStore.objects.filter(pk=pk).exists():
        return NotFound()

    notice = NoticeStore.objects.get(pk=pk)
    if notice.status != NoticeStore.StatusEnum.DRAFT:
        return ValidationFailed(ValidationFailedDetailEnum.DELETE_NOT_DRAFT.value)

    if notice.status == NoticeStore.StatusEnum.DONE:
        return ValidationFailed(ValidationFailedDetailEnum.DELETE_PUBLISHED.value)

    NoticeStore.objects.filter(pk=pk).update(
        is_deleted=True,
        updated_at=timezone.now()
    )

    return JsonResponse(data={})


def put_notice(data: dict, pk: int):
    notice = NoticeStore.objects.filter(pk=pk).first()
    if not notice:
        return NotFound()

    if notice.status != NoticeStore.StatusEnum.DRAFT:
        return ValidationFailed(ValidationFailedDetailEnum.CHANGE_NOT_DRAFT.value)

    f = NoticeForm(data)
    if not f.is_valid():
        return ValidationFailed(f.errors)

    data = f.cleaned_data
    data['notice_type_id'] = data.pop('type_id')

    update_params = {}
    for key, value in data.items():
        if hasattr(notice, key) and value != getattr(notice, key):
            update_params[key] = value
    if update_params:
        update_params['updated_at'] = timezone.now()
        NoticeStore.objects.filter(pk=pk).update(**update_params)
    return JsonResponse(data={})


@require_http_methods(['GET', 'PUT', 'DELETE'])
def some_notice(request: HttpRequest, pk: int):
    if request.method == 'DELETE':
        return delete_notice(pk)
    if request.method == 'PUT':
        return put_notice(json.loads(request.body), pk)
    return retrieve_notice(pk)


def change_timing(data: dict, pk: int):
    if not NoticeStore.objects.filter(pk=pk).exists():
        return NotFound()

    notice: NoticeStore = NoticeStore.objects.get(pk=pk)
    if notice.status == NoticeStore.StatusEnum.DRAFT:
        return ValidationFailed(ValidationFailedDetailEnum.CHANGE_DRAFT_TIMING.value)
    if notice.status == NoticeStore.StatusEnum.DONE:
        return ValidationFailed(ValidationFailedDetailEnum.CHANGE_PUBLISHED.value)

    f = ChangeTimingForm(data=data)
    if not f.is_valid():
        return ValidationFailed(f.errors)

    NoticeStore.objects.filter(pk=pk).update(
        publish_at=f.cleaned_data['publish_at'],
        updated_at=timezone.now()
    )
    return JsonResponse(data={})


def delete_timing(pk):
    """取消定时发送"""
    if not NoticeStore.objects.filter(pk=pk).exists():
        return NotFound()

    notice: NoticeStore = NoticeStore.objects.get(pk=pk)
    if notice.status == NoticeStore.StatusEnum.DRAFT:
        return ValidationFailed(ValidationFailedDetailEnum.DELETE_DRAFT_TIMING.value)
    if notice.status == NoticeStore.StatusEnum.DONE:
        return ValidationFailed(ValidationFailedDetailEnum.CHANGE_PUBLISHED.value)

    NoticeStore.objects.filter(pk=pk).update(
        is_draft=True,
        updated_at=timezone.now(),
        publish_at=None
    )
    return JsonResponse(data={})


@require_http_methods(['PUT', 'DELETE'])
def change_timing_notice(request: HttpRequest, pk: int):
    if request.method == 'PUT':
        data = json.loads(request.body)
        return change_timing(data, pk)
    return delete_timing(pk)
