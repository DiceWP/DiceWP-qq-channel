from qqbot.model.api_permission import APIPermissionDemandIdentify, PermissionDemandToCreate

TEXT_REQ = "申请授权【%s】权限\n允许授权后才能正常使用机器人「%s」功能"

POST_MESSAGE = APIPermissionDemandIdentify("/channels/{channel_id}/messages", "POST")


def post_message(channel_id, desc):
    return PermissionDemandToCreate(channel_id=channel_id, api_identify=POST_MESSAGE, desc=desc)


GET_CHANNELS = APIPermissionDemandIdentify("/guilds/{guild_id}/channels", "GET")


def get_channels(channel_id, desc):
    return PermissionDemandToCreate(channel_id=channel_id, api_identify=GET_CHANNELS, desc=desc)


GET_GUILD_MEMBER = APIPermissionDemandIdentify("/guilds/{guild_id}/members/{user_id}", "GET")


def get_guild_member(channel_id, desc):
    return PermissionDemandToCreate(channel_id=channel_id, api_identify=GET_GUILD_MEMBER, desc=desc)


GET_GUILD = APIPermissionDemandIdentify("/guilds/{guild_id}", "GET")


def get_guild(channel_id, desc):
    return PermissionDemandToCreate(channel_id=channel_id, api_identify=GET_GUILD, desc=desc)
