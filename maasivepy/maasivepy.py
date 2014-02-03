__author__ = 'ntrepid8'
from functools import wraps, partial
from collections import deque
from time import time, sleep
from pprint import pprint as lib_pprint
import requests
import json
import re


def limit_rate(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]
        if self.rl_window_ts == 0:
            self.rl_window_ts = time()
        elif time() - self.rl_window_ts < 1:
            # still inside the window
            if self.rl_window_count >= self.rps:
                sleep_time = time() - self.rl_window_ts
                if self.verbose is True:
                    print('sleeping for %s...' % str(sleep_time))
                sleep(sleep_time)
                self.rl_window_count = 0
                self.rl_window_ts = time()
        else:
            # new time window, new request quota
            self.rl_window_count = 0
            self.rl_window_ts = time()
        # increment the count and execute the request
        self.rl_window_count += 1
        return func(*args, **kwargs)
    return wrapper


def pr_pretty(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        r = func(*args, **kwargs)
        r_content_type = r.headers.get('content-type') or ''
        pretty_req = [
            re.search('application/json', r_content_type),
        ]
        pretty = None
        if all(pretty_req):
            pretty = r.json()
        r.pprint = partial(lib_pprint, pretty)
        return r
    return wrapper


def verbose_output(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]
        r = func(*args, **kwargs)
        if self.verbose is not True:
            return r
        if r.status_code == requests.codes.ok:
            status_msg = '%d %s %s in %s ms' % (
                r.status_code,
                str(func.__name__).upper(),
                str(r.url),
                str(r.elapsed.microseconds / 1000)
            )
        else:
            status_msg = '%d %s %s in %s ms - %s' % (
                r.status_code,
                str(func.__name__).upper(),
                str(r.url),
                str(r.elapsed.microseconds / 1000),
                r.reason
            )
        print(status_msg)
        return r
    return wrapper


def serialize_json_data(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        auto_serialize_cond = [
            isinstance(kwargs.get('data'), dict),
            isinstance(kwargs.get('data'), list),
        ]
        if any(auto_serialize_cond):
            kwargs['data'] = json.dumps(kwargs['data'])
            if isinstance(kwargs.get('headers'), dict):
                kwargs['headers']['Content-Type'] = 'application/json'
            else:
                kwargs['headers'] = {
                    'Content-Type': 'application/json'
                }
        return func(*args, **kwargs)
    return wrapper


def track_history(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]
        r = func(*args, **kwargs)
        h = (r.request.method, r.url, r)
        self._history.appendleft(h)
        return r
    return wrapper


class MaaSiveAPISession(object):
    """
    Class used for interaction with MaaSive.net

    init takes the base path to the api:
    api_uri = https://maasive.net/v2/<api_id>
    """

    def __init__(self,
                 api_uri,
                 requests_per_second=1,
                 verbose=True,
                 admin_key=None,
                 auth_token=None,
                 max_history=25):
        self.api_uri = api_uri
        self.last_call_timestamp = 0
        self.session = requests.Session()
        self.rl_window_ts = 0
        self.rps = requests_per_second
        self.rl_window_count = 0
        self.print_pretty = verbose
        self.verbose = verbose
        self.current_user = None
        if admin_key and auth_token:
            raise ValueError('use only one of api_key or auth_token')
        if admin_key:
            self.api_key = admin_key
            self.session.headers.update({'X-Admin-Key': admin_key})
        if auth_token:
            self.auth_token = auth_token
            self.session.headers.update({'X-Auth-Token': auth_token})
        self._history = deque(maxlen=max_history)
        self.store = {}

    @property
    def history(self):
        return list(self._history)

    def pprint(self, *args, **kwargs):
        arg_0 = args[0]
        args = args[1:]
        if isinstance(arg_0, str):
            arg_0 = getattr(self, arg_0)
        lib_pprint(arg_0, *args, **kwargs)

    @limit_rate
    @pr_pretty
    @verbose_output
    def login(self, email, password):
        other_auth = [
            self.admin_key is not None,
            self.auth_token is not None
        ]
        if any(other_auth):
            raise ValueError('auth via header already specified')
        r = self.session.post(
            self.api_uri + '/auth/login/',
            data=json.dumps({"email": email,
                             "password": password}))
        if r.status_code != requests.codes.ok:
            raise ValueError('login error: %s' % str(r.reason))
        self.current_user = r.json()
        return r

    @limit_rate
    @pr_pretty
    @verbose_output
    @track_history
    def options(self, url, **kwargs):
        return self.session.options(''.join([self.api_uri, url]), **kwargs)

    @limit_rate
    @pr_pretty
    @verbose_output
    @track_history
    @serialize_json_data
    def get(self, url, **kwargs):
        return self.session.get(''.join([self.api_uri, url]), **kwargs)

    @limit_rate
    @pr_pretty
    @verbose_output
    @track_history
    @serialize_json_data
    def post(self, url, **kwargs):
        return self.session.post(''.join([self.api_uri, url]), **kwargs)

    @limit_rate
    @pr_pretty
    @verbose_output
    @track_history
    @serialize_json_data
    def put(self, url, **kwargs):
        return self.session.put(''.join([self.api_uri, url]), **kwargs)

    @limit_rate
    @pr_pretty
    @verbose_output
    @track_history
    @serialize_json_data
    def delete(self, url, **kwargs):
        return self.session.delete(''.join([self.api_uri, url]), **kwargs)
