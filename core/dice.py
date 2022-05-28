__all__ = [
    "PC",
    "Group",
    "Stats",
    "Exp",
    "Dice"
]

import random
import re
import time
from typing import List, Match, Union

from constant.error import *
from constant.words import *
from constant.jrrp import *
from constant import config
from dao.dice import *
from dao.stats import *
from util.sec_check import *
from util.translate import translate
from core.model import Message

# https://regex101.com/ :-D
GET_DICE = re.compile("([+\-*/^%x()]*)(?:(?:([bp])(\d*))|(\d+)?d(?:(\d+)(?:[~～](\d+))?)?(k(\d*))?|(\d+))").sub

"""
([+\-*/x()]*) (?: (?:(?:([bp])(\d*)) | (\d+)?d(?:(\d+)(?:[~～](\d+))?)?(k(\d*))? | (\d+))
 g1 运算符        g2-g3 奖惩骰                        g4-g8 一般骰                g9 纯数字
"""


class PC:  # 调查员
    _setting: dict
    _talent: dict
    _jrrp: dict

    uid: str
    username: str
    group: str
    scope: str
    pc: str

    async def init(self, message: Message, group=None, pc=None):
        """
        :param message: 消息对象
        :param group: 用户组，为空则从message中读取
        :param pc: play card名称，为空则依据频道id和用户id从配置中读取
        """
        self._setting = {}
        self._talent = {}
        self._jrrp = None

        self.uid = message.author.id
        self.username = message.author.username
        self.group = group or ("global" if message.direct else message.guild_id)
        self.scope = "全局" if self.group == "global" else "当前频道"
        self.pc = pc or await self.get_setting("pc")

        self.stats = Stats(uid=self.uid, gid=None if self.group == "global" else self.group)

    async def self_check(self):
        """
        检查用户在指令设置的调查员名称是否违规
        如有违规会 raise SecCheckError
        """
        await text_check(self.pc)

    # setting operate

    async def get_setting(self, k, _format=None, use_cache=True, default=None):
        """
        获取配置
        :param k: 键
        :param _format: 格式化函数
        :param use_cache: 是否使用缓存
        :param default: 如无默认值
        :return: 值
        """
        if k in self._setting and use_cache:
            return self._setting[k]

        res = await get_setting(self.uid, self.group, k) or (
            config.user_default_setting[k] if default is None else default)  # 如不存在则从配置中读取默认值

        if _format:
            res = _format(res)
        self._setting[k] = res

        return res

    async def set_setting(self, k, v):
        """
        设置配置
        :param k: 键
        :param v: 值
        :return: 更新前的值（如果有）
        """

        if isinstance(v, str):
            await text_check(v)  # 文本安全

        self._setting[k] = v  # 更新缓存

        return await set_setting(self.uid, self.group, k, v)

    async def unset_setting(self, k):
        """
        删除配置
        :param k: 键
        :return: 更新前的值（如果有）
        """

        if k in self._setting:  # 更新缓存
            self._setting.pop(k)

        return await unset_setting(self.uid, self.group, k)

    async def tag_playcard(self, new_pc):
        """
        修改玩家卡
        :param new_pc:
        :return: 更新前的值（如果有）
        """
        length_check(new_pc, Noun.PC, 1, config.limit.max_length.pc)
        self._talent.clear()
        return await self.set_setting("pc", new_pc)

    async def set_nickname(self, new_nickname):
        """
        设置昵称
        :param new_nickname: 新昵称
        :return 更新前的值（如果有）
        """
        length_check(new_nickname, Noun.NICKNAME, 1, config.limit.max_length.nickname)
        return await self.set_setting('nickname', new_nickname)

    async def set_default_side(self, dst):
        """
        设置默认骰
        :param dst: 骰子面数
        :return 更新前的值（如果有）
        """
        number_check(dst, Noun.DICE_SIDE, 1, config.limit.dice.max_side)
        return await self.set_setting('default_side', dst)

    @property
    def default_side(self):
        return self.get_setting("default_side")

    @property
    def nickname(self):
        return self.get_setting("nickname", default=self.username)

    async def get_default_dice(self):
        return "D%s" % await self.default_side

    async def get_default_exp(self):
        exp = Exp()
        await exp.init(self, await self.get_default_dice())
        return exp

    # pc operate

    async def rename(self, new_pc):
        """
        重命名调查员
        :param new_pc: 重命名后的调查员
        """

        length_check(new_pc, Noun.PC, 1, config.limit.max_length.pc)
        await text_check(new_pc)

        await rename_pc(self.uid, self.pc, new_pc)
        self.pc = new_pc

    async def copy(self, new_pc):
        """
        复制调查员属性到新调查员
        :param new_pc: 复制后的调查员
        :return: 是否有复制属性
        """

        length_check(new_pc, Noun.PC, 1, config.limit.max_length.pc)
        await text_check(new_pc)

        return await copy_pc(self.uid, self.pc, new_pc)

    async def list(self):
        """
        获取用户全部调查员（已设置属性
        :return: [pcname,]
        """
        return await list_pc(self.uid)

    async def delete(self):
        """
        清空调查员的属性，清除统计并解除配置
        """
        await del_pc(self.uid, self.pc)

        self._talent.clear()
        self.pc = await self.get_setting("pc", use_cache=False)

    # talent operate

    async def clr(self):
        """
        清除用户所有调查员的 属性/统计/配置
        """

        await clr_pc(self.uid)

        self._talent.clear()
        self.pc = await self.get_setting("pc", use_cache=False)

    async def get_talent(self, k, use_cache=True):
        """
        获取属性
        :param k: 键
        :param use_cache: 是否使用缓存
        :return: 值/None
        """
        k = translate(k)

        if k in self._talent and use_cache:
            return self._talent[k]

        res = await get_talent(self.uid, self.pc, k)
        if res:
            res = int(res)

        self._talent[k] = res
        return res

    async def get_all_talent(self):
        """
        获取全部属性
        :return: ((键, 值),)
        """
        res = await get_all_talent(self.uid, self.pc)

        self._talent = {i["k"]: i["v"] for i in res}

        return [(i['k'], i['v']) for i in res]

    async def set_talent(self, k: str, v: Union[str, int]):
        """
        设置属性
        :param k: 键
        :param v: 值
        :return: 更新前的值（如果有）
        """

        k = translate(k)

        length_check(k, Noun.TALENT, 1, config.limit.max_length.talent)
        size_check(v, Noun.VALUE, 0, config.limit.dice.max_side)

        await text_check(k)  # 文本安全

        self._talent[k] = int(v)

        return await set_talent(self.uid, self.pc, k, v)

    async def del_talent(self, k):
        """
        删除属性
        :param k: 键
        :return: 更新前的值（如果有）
        """
        if k in self._talent:
            self._talent.pop(k)

        await del_talent(self.uid, self.pc, k)

    async def clear_talent(self):
        """
        清除属性
        """
        self._talent = {}

        await clr_talent(self.uid, self.pc)

    # jrrp operate

    async def get_jrrp(self):
        """
        获取jrrp
        :return: word
        """

        date = int((time.time() + 3600 * 8) / 86400)  # 日期计算

        if not self._jrrp:
            jrrp = await get_jrrp(self.uid)
            if jrrp:
                self._jrrp = jrrp
            else:
                self._jrrp = {"date": ""}

        if self._jrrp["date"] != date:
            self._jrrp["date"] = date
            self._jrrp["template"] = random.randint(0, len(JRRP_TEMPLATE) - 1)
            self._jrrp["v"] = random.randint(1, 100)
            await set_jrrp(self.uid, **self._jrrp)

        return JRRP_TEMPLATE[self._jrrp["template"]] % {"nick": await self.nickname, "v": self._jrrp["v"]}

    @property
    def jrrp(self):
        return self.get_jrrp()

    # dice operate

    async def Exp(self, exp, _parse=True):
        """
        生成投掷表达式
        :param exp: 投掷表达式
        :param _parse: 是否自动解析
        :return: 投掷表达式对象
        """
        _exp = Exp()
        await _exp.init(self, exp, _parse=_parse)
        return _exp


