import re
import random

import core.dice
from constant import config
from constant.words import *
from constant.error import ExpressionError, ErrorWithMsg
from constant.mad import *
from constant.coc import *
from util.dice import *
from util.sec_check import *
from core.bot import bot
from core.model import Message


async def PC(message: Message, group=None, pc=None):
    _pc = core.dice.PC()
    await _pc.init(message=message, group=group, pc=pc)
    return _pc


async def Group(message: Message):
    _group = core.dice.Group()
    await _group.init(message=message)
    return _group


@bot.command("r")
async def roll(message: Message):
    ctx = bot.ctx(message)
    pc = await PC(message)

    if "s" in message.args[0]:  # 短结果
        short = True
        message.args[0] = message.args[0].replace("s", "", 1)
    else:
        short = False

    text = ""

    if len(message.args) > 1:
        text += Roll.WITH_REASON % message.args[1]

    if "#" in message.args[0]:  # 多轮骰
        r = message.args[0].split("#")

        times = await pc.Exp(r[0] or "1")
        times = await times.roll()
        times = int(times[1])

        text += Roll.DICE_WITH_TIME % {"name": await pc.nickname, "time": times}

        if times > config.limit.dice.max_time:  # 检查轮数，因机制特殊（修正）所以不调用number_check
            times = config.limit.dice.max_time
            text = text[:-2] + Common.Fix.TOO_MANY % config.limit.dice.max_time

        elif times < config.limit.dice.min_time:
            times = config.limit.dice.min_time
            text = text[:-2] + Common.Fix.TOO_FEW % config.limit.dice.min_time

        exp = r[1]
        if not exp:
            exp = await pc.get_default_dice()  # 读取默认骰
        text += exp

        exp = await pc.Exp(exp)
        text += await times_roll(exp, times, short=short)

    else:
        exp = message.args[0]

        if not exp:
            exp = await pc.get_default_dice()  # 读取默认骰

        exp = await pc.Exp(exp)
        res = await exp.roll()

        text += Roll.DICE % await pc.nickname

        if exp.single or short:  # 短结果输出
            text += Common.Show.TWO_EQ % (exp.exp, res[1])
        else:
            text += Common.Show.THREE_EQ % (exp.exp, res[0], res[1])

    await ctx.send(text=text)


@bot.command("set")
async def set_default_side(message: Message):
    ctx = bot.ctx(message)
    pc = await PC(message)

    if not message.args[0]:
        await pc.unset_setting("default_side")
        await ctx.send(
            Set.Setting.Common.RESET % (pc.scope, Noun.DEFAULT_DICE_SIDE, config.user_default_setting.default_side))
        return

    if message.args[0] == "show":
        await ctx.send(Common.Show.THREE_DES % (await pc.nickname, Noun.DEFAULT_DICE_SIDE, await pc.default_side))
        return

    if not re.search(r"^\d+$", message.args[0]):
        await ctx.send(Common.Require.INT % Noun.DICE_SIDE + Set.Setting.EG.DEFAULT_SIDE)
        return

    dst = int(message.args[0])

    if dst == 0:
        # 诡计多端的〇（划掉）
        await ctx.send(Joke.ZERO_SIDE)
        return

    await pc.set_default_side(dst)

    if dst == 1:
        await ctx.send(Joke.REALLY + Set.Setting.Common.SET % (pc.scope, Noun.DEFAULT_DICE_SIDE, dst))
    else:
        await ctx.send(Set.Setting.Common.SET % (pc.scope, Noun.DEFAULT_DICE_SIDE, dst))


@bot.command("nn")
async def nickname(message: Message):
    ctx = bot.ctx(message)
    pc = await PC(message)

    if message.args[0] == "":
        await pc.unset_setting("nickname")
        await ctx.send(Set.Setting.Common.RESET % (pc.scope, Noun.NICKNAME, message.author.username))
        return

    await pc.set_nickname(message.args[0])

    await ctx.send(Set.Setting.Common.SET % (pc.scope, Noun.NICKNAME, message.args[0]))


