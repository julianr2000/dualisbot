import json
import re
from urllib.parse import urlparse, urlunparse

import aiohttp
from lxml import html

from dualisbot.config import get_config_val
from dualisbot.resultdata import Semester

# Functions for navigation the websites and extracting links

class PageInfo:
    def __init__(self, session, url, page):
        self.session = session
        self.url = url 
        self.page = page

    @classmethod
    async def init(cls, session, url):
        async with session.get(url) as response:
            page = html.fromstring(await response.text())
            return cls(session, url, page)

    @classmethod
    async def copy_session(cls, pageinfo, url):
        return await cls.init(pageinfo.session, url)

    @classmethod
    async def from_relurl(cls, session, relurl, base_url):
        return await cls.init(session, relurl_to_url(relurl, base_url))
    
    @classmethod
    async def copy_relurl(cls, pageinfo, relurl):
        return await cls.from_relurl(pageinfo.session, relurl, pageinfo.url)
    

def follow_mrefresh(pageinfo):
    return PageInfo.copy_session(pageinfo, get_mrefresh_url(pageinfo.page, pageinfo.url))

async def login(pageinfo):
    # find out where to send the data
    relurl, header = get_login_data(pageinfo.page)
    url = relurl_to_url(relurl, pageinfo.url)
    # send it
    async with pageinfo.session.post(url, data=header) as response:
        # parse response
        if response.headers.get('Set-cookie'):
            return await PageInfo.from_relurl(pageinfo.session, mrefresh_to_relurl(response.headers['REFRESH']), url)
    raise LoginFailed('Incorrect username or password')

def get_login_data(page):
    """Extract the path to the serverside script and the input form data from the Dualis login page"""
    form = page.xpath('//form[@id = "cn_loginForm"]')[0]
    inputs = form.xpath('.//input')
    header = { i.name: i.value for i in inputs if i.name is not None }
    header.update({ 'usrname': get_config_val('username'), 'pass': get_config_val('password') })
    return form.action, header

def go_to_semester_page(pageinfo):
    """Use the menu to get to the semester overview page"""
    # don't use the link id because it looks automatically generated
    # let's hope they don't change the layout
    relurl = pageinfo.page.xpath('//div[@id = "pageTopNavi"]//a/@href')[1]
    return PageInfo.copy_relurl(pageinfo, relurl)

class LoginFailed(Exception):
    pass

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

def parse_dropdown_menu(semester):
    """Get all semesters from the dropdown menu"""
    # Looks like Hansel and Gretel were short on pebbles this time
    # the dropdown menu only contains the semester-id, the other parts of the url
    # are inside the hidden input tags
    page = semester.pageinfo.page
    options = page.xpath('//option[not(@selected)]')
    inputs = page.xpath('//input[@type = "hidden"]')
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
        urlp = urlparse(semester.pageinfo.url)
        urlp = urlp._replace(query=urlargs)
        # First semester is at the bottom of the drop-down menu, therefore count following option
        number = len(opt.xpath('./following-sibling::option')) + 1
        # Inner lambda: wrap Pageinfo.copy_session in closure because asyncio complains about unused awaitables and
        # it may not be awaited
        # Outer lambda: Prevents scoping issues
        async_get_pageinfo = (lambda urlp: lambda: PageInfo.copy_session(semester.pageinfo, urlunparse(urlp)))(urlp)
        result.append(Semester(opt.text, number, async_get_pageinfo))
    return result

async def get_semesters(session):
    start = await PageInfo.init(session, get_config_val('url'))
    login_page = await follow_mrefresh(await follow_mrefresh(start)) # Two redirects
    main_page = await follow_mrefresh(await login(login_page))
    semester = Semester.from_pageinfo(await go_to_semester_page(main_page))
    semesters = parse_dropdown_menu(semester)
    return semesters