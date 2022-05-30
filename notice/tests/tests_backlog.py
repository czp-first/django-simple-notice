# -*- coding: UTF-8 -*-
"""
@Summary : docstr
@Author  : Rey
@Time    : 2022-05-27 16:09:44
@Run     : python manage.py test notice.tests.tests_backlog -v 3 --keepdb
"""

from datetime import datetime, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from notice.models import Backlog
from notice.settings import NOTICE_DATETIME_FORMAT


class TestCreateBacklog(TestCase):
    """test post backlog"""

    def setUp(self):
        User.objects.create_user('tester', 'user@test.com', '123456', pk=1)

    def client_request(self, data):
        self.client.login(username='tester', password='123456')
        return self.client.post(reverse('backlog'), data=data, content_type='application/json')

    def test_success_1(self):
        """test create complete backlog"""

        batch = 'batch1'
        is_done = False
        receivers = ['receiver1', 'receiver2']
        initiator = 'initiator1'
        initiator_name = 'initiator1 name'
        initiated_at = '2021-10-15 20:00:00'
        obj_name = 'obj1 name'
        obj_key = 'obj1 key'
        obj_status = 'obj1 status'
        handlers = ['handler1', 'handler2']
        candidates = ['candidate1', 'candidate2']
        obj_associated_data = 'cc1'
        obj_associated_data_type = 'cc1 type'
        company = 'company1'
        company_type = 'company1 type'
        data_data = {'username': 'username1'}

        data = {
            'batch': batch,
            'is_done': is_done,
            'receivers': receivers,
            'initiator': initiator,
            'initiator_name': initiator_name,
            'initiated_at': initiated_at,
            'obj_name': obj_name,
            'obj_key': obj_key,
            'obj_status': obj_status,
            'handlers': handlers,
            'candidates': candidates,
            'obj_associated_data': obj_associated_data,
            'obj_associated_data_type': obj_associated_data_type,
            'company': company,
            'company_type': company_type,
            'data' : data_data
        }
        resp = self.client_request(data)
        self.assertEqual(resp.status_code, 200)
        resp_json = resp.json()
        backlog_ids = resp_json['id']
        for idx, backlog_id in enumerate(backlog_ids):
            backlog: Backlog = Backlog.objects.get(pk=backlog_id)
            self.assertEqual(backlog.receiver, receivers[idx])
            self.assertEqual(backlog.batch, batch)
            self.assertEqual(backlog.is_done, is_done)
            self.assertEqual(backlog.initiator, initiator)
            self.assertEqual(backlog.initiator_name, initiator_name)
            self.assertEqual(backlog.initiated_at.strftime('%Y-%m-%d %H:%M:%S'), initiated_at)
            self.assertEqual(backlog.obj_name, obj_name)
            self.assertEqual(backlog.obj_key, obj_key)
            self.assertEqual(backlog.obj_status, obj_status)
            self.assertEqual(backlog.handlers, handlers)
            self.assertEqual(backlog.candidates, candidates)
            self.assertEqual(backlog.obj_associated_data, obj_associated_data)
            self.assertEqual(backlog.obj_associated_data_type, obj_associated_data_type)
            self.assertEqual(backlog.company, company)
            self.assertEqual(backlog.company_type, company_type)
            self.assertEqual(backlog.data, data_data)


class TestGetBacklogStatistics(TestCase):
    """test get backlog statistics"""

    def setUp(self) -> None:
        user = User.objects.create_user('tester', 'user@test.com', '123456', pk=1)
        Backlog.objects.bulk_create(
            [
                Backlog(receiver=str(user.pk), is_done=False),
                Backlog(receiver=str(user.pk), is_done=False),
                Backlog(receiver=str(user.pk), is_done=True),
                Backlog(receiver='system', is_done=False),
            ]
        )

    def client_request(self):
        self.client.login(username='tester', password='123456')
        return self.client.get(reverse('backlog'))

    def test_success(self):
        resp = self.client_request()
        self.assertEqual(resp.status_code, 200)
        resp_json = resp.json()
        self.assertEqual(resp_json['undo'], 2)
        self.assertEqual(resp_json['done'], 1)
        self.assertEqual(resp_json['total'], 3)