async def _tag_playcard(message: Message):
    ctx = bot.ctx(message)
    pc = await PC(message)

    if len(message.args) < 2 or message.args[1] == "":
        await pc.unset_setting("pc")
        await ctx.send(Set.Setting.Common.RESET % (pc.scope, Noun.PC, config.user_default_setting.pc))
        return

    await pc.tag_playcard(message.args[1])

    await ctx.send(Set.Setting.Common.SET % (pc.scope, Noun.PC, message.args[1]))


async def _show_playcard(message: Message):  # un test
    ctx = bot.ctx(message)

    if len(message.args) > 1 and message.args[1] != "":
        pc = await PC(message, pc=message.args[1])
        await pc.self_check()
    else:
        pc = await PC(message)

    await ctx.send(await show_talents(pc))


async def _rename_playcard(message: Message):
    ctx = bot.ctx(message)

    param_length_check(message, 2, Common.Require.PARAM % Noun.PC + Set.PC.EG.RENAME)

    if len(message.args) > 2:
        pc = await PC(message, pc=message.args[1])
        await pc.self_check()
        dst = message.args[2]
    else:
        pc = await PC(message)
        dst = message.args[1]

    name = pc.pc
    await pc.rename(dst)
    await ctx.send(Set.PC.Common.RENAME % (name, pc.pc))


async def _list_playcard(message: Message):
    ctx = bot.ctx(message)
    pc = await PC(message)
    pcs = await pc.list()

    if pc.pc not in pcs:
        pcs.append(pc.pc)

    if not pcs:
        await ctx.send(Set.PC.Common.NO_PC_TO_SHOW)
        return

    await ctx.send(Set.PC.Common.LIST % (await pc.nickname, await list_pc(pc, pcs)))


async def _copy_playcard(message: Message):
    ctx = bot.ctx(message)

    param_length_check(message, 2, Common.Require.PARAM % Noun.PC + Set.PC.EG.COPY)

    if len(message.args) > 2:
        pc = await PC(message, pc=message.args[1])
        await pc.self_check()
        dst = message.args[2]
    else:
        pc = await PC(message)
        dst = message.args[1]

    dst_pc = await PC(message, pc=dst)

    await pc.copy(dst)
    await ctx.send(Set.PC.Common.COPY % (pc.pc, dst))


async def _del_playcard(message: Message):
    ctx = bot.ctx(message)

    if len(message.args) > 1 and message.args[1]:
        pc = await PC(message, pc=message.args[1])
        await pc.self_check()
    else:
        pc = await PC(message)

    await ctx.confirm(Set.PC.Confirm.DEL % pc.pc)

    pc_name = pc.pc
    await pc.delete()
    await ctx.send(Set.PC.Common.DEL % (pc_name, pc.pc))


async def _clr_playcard(message: Message):
    ctx = bot.ctx(message)
    pc = await PC(message)

    await ctx.confirm(Set.PC.Confirm.CLR)

    await pc.clr()
    await ctx.send(Set.PC.Common.CLR)


@bot.command("pc")
async def playcard(message: Message):
    if message.args[0] == "tag":
        await _tag_playcard(message)

    elif message.args[0] == "show":
        await _show_playcard(message)

    elif message.args[0] == "nn":
        await _rename_playcard(message)

    elif message.args[0] == "list":
        await _list_playcard(message)

    elif message.args[0] == "cpy":
        await _copy_playcard(message)

    elif message.args[0] == "del":
        await _del_playcard(message)

    elif message.args[0] == "clr":
        await _clr_playcard(message)

    elif message.args[0] == "st":  # 奇怪的指令调用方式（
        message.text = re.sub(r"st ?", "", message.text)
        message.args = message.text.split(" ")
        await set_talent.run(message)

    else:
        ctx = bot.ctx(message)
        pc = await PC(message)
        await ctx.send(Set.PC.Common.DEFAULT % pc.pc)


async def _del_talent(message: Message):
    ctx = bot.ctx(message)
    pc = await PC(message)

    param_length_check(message, 2, Common.Require.PARAM % Noun.TALENT + Set.Talent.EG.DELETE)

    await pc.del_talent(message.args[1])
    await ctx.send(Set.Talent.Common.DELETE % (pc.pc, message.args[1]))


