import argparse

from dualisbot.config import config

def parse_args():
    parser = argparse.ArgumentParser()
    aa = parser.add_argument
    aa('-s', '--semester', help='Restrict output to one semester', type=int, choices=range(1,7))
    aa('-n', '--new', help='Only show new results', action='store_true')
    aa('-u', '--username', help='Username for Dualis')
    aa('-p', '--password', help='Password for Dualis')
    aa('-pu', '--pushbullet', help='Pushbullet API')
    aa('--json', help='Output to JSON', action='store_true')
    aa('--secrets', help='Location of file containing username, password and API Key. Defaults to ./data/secrets.json')
    aa('--config', help='Location of config file. Defaults to ./data/config.json')
    aa('--data', help='Location of data file. Defaults to ./data/data.json')
    args = parser.parse_args()
    for key, value in vars(args).items():
        if value is not None:
            config[key] = value

parse_args()