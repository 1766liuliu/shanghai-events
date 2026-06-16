"""内容安全过滤 —— 这是给孩子用的家庭 App,必须剔除不适合儿童的内容。

命中黑名单关键词的活动直接丢弃(如成人展)。黑名单按需扩充。
"""
from __future__ import annotations

from typing import List

from models import Event

# 不适合儿童/家庭的内容关键词(命中即丢弃)
BLOCK = [
    "成人展", "成人用品", "成人博览", "成人电影", "情趣", "性文化", "性博",
    "两性", "18禁", "18+", "色情", "脱衣", "夜店", "av展", "成人影",
]


def filter_safe(events: List[Event]) -> List[Event]:
    out: List[Event] = []
    dropped = 0
    for e in events:
        text = f"{e.title} {e.raw_text}".lower()
        if any(b.lower() in text for b in BLOCK):
            dropped += 1
            continue
        out.append(e)
    print(f"[safety] 拦截不适合儿童内容 {dropped} 条,保留 {len(out)} 条")
    return out
