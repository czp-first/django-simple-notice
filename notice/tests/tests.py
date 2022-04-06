# -*- coding: UTF-8 -*-
"""
@Summary : docstr
@Author  : Rey
@Time    : 2022-04-04 12:51:37
@Run     : python manage.py test notice -v 3 --keepdb
"""
from datetime import timedelta
import json

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils.timezone import now as timezone_now

from notice.forms import NoticeForm
from notice.models import NoticeStore, NoticeType, ReceiverType, ReceiverTag
from notice.settings import NOTICE_DATETIME_FORMAT


class AdminListALLNoticeTypeCase(TestCase):
    """test list_all_notice_types"""
    fixtures = ('notice_types.json',)
    def test_have_data(self):
        resp = self.client.get(reverse('admin-notice-types'))
        self.assertEqual(resp.status_code, 200)
        resp_json = resp.json()
        self.assertListEqual(resp_json, [{'id': 1, 'desc': 'SYSTEM'}, {'id': 3, 'desc': 'PRIVATE'}])

    def test_no_data(self):
        delete_info = NoticeType.all_objects.all().delete()
        self.assertEqual(delete_info[0], 3)
        resp = self.client.get(reverse('admin-notice-types'))
        self.assertEqual(resp.status_code, 200)
        resp_json = resp.json()
        self.assertListEqual(resp_json, [])


class AdminListAllReceiverTypeCase(TestCase):
    """test list_all_receiver_types"""
    fixtures = ('receiver_types.json',)

    def test_have_data(self):
        resp = self.client.get(reverse('admin-receiver-types'))
        self.assertEqual(resp.status_code, 200)
        resp_json = resp.json()
        self.assertListEqual(resp_json, [{'id': 1, 'desc': 'ALL'}, {'id': 3, 'desc': 'PART'}])

    def test_no_data(self):
        delete_info = ReceiverType.all_objects.all().delete()
        self.assertEqual(delete_info[0], 3)
        resp = self.client.get(reverse('admin-receiver-types'))
        self.assertEqual(resp.status_code, 200)
        resp_json = resp.json()
        self.assertListEqual(resp_json, [])


class AdminListNoticeCase(TestCase):
    """test get notice"""
    fixtures = ('notice_types.json', 'receiver_types.json', 'notice.json')

    def test_page_have_data(self):
        resp = self.client.get(reverse('admin-notice'))
        self.assertEqual(resp.status_code, 200)
        resp_json = resp.json()
        self.assertEqual(resp_json['total'], 4)
        self.assertEqual(resp_json['max_page'], 1)
        self.assertEqual(resp_json['page'], 1)
        items = resp_json['items']
        self.assertEqual(len(items), 4)

        # assert done notice
        self.assertEqual(items[0]['id'], 5)
        self.assertEqual(items[0]['title'], 'title5')
        self.assertEqual(items[0]['type'], 'PRIVATE')
        self.assertEqual(items[0]['status'], 'has been sent')

        # assert queue notice
        self.assertEqual(items[2]['id'], 3)
        self.assertEqual(items[2]['title'], 'title3')
        self.assertEqual(items[2]['type'], 'PRIVATE')
        self.assertEqual(items[2]['status'], 'ready to send')

        # assert draft notice
        self.assertEqual(items[3]['id'], 1)
        self.assertEqual(items[3]['title'], 'title1')
        self.assertEqual(items[3]['type'], 'SYSTEM')
        self.assertEqual(items[3]['status'], 'draft')

    def test_page_no_data(self):
        data = {'page': 2, 'size': 10}
        resp = self.client.get(reverse('admin-notice'), data=data)
        self.assertEqual(resp.status_code, 200)
        resp_json = resp.json()
        self.assertEqual(resp_json['total'], 4)
        self.assertEqual(resp_json['max_page'], 1)
        self.assertEqual(resp_json['page'], 2)
        self.assertListEqual(resp_json['items'], [])


