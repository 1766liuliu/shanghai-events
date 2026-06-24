"""上海重大活动 · 策展源 —— 读 data/curated.toml(数据与代码分离)。

为什么需要它:
  免费爬虫给不出"未来的重大活动"(WAIC/进博/大师赛等),还会混入过期、纯 B2B、
  不适合儿童的内容。本源是雷达的"可靠骨架"——少而精、有日期、已筛选。

数据在哪 / 怎么改:
  活动清单已外移到 `data/curated.toml`,可直接在 GitHub 网页编辑(文件头有说明),
  不用动这份代码。本文件只负责"读数据 + 判定形态(固定场馆/年度固定)"。
  万一 TOML 写坏 → 本源返回空 → 质量闸自动沿用上次好数据并在页面提示,不会崩。
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

DATA = os.path.join(os.path.dirname(__file__), "..", "..", "data", "curated.toml")

# 固定场馆(常年滚动排期,无单一日期)—— 命中即归"固定场馆",其余策展归"年度固定"
_VENUE_KW = ["天文馆", "自然博物馆", "科技馆", "玻璃博物馆", "马戏城",
             "儿童艺术剧场", "木偶剧团", "音乐厅", "大剧院", "东方艺术中心",
             "博物馆", "美术馆", "艺术宫", "水族馆", "动物园", "海洋公园",
             "乐高", "植物园", "科普中心", "文化广场",
             "宛平", "天蟾", "梅赛德斯", "足球场", "体育中心",
             "相声会馆", "脱口秀", "Livehouse", "育音堂"]


def _kind(title: str) -> str:
    return "固定场馆" if any(k in title for k in _VENUE_KW) else "年度固定"


class CuratedSource(BaseSource):
    name = "curated"
    compliance = "high"  # 人工策展,无抓取

    def fetch(self) -> List[Event]:
        try:
            with open(os.path.abspath(DATA), "rb") as f:
                rows = tomllib.load(f).get("event", [])
        except Exception as e:  # noqa: BLE001
            print(f"[curated] 读取 curated.toml 失败: {e}(质量闸将保留上次好数据)")
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
        print(f"[curated] 重大活动 {len(events)} 条(读自 curated.toml)")
        return events
