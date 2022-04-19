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
from psycopg2.errors import UniqueViolation

from notice.settings import NOTICE_ALLOWED_TYPED_CLASS
from notice.models import NoticeStore, ReceiverTag
from notice.response import AuthFailed, NotFound, ValidationFailed, ValidationFailedDetailEnum


def get_page_notice(receiver, page, size, title=None, **kwargs):
    allowed_notice_type_ids, allowed_receiver_type_ids = NOTICE_ALLOWED_TYPED_CLASS(receiver=receiver, **kwargs).judge()
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
        'receiver_type_ids__overlap': allowed_receiver_type_ids,
        'notice_type_id__in': allowed_notice_type_ids,
    }
    if title:
        filter_params['title__contains'] = title
    total = NoticeStore.objects.filter(**filter_params).count()
    max_page = math.ceil(total / size)

    items = [
        {
            'id': item.id,
            'title': item.title,
            'publish_at': item.published_at,
        }
        for item in NoticeStore.objects.filter(
            **filter_params
        ).only(
            'title', 'publish_at', 'is_draft'
        ).order_by('-id')[(page-1)*size: page*size]
    ] if page <= max_page else []

    if items:
        tags = ReceiverTag.objects.filter(
            receiver=receiver, noticestore_id__in=[i['id'] for i in items]
        ).values_list('noticestore_id', flat=True)
        for item in items:
            if item['id'] in tags:
                item['is_read'] = True
            else:
                item['is_read'] = False

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

    title = params.get('title', '')

    return get_page_notice(str(request.user.pk), page, size, title)


def retrieve_notice(receiver, pk, **kwargs):
    allowed_notice_type_ids, allowed_receiver_type_ids = NOTICE_ALLOWED_TYPED_CLASS(receiver, **kwargs).judge()
    if not allowed_notice_type_ids or not allowed_receiver_type_ids:
        return NotFound()

    filter_params = {
        'is_draft': False,
        'publish_at__lte': timezone.now(),
        'receiver_type_ids__overlap': allowed_receiver_type_ids,
        'notice_type_id__in': allowed_notice_type_ids,
        'pk': pk
    }
    notice = NoticeStore.objects.filter(**filter_params).only(
        'publish_at', 'title', 'content', 'is_draft'
    ).first()
    if not notice:
        return NotFound()

    if not ReceiverTag.objects.filter(
        receiver=receiver, noticestore_id=pk
    ).exists():
        try:
            ReceiverTag.objects.create(
                receiver=receiver,
                noticestore_id=pk,
                read_at=timezone.now()
            )
        except UniqueViolation:
            pass

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

    return retrieve_notice(str(request.user.pk), pk)


def get_unread_status(receiver, **kwargs):
    allowed_notice_type_ids, allowed_receiver_type_ids = NOTICE_ALLOWED_TYPED_CLASS(receiver=receiver, **kwargs).judge()
    filter_params = {
        'is_draft': False,
        'publish_at__lte': timezone.now(),
        'receiver_type_ids__overlap': allowed_receiver_type_ids,
        'notice_type_id__in': allowed_notice_type_ids,
    }
    total = NoticeStore.objects.filter(**filter_params).count()
    read_total = ReceiverTag.objects.filter(receiver=receiver).count()
    return JsonResponse(data={'is_unread': False if total == read_total else True})


@require_GET
def notice_status(request: HttpRequest):
    if not request.user.is_authenticated:
        return AuthFailed()
    return get_unread_status(str(request.user.pk))
