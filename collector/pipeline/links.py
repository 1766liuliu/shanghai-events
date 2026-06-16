"""链接兜底 —— 没有官方链接的活动补一个"按标题搜索"链接,保证每条都能点开。

  · 演出/体育 → 大麦搜索(方便找票)
  · 其他(展会等) → 百度搜索(找官方信息)
有些源(猫眼卡片走 JS、部分策展活动)本身没有 href,靠这一步补齐。
"""
from __future__ import annotations

from typing import List
from urllib.parse import quote

from models import Event


def add_fallback_links(events: List[Event]) -> List[Event]:
    n = 0
    for e in events:
        if e.official_url:
            continue
        if e.type in ("演出", "体育"):
            e.official_url = f"https://search.damai.cn/search.html?keyword={quote(e.title)}"
        else:
            e.official_url = f"https://www.baidu.com/s?wd={quote(e.title + ' 上海')}"
        n += 1
    print(f"[links] 补充搜索链接 {n} 条")
    return events
