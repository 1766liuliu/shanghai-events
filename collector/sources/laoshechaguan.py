"""北京老舍茶馆采集器 —— 官方排期页(服务端渲染,境外可达)。

线索来源:用户提供的票务代理宣传单(一次性快照,不可持续,只作发现场馆的线索)。
联网核实后发现老舍茶馆官网自带排期页 i.laoshechaguan.cn/list/,結构干净(Astro
框架 SSR,.card-link 卡片:标题/日期区间/场馆/价格),比宣传单更可靠、可长期抓取。

结构(2026-07 核实): .card-link a 标签,内含 .card-link__title(标题)+ 3 个 <p>
(日期区间"YYYY.MM.DD-MM.DD" / 场馆 / 价格"¥xx-xx起")。当前固定驻场综艺曲艺演出
(相声/评书/鼓曲/亲子皮影戏等),条数少但天然全部是北京、亲子友好度高。
"""
from __future__ import annotations

import re
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from models import Event
from sources.base import BaseSource

BASE = "https://i.laoshechaguan.cn"
LIST_URL = f"{BASE}/list/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
}
RE_FULL = re.compile(r"(\d{4})\.(\d{1,2})\.(\d{1,2})")
RE_SHORT_END = re.compile(r"-(\d{1,2})\.(\d{1,2})")


class LaosheChaguanSource(BaseSource):
    name = "laoshechaguan"
    compliance = "mid"

    def fetch(self) -> List[Event]:
        soup = self._get()
        if soup is None:
            return []
        events: List[Event] = []
        for a in soup.select(".card-link"):
            t = a.select_one(".card-link__title")
            title = t.get_text(strip=True) if t else ""
            if not title:
                continue
            ps = a.select("p")
            date_txt = ps[0].get_text(strip=True) if len(ps) > 0 else ""
            venue = ps[1].get_text(strip=True) if len(ps) > 1 else "老舍茶馆"
            price = ps[2].get_text(strip=True) if len(ps) > 2 else ""
            start, end = self._range(date_txt)
            href = a.get("href", "")
            if href.startswith("/"):
                href = BASE + href
            events.append(Event(
                title=title[:60], type="演出", source=self.name,
                official_url=href, venue=venue,
                start_date=start, end_date=end,
                price_range=price.lstrip("¥") if price else "",
                kid_friendly=("亲子" in title or "皮影" in title),
                raw_text=f"{title} {date_txt} {venue} {price}",
            ))
        print(f"[laoshechaguan] 解析到 {len(events)} 条")
        return events

    @staticmethod
    def _range(text: str):
        """日期形如 "2026.07.09-08.29"(结束日不重复年份,承接开始日的年)。"""
        m = RE_FULL.search(text)
        if not m:
            return "", ""
        y, mo, d = m.groups()
        start = f"{y}-{int(mo):02d}-{int(d):02d}"
        end = ""
        m2 = RE_SHORT_END.search(text[m.end():])
        if m2:
            mo2, d2 = m2.groups()
            end = f"{y}-{int(mo2):02d}-{int(d2):02d}"
        return start, end

    def _get(self) -> Optional[BeautifulSoup]:
        try:
            resp = requests.get(LIST_URL, headers=HEADERS, timeout=self.timeout)
            if resp.status_code != 200:
                print(f"[laoshechaguan] 返回 {resp.status_code},跳过")
                return None
            resp.encoding = resp.apparent_encoding
            return BeautifulSoup(resp.text, "html.parser")
        except Exception as e:  # noqa: BLE001
            print(f"[laoshechaguan] 抓取失败: {e}")
            return None
