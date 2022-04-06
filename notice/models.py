# -*- coding: UTF-8 -*-
"""
@Summary : orm
@Author  : Rey
@Time    : 2022-03-30 11:44:57
"""
from enum import Enum

from django.db import models
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
    receiver_type = models.ForeignKey(ReceiverType, on_delete=models.CASCADE, verbose_name=_('receiver type'))
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
    noticestore = models.OneToOneField(NoticeStore, on_delete=models.CASCADE, verbose_name=_('notice'))
    receiver_id = models.IntegerField(verbose_name=_('receiver'))
    read_at = models.DateTimeField(verbose_name=_('read time'))

    class Meta:
        db_table = 'notice_receiver_tag'
