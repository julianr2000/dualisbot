import copy
import json
import re
import textwrap
from itertools import zip_longest
from shutil import get_terminal_size

import colorama
from colorama import Style, Fore, Back
from lxml import html

from dualisbot.config import get_config_val

# Result extraction and printing

colorama.init()

def trim_space(string):
    if not string or string.isspace():
        return None
    return string.strip()

class Result:
    def __init__(self, title, results, final_results):
        self.title = title
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
        
        final_results_td = table[-1][3]
        final_results = trim_space(final_results_td.text.replace('\xa0', ' '))
        # Note: the td element that should contain the final grade is actually invalid html if no
        # grade has been set (this is a bug on website)
        # It is still parsed mostly correct as a td element, but the text ends up inside the tag (where the attributes should be) 
        if not final_results:
            match = re.match('^<[^>]*"\\s*(.*)\\s*>', html.tostring(final_results_td, encoding='unicode'))
            if match:
                final_results = match.group(1)

        return cls(title, results, final_results)

    def pretty_print(self):
        max_col_width = 35 # Chosen arbitrarily

        # Necessary headers
        # Using a dict for set operations because dicts preserve insertion order
        headers = list({ column : None for result in self.results for column in result.keys() }.keys())

        # Get column width
        termwidth, _ = get_terminal_size()
        termwidth -= len(headers) - 1 # Subtract spaces between columns
        col_width = min(termwidth // len(headers), max_col_width)

        def table_row(columns):
            return (
                '\n'.join(
                    map(
                        lambda row: ' '.join([col.ljust(col_width) for col in row]),
                        zip_longest(*[textwrap.wrap(col, width=col_width) for col in columns], fillvalue=''))))


        title_str = Fore.LIGHTBLUE_EX + self.title + Style.RESET_ALL

        headers_str = Fore.LIGHTGREEN_EX + table_row(headers) + Style.RESET_ALL

        res_strings = []
        for result in self.results:
            res_strings.append(table_row([result.get(column, '') for column in headers]))
        results_str = '\n'.join(res_strings)

        final_res_str = Fore.LIGHTYELLOW_EX + table_row(['Gesamt:', '',  self.final_results]) + Style.RESET_ALL

        print(title_str)
        print(headers_str)
        print(results_str)
        print(final_res_str)

    @classmethod
    def from_serializable(cls, data):
        return cls(*map(data.get, ['title', 'results', 'final_results']))

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
            if self.page_info:
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

    def pretty_print(self):
        for res in self.result_infos:
            res.pretty_print()


def sems_to_json(semesters):
    """Dump list of semesters to json""" 
    return json.dumps([sem.get_serializable() for sem in semesters], indent=4)

def sems_to_dict(semesters):
    return { sem.number: sem.get_serializable() for sem in semesters}

def sems_pretty_print(semesters):
    """Pretty print list of semesters"""
    if semesters:
        for sem in semesters[:-1]:
            sem.pretty_print()
            # print newline if something has been printed
            if list(sem.result_infos):
                print()
        semesters[-1].pretty_print()

def get_old_sems_dict():
    """Read the data file from disk and cache the result"""
    self = get_old_sems_dict
    if getattr(self, 'cache', None) is None:
        try:
            with open(get_config_val('data')) as file:
                data = json.load(file)
                self.cache = { sem['number']: sem for sem in data }
        except IOError:
            self.cache = {}
    return copy.deepcopy(self.cache)


def get_new_res(semesters):
    """Remove all results and semesters that are present in old_sems_dicts"""
    sems_d = sems_to_dict(semesters)
    old_sems_d = get_old_sems_dict()
    diff_sems = []
    for key, sem in sems_d.items():
        if old := old_sems_d.get(key):
            results = sem['results']
            sem['results'] = [r for r in results if r not in old['results']]
            diff_sems.append(Semester.from_serializable(sem))
            # restore original
            sem['results'] = results
        else:
            diff_sems.append(Semester.from_serializable(sem))
    return diff_sems

def do_output_io(semesters):
    """Print the data and update the data file"""
    to_display = get_config_val('semester')
    if to_display is not None:
        display_sems = [sem for sem in semesters if sem.number == to_display]
    else:
        display_sems = semesters

    if get_config_val('new'):
        output_sems_format(get_new_res(display_sems))
    else:
        output_sems_format(display_sems)

    update_data_file(display_sems)

def output_sems_format(semesters):
    """Output semesters in the desired output format"""
    if get_config_val('json'):
        print(sems_to_json(semesters))
    else:
        sems_pretty_print(semesters)

def update_data_file(display_sems):
    sems_d = sems_to_dict(display_sems)
    old_sems_d = get_old_sems_dict()
    old_sems_d.update(sems_d)
    try:
        with open(get_config_val('data'), 'w') as file:
            json.dump(list(old_sems_d.values()), file, indent=4)
    except IOError:
        pass