import re
from itertools import tee

import colorama
from colorama import Style, Fore, Back
from lxml import html

colorama.init()

def trim_space(string):
    if not string or string.isspace():
        return None
    return string.strip()

def fixed_size(string, size):
    return string.ljust(size)[:size]

class Result:
    def __init__(self, page_info):
        """Parse popup page into a more convenient datastructure"""
        htmltitle = page_info.page.xpath('//h1')[0]
        htmltable = htmltitle.xpath('./following-sibling::table')[0]
        table = [tr.getchildren() for tr in htmltable.getchildren() if tr.tag == 'tr']

        title = re.search('\\s*(.*)$', htmltitle.text)
        self.title = title.group(1) if title else ''
        
        # All headers visible on the page
        headers = []
        for row in table:
            for td in row:
                if 'tbsubhead' in row[0].classes and not td.text.isspace():
                    headers.append(td.text)
        
        self.results = []
        for row in table:
            if len(row) > 0 and 'tbdata' in row[0].classes:
                result = {}
                for i, td in enumerate(row):
                    text = trim_space(td.text)
                    if text and i < len(headers):
                        result[headers[i]] = text
                self.results.append(result)

        # Using a dict for set operations because dicts preserve insertion order
        self.headers = list({ column : None for result in self.results for column in result.keys() }.keys())
        
        final_results_td = table[-1][3]
        self.final_results = trim_space(final_results_td.text.replace('\xa0', ' '))
        # Note: the td element that should contain the final grade is actually invalid html if no
        # grade has been set (this is a bug on website)
        # It is still parsed mostly correct as a td element, but the text ends up inside the tag (where the attributes should be) 
        if not self.final_results:
            match = re.match('^<[^>]*"\\s*(.*)\\s*>', html.tostring(final_results_td, encoding='unicode'))
            if match:
                self.final_results = match.group(1)

    def pretty_print(self):
        column_width = 24

        title = Fore.LIGHTBLUE_EX + self.title + Style.RESET_ALL

        headers = Fore.LIGHTGREEN_EX + ''.join((fixed_size(column, column_width) for column in self.headers)) + Style.RESET_ALL

        res_strings = []
        for result in self.results:
            col_strings = []
            for column in self.headers:
                value = result.get(column)
                if value:
                    col_strings.append(fixed_size(value, column_width))
                else:
                    col_strings.append(' ' * column_width)
            res_strings.append(''.join(col_strings))
        results_string = '\n'.join(res_strings)

        final_res_string = (Fore.LIGHTYELLOW_EX
            + fixed_size('Gesamt: ', 2 * column_width)
            + fixed_size(self.final_results, column_width)
            + Style.RESET_ALL
        )

        print(title)
        print(headers)
        print(results_string)
        print(final_res_string)



class Semester:
    def __init__(self, page_info, name):
        self.page_info = page_info
        self.name = name
        self._result_infos_cache = None

    @classmethod
    def from_PageInfo(cls, page_info):
        return cls(page_info, page_info.page.xpath('//option[@selected = "selected"]/text()')[0])

    @property
    def result_infos(self):
        """Get the detailed info for the individual popup pages
        Returns a iterator and caches the results"""
        if self._result_infos_cache is None:
            it, self._result_infos_cache = tee(Result(page_info) for page_info in self.page_info.get_result_popups())
        else:
            it, self._result_infos_cache = tee(self._result_infos_cache)
        return it