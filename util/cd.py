import time
import asyncio
import copy
from typing import List, Dict

from constant import config
from constant.error import Interrupt, TooFast
from constant.words import BotReply

cache: Dict[str, List[float]] = {}


async def scavenger():  # 清洗任务
    while True:
        await asyncio.sleep(60)
        for user, lis in copy.deepcopy(cache).items():
            if not lis or time.time() - lis[0] > 60:
                cache.pop(user)


def check(uid):
    if uid not in cache or not cache[uid]:
        cache[uid] = [time.time()]
    else:
        while cache[uid] and time.time() - cache[uid][0] > config.limit.cd.time:
            cache[uid].pop(0)

        if len(cache[uid]) > config.limit.cd.size:
            raise Interrupt
        if len(cache[uid]) == config.limit.cd.size:
            cache[uid].append(time.time())
            raise TooFast(BotReply.TOO_FAST)

        cache[uid].append(time.time())


asyncio.get_event_loop().create_task(scavenger())
