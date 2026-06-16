"""上海本地宝采集器 —— 民间聚合(可立即跑通)。

合规等级: 中(转载),仅自用、不二次分发。
说明: 不同板块结构不同 ——
  · 展会(shzhanhui): <h3><a> 文本拼接,需正则解析,日期/场馆多在详情页;
  · 演出(yanchanghuitime): 表格 <tr><td>,标题在 td>a,日期/场馆在同行 td。
  体育板块桌面端列表 URL 不稳定(易 404),体育赛事改由久事官方源覆盖。
"""
from __future__ import annotations

import re
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from models import Event
from sources.base import BaseSource

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
}

# 每个板块: type / url / mode(解析方式)
LIST_PAGES = [
    {"type": "展会", "url": "https://sh.bendibao.com/xiuxian/shzhanhui/", "mode": "h3"},
    {"type": "演出", "url": "https://sh.bendibao.com/xiuxian/yanchanghuitime/", "mode": "table"},
]

GENERIC = {"点击查看", "查看", "详情", "查看详情", "更多", "点击购买", "购票"}
RE_DATE = re.compile(r"(\d{4})?[年./-]?\s*(\d{1,2})[月./-](\d{1,2})")
RE_VENUE = re.compile(
    r"(国家会展中心|新国际博览中心|世博展览馆|展览中心|大剧院|东方艺术中心|"
    r"音乐厅|体育馆|体育场|文化广场|奔驰文化中心|美术馆|博物馆|文化中心)"
)


class BendibaoSource(BaseSource):
    name = "bendibao"
    compliance = "mid"

    def fetch(self) -> List[Event]:
        events: List[Event] = []
        for page in LIST_PAGES:
            soup = self._get(page["url"])
            if soup is None:
                continue
            if page["mode"] == "h3":
                events += self._parse_h3(soup, page["type"])
            else:
                events += self._parse_table(soup, page["type"])
        print(f"[bendibao] 解析到 {len(events)} 条")
        return events

    def _get(self, url: str) -> Optional[BeautifulSoup]:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=self.timeout)
            if resp.status_code != 200:
                print(f"[bendibao] {url} 返回 {resp.status_code},跳过")
                return None
            resp.encoding = resp.apparent_encoding
            return BeautifulSoup(resp.text, "html.parser")
        except Exception as e:  # noqa: BLE001
            print(f"[bendibao] 抓取失败 {url}: {e}")
            return None

    def _parse_h3(self, soup: BeautifulSoup, etype: str) -> List[Event]:
        out: List[Event] = []
        for a in soup.select("h3 a[href]"):
            text = a.get_text(strip=True)
            if not text or len(text) < 4 or text in GENERIC:
                continue
            ev = self._build(text, a.get("href", ""), etype, text)
            if ev:
                out.append(ev)
        return out

    def _parse_table(self, soup: BeautifulSoup, etype: str) -> List[Event]:
        out: List[Event] = []
        for tr in soup.select("table tr"):
            title_a = None
            for a in tr.select("a[href]"):
                t = a.get_text(strip=True)
                if t and t not in GENERIC and len(t) >= 3:
                    title_a = a
                    break
            if not title_a:
                continue
            row_text = tr.get_text(" ", strip=True)
            ev = self._build(
                title_a.get_text(strip=True), title_a.get("href", ""), etype, row_text
            )
            if ev:
                out.append(ev)
        return out

    def _build(self, title: str, href: str, etype: str, text: str) -> Optional[Event]:
        if href.startswith("/"):
            href = "https://sh.bendibao.com" + href
        venue_m = RE_VENUE.search(text)
        date_m = RE_DATE.search(text)
        start = ""
        if date_m:
            year = date_m.group(1) or "2026"
            start = f"{year}-{int(date_m.group(2)):02d}-{int(date_m.group(3)):02d}"
        return Event(
            title=title[:60],
            type=etype,
            source=self.name,
            official_url=href,
            venue=venue_m.group(1) if venue_m else "",
            start_date=start,
            raw_text=text,
        )
