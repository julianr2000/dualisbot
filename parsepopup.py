#!/usr/bin/python

from lxml import html
import re

def trim_space(string):
    if not string or string.isspace():
        return None
    return string.strip()

class ResultInfo:
    def __init__(self, page):
        """Parse popup page into a more convenient datastructure"""
        title = page.xpath('//h1')[0]
        htmltable = title.xpath('./following-sibling::table')[0]
        table = [tr.getchildren() for tr in htmltable.getchildren() if tr.tag == 'tr']
        
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
        
        final_results_td = table[-1][3]
        self.final_results = trim_space(final_results_td.text.replace('\xa0', ' '))
        # Note: the td element that should contain the final grade is actually invalid html if no
        # grade has been set (this is a bug on website)
        # It is still parsed mostly correct as a td element, but the text ends up inside the tag (where the attributes should be) 
        if not self.final_results:
            match = re.match('^<[^>]*"\\s*(.*)\\s*>', html.tostring(final_results_td, encoding='unicode'))
            if match:
                self.final_results = match.group(1)