"""链接兜底 —— 没有官方链接的活动,指向"大麦购票搜索"(购票网站),拒绝百度。

策略:
  · 有官方/详情链接(策展官网、聚展、本地宝、文化广场等)→ 用其本身,不动;
  · 没有的(主要是猫眼演出、个别策展)→ 大麦站内搜索(购票网站),关键词做清洗
    (去年份、去"巡回演唱会/上海站"等后缀、去书名号),提高命中。
说明:用户明确拒绝百度搜索页;大麦覆盖演唱会/话剧/展览/赛事,是购票直达。
"""
from __future__ import annotations

import re
from typing import List
from urllib.parse import quote

from models import Event

_STRIP = re.compile(
    r"(20\d{2}年?|巡回演唱会|全国巡演|世界巡演|巡演|演唱会|粉丝见面会|见面会|"
    r"上海站|·上海站|-上海站|北京站|·北京站|-北京站|LIVE|tour)",
    re.IGNORECASE,
)
_PUNCT = re.compile(r"[《》「」【】（）()·\-—|/]+")


def _keyword(title: str) -> str:
    t = _STRIP.sub(" ", title)
    t = _PUNCT.sub(" ", t)
    t = " ".join(t.split())
    return (t[:24] or title).strip()


def add_fallback_links(events: List[Event]) -> List[Event]:
    n = 0
    for e in events:
        if e.official_url:
            continue
        e.official_url = (
            f"https://search.damai.cn/search.html?keyword={quote(_keyword(e.title))}"
        )
        n += 1
    print(f"[links] 大麦购票搜索兜底 {n} 条(无百度)")
    return events
