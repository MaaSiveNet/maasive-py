#MaaSivePy

A Python SDK for MaaSive.net

## Installation

Install with pip

  pip install -e git+https://github.com/MaaSiveNet/maasive-py.git@v1.2.2#egg=maasive-py

## Usage

    from maasivepy import MaaSiveAPISession

    m = maasivepy.MaaSiveAPISession('https://api.maasive.net/v2/52957bacc3034e4a0fe22f78', print_pretty=True)
    m.get('/comments/')

Check us out at [https://maassive.net](https://maassive.net)

## Changelog

**version 1.2.2**

- automatic batching of large reads and writes

**version 1.2.1**

- APISession object to package init
- APISession history
- automatic serialization to JSON
- built-in pretty print to response objects and APISession
- support for X-Admin-Key and X-Auth-Token headers in APISession constructor
