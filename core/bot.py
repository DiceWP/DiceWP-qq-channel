import time
import traceback
import asyncio
import re
from typing import Union, List

import qqbot
from qqbot.model.api_permission import PermissionDemandToCreate
from qqbot.core.exception.error import AuthenticationFailedError, ServerError

from constant import config
from constant.words import BotReply, Common
from constant.error import Interrupt, ErrorWithMsg
from constant import api_permission
from util.string import fuck_nl, harmless_message
from util.sec_check import black_words, text_check
from util.cd import check
from core.dice import Stats
from core.model import Message, Function

from util.tool import TimeRecorder

logger = qqbot.logging.getLogger("bot")


async def blank(*args, **kwargs):  # 空函数
    pass


ROLE_MANAGER = "2"
ROLE_CREATOR = "4"


class WaitBucket:
    def __init__(self):
        self.bucket = []

    def register(self, *args, **kwargs):  # 注册
        event = WaitEvent(*args, **kwargs, bucket=self)
        self.unregister(event.id)
        self.bucket.append(event)
        return event

    def unregister(self, id):  # 取消注册
        for event in self.bucket:
            if event.id == id:
                event.maxtime = -1

    def check(self, message: Message):  # 检查，如有匹配则传参
        for event in self.bucket:
            if message.author.id == event.id:
                event.result = message
                self.bucket.remove(event)
                return True

        return False

    def reject(self, message: Message):  # 检查，如有匹配则注销匹配事件
        for event in self.bucket:
            if message.author.id == event.id:
                self.unregister(event.id)

    def remove(self, event):  # 根据内存地址注销事件
        self.bucket.remove(event)


class WaitEvent:  # 等待事件
    def __init__(self, message: qqbot.Message, bucket: WaitBucket, timeout=30, maxtime=None):
        self.id = message.author.id
        self.bucket = bucket
        if maxtime:
            self.maxtime = maxtime
        else:
            self.maxtime = timeout + time.time()
        self.result = None

    async def wait_until_complete(self) -> Union[bool, None, Message]:
        while time.time() < self.maxtime:
            await asyncio.sleep(0.5)
            if self.result:  # 有结果，返回Message
                return self.result
        else:
            self.bucket.remove(self)
            if self.maxtime == -1:  # 被注销，返回False
                return False
            else:
                return None  # 超时，返回None