class Group:  # 群操作句柄
    gid: str
    _setting: dict

    async def init(self, message: Message = None, user_id=None, guild_id=None):
        """
        :param message: 消息对象
        :param guild_id: 频道id 优先选择
        """
        self.gid = guild_id or ("global" if message.direct else message.guild_id)
        self._setting = {}

        self.stats = Stats(uid=user_id or message.author.id, gid=None if self.gid == "global" else self.gid)

    async def get_setting(self, k, _format=None, use_cache=True, default=None):
        """
        获取配置
        :param k: 键
        :param _format: 格式化函数
        :param use_cache: 是否使用缓存
        :param default: 如无默认值
        :return: 值
        """
        if k in self._setting and use_cache:
            return self._setting[k]

        res = await get_group_setting(self.gid, k) or (
            config.group_default_setting[k] if default is None else default)  # 如不存在则从配置中读取默认值

        if _format:
            res = _format(res)
        self._setting[k] = res

        return res

    async def set_setting(self, k, v):
        """
        设置配置
        :param k: 键
        :param v: 值
        :return: 更新前的值（如果有）
        """

        if isinstance(v, str):
            await text_check(v)  # 文本安全

        self._setting[k] = v  # 更新缓存

        return await set_group_setting(self.gid, k, v)

    async def unset_setting(self, k):
        """
        删除配置
        :param k: 键
        :return: 更新前的值（如果有）
        """

        if k in self._setting:  # 更新缓存
            self._setting.pop(k)

        return await unset_group_setting(self.gid, k)

    async def set_coc_rule(self, id):

        await self.set_setting('coc_rule', id)

    async def unset_coc_rule(self):

        await self.unset_setting("coc_rule")

    @property
    def coc_rule(self):
        return self.get_setting("coc_rule")

    async def roll_check(self, r, v, pattern=None, repl=None):
        res = get_coc_rule(await self.get_setting("coc_rule"))(r, v)
        if res == "大成功":
            await self.stats.count("big_succ")
        elif res == "大失败":
            await self.stats.count("big_fail")

        if pattern and res in pattern:
            return repl
        return res


