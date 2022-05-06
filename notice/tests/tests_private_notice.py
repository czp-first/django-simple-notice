# -*- coding: utf-8 -*-
"""
@File        : tests_private_notice.py
@Author      : wangliang
@Time        : 2022/5/5 11:22
@Description : python manage.py test notice.tests.tests_private_notice.PrivateNoticeCase.test_privates  -v 3 --keepdb
"""
import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from notice.models import PrivateNotice
from notice.response import NotFound


class PrivateNoticeCase(TestCase):
    fixtures = ("private_notice.json",)

    def setUp(self):
        User.objects.create_user('tester', 'user@test.com', '123456', pk=1)

    def private_request(self, method, namespace, **kwargs):
        self.client.login(username='tester', password='123456')
        if method == "GET":
            return self.client.get(reverse(namespace), kwargs)
        elif method == "POST":
            return self.client.post(reverse(namespace), kwargs.get("data"))
        elif method == "PUT":
            return self.client.put(namespace, kwargs.get("data"), content_type='application/json')
        else:
            return NotFound()

    def test_privates(self):
        """Private message list unit test"""
        resp = self.private_request("GET", "privates", page=1, size=2)
        self.assertEqual(resp.status_code, 200)
        resp_json = resp.json()
        self.assertEqual(resp_json["total"], 3)
        self.assertEqual(resp_json['max_page'], 2)
        self.assertEqual(resp_json['page'], 1)
        self.assertEqual(resp_json['size'], 2)

        items = resp_json['items']
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['id'], 10)
        self.assertEqual(items[0]['title'], "title05")
        self.assertEqual(items[1]['id'], 6)
        self.assertEqual(items[1]['title'], "title001")

    def test_unread_private(self):
        """check if exist unread private notice"""
        self.assertTrue(PrivateNotice.objects.filter(receiver='1', is_read=False).exists())
        resp = self.private_request("GET", "private")
        self.assertEqual(resp.status_code, 200)
        resp_json = resp.json()
        self.assertEqual(resp_json["undo"], True)
        self.assertTrue(PrivateNotice.objects.filter(receiver='1', is_read=False).exists())

    def test_create_private(self):
        """Create unit tests for private messages"""
        node = "3"
        obj_key = "2"
        title = "hello"
        business_type = "4"

        data = {
            "creator": "1",
            'title': title,
            'receiver': "8,9,10",
            'obj_key': obj_key,
            'business_type': business_type,
            "node": node
        }

        resp = self.private_request("POST", "private", data=data)
        self.assertEqual(resp.status_code, 200)
        resp_json = resp.json()
        self.assertEqual(len(resp_json["id"]), len(data.get("receiver").split(',')))
        for pk in resp_json.get("id"):
            self.assertTrue(PrivateNotice.objects.filter(id=pk).exists())
            private: PrivateNotice = PrivateNotice.objects.get(pk=pk)
            self.assertEqual(private.title, title)
            self.assertEqual(private.node, node)
            self.assertEqual(private.obj_key, obj_key)
            self.assertEqual(private.business_type, business_type)

    def test_finish_private(self):
        """Set someone's private message as a read unit test"""
        # 当前用户为1，pk可取值1，6，10
        pk = 1
        url = f"/notice/finish_private/{pk}/"
        resp = self.private_request("PUT", url)
        self.assertEqual(resp.status_code, 200)
        privates: PrivateNotice = PrivateNotice.objects.filter(receiver=1, id=pk).only("is_read", "read_at")
        self.assertTrue(privates.exists())
        for private in privates:
            self.assertEqual(private.is_read, True)

    def test_change_node_status(self):
        """Modify the state unit test of the node on which the message resides"""
        data = {
            "obj_key": "2",
            "business_type": "1",
            "node": "1",
            "data": "",
        }
        url = f"/notice/private/node/status/"
        resp = self.private_request("PUT", url, data=data)
        self.assertEqual(resp.status_code, 200)
        privates: PrivateNotice = PrivateNotice.objects.filter(receiver=1, **data).only("is_node_done", "updated_at")
        self.assertTrue(privates.exists())
        for private in privates:
            self.assertEqual(private.is_node_done, True)
