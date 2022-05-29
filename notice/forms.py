# -*- coding: UTF-8 -*-
"""
@Summary : docstr
@Author  : Rey
@Time    : 2022-04-01 17:03:32
"""
from enum import Enum

from django import forms
from django.conf import settings
from django.contrib.postgres.forms.array import SimpleArrayField
from django.core.exceptions import ValidationError
from django.utils.timezone import get_default_timezone, now as timezone_now
from django.utils.translation import gettext_lazy as _

from notice.models import NoticeType, ReceiverType
from notice.response import ValidationFailedDetailEnum
from notice.settings import NOTICE_DATETIME_FORMAT


class NoticeForm(forms.Form):
    class SendWayEnum(Enum):
        NO = 'no'
        NOW = 'now'
        TIMING = 'timing'

    SendWayChoices = (
        (SendWayEnum.NO.value, _('No')),
        (SendWayEnum.NOW.value, _('Now')),
        (SendWayEnum.TIMING.value, _('Timing')),
    )

    title = forms.CharField(required=False, max_length=64)
    content = forms.CharField(required=False, widget=forms.Textarea)
    type_id = forms.IntegerField(required=False, min_value=1)
    receiver_type_ids = SimpleArrayField(required=False, base_field=forms.IntegerField(required=False, min_value=1))
    send_way = forms.ChoiceField(required=True, choices=SendWayChoices)
    publish_at = forms.DateTimeField(required=False, input_formats=[NOTICE_DATETIME_FORMAT])

    def clean_type_id(self):
        type_id = self.cleaned_data['type_id']
        if not type_id:
            return type_id
        if not NoticeType.objects.filter(pk=type_id).exists():
            raise ValidationError(ValidationFailedDetailEnum.NOTICE_TYPE.value)
        return type_id

    def clean_receiver_type_ids(self):
        receiver_type_ids = self.cleaned_data['receiver_type_ids']
        if not receiver_type_ids:
            return receiver_type_ids
        right_ids = ReceiverType.objects.filter(pk__in=receiver_type_ids).values_list('id', flat=True)
        if set(receiver_type_ids) != set(right_ids):
            raise ValidationError(ValidationFailedDetailEnum.RECEIVER_TYPE.value)
        return receiver_type_ids

    def clean_publish_at(self):
        send_way = self.cleaned_data.get('send_way')
        if send_way is None:
            raise ValidationError(ValidationFailedDetailEnum.SEND_WAY.value)
        if send_way == self.SendWayEnum.NO.value:
            self.cleaned_data['is_draft'] = True
            return None
        if send_way == self.SendWayEnum.NOW.value:
            self.cleaned_data['is_draft'] = False
            return timezone_now()
        if send_way == self.SendWayEnum.TIMING.value:
            self.cleaned_data['is_draft'] = False
            publish_at = self.cleaned_data.get('publish_at')
            if not publish_at:
                raise ValidationError(ValidationFailedDetailEnum.SEND_WAY.value)
            if settings.USE_TZ:
                if publish_at.replace(tzinfo=get_default_timezone()) <= timezone_now():
                    raise ValidationError(ValidationFailedDetailEnum.OUTDATE.value)
            else:
                if publish_at <= timezone_now():
                    raise ValidationError(ValidationFailedDetailEnum.OUTDATE.value)
            return publish_at
        raise ValidationError(ValidationFailedDetailEnum.SEND_WAY.value)


class ChangeTimingForm(forms.Form):
    publish_at = forms.DateTimeField(required=True, input_formats=[NOTICE_DATETIME_FORMAT])

    def clean_publish_at(self):
        publish_at: str = self.cleaned_data.get('publish_at')
        if not publish_at:
            raise ValidationError(ValidationFailedDetailEnum.PUBLISH_TIME.value)

        if settings.USE_TZ:
            if publish_at.replace(tzinfo=get_default_timezone()) <= timezone_now():
                raise ValidationError(ValidationFailedDetailEnum.OUTDATE.value)
        else:
            if publish_at <= timezone_now():
                raise ValidationError(ValidationFailedDetailEnum.OUTDATE.value)
        return publish_at


class PrivateForm(forms.Form, SimpleArrayField):
    """私信消息表单"""
    receiver = SimpleArrayField(required=True, base_field=forms.CharField(required=False))
    title = forms.CharField(required=False, max_length=64)
    content = forms.CharField(required=False, max_length=64)


class BacklogForm(forms.Form):
    """待办消息表单"""
    batch = forms.CharField(required=False, max_length=64)
    is_done = forms.BooleanField(required=False)
    receivers = SimpleArrayField(required=True, base_field=forms.CharField(required=True))
    initiator = forms.CharField(required=False, max_length=64)
    initiator_name = forms.CharField(required=False, max_length=64)
    initiated_at = forms.DateTimeField(required=False, input_formats=[NOTICE_DATETIME_FORMAT])
    obj_name = forms.CharField(required=False, max_length=64)
    obj_key = forms.CharField(required=False, max_length=64)
    obj_status = forms.CharField(required=False, max_length=64)
    handlers = SimpleArrayField(required=False, base_field=forms.CharField(required=False))
    candidates = SimpleArrayField(required=False, base_field=forms.CharField(required=False))
    obj_associated_data = forms.CharField(required=False, max_length=64)
    obj_associated_data_type = forms.CharField(required=False, max_length=64)
    company = forms.CharField(required=False, max_length=64)
    company_type = forms.CharField(required=False, max_length=64)


class HandleBacklogForm(forms.Form):
    batch = forms.CharField(required=True, max_length=64)
    is_done = forms.BooleanField(required=False)
    handler = forms.CharField(required=True, max_length=64)


class HandleObjForm(forms.Form):
    key = forms.CharField(required=True, max_length=64)
    status = forms.CharField(required=True, max_length=64)
