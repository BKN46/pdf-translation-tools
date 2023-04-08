import json
import os

if not os.path.isfile('settings.json'):
    open('settings.json', 'w').write('{}')

SETTINS = json.load(open('settings.json', 'r'))

def get_setting(setting):
    if setting in SETTINS:
        return SETTINS[setting]
    else:
        SETTINS[setting] = None
        open('settings.json', 'w').write(json.dumps(SETTINS,indent=2))
        return None
