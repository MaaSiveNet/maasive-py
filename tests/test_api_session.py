__author__ = 'ntrepid8'
import unittest
import maasivepy
import os


class TestMaaSiveApiSession(unittest.TestCase):

    def test_limit_zero(self):
        api_session = maasivepy.APISession(os.environ['MAASIVEPY_TEST_API_URL'])
        api_session.limit = 100
        options = api_session.options('/contacts/').json()
        r = api_session.get('/contacts/?limit=0')
        r_json = r.json()
        self.assertEqual(r.status_code, 200)
        self.assertEqual(len(r_json), options['resource_count'])

    def test_batch_upload(self):
        api_session = maasivepy.APISession(
            os.environ['MAASIVEPY_TEST_API_URL'],
            admin_key=os.environ['MAASIVEPY_TEST_API_ADMIN_KEY'])
        api_session.limit = 2
        c = api_session.get('/contacts/?limit=6').json()
        r = api_session.post('/contacts/', data=c)
        r_json = r.json()
        self.assertEqual(len(r_json), len(c))