class TestGetBacklogs(TestCase):
    """test get backlogs"""

    def setUp(self) -> None:
        User.objects.create_user('tester', 'user@test.com', '123456', pk=1)
        Backlog.objects.bulk_create([
            Backlog(receiver='aaaa', is_done=False, obj_key='objkey1', obj_name='objname1', initiator_name='initiatorname1', obj_status='通过',),
            Backlog(receiver='aaaa', is_done=True, obj_key='objkey3', obj_name='objname3', initiator_name='initiatorname3', obj_status='通过',),
            Backlog(receiver='1', is_done=False, obj_key='objkey1', obj_name='objname1', initiator_name='initiatorname1', obj_status='通过',),
            Backlog(receiver='1', is_done=True, obj_key='objkey2', obj_name='objname2', initiator_name='initiatorname2', obj_status='撤回',),
            Backlog(receiver='1', is_done=True, obj_key='objkey3', obj_name='objname3', initiator_name='initiatorname3', obj_status='通过',),
            Backlog(receiver='1', is_done=True, obj_key='objkey3', obj_name='objname3', initiator_name='initiatorname3', obj_status='通过',),
        ])

    def client_request(self, params):
        self.client.login(username='tester', password='123456')
        params_path = '?'
        for key, value in params.items():
            params_path += f'{key}={value if value else ""}&'
        if params_path.endswith('&'):
            params_path = params_path[:-1]
        path = reverse('backlogs') + params_path
        return self.client.get(path)

    def get_params(
        self, backlog_type: str = None,
        keyword: str = None,
        start: str = None,
        end: str = None,
        obj_status: str = None,
        page: str = '1',
        size: str = '10',
    ):
        return {
            'backlog_type': backlog_type,
            'keyword': keyword,
            'start': start,
            'end': end,
            'obj_status': obj_status,
            'page': page,
            'size': size,
        }

    def test_success_backlog_type_all(self):
        """get all backlogs"""
        params = self.get_params()
        resp = self.client_request(params)
        resp_json = resp.json()
        self.assertEqual(len(resp_json['items']), 4)

    def test_success_backlog_type_all_1(self):
        """get all backlogs"""
        params = self.get_params(backlog_type='')
        resp = self.client_request(params)
        resp_json = resp.json()
        self.assertEqual(len(resp_json['items']), 4)

    def test_success_backlog_type_undo(self):
        """get undo backlogs"""
        params = self.get_params(backlog_type='undo')
        resp = self.client_request(params)
        resp_json = resp.json()
        self.assertEqual(len(resp_json['items']), 1)

    def test_success_backlog_type_done(self):
        """get done backlogs"""
        params = self.get_params(backlog_type='done')
        resp = self.client_request(params)
        resp_json = resp.json()
        self.assertEqual(len(resp_json['items']), 3)

    def test_success_keyword_obj_key(self):
        """get backlogs filter obj key"""
        params = self.get_params(
            backlog_type='done', keyword='objkey3',
        )
        resp = self.client_request(params)
        resp_json = resp.json()
        self.assertEqual(len(resp_json['items']), 2)

    def test_success_keyword_obj_name(self):
        """get backlogs filter obj key"""
        params = self.get_params(
            backlog_type='done', keyword='objname3',
        )
        resp = self.client_request(params)
        resp_json = resp.json()
        self.assertEqual(len(resp_json['items']), 2)

    def test_success_keyword_initiator_name(self):
        """get backlogs filter initiator name"""
        params = self.get_params(
            backlog_type='done', keyword='initiatorname3',
        )
        resp = self.client_request(params)
        resp_json = resp.json()
        self.assertEqual(len(resp_json['items']), 2)

    def test_success_start_all(self):
        """get backlogs filter start all"""
        start = (datetime.now() - timedelta(days=1)).strftime(NOTICE_DATETIME_FORMAT)
        params = self.get_params(
            backlog_type='done', start=start,
        )
        resp = self.client_request(params)
        resp_json = resp.json()
        self.assertEqual(len(resp_json['items']), 3)

    def test_success_start_none(self):
        """get backlogs filter start none"""
        start = (datetime.now() + timedelta(days=1)).strftime(NOTICE_DATETIME_FORMAT)
        params = self.get_params(
            backlog_type='done', start=start,
        )
        resp = self.client_request(params)
        resp_json = resp.json()
        self.assertEqual(len(resp_json['items']), 0)

    def test_success_end_all(self):
        """get backlogs filter end all"""
        end = (datetime.now() + timedelta(days=1)).strftime(NOTICE_DATETIME_FORMAT)
        params = self.get_params(
            backlog_type='done', end=end,
        )
        resp = self.client_request(params)
        resp_json = resp.json()
        self.assertEqual(len(resp_json['items']), 3)

    def test_success_end_none(self):
        """get backlogs filter end none"""
        end = (datetime.now() - timedelta(days=1)).strftime(NOTICE_DATETIME_FORMAT)
        params = self.get_params(
            backlog_type='done', end=end,
        )
        resp = self.client_request(params)
        resp_json = resp.json()
        self.assertEqual(len(resp_json['items']), 0)

    def test_success_obj_status(self):
        """get backlogs filter obj_status"""
        params = self.get_params(
            backlog_type='done', obj_status='通过',
        )
        resp = self.client_request(params)
        resp_json = resp.json()
        self.assertEqual(len(resp_json['items']), 2)


