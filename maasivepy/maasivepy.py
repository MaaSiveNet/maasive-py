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
        if self.verbose is True:
            print('sending the request')
        self.rl_window_count += 1
        return func(*args, **kwargs)
    return wrapper


def pr_pretty(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]
        pretty = kwargs.pop('pretty', False)
        r = func(*args, **kwargs)
        if (self.print_pretty or pretty) and r is not None:
            try:
                print(json.dumps(r.json(), sort_keys=True, indent=2))
            except ValueError as e:
                print(e)
        return r
    return wrapper


def verbose_output(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        self = args[0]
        r = func(*args, **kwargs)
        if self.verbose:
            try:
                print('%s - %s in %s ms' % (
                    str(func.__name__).upper(),
                    str(r.url),
                    str(r.elapsed.microseconds / 1000)
                ))
                # print('time elapsed: %s ms' % str(r.elapsed.microseconds / 1000))
            except ValueError as e:
                print(e)
        else:
            print(r.status_code)
        return r
    return wrapper


class MaaSiveAPISession(object):
    """
    Class used for interaction with MaaSive.net

    init takes the base path to the api:
    api_uri = https://maasive.net/v2/<api_id>
    """

    def __init__(
            self, api_uri, requests_per_second=1, verbose=False):
        self.api_uri = api_uri
        self.last_call_timestamp = 0
        self.session = requests.Session()
        self.rl_window_ts = 0
        self.rps = requests_per_second
        self.rl_window_count = 0
        self.print_pretty = verbose
        self.verbose = verbose
        self.current_user = None

    @limit_rate
    @pr_pretty
    @verbose_output
    def login(self, email, password):
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
    def options(self, url, **kwargs):
        return self.session.options(''.join([self.api_uri, url]), **kwargs)

    @limit_rate
    @pr_pretty
    @verbose_output
    def get(self, url, **kwargs):
        return self.session.get(''.join([self.api_uri, url]), **kwargs)

    @limit_rate
    @pr_pretty
    @verbose_output
    def post(self, url, **kwargs):
        return self.session.post(''.join([self.api_uri, url]), **kwargs)

    @limit_rate
    @pr_pretty
    @verbose_output
    def put(self, url, **kwargs):
        return self.session.put(''.join([self.api_uri, url]), **kwargs)

    @limit_rate
    @pr_pretty
    @verbose_output
    def delete(self, url, **kwargs):
        return self.session.delete(''.join([self.api_uri, url]), **kwargs)
