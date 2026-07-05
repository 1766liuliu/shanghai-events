"""北京本地宝采集器 —— 与上海本地宝(bendibao.py)结构对称但独立成文件,
不共享任何状态;且实测两地页面 <table> 列结构不同,不能直接复用上海解析逻辑。

结构(2026-07 核实,bj.bendibao.com):
  · 演出 yanchanghuitime:<tr><td>艺人(纯文本,少数嵌<a>)</td>
    <td>日期(可能"开票日<br>演出日期区间",取最后一行为准)</td>
    <td>场馆</td><td>链接"点击查看"</td></tr>
  · 展会 zhanhuitime:<tr><td>标题</td><td>日期区间</td><td>场馆</td>
    <td>价格</td><td>链接"点击查看"</td></tr>(表格偏历史归档,当前在售占比低,
    过期由 freshness 管线过滤,不影响展示)。
  两表标题都是纯文本 td(不在<a>里),按列位置取值,比正则猜测更可靠。
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
RE_DATE = re.compile(r"(\d{4})\.(\d{1,2})\.(\d{1,2})")
GENERIC = {"点击查看", "查看", "详情", "查看详情", "更多"}


def _row_dates_last_line(td) -> tuple:
    """演出日期列可能是"开票日<br>演出日期区间"两行,取最后一行(真实演出日期)。"""
    lines = [l.strip() for l in td.get_text("\n", strip=True).split("\n") if l.strip()]
    if not lines:
        return "", ""
    return _range(lines[-1])


def _range(text: str) -> tuple:
    ds = RE_DATE.findall(text)
    if not ds:
        return "", ""
    y, m, d = ds[0]
    start = f"{y}-{int(m):02d}-{int(d):02d}"
    end = ""
    if len(ds) > 1:
        y2, m2, d2 = ds[-1]
        end = f"{y2}-{int(m2):02d}-{int(d2):02d}"
    return start, end


class BendibaoBeijingSource(BaseSource):
    name = "bendibao_beijing"
    compliance = "mid"

    def fetch(self) -> List[Event]:
        events: List[Event] = []
        soup = self._get("https://bj.bendibao.com/xiuxian/yanchanghuitime/")
        if soup is not None:
            events += self._parse_shows(soup)
        soup = self._get("https://bj.bendibao.com/xiuxian/zhanhuitime/")
        if soup is not None:
            events += self._parse_expos(soup)
        print(f"[bendibao_beijing] 解析到 {len(events)} 条")
        return events

    def _get(self, url: str) -> Optional[BeautifulSoup]:
        try:
            resp = requests.get(url, headers=HEADERS, timeout=self.timeout)
            if resp.status_code != 200:
                print(f"[bendibao_beijing] {url} 返回 {resp.status_code},跳过")
                return None
            resp.encoding = resp.apparent_encoding
            return BeautifulSoup(resp.text, "html.parser")
        except Exception as e:  # noqa: BLE001
            print(f"[bendibao_beijing] 抓取失败 {url}: {e}")
            return None

    def _title(self, td) -> str:
        t = td.get_text(strip=True)
        if t and t not in GENERIC:
            return t
        a = td.select_one("a")
        return a.get_text(strip=True) if a else ""

    def _href(self, tr) -> str:
        a = tr.select_one("a[href]")
        href = a.get("href", "") if a else ""
        if href.startswith("/"):
            href = "https://bj.bendibao.com" + href
        return href

    def _parse_shows(self, soup: BeautifulSoup) -> List[Event]:
        out: List[Event] = []
        for tr in soup.select("table tr"):
            tds = tr.select("td")
            if len(tds) < 3:
                continue
            title = self._title(tds[0])
            if not title or len(title) < 2:
                continue
            start, end = _row_dates_last_line(tds[1])
            if not start:
                continue
            venue = tds[2].get_text(strip=True)
            out.append(Event(
                title=title[:60], type="演出", source=self.name,
                official_url=self._href(tr), venue=venue,
                start_date=start, end_date=end, raw_text=tr.get_text(" ", strip=True),
            ))
        return out

    def _parse_expos(self, soup: BeautifulSoup) -> List[Event]:
        out: List[Event] = []
        for tr in soup.select("table tr"):
            tds = tr.select("td")
            if len(tds) < 4:
                continue
            title = self._title(tds[0])
            if not title or len(title) < 3:
                continue
            start, end = _range(tds[1].get_text(strip=True))
            if not start:
                continue
            venue = tds[2].get_text(strip=True)
            price = tds[3].get_text(strip=True) if len(tds) > 3 else ""
            out.append(Event(
                title=title[:60], type="展会", source=self.name,
                official_url=self._href(tr), venue=venue,
                start_date=start, end_date=end,
                price_range=price if price and price not in GENERIC else "",
                raw_text=tr.get_text(" ", strip=True),
            ))
        return out