def get_coc_rule(id):
    def default(r: int, v: int):
        """
        默认判定 成功/困难成功/失败...
        :param r: 投掷结果
        :param v: 属性
        :return: 鉴定状态
        """
        if r > v:
            return "失败"
        if r <= v / 5:
            return "极难成功"
        if r <= v / 2:
            return "困难成功"
        return "成功"

    if id == "0":
        def rule(r, v):
            """
            出1大成功 不满50出96-100大失败，满50出100大失败
            """

            if r == 1:
                return "大成功"

            if v < 50:
                if r > 95:
                    return "大失败"

            else:
                if r > 99:
                    return "大失败"

            return default(r, v)

    elif id == "1":
        def rule(r, v):
            """
            不满50出1大成功，满50出1-5大成功 不满50出96-100大失败，满50出100大失败
            """

            if v < 50:
                if r == 1:
                    return "大成功"
                if r > 95:
                    return "大失败"
            else:
                if r < 6:
                    return "大成功"
                if r > 99:
                    return "大失败"

            return default(r, v)

    elif id == "2":
        def rule(r, v):
            """
            出1-5且<=成功率大成功 出100或出96-99且>成功率大失败
            """
            if r < 6 and r <= v:
                return "大成功"
            if r > 95 and r > v:
                return "大失败"

            return default(r, v)

    elif id == "3":
        def rule(r, v):
            """
            出1-5大成功 出96-100大失败
            """
            if r < 6:
                return "大成功"
            if r > 95:
                return "大失败"

            return default(r, v)

    elif id == "4":
        def rule(r, v):
            """
            出1-5且<=成功率/10大成功 不满50且出>=96+成功率/10大失败，满50出100大失败
            """
            if r < 6 and r <= v / 10:
                return "大成功"
            if r > 100 or r > 95 + v / 10:
                return "大失败"

            return default(r, v)

    elif id == "5":
        def rule(r, v):
            """
            出1-2且<成功率/5大成功 不满50出96-100大失败，满50出99-100大失败
            """
            if r < 3 and r < v / 5:
                return "大成功"
            if v < 50:
                if r > 95:
                    return "大失败"
            else:
                if r > 98:
                    return "大失败"

            return default(r, v)

    else:
        rule = default

    return rule