class AdminCreateNoticeCase(TestCase):
    """test post notice"""
    fixtures = ('notice_types.json', 'receiver_types.json',)

    def setUp(self):
        User.objects.create_user('testuser', 'user@test.com', '123456')

    def test_success_draft(self):
        self.client.login(username='testuser', password='123456')
        title = 'notice title'
        content = 'notice content'
        data = {
            'title': title,
            'content': content,
            'receiver_type_id': 1,
            'send_way': NoticeForm.SendWayEnum.NO.value,
            'publish_at': None,
            'type_id': 1
        }
        self.client.json_encoder = json.JSONEncoder
        resp = self.client.post(reverse('admin-notice'), data=data, content_type='application/json')
        resp_json = resp.json()
        notice: NoticeStore = NoticeStore.objects.get(pk=resp_json['id'])
        self.assertEqual(notice.title, title)
        self.assertEqual(notice.content, content)
        self.assertEqual(notice.receiver_type_id, 1)
        self.assertEqual(notice.notice_type_id, 1)
        self.assertEqual(notice.status, NoticeStore.StatusEnum.DRAFT)

    def test_success_timing(self):
        self.client.login(username='testuser', password='123456')
        title = 'notice title'
        content = 'notice content'
        data = {
            'title': title,
            'content': content,
            'receiver_type_id': 1,
            'send_way': NoticeForm.SendWayEnum.TIMING.value,
            'publish_at': (timezone_now()+timedelta(days=2)).strftime(NOTICE_DATETIME_FORMAT),
            'type_id': 1
        }
        self.client.json_encoder = json.JSONEncoder
        resp = self.client.post(reverse('admin-notice'), data=data, content_type='application/json')
        resp_json = resp.json()
        notice: NoticeStore = NoticeStore.objects.get(pk=resp_json['id'])
        self.assertEqual(notice.title, title)
        self.assertEqual(notice.content, content)
        self.assertEqual(notice.receiver_type_id, 1)
        self.assertEqual(notice.notice_type_id, 1)
        self.assertEqual(notice.status, NoticeStore.StatusEnum.QUEUE)

    def test_success_now(self):
        self.client.login(username='testuser', password='123456')
        title = 'notice title'
        content = 'notice content'
        data = {
            'title': title,
            'content': content,
            'receiver_type_id': 1,
            'send_way': NoticeForm.SendWayEnum.NOW.value,
            'publish_at': (timezone_now()+timedelta(days=2)).strftime(NOTICE_DATETIME_FORMAT),
            'type_id': 1
        }
        self.client.json_encoder = json.JSONEncoder
        resp = self.client.post(reverse('admin-notice'), data=data, content_type='application/json')
        resp_json = resp.json()
        notice: NoticeStore = NoticeStore.objects.get(pk=resp_json['id'])
        self.assertEqual(notice.title, title)
        self.assertEqual(notice.content, content)
        self.assertEqual(notice.receiver_type_id, 1)
        self.assertEqual(notice.notice_type_id, 1)
        self.assertEqual(notice.status, NoticeStore.StatusEnum.DONE)


class AdminRetrieveNoticeCase(TestCase):
    fixtures = ('notice_types.json', 'receiver_types.json', 'notice.json')

    def test_draft(self):
        resp = self.client.get(reverse('admin-some-notice', kwargs={'pk': 1}))
        resp_json = resp.json()
        self.assertEqual(resp_json['id'], 1)
        self.assertEqual(resp_json['title'], 'title1')
        self.assertEqual(resp_json['content'], 'content1')
        self.assertIsNone(resp_json['publish_at'])

    def test_queue(self):
        resp = self.client.get(reverse('admin-some-notice', kwargs={'pk': 3}))
        resp_json = resp.json()
        self.assertEqual(resp_json['id'], 3)
        self.assertEqual(resp_json['title'], 'title3')
        self.assertEqual(resp_json['content'], 'content3')
        self.assertIsNone(resp_json['publish_at'])

    def test_done(self):
        resp = self.client.get(reverse('admin-some-notice', kwargs={'pk': 4}))
        resp_json = resp.json()
        self.assertEqual(resp_json['id'], 4)
        self.assertEqual(resp_json['title'], 'title4')
        self.assertEqual(resp_json['content'], 'content4')
        self.assertIsNotNone(resp_json['publish_at'])

    def test_deleted(self):
        resp = self.client.get(reverse('admin-some-notice', kwargs={'pk': 2}))
        self.assertEqual(resp.status_code, 404)

    def test_unknown(self):
        resp = self.client.get(reverse('admin-some-notice', kwargs={'pk': 2000}))
        self.assertEqual(resp.status_code, 404)


