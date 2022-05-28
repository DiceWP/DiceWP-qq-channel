from dao.db import DBConn


async def get_stats(id, scope, k):
    """
    获取统计结果
    :param id: id
    :param scope: 域 UESR/GUILD/GLOBAL
    :param k: 键
    :return: 值
    """
    async with DBConn() as c:
        run_sql = 'SELECT v FROM stats WHERE id=%s AND scope=%s AND k=%s'
        run_params = (id, scope, k)
        res = await c.fetch_all(sql=run_sql, params=run_params)
        return res[0]['v']


async def get_all_stats(id, scope):
    """
    获统全部统计结果
    :param id: id
    :param scope: 域 UESR/GUILD/GLOBAL
    :return: 值
    """
    async with DBConn() as c:
        run_sql = 'SELECT k,v FROM stats WHERE id=%s AND scope=%s'
        run_params = (id, scope)
        res = await c.fetch_all(sql=run_sql, params=run_params)
        return {i['k']: i['v'] for i in res}


async def update_stats(id, scope, k, increase: int = None, v: int = None):
    """
    更新统计
    :param id: id
    :param scope: 域
    :param k: 键
    :param increase: 增量
    :param v: 指定值 优先
    """
    async with DBConn() as c:
        run_sql = 'SELECT v FROM stats WHERE id=%s AND scope=%s AND k=%s'
        run_params = (id, scope, k)
        res = await c.fetch_all(sql=run_sql, params=run_params)

        if res:
            v = v or res[0]['v'] + increase
            run_sql = 'UPDATE stats SET v=%s WHERE id=%s AND scope=%s AND k=%s'
            run_params = (v, id, scope, k)
            await c.fetch_all(sql=run_sql, params=run_params)

        else:
            v = v or increase
            run_sql = 'INSERT INTO stats (id, scope, k, v) VALUES (%s, %s, %s, %s)'
            run_params = (id, scope, k, v)
            await c.insert(sql=run_sql, params=run_params)


async def clr_stats(id, scope):
    """
    清除统计
    :param id: id
    :param scope: 域
    :return:
    """
    async with DBConn() as c:
        run_sql = 'DELETE FROM stats WHERE id=%s AND scope=%s'
        run_params = (id, scope)
        await c.execute(sql=run_sql, params=run_params)
