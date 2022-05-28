__all__ = [
    "number_check",
    "size_check",
    "length_check",
    "text_check",
    "black_words"
]

from constant import domain_re, b_words
from constant.words import *
from constant.error import SecCheckError
from util.qq_api import qq_api


def base_check(target, noun, min, max, min_error, max_error):
    if target > max:
        raise SecCheckError(max_error % (noun, max))
    if target < min:
        raise SecCheckError(min_error % (noun, min))


def number_check(target, noun, min, max):
    base_check(target, noun, min, max, Common.Limit.TOO_FEW, Common.Limit.TOO_MANY)


def size_check(target, noun, min, max):
    base_check(target, noun, min, max, Common.Limit.TOO_SMALL, Common.Limit.TOO_BIG)


def length_check(target, noun, min, max):
    base_check(len(target), noun, min, max, Common.Limit.TOO_LONG, Common.Limit.TOO_FEW)


async def text_check(target):
    if domain_re.search(target):  # 链接拦截
        raise SecCheckError(BotReply.URL_NOT_ALLOWED)

    if await qq_api.msg_sec_check(target):  # 文本安全api
        raise SecCheckError(BotReply.SEC_CHECK)


def black_words(target):
    for word in b_words:
        if word in target:
            raise SecCheckError(BotReply.SEC_CHECK)
