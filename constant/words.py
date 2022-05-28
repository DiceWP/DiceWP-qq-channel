class BotReply:
    PERMISSION_REJECT = "该指令需要管理员权限才能使用哦"
    DIRECT_REJECT = "该指令需要在频道中使用哦"
    OVER_LENGTH = "消息过长，发送失败"
    SEC_CHECK = "文本含有违规内容，请重新提交"
    URL_NOT_ALLOWED = "好像有链接呢，吃掉！"
    TOO_FAST = "讲话太快啦，慢一点吧"
    HELP_NOT_FOUND = "未找到该指令"
    DEFAULT = "想要我做什么呢~"


class Noun:
    DICE = "骰子"
    DICE_SIDE = "骰子面数"
    DEFAULT_DICE_SIDE = "默认骰"
    NICKNAME = "昵称"
    PC = "调查员"
    KP = "守密人"
    TALENT = "属性"
    VALUE = "数值"
    SAN = "理智"
    WELCOME = "欢迎词"
    TIMES = "次数"


class Common:
    CONFIRM = "此操作将%s，请在%s秒内回复“确认”以执行"
    EG = "\n示例: "

    class Limit:
        TOO_MANY = "%s太多啦，少一点吧 (>%s)"
        TOO_FEW = "%s太少啦，多一点吧(<%s)"
        TOO_LONG = "%s太长啦，短一点吧 (>%s)"
        TOO_SHORT = "%s太短啦，长一点吧(<%s)"
        TOO_BIG = "%s太大啦，小一点吧(>%s)"
        TOO_SMALL = "%s太小啦，大一点吧(<%s)"

    class Fix:
        TOO_MANY = "(过多修正->%s): "
        TOO_FEW = "(过少修正->%s): "

    class Require:
        INT = "%s需要为整数"
        EXP = "%s需要为投掷表达式"
        PARAM = "不告我%s，可怎么操作呀"
        TWO_PARAM = "缺少%s和%s，我可不知道你想做什么哦"

    class Show:
        ONE_EQ = "=%s"
        TWO_EQ = "%s=%s"
        TWO_COLON = "%s: %s"
        THREE_EQ = "%s=%s=%s"
        THREE_DES = "%s的%s为%s"

        STATS = """%s的统计数据
总投掷: %s　总点数: %s
大成功: %s　大失败: %s"""


class Roll:
    DICE = "%s投掷: "
    WITH_REASON = "由于%s，"
    DICE_WITH_TIME = "%(name)s投掷%(time)d次: "

    class Check:
        SHOW = "%s/%s %s"
        EG = Common.EG + f"ra 力量 80 (如已设置{Noun.TALENT}可以省去{Noun.VALUE})"
        COMMON = "%s进行%s检定"
        TALENT_NOT_EXISTS = f"{Noun.PC}%s没有{Noun.TALENT}%s，可使用\"st {Noun.TALENT} {Noun.VALUE}\"设置"


class Expression:
    class Error:
        UNRESOLVED_TEXT = "投掷表达式错误: 未解析的字符: %s"
        K_MORE_THAN_N = "最大点数骰数超过骰子总数"
        CALC = "投掷表达式错误: 计算式错误"
        BRACKET = "投掷表达式错误: 括号无法成对"


class Set:
    class Setting:
        class Common:
            SET = "已在%s设置%s为%s"
            RESET = "已在%s重置%s为%s"

        class EG:
            DEFAULT_SIDE = Common.EG + "set 20"

    class Talent:
        class Show:
            SINGLE = f"{Noun.PC}%s的%s{Noun.TALENT}为%s"
            MULTIPLE = f"{Noun.PC}%s的{Noun.TALENT}列表为: \n"
            TALENT_NOT_EXISTS = f"唔，该{Noun.PC}没有{Noun.TALENT}%s"
            NO_TALENT_TO_SHOW = f"唔，该{Noun.PC}还未设置任何{Noun.TALENT}"

        class Confirm:
            CLR = f"清空{Noun.PC}%s的全部{Noun.TALENT}"

        class Common:
            SET = f"已设置{Noun.PC}%s的{Noun.TALENT}%s为%s"
            HALF = f"{Noun.PC}%s的{Noun.TALENT}"
            HEAD = f"正在设置{Noun.PC}%s的属性\n"
            DELETE = f"已删除{Noun.PC}%s的{Noun.TALENT}%s"
            CLR = f"已清空{Noun.PC}%s的全部{Noun.TALENT}"

        class EG:
            DELETE = Common.EG + "st del 力量"
            SET = Common.EG + "st 力量 80"
            SET_PS = Common.EG + "st 力量 +80"

        class Limit:
            TOO_MANY_ST = f"设置的{Noun.TALENT}太多啦，少一点吧(>%s)"

        class Error:
            TALENT_NOT_EXIST = f"操作失败，{Noun.PC}%s不存在%s{Noun.TALENT}"
            NOT_PAIR = f"多重导入失败，属性数值无法成对\n示例: st 力量 80 敏捷 +10"
            REPEAT = "设置失败，重复的属性: %s"

    class PC:
        class EG:
            RENAME = Common.EG + "pc nn 新名字"
            COPY = Common.EG + "pc copy 新调查员"

        class Confirm:
            PC_EXISTS_COPY = f"清空{Noun.PC}%s的全部{Noun.TALENT}"
            DEL = f"清空{Noun.PC}%s的全部{Noun.TALENT}并删除配置，如仅需清空{Noun.TALENT}请使用\"st clr\"指令"
            CLR = f"清除所有{Noun.PC}的属性、配置，且操作不可逆"

        class Common:
            RENAME = f"已将{Noun.PC}%s重命名为%s"
            LIST = f"%s的{Noun.PC}列表：%s"
            NO_PC_TO_SHOW = f"你还没有{Noun.PC}可以展示(需要先使用st指令添加属性)"
            COPY = f"已将{Noun.PC}%s的属性复制%s"
            DEL = f"已清空{Noun.PC}%s的全部{Noun.TALENT}并删除配置，{Noun.PC}自动切换至%s"
            CLR = f"已清除所有{Noun.PC}的属性、配置"
            DEFAULT = f"当前使用的{Noun.PC}: %s\n如需查看更多指令请发送\"help pc\""

    class Coc:
        RULES = [
            "出1大成功\n成功率不满50出96-100大失败，满50出100大失败",
            "成功率不满50出1大成功，满50出1-5大成功\n不满50出96-100大失败，满50出100大失败",
            "出1-5且<=成功率大成功\n出100-99且>成功率大失败"
            "出1-5大成功\n出96-100大失败",
            "出1-5且<=成功率/10大成功\n不满50且出>=96+成功率/10大失败，满50出100大失败",
            "出1-2且<成功率/5大成功\n不满50出96-100大失败，满50出99-100大失败"
        ]
        SHOW = "当前coc规则: %s\n%s\n可发送指令\"help setcoc\"查看所有可用规则"
        RULE_NOT_EXISTS = "该规则不存在，规则一览可以发送指令\"help setcoc\"查看"
        COMMON = "已设置coc规则: %s\n%s"
        RESET = "已将coc规则重置为: %s\n%s"

    class Welcome:
        RESET = f"已清除{Noun.WELCOME}"
        SET = f"已在当前子频道设置{Noun.WELCOME}"

    class Stats:
        CONFIRM = "清除%s的所有统计数据"
        CLR = "已清除%s的所有统计数据"


