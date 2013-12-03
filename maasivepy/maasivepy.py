__author__ = 'ntrepid8'
import requests
import json
from functools import wraps
from time import time, sleep


def limit_rate(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]
        if self.rl_window_ts == 0:
            self.rl_window_ts = time()
        if self.rl_window_count >= self.rps:
            sleep(1)
            self.rl_window_count = 0
            self.rl_window_ts = time()
        self.rl_window_count += 1
        return func(*args, **kwargs)
    return wrapper


def pr_pretty(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]
        r = func(*args, **kwargs)
        if self.print_pretty and r.status_code == requests.codes.ok:
            try:
                print(json.dumps(r.json(), sort_keys=True, indent=2))
            except ValueError as e:
                print(e)
        return r
    return wrapper


class MaaSiveAPISession(object):
    """
    Class used for interaction with MaaSive.net

    init takes the base path to the api:
    api_uri = https://maasive.net/v2/<api_id>
    """

    def __init__(self, api_uri, requests_per_second=1, print_pretty=False):
        self.api_uri = api_uri
        self.last_call_timestamp = 0
        self.session = requests.Session()
        self.rl_window_ts = 0
        self.rps = requests_per_second
        self.rl_window_count = 0
        self.print_pretty = print_pretty

    @limit_rate
    @pr_pretty
    def login(self, email, password):
        r = self.session.post(
            self.api_uri + '/auth/login/',
            data=json.dumps({"email": email,
                             "password": password}))
        if r.status_code != 200:
            raise ValueError('login error: %s' % str(r.reason))
        return r

    @limit_rate
    @pr_pretty
    def options(self, url, **kwargs):
        return self.session.options(''.join([self.api_uri, url]), **kwargs)

    @limit_rate
    @pr_pretty
    def get(self, url, **kwargs):
        return self.session.get(''.join([self.api_uri, url]), **kwargs)

    @limit_rate
    @pr_pretty
    def post(self, url, **kwargs):
        return self.session.post(''.join([self.api_uri, url]), **kwargs)

    @limit_rate
    @pr_pretty
    def put(self, url, **kwargs):
        return self.session.put(''.join([self.api_uri, url]), **kwargs)

    @limit_rate
    @pr_pretty
    def delete(self, url, **kwargs):
        return self.session.delete(''.join([self.api_uri, url]), **kwargs)
