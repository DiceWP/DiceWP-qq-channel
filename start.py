import os

if not os.path.exists("log"):
    os.mkdir("log")

os.environ["QQBOT_LOG_PATH"] = os.path.join(os.getcwd(), "log", "%(name)s.log")
os.environ[
    "QQBOT_LOG_PRINT_FORMAT"] = "%(asctime)s \033[1;33m[%(levelname)s] %(funcName)s (%(filename)s:%(lineno)s):\033[0m %(message)s"

import asyncio

from core import bot
from util.alive_report import reporter

asyncio.get_event_loop().create_task(reporter())

bot.run()