class TestReadBacklog(TestCase):
    """test read backlog"""

    def setUp(self):
        User.objects.create_user('tester', 'user@test.com', '123456', pk=1)
        Backlog.objects.bulk_create([
            Backlog(receiver='1', pk=1),
            Backlog(receiver='2', pk=2),
        ])

    def client_request(self, backlog_pk):
        self.client.login(username='tester', password='123456')
        return self.client.put(reverse('read-backlog', kwargs={'pk': backlog_pk}))

    def test_success(self):
        backlog = Backlog.objects.get(pk=1)
        self.assertFalse(backlog.is_read)
        resp = self.client_request(1)
        self.assertEqual(resp.status_code, 200)
        backlog = Backlog.objects.get(pk=1)
        self.assertTrue(backlog.is_read)


class TestBatchHandleBacklog(TestCase):
    def setUp(self):
        User.objects.create_user('tester', 'user@test.com', '123456', pk=1)
        Backlog.objects.bulk_create([
            Backlog(pk=1, is_deleted=False, receiver='1', handlers=['5'], is_done=False, batch='1', data={'node': 1}),
            Backlog(pk=2, is_deleted=False, receiver='2', handlers=['5'], is_done=False, batch='1', data={'node': 1}),
            Backlog(pk=3, is_deleted=False, receiver='3', handlers=['5'], is_done=False, batch='1', data={'node': 1}),
            Backlog(pk=4, is_deleted=False, receiver='2', handlers=['5'], is_done=False, batch='2', data={'node': 1}),
        ])

    def client_request(self, data):
        self.client.login(username='tester', password='123456')
        return self.client.post(reverse('handle-backlog'), data=data, content_type='application/json')

    def test_success_done(self):
        data = {
            'batch': '1',
            'is_done': True,
            'handler': '3'
        }
        resp = self.client_request(data)
        self.assertEqual(resp.status_code, 200)

        backlog1 = Backlog.all_objects.get(pk=1)
        self.assertTrue(backlog1.is_deleted)

        backlog2 = Backlog.all_objects.get(pk=2)
        self.assertTrue(backlog2.is_deleted)

        backlog3 = Backlog.objects.get(pk=3)
        self.assertListEqual(backlog3.handlers, ['5', '3'])
        self.assertTrue(backlog3.is_done)

        backlog3 = Backlog.objects.get(pk=4)
        self.assertFalse(backlog3.is_done)

    def test_success_undo(self):
        data = {
            'batch': '1',
            'is_done': False,
            'handler': '3'
        }
        resp = self.client_request(data)
        self.assertEqual(resp.status_code, 200)
        backlog1 = Backlog.objects.get(pk=1)
        self.assertListEqual(backlog1.handlers, ['5', '3'])
        self.assertFalse(backlog1.is_done)

        backlog2 = Backlog.objects.get(pk=2)
        self.assertListEqual(backlog2.handlers, ['5', '3'])
        self.assertFalse(backlog2.is_done)

        backlog3 = Backlog.objects.get(pk=3)
        self.assertListEqual(backlog3.handlers, ['5', '3'])
        self.assertFalse(backlog3.is_done)

        backlog3 = Backlog.objects.get(pk=4)
        self.assertFalse(backlog3.is_done)

    def test_success_done_with_data(self):
        data = {
            'batch': '1',
            'is_done': True,
            'handler': '3',
            'data': {'username': 'rey'}
        }
        resp = self.client_request(data)
        self.assertEqual(resp.status_code, 200)

        backlog1 = Backlog.all_objects.get(pk=1)
        self.assertTrue(backlog1.is_deleted)

        backlog2 = Backlog.all_objects.get(pk=2)
        self.assertTrue(backlog2.is_deleted)

        backlog3 = Backlog.objects.get(pk=3)
        self.assertListEqual(backlog3.handlers, ['5', '3'])
        self.assertTrue(backlog3.is_done)
        self.assertDictEqual(backlog3.data, {'node': 1, 'username': 'rey'})

        backlog3 = Backlog.objects.get(pk=4)
        self.assertFalse(backlog3.is_done)