async def _show_talent(message: Message):
    ctx = bot.ctx(message)
    pc = await PC(message)

    if len(message.args) < 2 or message.args[1] == "":
        await ctx.send(await show_talents(pc))
    else:
        talent = await pc.get_talent(message.args[1])
        if talent is None:
            await ctx.send(Set.Talent.Show.TALENT_NOT_EXISTS % message.args[1])
        else:
            await ctx.send(Set.Talent.Show.SINGLE % (pc.pc, message.args[1], talent))


async def _clear_talent(message: Message):
    ctx = bot.ctx(message)

    if len(message.args) > 1:
        pc = await PC(message, pc=message.args[1])
        await pc.self_check()
    else:
        pc = await PC(message)

    await ctx.confirm(Set.Talent.Confirm.CLR % pc.pc)

    await pc.clear_talent()

    await ctx.send(Set.Talent.Common.CLR % pc.pc)


async def _set_talent(message: Message):
    ctx = bot.ctx(message)

    if len(message.args) * 2 > config.limit.st.max_st_one_time:
        await ctx.send(Set.Talent.Limit.TOO_MANY_ST % config.limit.st.max_st_one_time)
        return

    text = []

    param_length_check(message, 2, Common.Require.TWO_PARAM % (Noun.TALENT, Noun.VALUE) + Set.Talent.EG.SET)

    if len(message.args) % 2 != 0:
        await ctx.send(Set.Talent.Error.NOT_PAIR)
        return

    if len(set(message.args[::2])) != len(message.args) / 2:  # 重设置过滤
        talents = message.args[::2]
        [talents.remove(t) for t in set(talents)]
        await ctx.send(Set.Talent.Error.REPEAT % talents[0])
        return

    pc = await PC(message)

    while message.args:
        try:
            talent = message.args.pop(0)
            value = message.args.pop(0)

            value = re.search("^([+\-])?(.+)$", value)

            if not value:
                await ctx.send(Common.Require.EXP % Noun.VALUE + Set.Talent.EG.SET_PS)
                return

            if re.search(r"^\d+$", value.group(2)):  # 优化
                res = (value.group(0), eval(value.group(0)))
            else:
                exp = await pc.Exp(value.group(0))
                res = await exp.roll()

            if value.group(1):
                v = await pc.get_talent(talent)
                if v is None:
                    v = 0

                dst = v + res[1]
                calc = "(%s)" % (("+" if res[1] > 0 else "-") + str(res[1]))
            else:
                dst = res[1]
                calc = ""

            await pc.set_talent(talent, dst)
            text.append(Set.Talent.Common.SET % (pc.pc, talent, dst) + calc)
        except ErrorWithMsg as e:
            text.append(e.msg)

    if len(text) == 1:
        await ctx.send(text[0])
    else:
        await ctx.send(Set.Talent.Common.HEAD % pc.pc
                       + ("\n".join(text)).replace(Set.Talent.Common.HALF % pc.pc, ""))


@bot.command("st")
async def set_talent(message: Message):
    if message.args[0] == "del":
        await _del_talent(message)

    elif message.args[0] == "show":
        await _show_talent(message)

    elif message.args[0] == "clr":
        await _clear_talent(message)

    else:
        if not (len(message.args) == 2 and re.search(r"^[+\-]?\d+$", message.args[1])):
            message.args = re.sub(r"(?<! )([+\-])", r" \1", message.text).replace(":", " ").split(" ")  # 参数重处理
        await _set_talent(message)


async def _reget_talent(pc, talent, value):
    if value == "str":
        return value

    return await pc.get_talent(talent)