class AdminPutNoticeCase(TestCase):
    fixtures = ('notice_types.json', 'receiver_types.json', 'notice.json')

    def client_request(self, pk, data):
        self.client.json_encoder = json.JSONEncoder
        return self.client.put(reverse('admin-some-notice', kwargs={'pk': pk}), data=data, content_type='application/json')

    def test_draft2queue(self):
        """turn draft to queue"""
        title = 'title11'
        content = 'content11'
        receiver_type_id = 3
        type_id = 3
        publish_at = (timezone_now()+timedelta(days=22)).strftime(NOTICE_DATETIME_FORMAT)
        data = {
            'title': title,
            'content': content,
            'receiver_type_id': receiver_type_id,
            'send_way': NoticeForm.SendWayEnum.TIMING.value,
            'publish_at': publish_at,
            'type_id': type_id
        }
        pk = 1
        resp = self.client_request(pk, data)
        self.assertEqual(resp.status_code, 200)
        notice: NoticeStore = NoticeStore.objects.get(pk=pk)
        self.assertEqual(notice.title, title)
        self.assertEqual(notice.content, content)
        self.assertEqual(notice.receiver_type_id, receiver_type_id)
        self.assertEqual(notice.notice_type_id, type_id)
        self.assertEqual(notice.publish_at.strftime(NOTICE_DATETIME_FORMAT), publish_at)
        self.assertEqual(notice.status, NoticeStore.StatusEnum.QUEUE)

    def test_draft2draft(self):
        """turn draft to draft"""
        title = 'title11'
        content = 'content11'
        receiver_type_id = 3
        type_id = 3
        publish_at = (timezone_now()+timedelta(days=22)).strftime(NOTICE_DATETIME_FORMAT)
        data = {
            'title': title,
            'content': content,
            'receiver_type_id': receiver_type_id,
            'send_way': NoticeForm.SendWayEnum.NO.value,
            'publish_at': publish_at,
            'type_id': type_id
        }
        pk = 1
        resp = self.client_request(pk, data)
        self.assertEqual(resp.status_code, 200)
        notice: NoticeStore = NoticeStore.objects.get(pk=pk)
        self.assertEqual(notice.title, title)
        self.assertEqual(notice.content, content)
        self.assertEqual(notice.receiver_type_id, receiver_type_id)
        self.assertIsNone(notice.publish_at)
        self.assertEqual(notice.notice_type_id, type_id)
        self.assertEqual(notice.status, NoticeStore.StatusEnum.DRAFT)

    def test_draft2draft(self):
        """turn draft to done"""
        title = 'title11'
        content = 'content11'
        receiver_type_id = 3
        type_id = 3
        publish_at = (timezone_now()+timedelta(days=22)).strftime(NOTICE_DATETIME_FORMAT)
        data = {
            'title': title,
            'content': content,
            'receiver_type_id': receiver_type_id,
            'send_way': NoticeForm.SendWayEnum.NOW.value,
            'publish_at': publish_at,
            'type_id': type_id
        }
        pk = 1
        resp = self.client_request(pk, data)
        self.assertEqual(resp.status_code, 200)
        notice: NoticeStore = NoticeStore.objects.get(pk=pk)
        self.assertEqual(notice.title, title)
        self.assertEqual(notice.content, content)
        self.assertEqual(notice.receiver_type_id, receiver_type_id)
        self.assertEqual(notice.status, NoticeStore.StatusEnum.DONE)

    def test_queue(self):
        title = 'title11'
        content = 'content11'
        receiver_type_id = 3
        type_id = 3
        publish_at = (timezone_now()+timedelta(days=22)).strftime(NOTICE_DATETIME_FORMAT)
        data = {
            'title': title,
            'content': content,
            'receiver_type_id': receiver_type_id,
            'send_way': NoticeForm.SendWayEnum.NOW.value,
            'publish_at': publish_at,
            'type_id': type_id
        }
        pk = 3
        resp = self.client_request(pk, data)
        self.assertEqual(resp.status_code, 400)

    def test_done(self):
        title = 'title11'
        content = 'content11'
        receiver_type_id = 3
        type_id = 3
        publish_at = (timezone_now()+timedelta(days=22)).strftime(NOTICE_DATETIME_FORMAT)
        data = {
            'title': title,
            'content': content,
            'receiver_type_id': receiver_type_id,
            'send_way': NoticeForm.SendWayEnum.NOW.value,
            'publish_at': publish_at,
            'type_id': type_id
        }
        pk = 4
        resp = self.client_request(pk, data)
        self.assertEqual(resp.status_code, 400)


class AdminDeleteNoticeCase(TestCase):
    fixtures = ('notice_types.json', 'receiver_types.json', 'notice.json')

    def test_draft(self):
        resp = self.client.delete(reverse('admin-some-notice', kwargs={'pk': 1}))
        self.assertEqual(resp.status_code, 200)
        notice = NoticeStore.all_objects.get(pk=1)
        self.assertTrue(notice.is_deleted)

    def test_queue(self):
        resp = self.client.delete(reverse('admin-some-notice', kwargs={'pk': 3}))
        self.assertEqual(resp.status_code, 400)

    def test_done(self):
        resp = self.client.delete(reverse('admin-some-notice', kwargs={'pk': 4}))
        self.assertEqual(resp.status_code, 400)


