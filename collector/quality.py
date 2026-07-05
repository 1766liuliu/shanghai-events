"""数据质量闸 —— 抓取后按源做"失败不空覆盖",并记录每源健康。

为什么:每个爬虫靠解析网页,源一改版就可能静默返回 0/骤减,而管线照样发布,
没人察觉(猫眼某天改版返回 0,65 条演出就无声消失)。本闸在源级别拦截:
  · 某源本次为 0、但上次有数据 → 判 failed,用上次好数据顶上;
  · 某源本次 < 上次 * DROP_FLOOR(且上次有一定量)→ 判 degraded,用上次好数据顶上;
  · 否则用本次新数据,并刷新"上次好数据"。
同时产出每源健康(status/count/last_success),交给页面展示(可观测性)。

状态文件(入库,Actions 跨次持久化):data/lastgood.json {source:{events,count,last_success}}
中继(relay)源的部分失败也被本闸兜住:cn_events.json 若缺了木偶,cnrelay 条数骤降→保留上次。
"""
from __future__ import annotations

import dataclasses
import datetime
import json
import os
from typing import List, Tuple

from models import Event

LASTGOOD = os.path.join(os.path.dirname(__file__), "..", "data", "lastgood.json")
DROP_FLOOR = 0.5  # 本次 < 上次*0.5 视为骤降
_VALID = {f.name for f in dataclasses.fields(Event)}


def _load(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:  # noqa: BLE001
        return {}


def _save(d: dict, path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)


def _to_event(d: dict) -> Event:
    return Event(**{k: v for k, v in d.items() if k in _VALID})


def gated_fetch(sources, today: str = "", lastgood_path: str = "") -> Tuple[List[Event], dict]:
    """lastgood_path 留空时用上海默认路径(与既有调用 100% 兼容);
    其他城市(如北京)传各自独立路径,状态文件互不覆盖。"""
    today = today or datetime.date.today().isoformat()
    lastgood_path = lastgood_path or LASTGOOD
    lastgood = _load(lastgood_path)
    all_events: List[Event] = []
    health: dict = {}

    for src in sources:
        name = src.name
        print(f"\n=== 采集源: {name} (合规:{src.compliance}) ===")
        try:
            fresh = src.fetch()
        except Exception as e:  # noqa: BLE001
            print(f"[{name}] 抓取异常: {e}")
            fresh = []

        prev = lastgood.get(name, {})
        prev_events = prev.get("events", [])
        prev_count = len(prev_events)
        n = len(fresh)

        if n == 0 and prev_count > 0:
            status = "failed"
        elif prev_count >= 4 and n < prev_count * DROP_FLOOR:
            status = "degraded"
        else:
            status = "ok"

        if status == "ok":
            all_events += fresh
            lastgood[name] = {
                "events": [e.to_dict() for e in fresh],
                "count": n, "last_success": today,
            }
            health[name] = {"status": "ok", "count": n, "last_success": today}
        else:
            all_events += [_to_event(d) for d in prev_events]
            health[name] = {
                "status": status, "count": n, "kept": prev_count,
                "last_success": prev.get("last_success", ""),
            }
            print(f"[质量闸] ⚠ {name} 本次{n}条 / 上次{prev_count}条 → {status},保留上次好数据")

    _save(lastgood, lastgood_path)
    bad = [k for k, v in health.items() if v["status"] != "ok"]
    print(f"[质量闸] 源健康: 正常 {len(health) - len(bad)} / 异常 {len(bad)}"
          + (f" ({', '.join(bad)})" if bad else ""))
    return all_events, health
