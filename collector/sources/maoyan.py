"""猫眼演出采集器 —— 演唱会/剧场/马戏/魔术等商业演出(SSR HTML)。

合规等级: 中(商业平台公开页,仅自用、不二次分发、不商用)。
结构(2026-06 核实): show.maoyan.com 首页热门区 .hotlist-item ——
  名称 .hotlist-item-name / 场馆 .location / 日期 .date。
说明:
  · 默认返回上海热门演出(城市由猫眼默认控制);如需锁定上海,可加 cityId cookie。
  · 卡片走 JS 跳转、无 href,详情链接留空(标题+场馆+日期已足够检索)。
"""
from __future__ import annotations

import re
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from models import Event
from sources.base import BaseSource

HOME = "https://show.maoyan.com/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
}
# 如需强制上海: COOKIES = {"cityId": "10"}  # 10 = 上海(以猫眼实际为准)
COOKIES: dict = {}
RE_DATE = re.compile(r"(\d{4})\.(\d{1,2})\.(\d{1,2})")


class MaoyanSource(BaseSource):
    name = "maoyan"
    compliance = "mid"

    def fetch(self) -> List[Event]:
        soup = self._get()
        if soup is None:
            return []
        events: List[Event] = []
        seen = set()
        for it in soup.select(".hotlist-item"):
            name_el = it.select_one(".hotlist-item-name")
            if not name_el:
                continue
            name = name_el.get_text(strip=True)
            if not name:
                continue

            venue_el = it.select_one(".location")
            date_el = it.select_one(".date")
            start, end = self._parse_dates(date_el.get_text(strip=True) if date_el else "")

            ev = Event(
                title=name[:60],
                type="演出",
                source=self.name,
                venue=venue_el.get_text(strip=True) if venue_el else "",
                start_date=start,
                end_date=end,
                raw_text=name,
            )
            if ev.event_id in seen:
                continue
            seen.add(ev.event_id)
            events.append(ev)
        print(f"[maoyan] 解析到 {len(events)} 条")
        return events

    @staticmethod
    def _parse_dates(text: str):
        dates = RE_DATE.findall(text)  # 如 "2026.08.15 / 08.16" → 只取整日期
        if not dates:
            return "", ""
        y, m, d = dates[0]
        start = f"{y}-{int(m):02d}-{int(d):02d}"
        end = ""
        if len(dates) > 1:
            y2, m2, d2 = dates[-1]
            end = f"{y2}-{int(m2):02d}-{int(d2):02d}"
        return start, end

    def _get(self) -> Optional[BeautifulSoup]:
        try:
            resp = requests.get(
                HOME, headers=HEADERS, cookies=COOKIES, timeout=self.timeout
            )
            resp.encoding = "utf-8"
            return BeautifulSoup(resp.text, "html.parser")
        except Exception as e:  # noqa: BLE001
            print(f"[maoyan] 抓取失败: {e}")
            return None
