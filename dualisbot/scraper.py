import json
import re
from itertools import tee
from urllib.parse import urlparse, urlunparse

import requests
from lxml import html

from dualisbot.configdata import data
from dualisbot.parsepopup import ResultInfo

session = requests.session()

class lazy_property:
    """Like @property, but cache the function result"""
    def __init__(self, func):
        self.func = func
        self.__doc__ = func.__doc__

    def __get__(self, instance, owner):
        if instance is None: # Access through class
            return self
        result = self.func(instance)
        setattr(instance, self.func.__name__, result)
        return result # return on first lookup

class PageInfo:
    def __init__(self, url):
        self.url = url
    
    @lazy_property
    def page(self):
        return get_page(self.url)

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

    def go_to_semester_page(self):
        """Use the menu to get to the semester overview page"""
        # don't use the link id because it looks automatically generated
        # let's hope they don't change the layout
        relurl = self.page.xpath('//div[@id = "pageTopNavi"]//a/@href')[1]
        return SemesterInfo.from_PageInfo(PageInfo(relurl_to_url(relurl, self.url)))

class SemesterInfo:
    def __init__(self, page_info, name):
        self.page_info = page_info
        self.name = name

    @classmethod
    def from_PageInfo(cls, page_info):
        return cls(page_info, page_info.page.xpath('//option[@selected = "selected"]/text()')[0])

    @lazy_property
    def result_infos(self):
        """Get the detailed info for the individual popup pages"""
        result_infos = []
        for relurl in self.page_info.page.xpath('//a[starts-with(@id, "Popup_details")]/@href'):
            result_infos.append(ResultInfo(get_page(relurl_to_url(relurl, self.page_info.url))))
        return result_infos

    def get_semester_infos(self):
        """Get the urls and semester names of all semester overview sites from the dropdown menu"""
        # Looks like Hansel and Gretel were short on pebbles this time
        # the dropdown menu only contains the semester-id, the other parts of the url
        # are inside the hidden input tags
        semester = self.page_info.page.xpath('//option[not(@selected)]')
        inputs = self.page_info.page.xpath('//input[@type = "hidden"]')
        args = { i.name : i.value for i in inputs }
        # special case for arguments
        for key in 'sessionno', 'menuno':
            args['ARGUMENTS'] = args['ARGUMENTS'].replace(key, '-N' + args[key])
            del args[key]
        result = [self]
        for sem in semester:
            # Construct query string
            urlargs = '&'.join(f'{key}={value}' for key, value in args.items())
            urlargs = urlargs.replace('semester', '-N' + sem.attrib['value'])
            # Use other parts from current url
            urlp = urlparse(self.page_info.url)
            urlp = urlp._replace(query=urlargs)
            result.append(SemesterInfo(PageInfo(urlunparse(urlp)), sem.text))
        return result


def get_page(url):
    with session.get(url) as response:
        # correct encoding, it's probably utf-16 or utf-8, but the site reports it as iso-8859-1
        response.encoding = response.apparent_encoding
        return html.fromstring(response.text)

def get_mrefresh_content(page):
    """Get the link of the metarefresh tag if it exists"""
    tags = page.xpath('//meta[@http-equiv = "refresh"]/@content')
    return tags[0]

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

def get_semesters():
    semesters = (
        PageInfo(data['config']['url'])
        .follow_mrefresh() # first redirect
        .follow_mrefresh() # second redirect, we should be at the login page now
        .login()
        .follow_mrefresh() # more breadcrumbs
        .go_to_semester_page()
        .get_semester_infos()
    )
    return semesters

if __name__ == '__main__': # for debugging
    sems = get_semesters()
