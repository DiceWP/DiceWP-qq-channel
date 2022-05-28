__all__ = [
    "max_len",
    "fuck_nl",
    "harmless_domain",
    "harmless_mention"
]

import re

from constant import domain_re
from core.model import Message
from typing import Match


def max_len(string: str, length: int) -> str:
    if len(string) > length:
        return string[:length] + "..."

    return string


def fuck_nl(text: str) -> str:  # :-D
    return text.replace("\n", r"\n").replace("\r", r"\r").replace("\r\n", r"\r\n")


def harmless_domain(text: str) -> str:
    return domain_re.sub("", text)


mention_re = re.compile(r"@everyone|<@[!&]?(\d*)>")


def harmless_mention(message: Message) -> Message:
    def _harmless_mention(match: Match):
        if match.group(1):
            for user in message.mentions:
                if user.id == match.group(1):
                    return "@%s" % user.username
            else:
                return "@%s" % match.group(1)

        else:
            return "@所有人"

    message.text = mention_re.sub(_harmless_mention, message.text)
    return message


def remove_mention(text: str) -> str:
    return mention_re.sub("", text)


def harmless_message(message: Message) -> Message:
    harmless_mention(message)
    message.text = harmless_domain(message.text)
    message.author.username = remove_mention(harmless_domain(message.author.username)) or "调查员"

    return message
