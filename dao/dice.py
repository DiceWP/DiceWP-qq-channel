from dao.db import DBConn


# setting operate

async def get_setting(uid, group, k):
    """
    获取配置
    :param uid: 用户id
    :param group: 频道id
    :param k: 键
    :return: 值
    """

    async with DBConn() as c:
        run_sql = 'SELECT v FROM user_setting WHERE uid=%s AND `group`=%s AND k=%s'
        run_params = (uid, group, k)
        res = await c.fetch_all(sql=run_sql, params=run_params)
        if res: return res[0]["v"]

        run_sql = 'SELECT v FROM user_setting WHERE uid=%s AND `group`="global" AND k=%s'
        run_params = (uid, k)
        res = await c.fetch_all(sql=run_sql, params=run_params)
        if res: return res[0]["v"]


async def set_setting(uid, group, k, v):
    """
    设置配置
    :param uid: 用户id
    :param group: 频道id
    :param k: 键
    :param v: 值
    :return: 更新前的值（如果有）
    """
    async with DBConn() as c:
        run_sql = 'SELECT v FROM user_setting WHERE uid=%s AND `group`=%s AND k=%s'
        run_params = (uid, group, k)
        res = await c.fetch_all(sql=run_sql, params=run_params)

        if res:
            run_sql = 'UPDATE user_setting SET v=%s WHERE uid=%s AND `group`=%s AND k=%s'
            run_params = (v, uid, group, k)
            await c.fetch_all(sql=run_sql, params=run_params)
            return res[0]["v"]

        else:
            run_sql = 'INSERT INTO user_setting (uid, `group`, k, v) VALUES (%s,%s,%s,%s)'
            run_params = (uid, group, k, v)
            await c.insert(sql=run_sql, params=run_params)


async def unset_setting(uid, group, k):
    """
    删除配置
    :param uid: 用户id
    :param group: 频道id
    :param k: 键
    """
    async with DBConn() as c:
        run_sql = 'DELETE FROM user_setting WHERE uid=%s AND `group`=%s AND k=%s'
        run_params = (uid, group, k)
        await c.fetch_all(sql=run_sql, params=run_params)


# group setting operate

async def get_group_setting(gid, k):
    """
    获取配置
    :param gid: 频道id
    :param k: 键
    :return: 值
    """

    async with DBConn() as c:
        run_sql = 'SELECT v FROM group_setting WHERE gid=%s AND k=%s'
        run_params = (gid, k)
        res = await c.fetch_all(sql=run_sql, params=run_params)
        if res: return res[0]["v"]


async def set_group_setting(gid, k, v):
    """
    设置配置
    :param gid: 频道id
    :param k: 键
    :param v: 值
    :return: 更新前的值（如果有）
    """
    async with DBConn() as c:
        run_sql = 'SELECT v FROM group_setting WHERE gid=%s AND k=%s'
        run_params = (gid, k)
        res = await c.fetch_all(sql=run_sql, params=run_params)

        if res:
            run_sql = 'UPDATE group_setting SET v=%s WHERE gid=%s AND k=%s'
            run_params = (v, gid, k)
            await c.fetch_all(sql=run_sql, params=run_params)
            return res[0]["v"]

        else:
            run_sql = 'INSERT INTO group_setting (gid, k, v) VALUES (%s,%s,%s)'
            run_params = (gid, k, v)
            await c.insert(sql=run_sql, params=run_params)


async def unset_group_setting(gid, k):
    """
    删除配置
    :param gid: 频道id
    :param k: 键
    """
    async with DBConn() as c:
        run_sql = 'DELETE FROM dice_wp.group_setting WHERE gid=%s AND k=%s'
        run_params = (gid, k)
        await c.fetch_all(sql=run_sql, params=run_params)


# pc operate

async def list_pc(uid):
    """获取用户全部调查员（已设置属性
    :param uid: 用户id
    :return: [pcname,]
    """
    async with DBConn() as c:
        run_sql = 'SELECT pc FROM talent WHERE uid=%s'
        run_params = uid
        res = await c.fetch_all(sql=run_sql, params=run_params)

    res = set(i["pc"] for i in res)
    return list(res)


async def rename_pc(uid, pc, new_pc):
    """
    重命名调查员
    :param uid: 用户id
    :param pc: 调查员
    :param new_pc: 重命名后的调查员
    """

    await copy_pc(uid, pc, new_pc)  # 复制属性
    await clr_talent(uid, pc)

    async with DBConn() as c:
        run_sql = 'UPDATE user_setting SET v=%s WHERE uid=%s AND k="pc" AND v=%s'  # 修改user_config绑定的pc
        run_params = (new_pc, uid, pc)
        await c.fetch_all(sql=run_sql, params=run_params)


async def copy_pc(uid, pc, new_pc):
    """
    复制调查员
    :param uid: 用户id
    :param pc: 调查员
    :param new_pc: 复制后的调查员
    :return: bool 是否有复制属性
    """

    talents = await get_all_talent(uid, pc)

    if talents:
        for talent in talents:
            await set_talent(uid, new_pc, talent["k"], talent["v"])
        return True
    else:
        return False