class Stats:  # 统计
    def __init__(self, uid=None, gid=None):
        self.uid = uid
        self.gid = gid

    async def get_user(self, k):
        return await get_stats(self.uid, "USER", k)

    async def get_guild(self, k):
        return await get_stats(self.gid, "GUILD", k)

    @staticmethod
    async def get_global(k):
        return await get_stats("G", "GLOBAL", k)

    async def get_user_all(self):
        return await get_all_stats(self.uid, "USER")

    async def get_guild_all(self):
        return await get_all_stats(self.gid, "GUILD")

    @staticmethod
    async def get_global_all():
        return await get_all_stats("G", "GLOBAL")

    async def clr_user(self):
        await clr_stats(self.uid, "USER")

    async def clr_guild(self):
        await clr_stats(self.gid, "GUILD")

    async def update(self, k, increase: int = None, v: int = None):
        """
        更新统计
        :param k: 键
        :param increase: 增量
        :param v: 指定值 优先
        """
        if self.uid:
            await update_stats(self.uid, "USER", k, increase=increase, v=v)

        if self.gid:
            await update_stats(self.gid, "GUILD", k, increase=increase, v=v)

        await update_stats("G", "GLOBAL", k, increase=increase, v=v)

    async def count(self, k):
        """
        计数类型统计
        :param k: 键
        """
        await self.update(k, increase=1)

    async def update_res(self, increase: int):
        """
        更新res统计项，添加了filter功能，用于保证数据不会太怪
        :param increase: 增量
        """

        if self.uid:
            await update_stats(self.uid, "USER", "res", increase=increase)

        if self.gid:
            await update_stats(self.gid, "GUILD", "res", increase=increase)

        if abs(increase) <= config.limit.stats.max_res:
            await update_stats("G", "GLOBAL", "res", increase=increase)


class Dice:  # 骰子
    match: Match
    pc: PC

    op: str

    exp: str
    calc: str
    res: int

    side: int
    min: int
    max: int
    num: int

    def __init__(self, match: Match):
        self.match = match

    async def init(self, pc: PC):
        self.pc = pc

        self.op = self.match.group(1) or ""
        self.op = self.op.replace("x", "*").replace("^", "**")

        self.exp = self.match.group(0)
        self.calc = ""
        self.res = 0

        self.side = 1
        self.min = 1
        self.max = 1
        self.num = 0

        if self.match.group(2):
            await self._parse_bp_dice()
        elif self.match.group(9):
            await self._parse_int()
        else:
            await self._parse_dice()

        self.side = self.max - self.min + 1

        self.sec_check()

    async def _parse_bp_dice(self):  # 解析奖惩骰
        self.type = "bp"

        self.num = int(self.match.group(3)) if self.match.group(3) else 1
        self.max = 100

        if self.match.group(2) == "b":
            self.roll = self.b_roll
        else:
            self.roll = self.p_roll

    async def _parse_dice(self):  # 解析一般骰
        self.type = "normal"

        self.num = int(self.match.group(4)) if self.match.group(4) else 1
        self.max = int(self.match.group(5)) if self.match.group(5) else await self.pc.default_side

        if self.match.group(6):
            self.min = int(self.match.group(6))
            if self.min > self.max:
                self.min, self.max = self.max, self.min

        if self.match.group(7):
            self.k = int(self.match.group(8)) if self.match.group(8) else 1
            if self.k > self.num:
                raise ExpressionFormatError(Expression.Error.K_MORE_THAN_N)
            self.roll = self.k_roll

    async def _parse_int(self):  # 解析纯数字
        self.type = "int"

        self.num = 1

        self.res = int(self.match.group(9))
        self.calc = self.match.group(9)

        self.roll = self.roll_nothing

    def roll(self):  # 一般骰 无直接返回，储存在 self.calc, self.res
        exp = []
        res = 0

        for i in range(self.num):
            r = random.randint(self.min, self.max)
            exp.append(str(r))
            res += r

        self.calc = "{%s}(%s)" % ("+".join(exp), res) if self.num > 1 else exp[0]
        self.res = res

    def k_roll(self):  # 最大点数骰
        res = []

        [res.append(random.randint(self.min, self.max)) for i in range(self.num)]

        res.sort(reverse=True)

        throw = res[self.k:]
        res = res[:self.k]

        exp = [str(i) for i in res]
        res = sum(res)

        self.calc = "{%s [%s]}(%s)" % ("+".join(exp), "/".join(str(i) for i in throw), res)
        self.res = res

    def b_roll(self):  # 奖励骰
        dice = random.randint(self.min, self.max)

        b_dice = [random.randint(0, 9) for i in range(self.num)]

        b_dice.sort()

        if b_dice[0] * 10 < dice:
            res = b_dice[0] * 10 + dice % 10
            if res == 0:
                res = 1
        else:
            res = dice

        self.calc = "{%s [b:%s]}(%s)" % (dice, " ".join(str(i) for i in b_dice), res)
        self.res = res

    def p_roll(self):  # 惩罚骰
        dice = random.randint(self.min, self.max)

        p_dice = [random.randint(0, 9) for i in range(self.num)]

        p_dice.sort(reverse=True)

        if p_dice[0] * 10 > dice:
            res = p_dice[0] * 10 + dice % 10
            if res == 0:
                res = 1
        else:
            res = dice

        self.calc = "{%s [p:%s]}(%s)" % (dice, " ".join(str(i) for i in p_dice), res)
        self.res = res

    @staticmethod
    def roll_nothing():  # 开摆！
        pass

    def sec_check(self):  # 合规检查
        if self.type == "int" and self.res == 0 and self.op == "/":
            raise ExpressionFormatError(Joke.ZERO_DIVIDE)
        if self.num < 1:
            raise ExpressionFormatError(Joke.ZERO_DICE)
        if self.side < 1:
            raise ExpressionFormatError(Joke.ZERO_SIDE)

        number_check(self.side, Noun.DICE_SIDE, 1, config.limit.dice.max_side)


