"""上海文化广场 排期采集器 —— 音乐剧/话剧/舞剧/亲子剧(服务端渲染,境外可达)。

合规等级: 中(剧场官网公开排期,仅自用)。
结构(2026-06 核实): programList.aspx 内 a[href*=ProgramDetails] 为剧目,标题在链接文字,
  日期在邻近"日期:2026.6.11-2026.6.21"。属"临时·有档期"→ 进"近期演出"。
"""
from __future__ import annotations

import re
from typing import List

import requests
from bs4 import BeautifulSoup

from models import Event
from sources.base import BaseSource

URL = "https://www.shcstheatre.com/Program/programList.aspx"
BASE = "https://www.shcstheatre.com/Program/"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
}
RE_D = re.compile(r"(20\d{2})[.\-/](\d{1,2})[.\-/](\d{1,2})")
# 按钮/导航文案(子串命中即剔除)——网站改版会给中文按钮加英文后缀
# (如"立即购票 Buy Tickets"),故用子串匹配而非精确匹配,避免漏判。
SKIP_KW = ["购票", "详情", "更多", "学生现场票", "演艺大世界",
           "Buy Ticket", "buy ticket", "Tickets", "更多剧目"]


class ShcstheatreSource(BaseSource):
    name = "shcstheatre"
    compliance = "mid"

    def fetch(self) -> List[Event]:
        try:
            r = requests.get(URL, headers=HEADERS, timeout=self.timeout)
            r.encoding = r.apparent_encoding
            s = BeautifulSoup(r.text, "html.parser")
        except Exception as e:  # noqa: BLE001
            print(f"[shcstheatre] 抓取失败: {e}")
            return []

        events: List[Event] = []
        seen = set()
        for a in s.select('a[href*="ProgramDetails"]'):
            title = a.get_text(strip=True)
            if (not title or len(title) < 4 or title in seen
                    or any(k in title for k in SKIP_KW)):
                continue
            seen.add(title)

            href = a.get("href", "")
            if href.startswith("http"):
                pass
            elif href.startswith("/"):
                href = "https://www.shcstheatre.com" + href
            else:
                href = BASE + href

            ctx, node = "", a
            for _ in range(5):
                node = node.parent
                if node is None:
                    break
                ctx = node.get_text(" ", strip=True)
                if RE_D.search(ctx):
                    break
            ds = RE_D.findall(ctx)
            start = end = ""
            if ds:
                y, m, d = ds[0]
                start = f"{y}-{int(m):02d}-{int(d):02d}"
                if len(ds) > 1:
                    y2, m2, d2 = ds[-1]
                    end = f"{y2}-{int(m2):02d}-{int(d2):02d}"

            events.append(
                Event(
                    title=title[:60], type="演出", source=self.name,
                    official_url=href, venue="上海文化广场",
                    start_date=start, end_date=end, raw_text=title,
                )
            )
        print(f"[shcstheatre] 解析到 {len(events)} 条")
        return events
