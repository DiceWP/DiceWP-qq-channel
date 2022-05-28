from typing import List

import qqbot


class Message(qqbot.Message):  # 添加了一些属性
    command: str
    text: str
    images: list
    args: List[str]
    direct: False


class Function:  # 功能类
    def __init__(self, func, command):
        self.run = func
        self.command = command
        # 统计用
        self.cmd = "cmd:" + command
