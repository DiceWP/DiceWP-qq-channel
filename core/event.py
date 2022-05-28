import qqbot
from qqbot.model.ws_context import WsContext
from qqbot.model.member import MemberWithGuildID
from core.bot import bot, logger
import core.dice


async def Group(data: MemberWithGuildID):
    _group = core.dice.Group()
    await _group.init(user_id=data.user.id,guild_id=data.guild_id)
    return _group


async def welcome(data: MemberWithGuildID):
    group = await Group(data)
    word: str = await group.get_setting("welcome_word", default=False)
    if not word:
        return

    channel = await group.get_setting("welcome_channel")

    word = word.replace("{nick}", data.user.username, 1)
    word = word.replace("{at}", "<@!%s>" % data.user.id, 1)

    await bot.send(text=word, channel_id=channel, msg_id="GUILD_MEMBER_ADD", guild_id=data.guild_id)


async def guild_member(context: WsContext, data: MemberWithGuildID):
    logger.info(f"{context.event_type} {data.guild_id} {data.user.username}({data.user.id})")
    if context.event_type == "GUILD_MEMBER_ADD":
        await welcome(data)


async def guild(context: WsContext, data: qqbot.Guild):
    if context.event_type in ["GUILD_CREATE", "GUILD_DELETE"]:
        logger.info(f"{context.event_type} {data.id}")


bot.handlers.extend([
    qqbot.Handler(qqbot.HandlerType.GUILD_MEMBER_EVENT_HANDLER, guild_member),
    qqbot.Handler(qqbot.HandlerType.GUILD_EVENT_HANDLER, guild)
])
