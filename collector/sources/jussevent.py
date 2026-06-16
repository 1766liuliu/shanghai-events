"""上海久事体育采集器 —— 官方赛事运营方(服务端渲染 HTML)。

合规等级: 中高(官网公开信息)。覆盖久事运营的大型赛事动态。
页面结构(2026-06 核实):
  每条在 div.flex_index 卡片内 —— 标题 .list_info_title / 日期 .content_list_bottom_time
  / 详情链接 a[href*=Detail.aspx]。
注意: 首页多为赛事动态新闻(含往期回顾),已过期项由 pipeline.freshness 统一过滤。
"""
from __future__ import annotations

import re
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from models import Event
from sources.base import BaseSource

HOME = "https://www.jussevent.com/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
}
RE_DATE = re.compile(r"(20\d{2})[-./年](\d{1,2})[-./月](\d{1,2})")


class JussventSource(BaseSource):
    name = "jussevent"
    compliance = "mid"  # 官方运营方,实质中高

    def fetch(self) -> List[Event]:
        soup = self._get()
        if soup is None:
            return []
        events: List[Event] = []
        for card in soup.select("div.flex_index"):
            title_el = card.select_one(".list_info_title")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            if not title or len(title) < 4:
                continue

            a = card.select_one("a[href*='Detail.aspx']")
            href = a.get("href", "") if a else ""
            if href and not href.startswith("http"):
                href = "https://www.jussevent.com/" + href.lstrip("./")

            date_el = card.select_one(".content_list_bottom_time")
            start = ""
            if date_el:
                m = RE_DATE.search(date_el.get_text(strip=True))
                if m:
                    start = f"{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}"

            events.append(
                Event(
                    title=title[:60],
                    type="体育",
                    source=self.name,
                    official_url=href,
                    start_date=start,
                    raw_text=card.get_text(" ", strip=True)[:200],
                )
            )
        print(f"[jussevent] 解析到 {len(events)} 条")
        return events

    def _get(self) -> Optional[BeautifulSoup]:
        try:
            resp = requests.get(HOME, headers=HEADERS, timeout=self.timeout)
            resp.encoding = resp.apparent_encoding
            return BeautifulSoup(resp.text, "html.parser")
        except Exception as e:  # noqa: BLE001
            print(f"[jussevent] 抓取失败: {e}")
            return None
