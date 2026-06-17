"""亲子 / 适龄 / 价格打标 —— 真正的差异化逻辑。"""
from __future__ import annotations

import re
from typing import List

from models import Event

KID_KEYWORDS = [
    "亲子", "儿童", "少儿", "科普", "绘本", "动画", "恐龙", "乐高", "互动",
    "手工", "研学", "家庭", "宝宝", "卡通", "童", "迪士尼", "魔术", "马戏",
    # 扩充:让现有源里的亲子内容更多被识别
    "玩具", "童博", "潮玩", "孕婴童", "母婴", "木偶", "杂技", "嘉年华",
    "积木", "启蒙", "早教", "童话", "天文", "太空", "萌宠", "水族",
    "海洋馆", "自然博物", "科技馆", "泡泡", "遛娃", "亲子游",
]
RE_AGE = re.compile(r"(\d{1,2})\s*[-~到至]\s*(\d{1,2})\s*岁")
RE_PRICE = re.compile(r"(\d+)\s*元")


def tag(events: List[Event]) -> List[Event]:
    for ev in events:
        text = f"{ev.title} {ev.raw_text}"

        # 亲子判定
        if any(k in text for k in KID_KEYWORDS):
            ev.kid_friendly = True
            if "亲子" not in ev.tags:
                ev.tags.append("亲子")

        # 适龄
        m = RE_AGE.search(text)
        if m:
            ev.age_range = f"{m.group(1)}-{m.group(2)}岁"

        # 价格
        prices = [int(x) for x in RE_PRICE.findall(text)]
        if prices:
            ev.price_min = min(prices)
            ev.price_range = (
                f"{min(prices)}-{max(prices)}元"
                if len(set(prices)) > 1
                else f"{prices[0]}元"
            )

        # 免费
        if "免费" in text:
            ev.price_min = 0
            if "免费" not in ev.tags:
                ev.tags.append("免费")

    n_kid = sum(1 for e in events if e.kid_friendly)
    print(f"[tag] 完成,其中亲子 {n_kid} 条")
    return events
