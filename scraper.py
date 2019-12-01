#!/usr/bin/python

import json
from lxml import html
import re
import requests
from urllib.parse import urlparse, urlunparse

with open('config.json') as file:
    config = json.load(file)
session = requests.session()

def get_page(url):
    with session.get(url) as response:
        # correct encoding, it's probably utf-16
        response.encoding = response.apparent_encoding
        return html.fromstring(response.text)
        
def get_metarefresh_url(page, page_url):
    tags = page.xpath('//meta[@http-equiv = "refresh"]/@content')
    urlstart = re.compile('.*URL=')
    if len(tags) > 1:
        raise ValueError(f'Unexpected number of metarefresh tags: {len(tags)}')
    elif len(tags) == 1:
        _, url = tags[0].split(';')
        url = urlstart.sub('', url)
        if url:
            return url_complete(url, page_url)
    return None

def url_complete(url, page_url):
    """Append a page-relative url to a full url if needed"""
    url = urlparse(url)
    page_url = urlparse(page_url)
    return urlunparse([el[0] or el[1] for el in zip(url, page_url)])

def follow_metarefesh_redir(url):
    return get_metarefresh_url(get_page(url), url)

def main():
    url = follow_metarefesh_redir(config['url'])
    url = follow_metarefesh_redir(url)
    return url