class Exp:  # 投掷表达式
    pc: PC
    exp: str
    dices: List[Dice]
    single: bool
    stats: Stats

    async def init(self, pc: PC, exp, _parse=True):
        self.pc = pc
        self.exp = exp
        self.dices = []
        self.single = False

        if _parse:
            await self._parse()

    async def _parse(self):  # 解析
        exp = GET_DICE(self._add_dice, self.exp.lower())  # re.sub 如替换后有剩余则表达式错误
        _exp = exp.replace(")", "")  # 忽视括号
        if _exp:
            raise ExpressionUnresolvedError(Expression.Error.UNRESOLVED_TEXT % _exp)
        self.op_end = exp

        [await dice.init(self.pc) for dice in self.dices]  # 异步初始化
        self.sec_check()

        if len(self.dices) == 1 and (
                self.dices[0].type == "int" or self.dices[0].type == "normal" and self.dices[0].num == 1):
            self.single = True

    def sec_check(self):  # 合规检查

        number_check(sum(dice.num for dice in self.dices), Noun.DICE, 1, config.limit.dice.max_dice)

    def _add_dice(self, match: Match):
        self.dices.append(Dice(match))

    async def roll(self):  # 投掷一次骰子 -> tuple(calc(计算过程), res(结果))
        calc = ""
        res = ""

        for dice in self.dices:
            dice.roll()
            calc += dice.op + dice.calc
            res += dice.op + str(dice.res)

        calc += self.op_end
        res += self.op_end

        while "()" in res:
            res = res.replace("()", "")  # 删除空括号

        try:
            res = eval(res)  # 小 心 注 入
        except ZeroDivisionError:
            raise ExpressionFormatError(Joke.ZERO_DIVIDE)
        except SyntaxError as e:
            if e.args[0] == "unmatched \")\"" or e.args[0] == "unexpected EOF while parsing":
                raise ExpressionFormatError(Expression.Error.BRACKET)
            elif e.args[0] == "invalid syntax":
                raise ExpressionFormatError(Expression.Error.CALC)
            else:
                raise e

        await self.pc.stats.count("roll")
        await self.pc.stats.update("dice_exp", len(self.dices))
        await self.pc.stats.update("dice", self.dice_num)
        await self.pc.stats.update_res(res)

        return calc, res

    @property
    def dice_num(self):
        return sum(dice.num for dice in self.dices)

    async def _max(self):
        res = sum(dice.max for dice in self.dices)
        await self.pc.stats.count("roll")
        await self.pc.stats.update("dice_exp", len(self.dices))
        await self.pc.stats.update("dice", self.dice_num)
        await self.pc.stats.update_res(res)
        return res

    @property
    def max(self):
        return self._max()