@bot.command("ra")
@bot.command("rc")
async def roll_check(message: Message):
    ctx = bot.ctx(message)
    pc = await PC(message)

    pattern = None
    repl = None

    if message.args[0] == "":
        await ctx.send(Common.Require.PARAM % Noun.TALENT + Roll.Check.EG)
        return

    if len(message.args) > 2:
        # 表达式 属性 指定值
        exp = message.args[0]
        talent = message.args[1]
        value = message.args[2]
    elif len(message.args) == 2:
        # 表达式 属性 / 属性 指定值

        value = await pc.get_talent(message.args[0])
        if value:  # 属性 指定值
            exp = await pc.get_default_dice()
            talent = message.args[0]
            value = message.args[1]
        else:  # 进一步确认
            try:
                await pc.Exp(message.args[0].replace("s", "", 1).replace("#", "", 1))
                # 如无异常，则 表达式 属性
                exp = message.args[0]
                talent = message.args[1]
                value = await pc.get_talent(talent)

            except ExpressionError:
                # 如异常 属性 指定值
                exp = await pc.get_default_dice()
                talent = message.args[0]
                value = message.args[1]
    else:
        # 属性
        exp = await pc.get_default_dice()
        talent = message.args[0]
        value = await pc.get_talent(talent)

    # 格式检查

    await text_check(talent)

    if talent.startswith("自动成功"):
        pattern = ["失败"]
        repl = "成功"
        value = await _reget_talent(pc, talent.replace("自动成功", "", 1), value)

    if talent.startswith("困难"):
        pattern = ["成功"]
        repl = "失败"
        value = await _reget_talent(pc, talent.replace("困难", "", 1), value)

    if talent.startswith("极难"):
        pattern = ["成功", "困难成功"]
        repl = "失败"
        value = await _reget_talent(pc, talent.replace("极难", "", 1), value)

    if value is None:
        await ctx.send(Roll.Check.TALENT_NOT_EXISTS % (pc.pc, re.sub(r"^(极难|困难|自动成功)", "", talent)))
        return

    if isinstance(value, str):

        if not re.search(r"^\d+$", value):
            await ctx.send(Common.Require.INT % Noun.VALUE)
            return

        value = int(value)
        size_check(value, Noun.VALUE, 0, config.limit.dice.max_side)

    group = await Group(message)

    if "s" in exp:
        short = True
        exp = exp.replace("s", "", 1)
    else:
        short = False

    if "#" in exp:
        r = exp.split("#")

        times = await pc.Exp(r[0] or "1")
        times = await times.roll()
        times = int(times[1])

        if times > config.limit.dice.max_time:  # 检查轮数，因机制特殊（修正）所以不调用number_check
            times = config.limit.dice.max_time

        elif times < config.limit.dice.min_time:
            times = config.limit.dice.min_time

        exp = r[1]
        if not exp:
            exp = await pc.get_default_dice()  # 读取默认骰

        exp = await pc.Exp(exp)
        await ctx.send(
            Roll.Check.COMMON % (await pc.nickname, talent) + await times_check(group, exp, value, times,
                                                                                short=short or exp.single,
                                                                                pattern=pattern, repl=repl))

    else:
        exp = await pc.Exp(exp)

        res = await exp.roll()
        succ = await group.roll_check(res[1], value, pattern=pattern, repl=repl)

        if exp.single or short:
            await ctx.send(
                Roll.Check.COMMON % (await pc.nickname, talent) + Roll.Check.SHOW % (
                    Common.Show.TWO_EQ % (exp.exp, res[1]), value, succ))
        else:
            await ctx.send(
                Roll.Check.COMMON % (await pc.nickname, talent) + Roll.Check.SHOW % (
                    Common.Show.THREE_EQ % (exp.exp, res[0], res[1]), value, succ))


@bot.role_check
@bot.command("setcoc")
async def setcoc(message: Message):
    ctx = bot.ctx(message)
    group = await Group(message)

    if not message.args[0]:
        await group.unset_coc_rule()
        await ctx.send(Set.Coc.RESET % (config.group_default_setting.coc_rule,
                                        Set.Coc.RULES[int(config.group_default_setting.coc_rule)]))
        return

    if message.args[0] == "show" or not re.search(r"^\d+$", message.args[0]):
        coc_rule = await group.coc_rule
        await ctx.send(Set.Coc.SHOW % (coc_rule, Set.Coc.RULES[int(coc_rule)]))
        return

    if int(message.args[0]) > len(Set.Coc.RULES):
        await ctx.send(Set.Coc.RULE_NOT_EXISTS)
        return

    await group.set_coc_rule(message.args[0])

    await ctx.send(Set.Coc.COMMON % (message.args[0], Set.Coc.RULES[int(message.args[0])]))


