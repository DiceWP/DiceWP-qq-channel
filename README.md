# 骰娘白鸮
TRPG跑团骰娘  
  
*欢迎批评和建议*

## 支持的功能

 - r
 - ra
 - sc
 - set
 - st
 - en
 - nn
 - pc
 - coc
 - setcoc
 - welcome
 - ti/tl
 - jrrp
 - stats

## TODO

- [ ] 优化数据库
- [ ] deck/draw 牌堆
- [ ] ri 先攻

## 鸣谢

- [tencent-connect/bot-onduty](https://github.com/tencent-connect/bot-onduty) 提供了dao/db.py 的同步版本，以及代码结构的参考

## 官网

- [https://dicewp.rhodescafe.net/](https://dicewp.rhodescafe.net/docs/)

## 代码说明
```
.
├── LICENSE
├── README.md
├── config.example.yaml # 配置文件模版
├── config.yaml         # 实际的读取配置文件（需要自己从example复制一份修改参数）
├── start.py            # 程序运行入口
├── constant            # 代码常量，包含一些模板和数据
│ ├── api_permission.py     # api权限申请
│ ├── b_words.json          # 违禁词
│ ├── coc.py                # coc随机调查员
│ ├── config.py             # 读取配置文件的
│ ├── domains.json          # 顶级域名一拉
│ ├── error.py              # 自定异常
│ ├── jrrp.py               # 今日人品模板
│ ├── mad.py                # ti/li 模板
│ └── words.py              # 回复模板
├── core                # 核心逻辑处理
│ ├── bot.py                # 功能注册，api封装 
│ ├── dice.py               # 骰娘相关操作
│ ├── event.py              # 事件处理
│ ├── function.py           # 功能函数及逻辑
│ └── model.py              # 一些模板
├── dao                 # 数据库操作层，处理数据库连接以及业务逻辑的sql
│ ├── db.py                 # 数据库工具
│ ├── dice.py               # 骰娘相关操作
│ └── stats.py              # 统计操作
└── util                # 工具包
    ├── alive_report        # 存活上报
    ├── cd.py               # 冷却
    ├── dice.py             # 骰娘输出格式化
    ├── format.py           # 格式化，主要为dict2obj 这字典咱是一秒也看不下去了(笑)
    ├── qq_api.py           # 小程序api
    ├── sec_check.py        # 参数合规性检查
    ├── tool.py             # 一些小工具
    └── translate.py        # 为st提供同义词翻译
```