class AdminDeleteTimingCase(TestCase):
    fixtures = ('notice_types.json', 'receiver_types.json', 'notice.json')

    def test_draft(self):
        resp = self.client.delete(reverse('admin-change-timing-notice', kwargs={'pk': 1}))
        self.assertEqual(resp.status_code, 400)

    def test_queue(self):
        resp = self.client.delete(reverse('admin-change-timing-notice', kwargs={'pk': 3}))
        self.assertEqual(resp.status_code, 200)
        notice = NoticeStore.all_objects.get(pk=3)
        self.assertTrue(notice.is_draft)
        self.assertIsNone(notice.publish_at)
        self.assertEqual(notice.status, NoticeStore.StatusEnum.DRAFT)

    def test_done(self):
        resp = self.client.delete(reverse('admin-change-timing-notice', kwargs={'pk': 4}))
        self.assertEqual(resp.status_code, 400)


class AdminPutTimingCase(TestCase):
    fixtures = ('notice_types.json', 'receiver_types.json', 'notice.json')

    def client_request(self, pk, publish_at):
        self.client.json_encoder = json.JSONEncoder
        data = {
            'publish_at': publish_at.strftime(NOTICE_DATETIME_FORMAT)
        }
        return self.client.put(reverse('admin-change-timing-notice', kwargs={'pk': pk}), data=data, content_type='application/json')

    def test_draft(self):
        resp = self.client_request(1, timezone_now()+timedelta(days=3))
        self.assertEqual(resp.status_code, 400)

    def test_queue(self):
        publish_at = timezone_now()+timedelta(days=3)
        resp = self.client_request(3, publish_at)
        self.assertEqual(resp.status_code, 200)
        notice = NoticeStore.all_objects.get(pk=3)
        self.assertEqual(notice.publish_at.strftime(NOTICE_DATETIME_FORMAT), publish_at.strftime(NOTICE_DATETIME_FORMAT))
        self.assertEqual(notice.status, NoticeStore.StatusEnum.QUEUE)

    def test_done(self):
        resp = self.client_request(4, timezone_now()+timedelta(days=3))
        self.assertEqual(resp.status_code, 400)


class ClientListNotice(TestCase):
    fixtures = ('notice_types.json', 'receiver_types.json', 'notice.json', 'notice_tag.json')

    def setUp(self):
        User.objects.create_user('testuser', 'user@test.com', '123456', pk=1)

    def test_have_data(self):
        self.client.login(username='testuser', password='123456')
        resp = self.client.get(reverse('client-list-notice'))
        resp_json = resp.json()
        self.assertEqual(resp_json['total'], 2)
        self.assertEqual(resp_json['max_page'], 1)
        self.assertEqual(resp_json['page'], 1)

        items = resp_json['items']
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]['id'], 5)
        self.assertTrue(items[0]['is_read'])

        self.assertFalse(items[1]['is_read'])


class ClientRetreiveNotice(TestCase):
    fixtures = ('notice_types.json', 'receiver_types.json', 'notice.json', 'notice_tag.json')

    def setUp(self):
        User.objects.create_user('testuser', 'user@test.com', '123456', pk=1)

    def client_request(self, pk):
        self.client.login(username='testuser', password='123456')
        return self.client.get(reverse('client-retrieve-notice', kwargs={'pk': pk}))

    def test_draft(self):
        resp = self.client_request(1)
        self.assertEqual(resp.status_code, 404)

    def test_deleted(self):
        resp = self.client_request(2)
        self.assertEqual(resp.status_code, 404)

    def test_queue(self):
        resp = self.client_request(3)
        self.assertEqual(resp.status_code, 404)

    def test_unread(self):
        self.assertFalse(ReceiverTag.objects.filter(noticestore_id=4, receiver_id=1).exists())
        resp = self.client_request(4)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(ReceiverTag.objects.filter(noticestore_id=4, receiver_id=1).exists())

    def test_unread(self):
        self.assertTrue(ReceiverTag.objects.filter(noticestore_id=5, receiver_id=1).exists())
        resp = self.client_request(5)
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(ReceiverTag.objects.filter(noticestore_id=5, receiver_id=1).exists())