#!/usr/bin/python

import json
from lxml import html
import re
import requests
from urllib.parse import urlparse, urlunparse

from configdata import data


session = requests.session()

def get_page(url):
    with session.get(url) as response:
        # correct encoding, it's probably utf-16
        response.encoding = response.apparent_encoding
        return html.fromstring(response.text)
        
def get_mrefresh_content(page):
    """Get the link of the metarefresh tag if it exists"""
    tags = page.xpath('//meta[@http-equiv = "refresh"]/@content')
    if len(tags) > 1:
        raise ValueError(f'Unexpected number of metarefresh tags: {len(tags)}')
    elif len(tags) == 1:
        return tags[0]
    return None

def mrefresh_to_relurl(content):
    """Get a relative url from the contents of a metarefresh tag"""
    urlstart = re.compile('.*URL=')
    _, url = content.split(';')
    url = urlstart.sub('', url)
    return url

def relurl_to_url(relurl, base_url):
    """Append a page-relative url to a full url"""
    relurl = urlparse(relurl)
    base_url = urlparse(base_url)
    return urlunparse(base_url[:2] + relurl[2:])

def get_mrefresh_url(page, url):
    return relurl_to_url(mrefresh_to_relurl(get_mrefresh_content(page)), url)

def follow_mrefresh(url):
    return get_mrefresh_url(get_page(url), url)

def get_login_data(page):
    """Extract the path to the serverside script and the input form data from the Dualis login page"""
    form = page.xpath('//form[@id = "cn_loginForm"]')[0]
    inputs = form.xpath('.//input')
    header = { i.name : i.value for i in inputs if i.name is not None }
    header.update({ 'usrname': data['secrets']['username'], 'pass': data['secrets']['password'] })
    return form.action, header

def login(url):
    relurl, header = get_login_data(get_page(url))
    url = relurl_to_url(relurl, url)
    response = session.post(url, data=header)
    login_url = relurl_to_url(mrefresh_to_relurl(response.headers['REFRESH']), url)
    return login_url

def main():
    url = follow_mrefresh(data['config']['url']) # first redirect
    url = follow_mrefresh(url) # second redirect
    # we should be at the login page now
    url = login(url)
    url = follow_mrefresh(url) # redirect again...
    return get_page(url)