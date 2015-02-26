#!/usr/bin/env python

import argparse
import json
import os
import sys

import maasivepy


class CommandLineTool(object):
    def __init__(self, *args, **kwargs):
        # Set up arg parser
        self.argparser = argparse.ArgumentParser()
        self.argparser.description = "Helper script for managing maasive APIs"
        self.argparser.add_argument('endpoint', metavar='URL', nargs=1, help='API endpoint; "users", "devices", etc. Trailing slash is added for you.')
       
        self.argparser.add_argument('--method', '-m', action='store', default='OPTIONS', help='API method to call. Options are GET, OPTIONS, POST, and DELETE are supported.')
        self.argparser.add_argument('--verbose', '-v', action='store_true', default=False, help='Enables verbose output. Don\'t use this if you want to redirect output to a valid json file.')
        self.argparser.add_argument('--bulkadd', '-b', action='store_true', default=False, help='Bulk addition. Strips the id field off each entry in the input file so new items are created. Also, user passwords are replaced with the default value.')

        self.argparser.add_argument('--id', action='store', default=None, help='Id of the item to manipulate.')
        self.argparser.add_argument('--inputstring', '-i', action='store', default=None, help='Either an inline json object or a path to a file containing data to upload.')
        self.argparser.add_argument('--query', '-q', action='store', default=None, help='JSON query to execute')
        self.argparser.add_argument('--key', '-k', action='store', default=None, help='Extract the value "key", putting each value on a new line.')
        self.argparser.add_argument('--limit', '-l', action='store', default=None, help='Max # items to return.')
        self.argparser.add_argument('--config', action='store', default=None, help='Path to json config file or inline config object.')

        self.args = self.argparser.parse_args()

        ##########################
        # Grab config and extract
        ##########################
        self.args.config = self.args.config or os.environ.get('MAASIVEAPICONF')
        if not self.args.config:
            print("'MAASIVEAPICONF' environmental variable is not set and no configuration was passed. Exiting.")
            sys.exit(1)
        
        conf = self.get_input(self.args.config)
        self.API_ENDPOINT = conf['endpoint']  # endpoint is required
        self.NEW_USER_PASSWORD = conf.get('newUserDefaultPassword', 'password')  # default new password

        # Can authenticate with username and password or API key
        self.APIKEY = conf.get('API-Key')
        self.ADMINKEY = conf.get('Admin-Key')
        self.USERNAME = conf.get('username')
        self.PASSWORD = conf.get('password')

        ##########################
        # Set up endpoint for this request
        ##########################
        self.URL = "%s/" % self.args.endpoint[0]

        ##########################
        # Setup maasive session
        ##########################
        options = dict()
        options["verbose"] = self.args.verbose
        if self.APIKEY:
            options["api_key"] = self.APIKEY
        if self.ADMINKEY:
            options["admin_key"] = self.ADMINKEY

        self.MAASIVE_SESSION = maasivepy.MaaSiveAPISession(
            self.API_ENDPOINT,
            **options
        )

        # Login if no api key available
        if not (self.APIKEY or self.ADMINKEY) and (self.USERNAME and self.PASSWORD):
            self.MAASIVE_SESSION.login(self.USERNAME, self.PASSWORD)

    def run(self):
        if self.args.method == 'GET':
            self.get_items()
        if self.args.method == 'POST':
            self.post_items()
        if self.args.method == 'PUT':
            self.put_items()
        if self.args.method == 'DELETE':
            self.delete_item()
        if self.args.method == 'OPTIONS':
            self.get_options()

        self.close_session()

    def close_session(self):
        self.MAASIVE_SESSION.get('/auth/logout/')

    @staticmethod
    def get_input(inputstring):
        """Returns the object from either a filename or an inline object """
        if os.path.isfile(inputstring):
            with open(inputstring, 'r') as f:
                o = json.load(f)
        else:
            o = json.loads(inputstring)
        return o

    def get_items(self):
        if self.args.id:
            res = self.MAASIVE_SESSION.get("%s%s" % (self.URL, self.args.id)).json()
        else:
            params = {}
            if self.args.query:
                params['q'] = self.args.query
            if self.args.limit:
                params['limit'] = self.args.limit
            res = self.MAASIVE_SESSION.get("%s" % (self.URL), params=params).json()

        if not self.args.key:
            print(json.dumps(res, indent=4))
        else:
            for item in res:
                print(item.get(self.args.key))

    def put_items(self):
        if not self.args.id:
            print("PUT currently requires a single object id")
            sys.exit(1)

        if not self.args.inputstring:
            print("PUT requires data to be passed via the `--inputstring` argument")
            sys.exit(1)

        d = json.dumps(self.get_input(self.args.inputstring))

        res = self.MAASIVE_SESSION.put("%s%s" % (self.URL, self.args.id), data=d).json()
        print(json.dumps(res, indent=4))

    def post_items(self):
        """Opening the file and reading as JSON ensures a correctly formatted datafile before the
        request is made """
        o = self.get_input(self.args.inputstring)

        # If it is a bulk upload, remove the id field of each item
        if isinstance(o, list):
            for item in o:
                # Remove the id field of each item
                if self.args.bulkadd and 'id' in item.keys():
                    del item['id']

                # Replace the password field
                if self.args.bulkadd and self.__class__.__name__ == 'UsersTool':
                    item['password'] = self.NEW_USER_PASSWORD

        d = json.dumps(o)
        res = self.MAASIVE_SESSION.post(self.URL, data=d).json()
        print(json.dumps(res, indent=4))

    def delete_item(self):
        if self.args.id:
            res = self.MAASIVE_SESSION.delete("%s%s" % (self.URL, self.args.id)).json()
        else:
            res = self.MAASIVE_SESSION.delete("%s" % (self.URL)).json()
            #print "DELETE requires an id"
            #sys.exit(1)

        print(json.dumps(res, indent=4))

    def get_options(self):
        res = self.MAASIVE_SESSION.options(self.URL).json()
        print(json.dumps(res, indent=4))


def main():
    tool = CommandLineTool()
    tool.run()    

if __name__ == "__main__":
    main()
