"""时效过滤 —— 雷达只看未来,丢弃明显已过期的活动。

规则:
  1) 有明确开始日期且早于今天 → 丢弃;
  2) 无开始日期 + 形态="临时" → 丢弃("档期待定的临时活动"无价值,用户要求);
  3) 无开始日期 + 形态=年度固定/固定场馆 → 保留(年度锚点待公布 / 常驻场馆无单一日期);
  4) 无开始日期、但标题里出现的最大年份 < 今年 → 视为往期,丢弃。
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
        # 无日期 + 临时 → 丢弃(档期待定无价值)
        if e.kind == "临时":
            continue
        # 无日期的年度/场馆锚点:标题若标了过去年份则丢,否则保留
        years = [int(y) for y in RE_YEAR.findall(e.title)]
        if years and max(years) < cur_year:
            continue
        out.append(e)
    print(f"[freshness] 丢弃过期 {len(events) - len(out)} 条,保留 {len(out)} 条")
    return out
