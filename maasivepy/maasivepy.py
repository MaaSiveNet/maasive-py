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


LIMIT_RE = re.compile(r'(limit=0)($|&)')
OFFSET_RE = re.compile(r'(offset=[0-9a-fA-F]{24})($|&)')


def limit_zero_read_iterator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]
        limit_zero = LIMIT_RE.search(args[1])
        if not limit_zero:
            return func(*args, **kwargs)
        original_offset = OFFSET_RE.search(args[1])
        has_more = False
        url = re.sub(r'limit=0', 'limit=%d' % self.limit, args[1])
        response = func(self, url, **kwargs)
        r_json = response.json()
        offset = None
        content_length = int(response.headers['Content-Length'])
        if isinstance(r_json, list) and len(r_json) == self.limit:
            offset = r_json[-1]['id']
            has_more = True
        if original_offset and offset:
            url = re.sub(r'offset=[0-9a-fA-F]{24}', 'offset=%s' % offset, url)
        elif offset:
            url += '&offset=%s' % offset
        while has_more:
            r = func(self, url, **kwargs)
            r_json = r.json()
            setattr(response, '_content', b','.join([response.content[:-1], r.content[1:]]))
            content_length += int(r.headers['Content-Length'])
            if len(r_json) < self.limit:
                has_more = False
            else:
                offset = r_json[-1]['id']
                url = re.sub(r'offset=[0-9a-fA-F]{24}', 'offset=%s' % offset, url)
        response.headers['Content-Length'] = str(content_length)
        return response

    return wrapper


def batch_write_iterator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]
        if not (isinstance(kwargs.get('data'), list) and len(kwargs['data']) > self.limit):
            return func(*args, **kwargs)
        data = kwargs.pop('data')
        batch_count = int(len(data) / self.limit)
        if (len(data) % self.limit) == 0:
            batch_count -= 1
        response = func(*args, data=data[:self.limit])
        content_length = int(response.headers['Content-Length'])
        for bc in range(batch_count):
            slice_start = (bc+1) * self.limit
            slice_stop = slice_start + self.limit
            if slice_stop > len(data):
                slice_stop = len(data)
            r = func(*args, data=data[slice_start:slice_stop])
            setattr(response, '_content', b','.join([response.content[:-1], r.content[1:]]))
            content_length += int(r.headers['Content-Length'])
        return response

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
                 max_history=25,
                 limit=100):
        self.api_uri = api_uri
        self.last_call_timestamp = 0
        self.session = requests.Session()
        self.rl_window_ts = 0
        self.rps = requests_per_second
        self.rl_window_count = 0
        self.print_pretty = verbose
        self.verbose = verbose
        self.current_user = None
        self.limit = limit
        if admin_key and auth_token:
            raise ValueError('use only one of api_key or auth_token')
        self.admin_key = None
        if admin_key:
            self.admin_key = admin_key
            self.session.headers.update({'X-Admin-Key': admin_key})
        self.auth_token = None
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
    @track_history
    @serialize_json_data
    @limit_zero_read_iterator
    @verbose_output
    def get(self, url, **kwargs):
        return self.session.get(''.join([self.api_uri, url]), **kwargs)

    @limit_rate
    @pr_pretty
    @verbose_output
    @track_history
    @batch_write_iterator
    @serialize_json_data
    def post(self, url, **kwargs):
        return self.session.post(''.join([self.api_uri, url]), **kwargs)

    @limit_rate
    @pr_pretty
    @verbose_output
    @track_history
    @batch_write_iterator
    @serialize_json_data
    def put(self, url, **kwargs):
        return self.session.put(''.join([self.api_uri, url]), **kwargs)

    @limit_rate
    @pr_pretty
    @verbose_output
    @track_history
    @serialize_json_data
    @limit_zero_read_iterator
    def delete(self, url, **kwargs):
        return self.session.delete(''.join([self.api_uri, url]), **kwargs)