class TestBatchHandleObj(TestCase):
    def setUp(self):
        User.objects.create_user('tester', 'user@test.com', '123456', pk=1)
        Backlog.objects.bulk_create([
            Backlog(pk=1, is_deleted=False, receiver='1', obj_key='key1', handlers=['5'], is_done=False, batch='1', data={'node': 1}),
            Backlog(pk=2, is_deleted=False, receiver='2', obj_key='key1', handlers=['5'], is_done=False, batch='1', data={'node': 1}),
            Backlog(pk=3, is_deleted=False, receiver='3', obj_key='key1', handlers=['5'], is_done=False, batch='1', data={'node': 1}),
            Backlog(pk=4, is_deleted=False, receiver='2', obj_key='key2', handlers=['5'], is_done=False, batch='2', data={'node': 1}),
        ])

    def client_request(self, data):
        self.client.login(username='tester', password='123456')
        return self.client.post(reverse('handle-obj'), data=data, content_type='application/json')

    def test_handle_with_data(self):
        data = {
            'key': 'key1',
            'status': 'pending',
            'data': {'username': 'rey'}
        }
        resp = self.client_request(data)
        self.assertEqual(resp.status_code, 200)

        backlogs = Backlog.objects.filter(pk__in=[1, 2, 3])
        for backlog in backlogs:
            self.assertEqual(backlog.obj_status, 'pending')
            self.assertDictEqual(backlog.data, {'node': 1, 'username': 'rey'})

        backlog4 = Backlog.objects.get(pk=4)
        self.assertIsNone(backlog4.obj_status)
        self.assertDictEqual(backlog4.data, {'node': 1})

    def test_handle_with_no_data(self):
        data = {
            'key': 'key1',
            'status': 'pending',
        }
        resp = self.client_request(data)
        self.assertEqual(resp.status_code, 200)

        backlogs = Backlog.objects.filter(pk__in=[1, 2, 3])
        for backlog in backlogs:
            self.assertEqual(backlog.obj_status, 'pending')
            self.assertDictEqual(backlog.data, {'node': 1})

        backlog4 = Backlog.objects.get(pk=4)
        self.assertIsNone(backlog4.obj_status)
        self.assertDictEqual(backlog4.data, {'node': 1})
