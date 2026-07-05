"""北京重大活动 · 策展源 —— 读 data/curated_beijing.toml(数据与代码分离)。

与 sources/curated.py(上海版)结构对称,但完全独立成文件:独立数据文件、
独立场馆关键词表、独立类实例,physically 不共享任何状态,避免两城市数据
在这一步产生交叉。万一 TOML 写坏 → 本源返回空 → 质量闸自动沿用上次好数据。
"""
from __future__ import annotations

import os
from typing import List

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # pragma: no cover
    import tomli as tomllib  # 旧版回退(需 pip install tomli)

from models import Event
from sources.base import BaseSource

DATA = os.path.join(os.path.dirname(__file__), "..", "..", "data", "curated_beijing.toml")

# 固定场馆(常年滚动排期,无单一日期)—— 命中即归"固定场馆",其余策展归"年度固定"
_VENUE_KW = ["大剧院", "剧院", "剧场", "体育场", "Livehouse",
             "博物馆", "美术馆", "艺术区", "艺术中心", "德云社",
             "茶馆", "大舞台"]


def _kind(title: str) -> str:
    return "固定场馆" if any(k.lower() in title.lower() for k in _VENUE_KW) else "年度固定"


class CuratedBeijingSource(BaseSource):
    name = "curated_beijing"
    compliance = "high"  # 人工策展,无抓取

    def fetch(self) -> List[Event]:
        try:
            with open(os.path.abspath(DATA), "rb") as f:
                rows = tomllib.load(f).get("event", [])
        except Exception as e:  # noqa: BLE001
            print(f"[curated_beijing] 读取 curated_beijing.toml 失败: {e}(质量闸将保留上次好数据)")
            return []

        events: List[Event] = []
        for e in rows:
            title = (e.get("title") or "").strip()
            if not title:
                continue
            events.append(Event(
                title=title, type=e.get("type", "演出"), source=self.name,
                official_url=e.get("url", ""), venue=e.get("venue", ""),
                start_date=e.get("start", ""), end_date=e.get("end", ""),
                kid_friendly=bool(e.get("kid", False)), age_range=e.get("age", ""),
                featured=bool(e.get("featured", False)), note=e.get("note", ""),
                tags=list(e.get("tags", [])), kind=_kind(title), raw_text=title,
            ))
        print(f"[curated_beijing] 重大活动 {len(events)} 条(读自 curated_beijing.toml)")
        return events
