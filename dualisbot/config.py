import json

data = {
    'config': {
        'url': 'https://dualis.dhbw.de' # Hardcoded here because it should not be configurable
    }
}

def read_config():
    global data
    for filename in ['secrets', 'config']:
        with open(f'data/{filename}.json') as file:
            file_data = json.load(file)
            # Do not overwrite command line options
            new_config = file_data
            for key, value in data['config'].items():
                if new_config.get(key) is None:
                    new_config[key] = value
            data['config'] = new_config

def get_config_val(name):
    return data['config'][name]
