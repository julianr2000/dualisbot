import argparse

from dualisbot.config import data

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--semester', help='Restrict output to one semester', type=int, choices=range(1,7))
    parser.add_argument('-d', '--diff', help='Only show results that have changed since the last invocation', action='store_true')
    parser.add_argument('-u', '--username', help='Username for Dualis')
    parser.add_argument('-p', '--password', help='Password for Dualis')
    args = parser.parse_args()
    data['config'].update(vars(args))

parse_args()