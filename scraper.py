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
        
def extract_metarefresh_tag_content(page):
    """Get the link of the metarefresh tag if it exists"""
    tags = page.xpath('//meta[@http-equiv = "refresh"]/@content')
    if len(tags) > 1:
        raise ValueError(f'Unexpected number of metarefresh tags: {len(tags)}')
    elif len(tags) == 1:
        return tags[0]
    return None

def parse_metarefresh_tag_content(content):
    """Get a relative url from the contents of a metarefresh tag"""
    urlstart = re.compile('.*URL=')
    _, url = content.split(';')
    url = urlstart.sub('', url)
    return url

def url_relative_replace(relative_url, base_url):
    """Append a page-relative url to a full url"""
    relative = urlparse(relative_url)
    base_url = urlparse(base_url)
    return urlunparse(base_url[:2] + relative[2:])

def get_metarefresh_url(page, base_url):
    return url_relative_replace(parse_metarefresh_tag_content(extract_metarefresh_tag_content(page)), base_url)

def follow_metarefesh_redir(url):
    return get_metarefresh_url(get_page(url), url)

def extract_form_data(page):
    """Extract the path to the serverside script and the input form data from the Dualis login page"""
    form = page.xpath('//form[@id = "cn_loginForm"]')[0]
    inputs = form.xpath('.//input')
    header = { i.name : i.value for i in inputs if i.name is not None }
    header.update({ 'usrname': data['secrets']['username'], 'pass': data['secrets']['password'] })
    return form.action, header

def login(base_url):
    partial_url, header = extract_form_data(get_page(base_url))
    url = url_relative_replace(partial_url, base_url)
    response = session.post(url, data=header)
    login_url = url_relative_replace(parse_metarefresh_tag_content(response.headers['REFRESH']), base_url)
    return login_url

def main():
    url = follow_metarefesh_redir(data['config']['url'])
    url = follow_metarefesh_redir(url)
    url = login(url)
    url = follow_metarefesh_redir(url)
    return get_page(url)