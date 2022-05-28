__all__ = [
    "times_roll",
    "times_check",
    "show_talents",
    "format_talents",
    "list_pc",
    "param_length_check",
    "show_stats"
]

from constant.words import *
from core.model import Message
from constant.error import DiceError
from core.dice import PC, Group, Exp


async def times_roll(exp: Exp, times, short=False):
    res = [await exp.roll() for i in range(times)]
    if short:
        return "\n" + "\n".join(Common.Show.ONE_EQ % r[1] for r in res)
    else:
        return "\n" + "\n".join(Common.Show.TWO_EQ % r for r in res)


async def times_check(group: Group, exp: Exp, value, times, pattern=None, repl=None, short=False):
    res = [await exp.roll() for i in range(times)]
    if short:
        return "\n" + "\n".join(
            [Roll.Check.SHOW % (Common.Show.TWO_EQ % (exp.exp, r[1]), value,
                                await group.roll_check(r[1], value, pattern=pattern, repl=repl))
             for r in res])
    else:
        return "\n" + "\n".join(
            [Roll.Check.SHOW % (
                Common.Show.THREE_EQ % (exp.exp, r[0], r[1]), value,
                await group.roll_check(r[1], value, pattern=pattern, repl=repl))
             for r in res])


max_length = 30


def format_talents(talents):
    lines = []
    line = ""
    talents.sort()
    for talent in talents:
        if not line:
            line = Common.Show.TWO_COLON % talent
        else:
            if len(line + "　" + Common.Show.TWO_COLON % talent) <= max_length:
                line += "　" + Common.Show.TWO_COLON % talent
            else:
                lines.append(line)
                line = Common.Show.TWO_COLON % talent
    else:
        lines.append(line)

    return "\n".join(lines)


async def show_talents(pc: PC):
    talents = await pc.get_all_talent()

    text = Set.Talent.Show.MULTIPLE % pc.pc
    if talents:
        text += format_talents(talents)
    else:
        text += Set.Talent.Show.NO_TALENT_TO_SHOW

    return text


async def list_pc(pc: PC, pcs):
    text = ""
    for i in range(len(pcs)):
        text += "\n[%s] %s" % ("×" if pcs[i] == pc.pc else i, pcs[i])

    return text


def param_length_check(message: Message, require: int, show_text):
    """
    参数长度检查
    :param message: Message对象
    :param require: 最少参数长度
    :param show_text: 不符合时返回的文本
    :return: 不符合直接raise交给bot.router处理
    """
    if len(message.args) < require:
        raise DiceError(show_text)


def show_stats(name, stats):
    return Common.Show.STATS % (name,
                                stats.get("roll") or 0,
                                stats.get("res") or 0,
                                stats.get("big_succ") or 0,
                                stats.get("big_fail") or 0)
