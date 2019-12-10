import json
import re
from urllib.parse import urlparse, urlunparse

import requests
from lxml import html

from dualisbot.config import get_config_val
from dualisbot.resultdata import Semester

# Functions for navigation the websites and extracting links

session = requests.session()

class lazy_property:
    """Like @property, but cache the function result"""
    def __init__(self, func):
        self.func = func

    def __get__(self, instance, owner):
        if instance is None: # Access through class
            return self
        result = self.func(instance)
        setattr(instance, self.func.__name__, result)
        return result # return on first lookup

class PageInfo:
    def __init__(self, url):
        self.url = url

    @classmethod
    def from_relurl(cls, relurl, base_url):
        return cls(relurl_to_url(relurl, base_url))
    
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
        return PageInfo.from_relurl(mrefresh_to_relurl(response.headers['REFRESH']), url)

    def go_to_semester_page(self):
        """Use the menu to get to the semester overview page"""
        # don't use the link id because it looks automatically generated
        # let's hope they don't change the layout
        relurl = self.page.xpath('//div[@id = "pageTopNavi"]//a/@href')[1]
        return Semester.from_PageInfo(PageInfo.from_relurl(relurl, self.url))

    def get_result_popups(self):
        """List all pages that contain result details (the annoying popups)"""
        return [
            self.from_relurl(relurl, self.url)
            for relurl in self.page.xpath('//a[starts-with(@id, "Popup_details")]/@href')
        ]



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
    header.update({ 'usrname': get_config_val('username'), 'pass': get_config_val('password') })
    return form.action, header

def parse_dropdown_menu(semester):
    """Get all semesters from the dropdown menu"""
    # Looks like Hansel and Gretel were short on pebbles this time
    # the dropdown menu only contains the semester-id, the other parts of the url
    # are inside the hidden input tags
    options = semester.page_info.page.xpath('//option[not(@selected)]')
    inputs = semester.page_info.page.xpath('//input[@type = "hidden"]')
    args = { i.name : i.value for i in inputs }
    # special case for arguments
    for key in 'sessionno', 'menuno':
        args['ARGUMENTS'] = args['ARGUMENTS'].replace(key, '-N' + args[key])
        del args[key]
    result = [semester]
    for opt in options:
        # Construct query string
        urlargs = '&'.join(f'{key}={value}' for key, value in args.items())
        urlargs = urlargs.replace('semester', '-N' + opt.attrib['value'])
        # Use other parts from current url
        urlp = urlparse(semester.page_info.url)
        urlp = urlp._replace(query=urlargs)
                # First semester is at the bottom of the drop-down menu, therefore count following option
        number = len(opt.xpath('./following-sibling::option')) + 1
        result.append(Semester(PageInfo(urlunparse(urlp)), opt.text, number))
    return result

def get_semesters():
    semester = (
        PageInfo(get_config_val('url'))
        .follow_mrefresh() # first redirect
        .follow_mrefresh() # second redirect, we should be at the login page now
        .login()
        .follow_mrefresh() # more breadcrumbs
        .go_to_semester_page()
    )
    return parse_dropdown_menu(semester)