class BotFactory:
    def __init__(self, app_id, token, sandbox):
        self.token = qqbot.Token(app_id, token)
        self.sandbox = sandbox
        self.id = qqbot.UserAPI(self.token, self.sandbox).me().id
        self.get_text = re.compile("(?:<@[!&]?%s> ?/?|^/)[.。!！]?|^[.。!！]" % self.id).sub  # 清洗字符串
        self.wait_bucket = WaitBucket()

        self.functions: List[Function] = []
        self._default = blank  # 无匹配默认路由函数
        self.handlers = [qqbot.Handler(qqbot.HandlerType.AT_MESSAGE_EVENT_HANDLER, self.router),
                         qqbot.Handler(qqbot.HandlerType.DIRECT_MESSAGE_EVENT_HANDLER, self.router)]

        self.msg_api = qqbot.AsyncMessageAPI(self.token, self.sandbox, timeout=10)
        self.dms_api = qqbot.AsyncDmsAPI(self.token, self.sandbox)
        self.guild_api = qqbot.AsyncGuildAPI(self.token, self.sandbox)
        self.guild_member_api = qqbot.AsyncGuildMemberAPI(self.token, self.sandbox)
        self.channel_api = qqbot.AsyncChannelAPI(self.token, self.sandbox)
        self.api_permission_api = qqbot.AsyncAPIPermissionAPI(self.token, self.sandbox)

    async def router(self, event, message: qqbot.Message):  # 路由函数
        tr = TimeRecorder()

        if message.guild_id == config.bot.sandbox_guild and not config.bot.sandbox:
            logger.info("sandbox reject")
            return

        if not hasattr(message, "content"):
            message.content = ""

        message.images = ["https://" + i.url for i in
                          message.attachments] if hasattr(message, "attachments") else []  # 解析图片

        if hasattr(message, "src_guild_id"):
            logger.info(
                f"{message.src_guild_id}(Direct) {message.author.username}({message.author.id}) -> %s {message.images or ''}" % fuck_nl(
                    message.content))
            message.direct = True
            stats = Stats(uid=message.author.id)  # 实例化统计句柄
        else:
            logger.info(
                f"{message.guild_id}({message.channel_id}) {message.author.username}({message.author.id}) -> %s {message.images or ''}" % fuck_nl(
                    message.content))
            message.direct = False
            stats = Stats(uid=message.author.id, gid=message.guild_id)  # 实例化统计句柄

        await stats.count("recv")

        message.text = self.get_text("", message.content)  # 提取字符串

        try:
            check(message.author.id)  # cd检测

            for func in self.functions:
                if message.text.startswith(func.command):
                    black_words(message.content)  # 基础安全检测
                    await text_check(message.content)  # 文本安全api，增加0.1s~0.4s延迟
                    harmless_message(message)

                    # 统计信息
                    await stats.count("spark")
                    await stats.count(func.cmd)

                    message.command = func.command
                    message.text = re.sub(f"{func.command} ?", "", message.text, 1)  # 清除指令
                    message.args = re.split(" +", message.text)  # 解析参数
                    await func.run(message)
                    # self.wait_bucket.reject(message)
                    tr.rec()
                    return
            else:
                if self.wait_bucket.check(message):  # 等待桶检测
                    return
                await self._default(message)
        except Interrupt:
            pass
        except ErrorWithMsg as e:
            await self.ctx(message).send(e.msg)
        except Exception:
            logger.error("Error ->\n" + traceback.format_exc())

    def command(self, cmd):
        # 指令注册装饰器

        def _warp(func):
            if isinstance(func, Function):
                function = Function(func.run, cmd)
            else:
                function = Function(func, cmd)

            self.functions.append(function)
            return function

        return _warp

    def role_check(self, func: Union[Function, callable]):
        # 权限检查装饰器

        if isinstance(func, Function):
            run = func.run

            async def check(message: Message):
                if message.direct:
                    raise ErrorWithMsg(BotReply.DIRECT_REJECT)

                member = await self.get_guild_member(message.guild_id, message.author.id, channel_id=message.channel_id,
                                                     desc="管理员权限识别")
                if ROLE_MANAGER in member.roles or ROLE_CREATOR in member.roles:
                    return await run(message)
                else:
                    raise ErrorWithMsg(BotReply.PERMISSION_REJECT)

            func.run = check

            return func
        else:
            async def check(message: Message):
                if message.direct:
                    raise ErrorWithMsg(BotReply.DIRECT_REJECT)

                member = await self.get_guild_member(message.guild_id, message.author.id, channel_id=message.channel_id,
                                                     desc="管理员权限识别")
                if ROLE_MANAGER in member.roles or ROLE_CREATOR in member.roles:
                    return await func(message)
                else:
                    raise ErrorWithMsg(BotReply.PERMISSION_REJECT)

            return check

    async def check_permission(self, message: Message):
        member = await self.get_guild_member(message.guild_id, message.author.id,
                                             channel_id=message.channel_id,
                                             desc="管理员权限识别")
        if ROLE_MANAGER in member.roles or ROLE_CREATOR in member.roles:
            return True
        else:
            raise ErrorWithMsg(BotReply.PERMISSION_REJECT)

    @staticmethod
    async def check_direct(message: Message):
        if message.direct:
            raise ErrorWithMsg(BotReply.DIRECT_REJECT)

    def default(self, func):
        # 设置默认路由函数
        self._default = func
        return func

    async def send(self, text="", image="", channel_id=None, msg_id=None, guild_id="", check_auth=True):
        """
        发送频道消息
        :param text: 文本
        :param image: 图片
        :param channel_id: 子频道
        :param msg_id: 消息id
        :param guild_id: 频道id（日志用）
        :return:
        """

        logger.info(f"Guild {guild_id}({channel_id}) <- " + text.replace("\n", r"\n") + f" {image}")

        req = qqbot.MessageSendRequest(content=text, image=image, msg_id=msg_id)

        try:
            return await self.msg_api.post_message(channel_id=channel_id, message_send=req)
        except AuthenticationFailedError:
            if not check_auth:
                return
            await self.api_permission_api.post_permission_demand(
                guild_id=guild_id,
                request=api_permission.post_message(channel_id=channel_id, desc="发送消息")
            )
            raise Interrupt

    async def direct_send(self, text="", image="", guild_id="", msg_id=None, src_guild_id=None, user_id=None):
        """
        发送私信消息
        :param text: 文本
        :param image: 图片
        :param guild_id: 私信频道
        :param msg_id: 消息id
        :param src_guild_id: 源频道（日志用）
        :param user_id: 用户id（日志用）
        :return:
        """

        logger.info(f"Direct {src_guild_id or guild_id}({user_id}) <- %s {image}" % text.replace("\n", r"\n"))

        req = qqbot.MessageSendRequest(content=text, image=image, msg_id=msg_id)
        return await self.dms_api.post_direct_message(guild_id=guild_id, message_send=req)

    """
    api warp
    """

    # nmd，wsm
    async def post_permission_demand(self, guild_id: str, request: PermissionDemandToCreate, name=""):
        """
        发送权限申请
        :param guild_id: 频道id
        :param request: ？
        :param name: 申请权限的名称
        :return: raise Interrupt :-D
        """
        try:
            await self.api_permission_api.post_permission_demand(
                guild_id=guild_id,
                request=request
            )
            raise Interrupt  # 防止代码继续运行对逻辑造成更大影响
        except ServerError as e:
            # TODO 0:00~6:00 / 超过主动消息 如何解决？
            if e.msgs == "hit rate limit" and request.api_identify.path != api_permission.POST_MESSAGE:
                await self.send(
                    text=api_permission.TEXT_REQ % (name, request.desc),
                    channel_id=request.channel_id,
                    check_auth=False  # 不会吧不会吧，不会有人超过三次还没给发消息权限吧
                )
                raise Interrupt
            else:
                raise e

    async def get_channels(self, guild_id, channel_id=None, desc="获取子频道列表"):
        """
        获取子频道列表
        :param guild_id: 频道id
        :param channel_id: 子频道id
        :param desc: 申请权限时的理由
        :return:
        """
        try:
            return await self.channel_api.get_channels(guild_id)
        except AuthenticationFailedError:
            await self.post_permission_demand(
                guild_id=guild_id,
                request=api_permission.get_channels(channel_id, desc),
                name="获取频道内子频道列表"
            )

    async def get_guild_member(self, guild_id, user_id, channel_id=None, desc="获取频道成员信息"):
        """
        获取频道成员信息
        :param guild_id: 频道id
        :param user_id: 用户id
        :param channel_id: 子频道id
        :param desc: 申请权限时的理由
        :return:
        """
        try:
            return await self.guild_member_api.get_guild_member(guild_id=guild_id, user_id=user_id)
        except AuthenticationFailedError:
            await self.post_permission_demand(
                guild_id=guild_id,
                request=api_permission.get_guild_member(channel_id, desc),
                name="获取当前频道成员信息"
            )

    async def get_guild(self, guild_id, channel_id=None, desc="获取频道详情"):
        """
        获取频道信息
        :param guild_id: 频道id
        :param channel_id: 子频道id
        :param desc: 申请权限时的理由
        :return:
        """
        try:
            return await self.guild_api.get_guild(guild_id=guild_id)
        except AuthenticationFailedError:
            await self.post_permission_demand(
                guild_id=guild_id,
                request=api_permission.get_guild(channel_id, desc),
                name="获取频道"
            )

    """
    end
    """

    def ctx(self, message: Message):  # 实例化句柄
        return CTX(bot=self, message=message)

    def run(self, ret_coro=False):
        self.functions.sort(key=lambda x: x.command, reverse=True)  # 指令以长度倒序

        try:
            return qqbot.async_listen_events(self.token, self.sandbox, *self.handlers, ret_coro=ret_coro)
        except Exception as e:
            logger.error("Fatal Error ->\n" + traceback.format_exc())


