#!/usr/bin/python

import json
from lxml import html
import re
import requests
from urllib.parse import urlparse, urlunparse

from configdata import data

session = requests.session()


class PageInfo:
    def __init__(self, url):
        self.url = url
        self.page = get_page(url)

    def follow_mrefresh(self):
        return PageInfo(get_mrefresh_url(self.page, self.url))

    def login(self):
        # find out where to send the data
        relurl, header = get_login_data(self.page)
        url = relurl_to_url(relurl, self.url)
        # send it
        response = session.post(url, data=header)
        # parse response
        success_url = relurl_to_url(mrefresh_to_relurl(response.headers['REFRESH']), url)
        return PageInfo(success_url)

    def go_to_result_page(self):
        """Use the menu to get to the results page"""
        # don't use the link id because it looks automatically generated
        # let's hope they don't change the layout
        relurl = self.page.xpath('//div[@id = "pageTopNavi"]//a/@href')[1]
        return PageInfo(relurl_to_url(relurl, self.url))
    
    def get_other_results(self):
        """Get the other result pages from the dropdown menu"""
        # Looks like Hansel and Gretel were short on pebbles this time
        semester = self.page.xpath('//option[not(@selected)]/@value')
        inputs = self.page.xpath('//input[@type = "hidden"]')
        args = { i.name : i.value for i in inputs }
        # special case for arguments
        for key in 'sessionno', 'menuno':
            args['ARGUMENTS'] = args['ARGUMENTS'].replace(key, '-N' + args[key])
            del args[key]
        result = []
        for sem in semester:
            # Construct query string
            urlargs = '&'.join(f'{key}={value}' for key, value in args.items())
            urlargs = urlargs.replace('semester', '-N' + sem)
            # Use other parts from current url
            urlp = urlparse(self.url)
            urlp = urlp._replace(query=urlargs)
            result.append(PageInfo(urlunparse(urlp)))
        return result

    def get_popup_urls(self):
        """Get the urls of the popup windows from the results page"""
        return [relurl_to_url(relurl, self.url) for relurl in self.page.xpath('//a[starts-with(@id, "Popup_details")]/@href')]


def get_page(url):
    with session.get(url) as response:
        # correct encoding, it's probably utf-16 or utf-8, but the site reports it as iso-8859-1
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

def get_login_data(page):
    """Extract the path to the serverside script and the input form data from the Dualis login page"""
    form = page.xpath('//form[@id = "cn_loginForm"]')[0]
    inputs = form.xpath('.//input')
    header = { i.name: i.value for i in inputs if i.name is not None }
    header.update({ 'usrname': data['secrets']['username'], 'pass': data['secrets']['password'] })
    return form.action, header

def main():
    position = (
        PageInfo(data['config']['url'])
        .follow_mrefresh() # first redirect
        .follow_mrefresh() # second redirect, we should be at the login page now
        .login()
        .follow_mrefresh() # more breadcrumbs
        .go_to_result_page() # go to results page
    )
    # Get result overview pages for all semesters
    res_overviews = position.get_other_results()
    res_overviews.append(position)
    # Get links to details for individual courses (the annoying popups)
    popup_urls = [url for result in res_overviews for url in result.get_popup_urls()]
    return popup_urls