@bot.command("en")
async def enchant(message: Message):
    ctx = bot.ctx(message)
    pc = await PC(message)

    if message.args[0] == "":
        await ctx.send(Common.Require.PARAM % Noun.TALENT + En.EG)
        return

    if len(message.args) == 1:
        value = await pc.get_talent(message.args[0])
        if value is None:
            value = 0
    else:
        if not re.search(r"^\d+$", message.args[1]):
            await ctx.send(Common.Require.INT % Noun.VALUE)
            return

        value = int(message.args[1])

    exp = await pc.Exp(await pc.get_default_dice())
    res = await exp.roll()

    if res[1] < value:
        succ = "失败"
    else:
        succ = "成功"

    await ctx.send(En.COMMON % (pc.pc, message.args[0], Common.Show.TWO_EQ % (exp.exp, res[1]), value, succ))


@bot.command("sc")
async def san_check(message: Message):
    ctx = bot.ctx(message)
    pc = await PC(message)
    group = await Group(message)

    exps = message.args[0].split("/", 1)
    if len(exps) < 2:
        await ctx.send(SanCheck.FORMAT_ERROR + SanCheck.EG)
        return

    if len(message.args) > 1:
        if not re.search(r"^\d+$", message.args[1]):
            await ctx.send(Common.Require.INT % Noun.VALUE)
            return

        san = int(message.args[1])
        update = False
    else:
        san = await pc.get_talent(Noun.SAN)
        if san is None:
            await ctx.send(SanCheck.NEED_SAN)
            return

        update = True

    text = SanCheck.COMMON % await pc.nickname

    exp = await pc.get_default_exp()
    res = await exp.roll()

    succ = await group.roll_check(res[1], san)
    text += Roll.Check.SHOW % (Common.Show.TWO_EQ % (exp.exp, res[1]), san, succ)

    if res[1] > san:
        exp = await pc.Exp(exps[1])

        if succ == "大失败":
            calc = ""
            lose = await exp.max
        else:
            calc, lose = await exp.roll()

    else:
        exp = await pc.Exp(exps[0])
        calc, lose = await exp.roll()

    if not succ == "大失败" and not exp.single:
        text += "\n" + Common.Show.THREE_EQ % (exp.exp, calc, lose)

    remain = san - lose

    await pc.stats.update("lose_san", lose)

    text += SanCheck.LOSE % (await pc.nickname, lose, remain)

    if remain < 1:
        text += Joke.ZERO_SAN

    await ctx.send(text)

    if update:
        if remain < 0:
            remain = 0
        await pc.set_talent(Noun.SAN, remain)


@bot.command("ti")
@bot.command("li")
async def are_you_mad_are_you_unhappy_are_you_sad(message: Message):
    # :-D
    ctx = bot.ctx(message)
    pc = await PC(message)

    sort = random.randint(0, 9)
    if message.command == "ti":
        symptom = TI[sort]
        reply = Mad.TI
    else:
        symptom = LI[sort]
        reply = Mad.LI

    params = {"last": Common.Show.TWO_EQ % ("1D10", random.randint(1, 10))}

    if sort == 8:
        params["symptom"] = random.choice(FEAR)
    elif sort == 9:
        params["symptom"] = random.choice(MANIC)

    await ctx.send(reply % (await pc.nickname, symptom % params))


@bot.command("jrrp")
async def jrrp(message: Message):
    ctx = bot.ctx(message)
    pc = await PC(message)

    await ctx.send(await pc.jrrp)


@bot.command("stats")
async def stats(message: Message):
    ctx = bot.ctx(message)
    pc = await PC(message)

    if message.args[0] == "me":

        if len(message.args) > 1 and message.args[1] == "clr":
            await ctx.confirm(Set.Stats.CONFIRM % "个人")
            await pc.stats.clr_user()
            await ctx.send(Set.Stats.CLR % await pc.nickname)
            return

        stats = await pc.stats.get_user_all()
        text = show_stats(await pc.nickname, stats)

    elif message.args[0] == "guild":
        await bot.check_direct(message)

        if len(message.args) > 1 and message.args[1] == "clr":
            await bot.check_permission(message)
            await ctx.confirm(Set.Stats.CONFIRM % "频道")
            await pc.stats.clr_guild()
            await ctx.send(Set.Stats.CLR % (await bot.get_guild(message.guild_id)).name)
            return

        stats = await pc.stats.get_guild_all()
        guild_name = (await bot.get_guild(message.guild_id, channel_id=message.channel_id, desc="获取频道名称")).name
        black_words(guild_name)
        text = show_stats(guild_name, stats)

    elif message.args[0] == "global":
        if len(message.args) > 1 and message.args[1] == "clr":
            await ctx.send(Joke.NO_PERMISSION)
            return
        stats = await pc.stats.get_global_all()
        text = show_stats("全局", stats)

    else:
        if pc.group == "global":

            stats = await pc.stats.get_user_all()
            text = show_stats(await pc.nickname, stats)
        else:
            stats = await pc.stats.get_guild_all()
            guild_name = (await bot.get_guild(message.guild_id, channel_id=message.channel_id, desc="获取频道名称")).name
            black_words(guild_name)
            text = show_stats(guild_name, stats)

    await ctx.send(text)


