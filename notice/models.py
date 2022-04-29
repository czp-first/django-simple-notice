# -*- coding: UTF-8 -*-
"""
@Summary : orm
@Author  : Rey
@Time    : 2022-03-30 11:44:57
"""
from enum import Enum

import django

if django.VERSION > (4, 0):
    from django.db.models import JSONField
else:
    from django.contrib.postgres.fields import JSONField
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import JSONField
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from notice.settings import NOTICE_DATETIME_FORMAT


class BaseTimeModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('create time'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('latest update time'))

    class Meta:
        abstract = True


class IsDeletedManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_deleted=False)


class IsDeletedModel(models.Model):
    is_deleted = models.BooleanField(default=False, verbose_name=_('delete tag'))

    objects = IsDeletedManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True


class NameDescModel(models.Model):
    name = models.CharField(max_length=64, verbose_name=_('name'))
    desc = models.CharField(max_length=256, verbose_name=_('description'))

    class Meta:
        abstract = True


class ReceiverType(BaseTimeModel, IsDeletedModel, NameDescModel):
    class Meta:
        db_table = 'notice_receiver_type'


class NoticeType(BaseTimeModel, IsDeletedModel, NameDescModel):
    class Meta:
        db_table = 'notice_type'


class NoticeStore(BaseTimeModel, IsDeletedModel):
    title = models.CharField(null=True, max_length=64, verbose_name=_('title'))
    content = models.TextField(null=True, verbose_name=_('content'))
    notice_type = models.ForeignKey(NoticeType, on_delete=models.CASCADE, verbose_name=_('notice type'))
    receiver_type_ids = ArrayField(models.IntegerField(), null=True, verbose_name=_('receiver type'))
    is_draft = models.BooleanField(default=True, verbose_name=_('draft tag'))
    creator_id = models.IntegerField(verbose_name=_('creator id'))
    publish_at = models.DateTimeField(null=True, verbose_name=_('publish time'))

    class StatusEnum(Enum):
        DRAFT = 'draft'
        QUEUE = 'queue'
        DONE = 'done'

    StatusLabel = {
        StatusEnum.DRAFT: _('Draft'),
        StatusEnum.QUEUE: _('Queue'),
        StatusEnum.DONE: _('Done'),
    }

    @property
    def status(self):
        if self.is_draft:
            return self.StatusEnum.DRAFT
        if self.publish_at > timezone.now():
            return self.StatusEnum.QUEUE
        return self.StatusEnum.DONE

    @property
    def published_at(self):
        if not self.is_draft and self.publish_at <= timezone.now():
            return self.publish_at.strftime(NOTICE_DATETIME_FORMAT)
        return None


class ReceiverTag(BaseTimeModel, IsDeletedModel):
    noticestore = models.ForeignKey(NoticeStore, on_delete=models.CASCADE, verbose_name=_('notice'))
    receiver = models.CharField(verbose_name=_('receiver'), max_length=64)
    read_at = models.DateTimeField(verbose_name=_('read time'))

    class Meta:
        db_table = 'notice_receiver_tag'


class Backlog(BaseTimeModel):
    creator = models.CharField(verbose_name=_('creator'), max_length=64, null=True)
    receiver = models.CharField(verbose_name=_('receiver'), max_length=64)
    title = models.CharField(null=True, max_length=64, verbose_name=_('title'))
    data = JSONField(verbose_name=_('data'), null=True)
    redirect_url = models.CharField(max_length=1024, null=True, verbose_name=_('redirect url'))
    is_done = models.BooleanField(default=False, verbose_name=_('completed status'))
    done_at = models.DateTimeField(null=True, verbose_name=_('completed datetime'))

    class Meta:
        db_table = 'notice_backlog'


class PrivateNotice(BaseTimeModel):
    creator = models.CharField(verbose_name=_('creator'), max_length=64, null=True)
    receiver = models.CharField(verbose_name=_('receiver'), max_length=64)
    title = models.CharField(null=True, max_length=64, verbose_name=_('title'))
    obj_key = models.CharField(max_length=64, verbose_name=_('obj key'))
    business_type = models.CharField(max_length=64, verbose_name=_('business type'))
    node = models.CharField(max_length=64, verbose_name=_('node'))
    is_node_done = models.BooleanField(default=False, verbose_name=_('completed status'))
    data = models.JSONField(null=True, verbose_name=_('data'))
    is_read = models.BooleanField(default=False, verbose_name=_('read status'))
    read_at = models.DateTimeField(null=True, verbose_name=_('read time'))

    class Meta:
        db_table = 'notice_private_notice'
        unique_together = (
            ("receiver", "title", "obj_key", "business_type")
        )
