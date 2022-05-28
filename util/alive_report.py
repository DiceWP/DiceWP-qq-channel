import aiohttp
import asyncio

from constant import config

client = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(5))


async def reporter():
    while True:
        async with client.get(config.alive_report) as r:
            await r.text()
        await asyncio.sleep(60)


asyncio.get_event_loop().create_task(reporter())