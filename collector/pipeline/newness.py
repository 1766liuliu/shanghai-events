"""新增识别 —— 记录每条活动的"首次出现日期",供页面"最新"分类使用。

机制:
  · data/seen.json 持久化 {event_id: 首次出现日期}(跨每次运行累积,不清理);
  · 本次出现、但 seen.json 里没有的 → 标为今天新增;已有的 → 沿用原首见日期;
  · 首次启用时(seen.json 不存在),把当时所有活动回填为旧日期,避免"全部都算新"。
NEW_WINDOW_DAYS 天内首次出现的,前端归入"最新"。
"""
from __future__ import annotations

import datetime
import json
import os
from typing import List

from models import Event

SEEN_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "seen.json")
NEW_WINDOW_DAYS = 7
_BASELINE = "2000-01-01"  # 首次启用时的回填日期(永远不算"新")


def _load() -> dict:
    try:
        with open(SEEN_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return {}


def _save(seen: dict) -> None:
    os.makedirs(os.path.dirname(SEEN_PATH), exist_ok=True)
    with open(SEEN_PATH, "w", encoding="utf-8") as f:
        json.dump(seen, f, ensure_ascii=False, indent=1)


def mark_new(events: List[Event], today: str = "") -> List[Event]:
    today = today or datetime.date.today().isoformat()
    seen = _load()
    first_run = not seen
    for e in events:
        eid = e.event_id
        if eid in seen:
            e.first_seen = seen[eid]
        else:
            e.first_seen = _BASELINE if first_run else today
            seen[eid] = e.first_seen
    _save(seen)
    cutoff = (datetime.date.fromisoformat(today)
              - datetime.timedelta(days=NEW_WINDOW_DAYS - 1)).isoformat()
    n_new = sum(1 for e in events if e.first_seen >= cutoff)
    tip = "(首次启用,全部回填为非新)" if first_run else ""
    print(f"[newness] {NEW_WINDOW_DAYS} 天内新增 {n_new} 条 {tip}")
    return events
