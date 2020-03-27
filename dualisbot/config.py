import json
import sys
from getpass import getpass
from pathlib import Path

# Functions for loading config values

def path_complete(path):
    return (Path(sys.argv[0]).parent / path).resolve()

config = {
    'url': 'https://dualis.dhbw.de', # Hardcoded here because it should not be configurable
    'secrets': path_complete('data/secrets.json'),
    'config': path_complete('data/config.json'),
    'data': path_complete('data/data.json')
}

secrets_keys = ['username', 'password']
did_read_from_input = False

def read_config():
    global did_read_from_input

    load_secrets()
    load_config()

    for config_val in secrets_keys:
        if get_config_val(config_val) is None:
            config[config_val] = get_from_input(config_val)
            did_read_from_input = True

def save_credentials():
    if did_read_from_input:
        # n actually has no special meaning, only y does
        choice = input('Login successful.\nDo you want to store username and password (unencrypted) on disk? [y/n]\n')
        if choice.startswith('y') or choice.startswith('Y'):
            try:
                with open(get_config_val('secrets'), 'w') as file:
                    json.dump({ key: get_config_val(key) for key in secrets_keys }, file, indent=4)
            except IOError:
                pass

def get_from_input(config_val):
    if config_val == 'username':
        return input('Enter username for Dualis:\n')
    elif config_val == 'password':
        return getpass('Enter password:\n')

def config_load_json(configval):
    def dec(func):
        def wrapper(*args, **kwargs):
            ret = None
            try:
                with open(get_config_val(configval)) as file:
                    file_data = json.load(file)
                    kwargs['file_data'] = file_data
                    ret = func(*args, **kwargs)
            except IOError:
                pass
            finally:
                return ret
        return wrapper
    return dec

@config_load_json('secrets')
def load_secrets(file_data):
    global config
    for key in secrets_keys:
        # Do not overwrite command line options
        if config.get(key) is None:
            config[key] = file_data.get(key)

@config_load_json('config')
def load_config(file_data):
    global config
    for key, value in file_data.items():
        if config.get(key) is None and key not in secrets_keys:
            config[key] = value

def get_config_val(name):
    return config.get(name)