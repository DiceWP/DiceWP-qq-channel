WORDS = {
    "str": "力量",
    "con": "体质",
    "siz": "体型",
    "dex": "敏捷",
    "app": "外貌",
    "int": "智力",
    "pow": "意志",
    "edu": "教育",
    "san": "理智",
    "luck": "幸运"
}


def translate(talent: str):
    return WORDS.get(talent.lower()) or talent
