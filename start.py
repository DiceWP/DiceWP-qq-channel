import asyncio
from core import bot
from util.alive_report import reporter

asyncio.get_event_loop().create_task(reporter())

bot.run()
