"""时效过滤 —— 雷达只看未来,丢弃明显已过期的活动。

规则:
  1) 有明确开始日期且早于今天 → 丢弃;
  2) 无开始日期、但标题里出现的最大年份 < 今年 → 视为往期,丢弃(如"2024演唱会");
  3) 其余(未来 / 无日期且未标过去年份)→ 保留。
"""
from __future__ import annotations

import datetime
import re
from typing import List

from models import Event

RE_YEAR = re.compile(r"20\d{2}")


def keep_upcoming(events: List[Event], today: str = "") -> List[Event]:
    today = today or datetime.date.today().isoformat()
    cur_year = int(today[:4])
    out: List[Event] = []
    for e in events:
        if e.start_date:
            # 进行中(结束日期未过)或未来都保留
            effective = e.end_date or e.start_date
            if effective >= today:
                out.append(e)
            continue
        # 无日期: 看标题年份
        years = [int(y) for y in RE_YEAR.findall(e.title)]
        if years and max(years) < cur_year:
            continue
        out.append(e)
    print(f"[freshness] 丢弃过期 {len(events) - len(out)} 条,保留 {len(out)} 条")
    return out
