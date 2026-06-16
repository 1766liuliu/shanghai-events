"""聚展(jufair)国际展会采集器 —— 上海国际展览(带日期 + 详情链接)。

合规等级: 中(第三方展会聚合,仅自用、不二次分发)。
结构(2026-06 核实): 列表页 a[href*=/exhibition/] 为展会详情,名称在链接文字,
  日期/场馆在邻近祖先文本(取"下一届"时间,过期由 freshness 过滤)。
覆盖: 上海地区国际展会(519=上海地区);可加翻页扩量。
"""
from __future__ import annotations

import re
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from models import Event
from sources.base import BaseSource

BASE = "https://www.jufair.com"
LIST_URLS = [f"{BASE}/exhibition-0-0-1-519-0-0-{p}/" for p in (1, 2)]
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
}
RE_DATE = re.compile(r"(20\d{2})[-./年](\d{1,2})[-./月](\d{1,2})")
RE_VENUE = re.compile(
    r"(国家会展中心|新国际博览中心|世博展览馆|展览中心|跨国采购|世贸商城|"
    r"光大会展|国际会议中心|农展馆)"
)


class JufairSource(BaseSource):
    name = "jufair"
    compliance = "mid"

    def fetch(self) -> List[Event]:
        events: List[Event] = []
        seen = set()
        for url in LIST_URLS:
            soup = self._get(url)
            if soup is None:
                continue
            for a in soup.select('a[href*="/exhibition/"]'):
                name = a.get_text(strip=True)
                if len(name) < 4 or name in seen:
                    continue
                seen.add(name)
                href = a.get("href", "")
                if href.startswith("/"):
                    href = BASE + href

                ctx, node = "", a
                for _ in range(4):
                    node = node.parent
                    if node is None:
                        break
                    ctx = node.get_text(" ", strip=True)
                    if RE_DATE.search(ctx):
                        break
                dm = RE_DATE.search(ctx)
                start = (
                    f"{dm.group(1)}-{int(dm.group(2)):02d}-{int(dm.group(3)):02d}"
                    if dm else ""
                )
                vm = RE_VENUE.search(ctx)
                events.append(
                    Event(
                        title=name[:60], type="展会", source=self.name,
                        official_url=href, venue=vm.group(1) if vm else "",
                        start_date=start, tags=["国际"], raw_text=ctx[:120],
                    )
                )
        print(f"[jufair] 解析到 {len(events)} 条")
        return events

    def _get(self, url: str) -> Optional[BeautifulSoup]:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=self.timeout)
            resp.encoding = resp.apparent_encoding
            return BeautifulSoup(resp.text, "html.parser")
        except Exception as e:  # noqa: BLE001
            print(f"[jufair] 抓取失败 {url}: {e}")
            return None
