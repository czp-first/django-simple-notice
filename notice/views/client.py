# -*- coding: UTF-8 -*-
"""
@Summary : docstr
@Author  : Rey
@Time    : 2022-04-02 10:24:24
"""
import math

from django.http import HttpRequest, JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from notice.settings import NOTICE_ALLOWED_TYPED_CLASS
from notice.models import NoticeStore, ReceiverTag
from notice.response import AuthFailed, NotFound, ValidationFailed, ValidationFailedDetailEnum


def get_page_notice(receiver_id, page, size, **kwargs):
    allowed_notice_type_ids, allowed_receiver_type_ids = NOTICE_ALLOWED_TYPED_CLASS(receiver_id=receiver_id, **kwargs).judge()
    if not allowed_notice_type_ids or not allowed_receiver_type_ids:
        return JsonResponse(data={
            'total': 0,
            'max_page': 1,
            'page': page,
            'items': []
        })

    filter_params = {
        'is_draft': False,
        'publish_at__lte': timezone.now(),
        'receiver_type_id__in': allowed_receiver_type_ids,
        'notice_type_id__in': allowed_notice_type_ids
    }
    total = NoticeStore.objects.filter(**filter_params).count()
    max_page = math.ceil(total / size)

    items = [
        {
            'id': item.id,
            'title': item.title,
            'publish_at': item.published_at,
            'is_read': True if hasattr(item, 'receivertag') else False,
        }
        for item in NoticeStore.objects.filter(
            **filter_params
        ).only(
            'title', 'publish_at', 'receivertag__id', 'is_draft'
        ).order_by('-id')[(page-1)*size: page*size]
    ] if page <= max_page else []

    return JsonResponse(data={
        'total': total,
        'max_page': max_page,
        'page': page,
        'items': items
    })


@require_GET
def list_notice(request: HttpRequest):
    if not request.user.is_authenticated:
        return AuthFailed()

    params = request.GET
    page = params.get('page', '1')
    if not page.isdigit():
        return ValidationFailed(ValidationFailedDetailEnum.PAGE.value)
    page = int(page)

    size = params.get('size', '10')
    if not size.isdigit():
        return ValidationFailed(ValidationFailedDetailEnum.SIZE.value)
    size = int(size)

    return get_page_notice(request.user.pk, page, size)


def retrieve_notice(receiver_id, pk, **kwargs):
    allowed_notice_type_ids, allowed_receiver_type_ids = NOTICE_ALLOWED_TYPED_CLASS(receiver_id, **kwargs).judge()
    if not allowed_notice_type_ids or not allowed_receiver_type_ids:
        return NotFound()

    filter_params = {
        'is_draft': False,
        'publish_at__lte': timezone.now(),
        'receiver_type_id__in': allowed_receiver_type_ids,
        'notice_type_id__in': allowed_notice_type_ids,
        'pk': pk
    }
    notice = NoticeStore.objects.filter(**filter_params).only(
        'publish_at', 'title', 'content', 'is_draft'
    ).first()
    if not notice:
        return NotFound()

    if not ReceiverTag.objects.filter(
        receiver_id=receiver_id, noticestore_id=pk
    ).exists():
        ReceiverTag.objects.create(
            receiver_id=receiver_id,
            noticestore_id=pk,
            read_at=timezone.now()
        )

    resp = {
        'id': notice.id,
        'title': notice.title,
        'content': notice.content,
        'publish_at': notice.published_at,
    }
    return JsonResponse(data=resp)


@require_GET
def some_notice(request: HttpRequest, pk: int):
    if not request.user.is_authenticated:
        return AuthFailed()

    return retrieve_notice(request.user.pk, pk)
