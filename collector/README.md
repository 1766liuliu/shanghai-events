# 采集层（本机 Python）

抓取上海各活动源 → 清洗去重 → 亲子/适龄/价格打标 → 写本地 JSON 或微信云数据库。

## 跑起来

```bash
pip3 install -r requirements.txt
python3 main.py          # 写 ../data/events.json
python3 main.py --cloud  # 同时写云数据库(需 config.py)
```

## 结构

```
collector/
├── main.py            调度入口(在此启用/新增源)
├── models.py          Event 数据模型
├── config.example.py  配置模板(复制为 config.py)
├── sources/           数据源(一源一文件,继承 BaseSource)
│   ├── base.py
│   ├── bendibao.py    ✅ 参考实现,可跑通
│   └── wenhuayun.py   ⏳ 待抓包对接(亲子,优先)
├── pipeline/          clean(去重) / tagging(亲子打标)
└── store/             local_json(调试) / cloudbase(云库)
```

## 新增一个数据源

1. 复制 `sources/bendibao.py` 为 `sources/你的源.py`，实现 `fetch()` 返回 `List[Event]`；
2. 在 `main.py` 的 `ENABLED_SOURCES` 里加上它。

> 仅自用、不二次分发、不商用。`config.py` 含密钥，不要外传。
