class Dict(dict):
    __setattr__ = dict.__setitem__
    __getattr__ = dict.__getitem__


def dict2obj(dic):
    """
    将字典转为类
    :param dic: 字典
    :return: 类
    """
    if not isinstance(dic, dict):
        return dic
    d = Dict()
    for k, v in dic.items():
        d[k] = dict2obj(v)
    return d
