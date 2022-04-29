# -*- coding: UTF-8 -*-
"""
@Summary : urls
@Author  : Rey
@Time    : 2022-04-02 17:12:23
"""
from django.urls import path

from notice.views import admin as admin_views
from notice.views import client as client_views
from notice.views import private_notice

admin_urlpatterns = [
    path('admin/', admin_views.notice, name='admin-notice'),
    path('admin/<int:pk>/', admin_views.some_notice, name='admin-some-notice'),
    path('admin/receiver_types/', admin_views.list_all_receiver_types, name='admin-receiver-types'),
    path('admin/types/', admin_views.list_all_notice_types, name='admin-notice-types'),
    path('admin/timing/<int:pk>/', admin_views.change_timing_notice, name='admin-change-timing-notice'),
]

client_urlpatterns = [
    path('client/', client_views.list_notice, name='client-list-notice'),
    path('client/<int:pk>/', client_views.some_notice, name='client-retrieve-notice'),
    path('client/status/', client_views.notice_status, name='client-notice-status'),
]

private_urlpatterns = [
    path('private/', private_notice.private, name="backlog-private"),
    path('privates/', private_notice.privates, name="backlog-privates"),
    path('private/<int:pk>/', private_notice.private_notice_detail, name="private-notice-detail"),
    path('finish_private/<int:pk>/', private_notice.f_private, name="finish-private"),
    path('private/node/status/', private_notice.alter_node_status, name="alter-node-status"),
]

urlpatterns = admin_urlpatterns + client_urlpatterns + private_urlpatterns
