#MaaSivePy

A Python SDK for MaaSive.net

## Installation

Install with pip

    $ pip install git+https://github.com/MaaSiveNet/maasive-py.git#egg=maasive-py

## RESTful Usage

The `maasivepy` library is easy to use as part of your Python scripts or in the interactive interpreter.
It's like having an interactive console for your REST API!

### GET

    In [1]: import maasivepy
    
    In [2]: m = maasivepy.APISession('https://api.maasive.net/v2.4.2/53adbcdb68fdfb3e5be1a99c')
    
    In [3]: m.get('/comments/?limit=1').json()
    200 GET https://api.maasive.net/v2.4.2/53adbcdb68fdfb3e5be1a99c/comments/?limit=1 in 213.03 ms for 219.85 ms
    Out[3]: 
    [{'_created_by': '53adbcdb68fdfb3e5be1a99c',
      '_created_ts': 1410437585,
      '_updated_by': '53adbcdb68fdfb3e5be1a99c',
      '_updated_ts': 1410437585,
      '_version': 1,
      'aliases': [],
      'email': 'josh@maasive.net',
      'id': '541191d179e19137084e5305',
      'tags': [],
      'text': 'testing for valid ts'}]
      
Don't worry, you can require Authentication and Authorization to protect your resources if needed:

    In [4]: m.get('/comments/').json()
    401 GET https://api.maasive.net/v2.4.2/53adbcdb68fdfb3e5be1a99c/comments/ in 182.10 ms for 183.72 - Unauthorized
    Out[5]: 
    {'error': {'extended_code': None,
      'message': None,
      'reason': 'Unauthorized',
      'status_code': 401}}
      
### POST

It's easy to add resources to your collections with POST.

    In [6]: comment = {'email': 'josh@maasive.net', 
                       'text': 'Chuck Norris doesn\'t do pushups, he pushes the world down.'}
    
    In [7]: m.post('/comments/', data=comment).json()
    200 POST https://api.maasive.net/v2.4.2/53adbcdb68fdfb3e5be1a99c/comments/ in 64.66 ms for 66.26 ms
    Out[7]: 
    {'existing': False,
     'id': '5414d214db6dff4cddae7eb0',
     'status': 'success',
     'version': '1'}
     
And then the resource is available for use.

    In [8]: m.get('/comments/5414d214db6dff4cddae7eb0').json()
    200 GET https://api.maasive.net/v2.4.2/53adbcdb68fdfb3e5be1a99c/comments/5414d214db6dff4cddae7eb0 in 189.00 ms for 190.45 ms
    Out[8]: 
    {'_created_by': None,
     '_created_ts': 1410650644,
     '_updated_by': None,
     '_updated_ts': 1410650644,
     '_version': 1,
     'aliases': [],
     'email': 'josh@maasive.net',
     'id': '5414d214db6dff4cddae7eb0',
     'tags': [],
     'text': "Chuck Norris doesn't do pushups, he pushes the world down."}

### PUT

Modify resources like this:

    In [10]: m.put('/comments/5414d214db6dff4cddae7eb0', data={'email': 'matt@maasive.net'}).json()
    200 PUT https://api.maasive.net/v2.4.2/53adbcdb68fdfb3e5be1a99c/comments/5414d214db6dff4cddae7eb0 in 65.16 ms for 66.14 ms
    Out[10]: 
    {'existing': True,
     'id': '5414d214db6dff4cddae7eb0',
     'status': 'success',
     'version': '2'}

### DELETE

Delete resources like this:

    In [11]: m.delete('/comments/5414d214db6dff4cddae7eb0').json()
    200 DELETE https://api.maasive.net/v2.4.2/53adbcdb68fdfb3e5be1a99c/comments/5414d214db6dff4cddae7eb0 in 191.46 ms for 192.42 ms
    Out[11]: {'id': '5414d214db6dff4cddae7eb0', 'method': 'DELETE', 'status': 'success'}
    
And confirm that the resource is no longer available:
    
    In [12]: m.get('/comments/5414d214db6dff4cddae7eb0').json()
    404 GET https://api.maasive.net/v2.4.2/53adbcdb68fdfb3e5be1a99c/comments/5414d214db6dff4cddae7eb0 in 186.25 ms for 187.85 - resource not found
    Out[12]: 
    {'error': {'extended_code': None,
      'message': None,
      'reason': 'resource not found',
      'status_code': 404}}
      
## Other features
      
This library also has some convenience functions.
       
### CSV export

Sometimes you just need to get your resources as CSV files instead of JSON.

    In [13]: f = open('example.csv','w')
    
    In [14]: m.export_csv('/comments/?limit=0', csvfile=f)
    200 OPTIONS https://api.maasive.net/v2.4.2/53adbcdb68fdfb3e5be1a99c/comments/?limit=0 in 212.78 ms for 213.84 ms
    sleeping for 0.21409177780151367...
    200 GET https://api.maasive.net/v2.4.2/53adbcdb68fdfb3e5be1a99c/comments/?limit=0 in 65.76 ms for 67.15 ms
    Out[14]: <Response [200]>
    
    In [15]: f.close()


Check us out at [https://maassive.net](https://maassive.net)

## Changelog

**version 1.2.7**

- CSV export

**version 1.2.6**

- Better support for streaming very large batches

**version 1.2.5**

- bugfixes

**version 1.2.4**

- bugfixes

**version 1.2.3**

- bugfixes

**version 1.2.2**

- automatic batching of large reads and writes

**version 1.2.1**

- APISession object to package init
- APISession history
- automatic serialization to JSON
- built-in pretty print to response objects and APISession
- support for X-Admin-Key and X-Auth-Token headers in APISession constructor
