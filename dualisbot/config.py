import json
import sys
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

def read_config():
    load_secrets()
    load_config()

def config_load_json(configval):
    def dec(func):
        def wrapper(*args, **kwargs):
            ret = None
            try:
                with open(get_config_val(configval)) as file:
                    file_data = json.load(file)
                    ret = func(*args, file_data, **kwargs)
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