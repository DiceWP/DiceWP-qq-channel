__all__ = ["config"]

import yaml
import sys

from util.format import dict2obj

with open("config.yaml", mode="r", encoding="utf-8") as f:
    config = yaml.safe_load(f)


class Bot:
    appid: str
    token: str
    secret: str
    sandbox: bool
    sandbox_guild: str


class DataBase:
    host: str
    port: int
    user: str
    db: str
    password: str


class Dice:
    max_dice: int
    max_side: int
    max_time: int
    min_time: int


class MaxLength:
    nickname: int
    talent: int
    pc: int
    welcome: int


class CD:
    time: int
    size: int


class Stats:
    max_res: int


class ST:
    max_st_one_time: int


class Limit:
    dice: Dice
    max_length: MaxLength
    cd: CD
    stats: Stats
    st: ST


class UserDefaultSetting:
    default_side: int
    pc: str


class GroupDefaultSetting:
    coc_rule: str


class TokenServer:
    url: str
    token: str


class Config:
    bot: Bot
    database: DataBase
    limit: Limit
    user_default_setting: UserDefaultSetting
    group_default_setting: GroupDefaultSetting
    token_server: TokenServer
    resource: str
    alive_report: str


# 这字典我是一天也看不下去了
config: Config = dict2obj(config)
# 对象赛高（）


if not hasattr(config.database, "port"):
    config.database.port = 3306

if not hasattr(config.bot, "sandbox"):
    config.bot.sandbox = False

if len(sys.argv) > 1:
    for arg in sys.argv:
        if arg in ["-s", "--sandbox"]:
            config.bot.sandbox = True
            break

if not hasattr(config.bot, "sandbox_guild"):
    config.bot.sandbox = ""

# max_st_one_time 实际体现为对args的限长
config.limit.st.max_st_one_time = config.limit.st.max_st_one_time * 2
