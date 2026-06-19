"""清洗与去重 —— 来源/日期无关的"归一化去重",彻底解决同一展会多条目。

为什么旧版去不掉重复:旧 key = 来源|标题|开始日期。于是
  · 不同来源的同一展会、② 本地宝同展会的多篇 SEO 文章(时间/门票/报名…)、
  · 同名不同场次 —— 标题或来源一不同,就被当成新条目。
新版:把标题"归一化"(去年份/届次 + 砍掉 SEO 尾巴 + 去标点)当 key,跨来源、跨日期合并;
  组内挑最佳代表(策展/有日期/真实链接优先)并补全空字段;
  再做"策展优先":爬虫里与策展同名的大会冗余条目直接去掉。
"""
from __future__ import annotations

import re
from typing import Dict, List

from models import Event

# SEO / 文章尾巴关键词:标题里一旦出现,后面的都不算展会名
_SEO = (
    r"时间|门票|地址|地点|官网|购票|价格|入口|举办|一览|攻略|流程|预约|领票|"
    r"报名|截止|名单|须知|交通|停车|开幕|开票|参观|怎么|最新"
)
_PUNCT = re.compile(r"""[\s\-—_、,，。.·()（）《》【】"'+/|!！?？:：]""")

# 这些大会由 curated 权威收录;爬虫里同名的冗余条目让位(避免重复)
COVERED = [
    "进博会", "工博会", "世界人工智能", "WAIC", "劳力士大师赛", "上海马拉松",
    "上海国际电影节", "MWC上海", "ChinaJoy", "华为全连接", "HUAWEI CONNECT",
    "上海旅游节", "上海书展", "上海国际艺术节",
]


def _key(title: str) -> str:
    t = re.sub(r"20\d{2}年?", "", title)
    t = re.sub(r"第[0-9一二三四五六七八九十]+届", "", t)
    t = re.split(_SEO, t)[0]
    return _PUNCT.sub("", t).lower()


def _score(e: Event):
    # 代表优先级:重磅 > 有日期 > 有真实链接(非百度兜底) > 标题更短(更干净)
    return (e.featured, bool(e.start_date), "baidu.com" not in e.official_url, -len(e.title))


def clean(events: List[Event]) -> List[Event]:
    for e in events:
        e.title = " ".join(e.title.split())

    groups: Dict[str, List[Event]] = {}
    for e in events:
        if not e.title:
            continue
        groups.setdefault(_key(e.title), []).append(e)

    deduped: List[Event] = []
    for grp in groups.values():
        rep = max(grp, key=_score)
        for e in grp:  # 用同组其它条目补全代表的空字段
            if not rep.start_date and e.start_date:
                rep.start_date, rep.end_date = e.start_date, e.end_date
            if not rep.venue and e.venue:
                rep.venue = e.venue
            if ("baidu.com" in rep.official_url or not rep.official_url) \
                    and e.official_url and "baidu.com" not in e.official_url:
                rep.official_url = e.official_url
        # 一剧多档期:同名合并后保留所有不同日期(否则木偶馆7/21、7/28会被压成一条)
        dates = sorted({e.start_date for e in grp if e.start_date})
        if len(dates) > 1:
            rep.sessions = dates
            rep.start_date = dates[0]  # 主日期取最早一场(供排序/倒计时)
        deduped.append(rep)

    # 策展优先:仅当某大会确实有 curated 条目存活时,去掉爬虫里的同名冗余
    covered = {kw for kw in COVERED
               if any(kw in e.title for e in deduped if e.source == "curated")}
    out = [e for e in deduped
           if e.source == "curated" or not any(kw in e.title for kw in covered)]

    print(f"[clean] 去重后 {len(out)} 条(原 {len(events)})")
    return out
