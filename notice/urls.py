# -*- coding: UTF-8 -*-
"""
@Summary : urls
@Author  : Rey
@Time    : 2022-04-02 17:12:23
"""
from django.urls import path

from notice.views import admin as admin_views
from notice.views import client as client_views

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
]

urlpatterns = admin_urlpatterns + client_urlpatterns