class En:
    EG = Common.EG + "en 力量"
    COMMON = "%s的%s成长鉴定:\n%s/%s %s"


class SanCheck:
    FORMAT_ERROR = "理智表达式格式错误，正确的格式为 sc [成功损失]/[失败损失] (当前理智)"
    EG = Common.EG + "sc 0/1d6 60 (如已设置理智属性可省略60)"
    COMMON = "%s进行理智检定\n"
    LOSE = f"\n%s的{Noun.SAN}减少%s点，当前剩余%s点"
    NEED_SAN = Set.Talent.Show.TALENT_NOT_EXISTS % Noun.SAN + f"，我无法自动读取，可以的话请指定{Noun.SAN}或使用st指令设置"
    MAD = ""


class Mad:
    TI = "%s的疯狂发作-临时症状\n%s"
    LI = "%s的疯狂发作-症状总结\n%s"


class Coc:
    # normal talent 8 luck 1 sum 2 total 11
    SHOW = "%s的coc7随机人物卡如下:\n\n"
    CARD = "力量: %s 体质: %s 体型: %s 敏捷: %s 外貌: %s\n智力: %s 意志: %s 教育: %s 幸运: %s 共计: %s/%s"
    DETAIL = "\n\n思想/信念: %s\n重要之人: %s\n意义非凡之地: %s\n宝贵之物: %s\n特点: %s"
    QUICK_ST = "\n\nst 力量:%s 体质:%s 体型:%s 敏捷:%s 外貌:%s 智力:%s 意志:%s 教育:%s 幸运:%s"


class Help:
    MENU = """发送 "help [功能]" 查看详细介绍
r    |  nn  |  pc
ra  |  st   |  en
ti   |  li    |  set
setcoc    |  stats
welcome"""

    R = """r (表达式) (投掷原因) // 最基础的投掷功能
支持的骰子类型：
多面(d12) 多骰(3d) 最大骰(4dk2) 奖惩(b5)
支持逻辑运算(+-*/)和括号
支持在r后添加s表示缩减表达结果
支持在r后添加 (表达式)# 表示多轮投掷(最大支持十轮)"""

    NN = """nn (昵称) // 设置群内昵称，私信则设置全局昵称
省略昵称视为重置昵称"""

    PC = f"""pc // 查看当前使用的{Noun.PC}
    
pc tag ({Noun.PC}) // 在当前频道绑定{Noun.PC}，私信则设置全局{Noun.PC}
省略{Noun.PC}视为重置{Noun.PC}绑定

pc show ({Noun.PC}) // 查看当前/指定{Noun.PC}的属性

pc nn [新名字] // 重命名当前{Noun.PC}

pc list // 展示所有已设置属性的{Noun.PC}

pc cpy [{Noun.PC}1] [{Noun.PC}2] // 将1的属性复制给2，不存在则新建

pc del ({Noun.PC}) // 删除当前/指定{Noun.PC}的属性/配置/统计

pc clr // 清空所有{Noun.PC}的属性/配置/统计"""

    RA = f"""ra (表达式) ({Noun.TALENT}) (成功率) // 鉴定指令，当{Noun.PC}设置了{Noun.TALENT}时，可省略成功率
可在ra后添加s表示缩减表达结果
可在ra后添加 (表达式)# 表示多轮投掷(最大支持十轮)"""


class Joke:
    REALLY = "真的吗...好吧，你开心就好，"
    ZERO_DICE = "零个骰子？这可不好"
    ZERO_SIDE = "零面骰？这可不行"
    ZERO_DIVIDE = "请不要用0除任何数字"
    ZERO_SAN = "\n哦，看来又有一位调查员理智清零了"
    NO_PERMISSION = "正在读取权限...权限不足"
