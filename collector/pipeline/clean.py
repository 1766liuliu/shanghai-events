"""清洗与去重。"""
from __future__ import annotations

from typing import List

from models import Event


def clean(events: List[Event]) -> List[Event]:
    seen = set()
    out: List[Event] = []
    for ev in events:
        ev.title = " ".join(ev.title.split())
        if not ev.title:
            continue
        eid = ev.event_id
        if eid in seen:
            continue
        seen.add(eid)
        out.append(ev)
    print(f"[clean] 去重后 {len(out)} 条")
    return out
