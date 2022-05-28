#! /usr/bin/python
# -*- coding: UTF-8 -*-
# 异步版 https://github.com/tencent-connect/bot-onduty

from timeit import default_timer
import qqbot
import aiomysql

from constant import config


class DBConfig:
    def __init__(self, host, db, user, password, port=3306):
        """
        :param host:数据库ip地址
        :param port:数据库端口
        :param db:库名
        :param user:用户名
        :param password:密码
        :param charset:字符编码
        """
        self.host = host
        self.port = port
        self.db = db
        self.user = user
        self.password = password

        self.charset = "utf8"


class Mysql:
    def __init__(self, config: DBConfig):
        self.config = config

    async def get_conn(self) -> aiomysql.Connection:
        return await aiomysql.connect(
            charset=self.config.charset,
            host=self.config.host,
            port=self.config.port,
            db=self.config.db,
            user=self.config.user,
            password=self.config.password,
        )


# 初始化DB配置和链接池
db_config = DBConfig(
    config.database.host,
    config.database.db,
    config.database.user,
    config.database.password,
    config.database.port,
)

mysql = Mysql(db_config)


# ---- 使用 with 的方式来优化代码, 利用 __enter__ 和 __exit__ 控制with的进入和退出处理
class DBConn(object):
    def __init__(self, commit=True, log_time=True, log_label="总用时"):
        """
        :param commit: 是否在最后提交事务(设置为False的时候方便单元测试)
        :param log_time:  是否打印程序运行总时间
        :param log_label:  自定义log的文字
        """
        self._log_time = log_time
        self._commit = commit
        self._log_label = log_label

    async def __aenter__(self):

        # 如果需要记录时间
        if self._log_time is True:
            self._start = default_timer()

        # 从连接池获取数据库连接
        conn = await mysql.get_conn()
        await conn.ping(reconnect=True)
        cursor: aiomysql.Cursor = await conn.cursor(aiomysql.cursors.DictCursor)
        conn.autocommit = False

        self._conn = conn
        self._cursor = cursor
        return self

    async def __aexit__(self, *exc_info):
        # 提交事务
        if self._commit:
            await self._conn.commit()
        # 在退出的时候自动关闭连接和cursor
        await self._cursor.close()
        self._conn.close()

        if self._log_time is True:
            diff = default_timer() - self._start
            qqbot.logger.debug("-- %s: %.6f 秒" % (self._log_label, diff))

    # ========= 一系列封装的方法
    async def insert(self, sql, params=None):
        await self.cursor.execute(sql, params)
        return self.cursor.lastrowid

    # 返回 count
    async def get_count(self, sql, params=None, count_key="count(id)"):
        await self.cursor.execute(sql, params)
        data = await self.cursor.fetchone()
        if not data:
            return 0
        return data[count_key]

    async def fetch_one(self, sql, params=None):
        await self.cursor.execute(sql, params)
        return await self.cursor.fetchone()

    async def fetch_all(self, sql, params=None):
        await self.cursor.execute(sql, params)
        return await self.cursor.fetchall()

    async def fetch_by_pk(self, sql, pk):
        await self.cursor.execute(sql, (pk,))
        return await self.cursor.fetchall()

    async def update_by_pk(self, sql, params=None):
        await self.cursor.execute(sql, params)

    async def delete(self, sql, params=None):
        await self.cursor.execute(sql, params)

    @property
    def cursor(self):
        return self._cursor