async def del_pc(uid, pc):
    """
    删除调查员的 属性/配置
    :param uid: 用户id
    :param pc: 调查员
    """

    async with DBConn() as c:
        run_sql = 'DELETE FROM talent WHERE uid=%s AND pc=%s'
        run_params = (uid, pc)
        await c.fetch_all(sql=run_sql, params=run_params)

        run_sql = 'DELETE FROM user_setting WHERE uid=%s AND k="pc" AND v=%s'
        run_params = (uid, pc)
        await c.fetch_all(sql=run_sql, params=run_params)


async def clr_pc(uid):
    """
    清空该用户所有调查员的属性/配置
    :param uid: 用户id
    """
    async with DBConn() as c:
        run_sql = 'DELETE FROM talent WHERE uid=%s'
        run_params = uid
        await c.fetch_all(sql=run_sql, params=run_params)

        run_sql = 'DELETE FROM user_setting WHERE uid=%s AND k="pc"'
        run_params = uid
        await c.fetch_all(sql=run_sql, params=run_params)


# talent operate

async def get_talent(uid, pc, k):
    """
    获取调查员的属性
    :param uid: 用户id
    :param pc: 调查员名称
    :param k: 键
    :return: 值
    """
    async with DBConn() as c:
        run_sql = 'SELECT v FROM talent WHERE uid=%s AND pc=%s AND k=%s'
        run_params = (uid, pc, k)
        res = await c.fetch_all(sql=run_sql, params=run_params)

    if res: return res[0]["v"]


async def get_all_talent(uid, pc):
    """
    获取调查员的全部属性
    :param uid: 用户id
    :param pc: 调查员名称
    :return: ({k:,v:},)
    """

    async with DBConn() as c:
        run_sql = 'SELECT k,v FROM talent WHERE uid=%s AND pc=%s'
        run_params = (uid, pc)
        res = await c.fetch_all(sql=run_sql, params=run_params)

    return res


async def set_talent(uid, pc, k, v):
    """
    设置属性
    :param uid: 用户id
    :param pc: 调查员
    :param k: 键
    :param v: 值
    :return: 更新前的值（如果有）
    """

    async with DBConn() as c:
        run_sql = 'SELECT v FROM talent WHERE uid=%s AND pc=%s AND k=%s'
        run_params = (uid, pc, k)
        res = await c.fetch_all(sql=run_sql, params=run_params)

        if res:
            run_sql = 'UPDATE talent SET v=%s WHERE uid=%s AND pc=%s AND k=%s'
            run_params = (v, uid, pc, k)
            await c.fetch_all(sql=run_sql, params=run_params)
            return res[0]["v"]
        else:
            run_sql = 'INSERT INTO talent (uid, pc, k, v) VALUES (%s, %s, %s, %s)'
            run_params = (uid, pc, k, v)
            await c.insert(sql=run_sql, params=run_params)


async def del_talent(uid, pc, k):
    """
    删除属性
    :param uid: 用户id
    :param pc: 调查员
    :param k: 键
    """
    async with DBConn() as c:
        run_sql = 'DELETE FROM talent WHERE uid=%s AND pc=%s AND k=%s'
        run_params = (uid, pc, k)
        await c.fetch_all(sql=run_sql, params=run_params)


async def clr_talent(uid, pc):
    """
    清除某调查员的全部属性
    :param uid: 用户id
    :param pc: 调查员
    """
    async with DBConn() as c:
        run_sql = 'DELETE FROM talent WHERE uid=%s AND pc=%s'
        run_params = (uid, pc)
        await c.fetch_all(sql=run_sql, params=run_params)


# jrrp operate

async def get_jrrp(uid):
    """
    获取jrrp
    :param uid: 用户id
    :return: date template v
    """
    async with DBConn() as c:
        run_sql = 'SELECT date, template,v FROM jrrp WHERE uid=%s'
        run_params = uid
        res = await c.fetch_all(sql=run_sql, params=run_params)

    if res: return res[0]


async def set_jrrp(uid, date, template, v):
    """
    设置jrrp
    :param uid: 用户id
    :param date: timestamp//86400
    :param template: 模板id
    :param v: 数值 1-100
    """

    async with DBConn() as c:
        run_sql = 'SELECT date, template,v FROM jrrp WHERE uid=%s'
        run_params = uid
        res = await c.fetch_all(sql=run_sql, params=run_params)

        if res:
            run_sql = 'UPDATE jrrp SET date=%s, template=%s, v=%s WHERE uid=%s'
            run_params = (date, template, v, uid)
            await c.fetch_all(sql=run_sql, params=run_params)

        else:
            run_sql = 'INSERT INTO jrrp (uid, date, template, v) VALUES (%s, %s, %s, %s)'
            run_params = (uid, date, template, v)
            await c.insert(sql=run_sql, params=run_params)
