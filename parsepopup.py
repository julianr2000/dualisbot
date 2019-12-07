#!/usr/bin/python

import colorama
from colorama import Style, Fore, Back
from lxml import html
import re

colorama.init()

def trim_space(string):
    if not string or string.isspace():
        return None
    return string.strip()

def fixed_size(string, size):
    return string.ljust(size)[:size]

class ResultInfo:
    def __init__(self, page):
        """Parse popup page into a more convenient datastructure"""
        title = page.xpath('//h1')[0]
        htmltable = title.xpath('./following-sibling::table')[0]
        table = [tr.getchildren() for tr in htmltable.getchildren() if tr.tag == 'tr']
        
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
        title = Fore.LIGHTGREEN_EX + ''.join((fixed_size(column, column_width) for column in self.headers)) + Style.RESET_ALL

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
            + Fore.BLUE
            + fixed_size(self.final_results, column_width)
            + Style.RESET_ALL
        )

        print(title)
        print(results_string)
        print(final_res_string)



with open('page3.html') as file:
    page = html.fromstring(file.read())

res = ResultInfo(page)
res.pretty_print()