def _gen_coc7():
    t1 = [sum(random.randint(1, 6) for i in range(3)) * 5 for x in range(6)]
    t2 = [(sum(random.randint(1, 6) for i in range(2)) + 6) * 5 for x in range(3)]

    t1.insert(2, t2[0])
    t1.insert(5, t2[1])
    t1.insert(7, t2[2])

    t1.append(sum(t1[:8]))
    t1.append(sum(t1[:9]))

    return tuple(t1)


@bot.command("coc")
async def coc(message: Message):
    ctx = bot.ctx(message)
    pc = await PC(message)

    if message.args[0] == "d":
        r = _gen_coc7()
        text = Coc.SHOW % await pc.nickname + Coc.CARD % r + Coc.DETAIL % (
            THOUGHT[random.randint(0, 9)],
            PEOPLE[random.randint(0, 9)],
            PLACE[random.randint(0, 9)],
            ITEM[random.randint(0, 9)],
            FEATURE[random.randint(0, 9)]
        ) + Coc.QUICK_ST % r[:9]

    else:
        if message.args[0] == "":
            times = 1
        else:
            if not re.search(r"^\d+$", message.args[0]):
                await ctx.send(Common.Require.INT % Noun.TIMES)
                return

            times = int(message.args[0])
            number_check(times, Noun.TIMES, 1, config.limit.dice.max_time)

        text = Coc.SHOW % await pc.nickname + "\n\n".join(Coc.CARD % _gen_coc7() for i in range(times))

    await ctx.send(text)


@bot.role_check
@bot.command("welcome")
async def welcome(message: Message):
    ctx = bot.ctx(message)
    group = await Group(message)

    if message.text == "":
        await group.unset_setting("welcome_word")
        await group.unset_setting("welcome_channel")
        await ctx.send(Set.Welcome.RESET)
    else:
        length_check(message.text, Noun.WELCOME, 1, config.limit.max_length.welcome)

        channels = re.findall(r"#(.{1,10}) ", message.text)
        for channel in channels:
            if await ctx.get_channel_by_name(channel):
                message.text = message.text.replace(f"#%s " % channel,
                                                    "<#%s>" % (await ctx.get_channel_by_name(channel)).id, 1)

        message.text = re.sub(r"[｛{]nick[}｝]", "{nick}", message.text, flags=re.I)
        message.text = re.sub(r"[｛{]at[}｝]", "{at}", message.text, flags=re.I)

        await group.set_setting("welcome_word", message.text)
        await group.set_setting("welcome_channel", message.channel_id)
        await ctx.send(Set.Welcome.SET)


commands = [
    "r", "ra", "sc",
    "set", "st", "en",
    "nn", "pc", "coc",
    "setcoc", "welcome",
    "ti", "li", "stats", "jrrp"
]

commands.sort(reverse=True)


@bot.command("help")
async def help(message: Message):
    ctx = bot.ctx(message)

    if not message.args[0]:
        await ctx.send(image=config.resource + "help/help.png")
        return

    cmd = message.args[0].lower()

    for command in commands:
        if cmd.startswith(command):
            await ctx.send(image=config.resource + "help/%s.png" % command)
            return
    else:
        await ctx.send(BotReply.HELP_NOT_FOUND, image=config.resource + "help/help.png")


@bot.default
async def default(message: Message):
    ctx = bot.ctx(message)
    await ctx.send(BotReply.DEFAULT, image=config.resource + "help/help.png")
