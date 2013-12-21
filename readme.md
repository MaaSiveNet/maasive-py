#MaaSivePy

A Python SDK for MaaSive.net

## Installation

Install with pip

  pip install -e git+https://github.com/MaaSiveNet/maasive-py.git@v1.2#egg=maasive-py

## Usage

    from maasivepy import MaaSiveAPISession

    m = maasivepy.MaaSiveAPISession('https://api.maasive.net/v2/52957bacc3034e4a0fe22f78', print_pretty=True)
    m.get('/comments/')

Check us out at [https://maassive.net](https://maassive.net)
