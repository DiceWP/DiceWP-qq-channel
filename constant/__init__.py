from constant.config import config
import json
import re

with open("constant\\domains.json", mode="rt", encoding="utf-8") as f:
    domains = json.load(f)

domain_re = re.compile(r"\.(?=%s)" % "|".join(domains))

with open('constant\\b_words.json', mode='rt', encoding='utf-8') as f:
    b_words = json.load(f)