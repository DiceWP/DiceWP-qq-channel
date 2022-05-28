import time
import hashlib
import json

import aiohttp
from qqbot.core.util.logging import getLogger

from constant import config
from constant.error import QQAPIError
from util.string import fuck_nl

logger = getLogger("security")


class QQAPI:
    def __init__(self, appid, secret, server_url, server_token):
        """
        :param appid: 机器人id
        :param secret: 机器人密钥
        :param server_url: 中控服务器url
        :param server_token: 中控服务器token
        """
        self.appid = appid
        self.secret = secret
        self.server_url = server_url
        self.server_token = server_token
        self.client = aiohttp.ClientSession()
        self._token = None
        self.expires = 0

    async def _get_token(self):
        """
        从中控服务器获取access_token
        使用
        """
        timestamp = str(int(time.time()))
        signature = hashlib.sha256(
            f"{timestamp}{self.appid}{self.secret}{self.server_token}".encode("utf-8")).hexdigest()
        async with self.client.post(self.server_url,
                                    headers={"signature": signature, "timestamp": timestamp},
                                    data={"app_id": self.appid}) as r:

            if r.ok:
                res = json.loads(await r.text())
                self._token = res["access_token"]
                self.expires = res["expires"]
                return True
            else:
                if r.status == 500:
                    logger.error(f"token get failed {r.text}")
                    raise QQAPIError(f"token get failed {await r.text()}")
                else:
                    logger.error(f"token get failed {r.status}")
                    raise QQAPIError(f"token get failed {r.status}")

    async def get_token(self):
        if time.time() > self.expires:
            if not await self._get_token():
                return False
        return self._token

    @property
    def token(self):
        return self.get_token()

    async def msg_sec_check(self, content: str) -> bool:
        """
        文本检查
        :param content: 要检查的文本
        :return: 是否违规
        """
        async with self.client.post("https://api.q.qq.com/api/json/security/MsgSecCheck",
                                    params={"access_token": await self.token},
                                    json={"appid": self.appid, "content": content}) as r:
            res = await r.json()

        if "code" in res:
            logger.error(f"msg_src_check failed {res}")
            return False
        if res["errCode"]:
            if res["errCode"] == 87014:
                logger.info("bad msg " + fuck_nl(content))
                return True
            else:
                logger.error(f"msg_sec_check failed {res}")
                raise QQAPIError(f"msg_sec_check failed {res}")
        else:
            return False

    async def img_sec_check(self, media: bytes, show_msg=None) -> bool:
        """
        图片检查
        :param media: 图片二进制
        :param show_msg: 用于显示在日志里的文本
        :return: 是否违规
        """
        async with self.client.post("https://api.q.qq.com/api/json/security/ImgSecCheck",
                                    params={"access_token": await self.token},
                                    data={"appid": self.appid, "media": media}) as r:
            res = await r.json()
        if "code" in res:
            logger.error(f"img_src_check failed {res}")
            return False
        if res["errCode"]:
            if res["errCode"] == 87014:
                logger.info("bad img " + (show_msg or ""))
                return True
            else:
                logger.error(f"img_sec_check failed {res}")
                if res["errCode"] != -13010:
                    raise QQAPIError(f"img_sec_check failed {res}")
        else:
            return False

    async def close(self):
        await self.client.close()


qq_api = QQAPI(config.bot.appid, config.bot.secret, config.token_server.url, config.token_server.token)
