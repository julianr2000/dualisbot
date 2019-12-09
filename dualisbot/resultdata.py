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
    def __init__(self, title, headers, results, final_results):
        self.title = title
        self.headers = headers
        self.results = results
        self.final_results = final_results

    @classmethod
    def from_PageInfo(cls, page_info):
        """Parse popup page into a more convenient datastructure"""
        htmltitle = page_info.page.xpath('//h1')[0]
        htmltable = htmltitle.xpath('./following-sibling::table')[0]
        table = [tr.getchildren() for tr in htmltable.getchildren() if tr.tag == 'tr']

        title_match = re.search('\\s*(.*)$', htmltitle.text)
        title = title_match.group(1) if title_match else ''
        
        # All headers visible on the page
        all_headers = []
        for row in table:
            for td in row:
                if 'tbsubhead' in row[0].classes and not td.text.isspace():
                    all_headers.append(td.text)
        
        results = []
        for row in table:
            if len(row) > 0 and 'tbdata' in row[0].classes:
                result = {}
                for i, td in enumerate(row):
                    text = trim_space(td.text)
                    if text and i < len(all_headers):
                        result[all_headers[i]] = text
                results.append(result)

        # Necessary headers
        # Using a dict for set operations because dicts preserve insertion order
        headers = list({ column : None for result in results for column in result.keys() }.keys())
        
        final_results_td = table[-1][3]
        final_results = trim_space(final_results_td.text.replace('\xa0', ' '))
        # Note: the td element that should contain the final grade is actually invalid html if no
        # grade has been set (this is a bug on website)
        # It is still parsed mostly correct as a td element, but the text ends up inside the tag (where the attributes should be) 
        if not final_results:
            match = re.match('^<[^>]*"\\s*(.*)\\s*>', html.tostring(final_results_td, encoding='unicode'))
            if match:
                final_results = match.group(1)

        return cls(title, headers, results, final_results)

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

    @classmethod
    def from_serializable(cls, data):
        return cls(*map(data.get, ['title', 'headers', 'results', 'final_results']))

    def get_serializable(self):
        """Get a representation of the object that can be serialized using the builtin json module"""
        return self.__dict__



class Semester:
    def __init__(self, page_info, name, number):
        self.page_info = page_info
        self.name = name
        self.number = number
        self._result_infos_cache = []

    @classmethod
    def from_PageInfo(cls, page_info):
        selected = page_info.page.xpath('//option[@selected = "selected"]')[0]
        # First semester is at the bottom of the drop-down menu, count following options
        number = len(selected.xpath('./following-sibling::option')) + 1
        return cls(page_info, selected.text, number)

    @classmethod
    def from_serializable(cls, data):
        """Recreate object from a dict created by self.get_serializable"""
        obj = cls(None, data.get('name'), data.get('number'))
        results_dict = data.get('results')
        results = [Result.from_serializable(res) for res in results_dict]
        obj._result_infos_cache = results
        return obj


    @property
    def result_infos(self):
        """Get the detailed info for the individual popup pages
        Returns a generator and caches the results"""
        def cache_results():
            for page_info in self.page_info.get_result_popups():
                res = Result.from_PageInfo(page_info)
                yield res
                self._result_infos_cache.append(res)

        return self._result_infos_cache or cache_results()

    def get_serializable(self):
        """Dump relevant information to dict
        
        (page_info will not be stored)"""
        return {
            'name': self.name,
            'number': self.number,
            'results': [res.get_serializable() for res in self.result_infos]
        }