class CTX:  # 操作句柄
    def __init__(self, bot: BotFactory, message: Message):
        self.bot = bot
        self.message = message

        self._cache = {}

    async def send(self, text="", image="", target=None):
        """
        :param text: 文本
        :param image: 图片
        :param target: channel_id(频道)/guild_id(私信)
        """
        if len(text) > 10000:  # 防止发送失败
            text = BotReply.OVER_LENGTH
            image = None

        if self.message.direct:
            await Stats(uid=self.message.author.id).count("send")
            return await self.bot.direct_send(text=text, image=image, guild_id=target or self.message.guild_id,
                                              msg_id=self.message.id, src_guild_id=self.message.src_guild_id,
                                              user_id=self.message.author.id)
        else:
            await Stats(uid=self.message.author.id, gid=self.message.guild_id).count("send")
            return await self.bot.send(text=text, image=image, channel_id=target or self.message.channel_id,
                                       guild_id=self.message.guild_id, msg_id=self.message.id)

    async def wait(self, timeout=60, maxtime=None) -> Union[Message, bool, None]:
        """
        等待函数
        :param timeout: 超时的时间
        :param maxtime: 超时时间戳，当timeout和maxtime同时传入以maxtime为准
        :return:
        """
        return await self.bot.wait_bucket.register(message=self.message, timeout=timeout,
                                                   maxtime=maxtime).wait_until_complete()

    async def confirm(self, text=None, full_text=None, confirm="确认", timeout=60, maxtime=None) -> bool:
        """
        :param text: 自动填入模板的消息
        :param full_text: 完整的消息，取代模板消息
        :param confirm: 匹配的字符串
        :param timeout: 超时的时间
        :param maxtime: 超时时间戳，当timeout和maxtime同时传入以maxtime为准
        :return: true->成功确认 false-> 没有false，超时/非确认词直接raise -> line: 129
        """

        if text:
            await self.send(text=full_text or Common.CONFIRM % (text, timeout or int(maxtime - time.time())))

        message = await self.wait(timeout=timeout, maxtime=maxtime)

        if not message:
            raise Interrupt

        if message.text != confirm:
            raise Interrupt

        return True

    async def get_channel_by_name(self, name, guild_id=None, channel_id=None, use_cache=True) -> qqbot.Channel:
        if "channels" in self._cache and use_cache:
            channels = self._cache["channels"]
        else:
            channels = await self.bot.get_channels(
                guild_id or self.message.guild_id,
                channel_id=channel_id or self.message.channel_id,
                desc="识别子频道转跳"
            )

        for channel in channels:
            if channel.name == name:
                return channel


bot = BotFactory(config.bot.appid, config.bot.token, config.bot.sandbox)
