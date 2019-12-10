import argparse

from dualisbot.config import config

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--semester', help='Restrict output to one semester', type=int, choices=range(1,7))
    parser.add_argument('-d', '--diff', help='Only show results that have changed since the last invocation', action='store_true')
    parser.add_argument('-u', '--username', help='Username for Dualis')
    parser.add_argument('-p', '--password', help='Password for Dualis')
    parser.add_argument('--secrets', help='Location of file containing username and password. Defaults to ./data/secrets.json')
    parser.add_argument('--config', help='Location of config file. Defaults to ./data/config.json')
    parser.add_argument('--json', help='Output to JSON', action='store_true')
    args = parser.parse_args()
    for key, value in vars(args).items():
        if value is not None:
            config[key] = value

parse_args()