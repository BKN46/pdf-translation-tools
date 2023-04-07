import json
import requests

from utils.settings import SETTINS

url = f"https://transmart.qq.com/api/imt"
user = SETTINS['mt_user']
token = SETTINS['mt_token']

def get_translate_block(text, src_lang="en", tgt_lang="zh"):
    body = {
        "header": {
            "fn": "auto_translation_block",
            "token": token,
            "user": user,
        },
        "type": "plain",
        "source": {
            "lang": src_lang,
            "text_block": text,
        },
        "target": {
            "lang": tgt_lang,
        },
    }
    res = requests.post(url, json=body).json()
    # print(json.dumps(res, indent=2))
    try:
        translation = res["auto_translation"]
        return translation
    except Exception as e:
        return json.dumps(res, indent=2)
