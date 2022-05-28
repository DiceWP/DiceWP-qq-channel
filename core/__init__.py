# 加载
import os

if not os.path.exists("log"):
    os.mkdir("log")

os.environ["QQBOT_LOG_PATH"] = os.path.join(os.getcwd(), "log", "%(name)s.log")
os.environ[
    "QQBOT_LOG_PRINT_FORMAT"] = "%(asctime)s \033[1;33m[%(levelname)s] %(funcName)s (%(filename)s:%(lineno)s):\033[0m %(message)s"


from core.bot import bot
import core.function
import core.event
