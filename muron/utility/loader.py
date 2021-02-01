import json
import random

config = {}
config_server = {}
config_testserver = {}
narration = {}

with open('config.json', encoding="utf-8") as json_data_file:
    config = json.load(json_data_file)

with open('config_server.json', encoding="utf-8") as json_data_file:
    config_server = json.load(json_data_file)

with open('config_testserver.json', encoding="utf-8") as json_data_file:
    config_testserver = json.load(json_data_file)

with open('narration.json', encoding="utf-8") as json_data_file:
    narration = json.load(json_data_file)


def config_mode(mode):
    """Use one of ['main','test'] for using the associate config file"""
    global config
    global config_server
    global config_testserver

    if mode == 'main':
        config.update(config_server)
    elif mode == 'test':
        config.update(config_testserver)
    else:
        raise Exception('Use a valid mode')

def conf(path,rand=False):
    """Return a element from the config file, you can use path ==> key1.key2.key3 etc ..
    if kwargs rand is set to True, pick a random element from the end list of the path"""
    global config
    try:
        out = config
        sub_paths = path.split('.')
        for sub_path in sub_paths:
            out = out[sub_path]
        if rand:
            return random.choice(out)
        return out
    except:
        raise Exception(f'conf path does not exist : {path}')


def narr(path,rand=False):
    """Return a element from the narration file, you can use path ==> key1.key2.key3 etc ..
    if kwargs rand is set to True, pick a random element from the end list of the path"""
    global narration
    try:
        out = narration
        sub_paths = path.split('.')
        for sub_path in sub_paths:
            out = out[sub_path]
        if rand:
            return random.choice(out)
        return out
    except:
        raise Exception(f'narr path does not exist : {path}')