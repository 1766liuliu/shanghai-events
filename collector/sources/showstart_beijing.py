"""秀动网(showstart.com)北京演出采集器 —— 破解其匿名签名接口,直取 JSON。

背景/为什么值得做:北京一直缺一个像上海猫眼那样稳定产出大量近期演唱会/livehouse
演出的自动源(本地宝演出表是历史归档、更新少)。秀动是专业 livehouse/演出票务
平台,接口按 cityCode 天然锁城,数据干净(标题/日期/场馆/票价全有)。

接口调用方式(2026-07 逆向前端 Nuxt bundle 得到,匿名可用、无需登录):
  1) 先 GET /api/waf/gettoken 拿匿名 accessToken(WAF 令牌);
  2) 再 POST /api/web/activity/list 带 18 个 filter 参数 + sortType=1(时间升序);
  两个请求都要带一组自定义头,其中签名头 CRPSIGN = MD5(拼接串),拼接规则:
    w = accessToken + CUSUT + idToken + CUSID + "web" + CDEVICENO
        + 请求体JSON + 请求路径 + "999web" + CRTRACEID
  匿名态下 CUSUT/idToken/CUSID/CDEVICENO 均为空串。
  必须带 CDEVICEINFO 头(URL 编码的设备信息 JSON),否则报"参数不全"。

脆弱性提示:这是逆向出来的私有接口,秀动改签名算法/参数即会失效——因此本源
异常(拿不到 token / 结构变化)时静默返回已抓到的部分或空,交由质量闸兜住,
绝不让它拖垮整条北京管线。
"""
from __future__ import annotations

import hashlib
import json
import random
import time
from typing import List, Optional
from urllib.parse import quote

import requests

from models import Event
from sources.base import BaseSource

API = "https://www.showstart.com/api"
CITY_CODE = 10  # 北京
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
_DEV = quote(json.dumps({
    "vendorName": "", "deviceMode": "", "deviceName": "", "systemName": "",
    "systemVersion": "", "cpuMode": " ", "cpuCores": "", "cpuArch": "",
    "memerySize": "", "diskSize": "", "network": "", "resolution": "1920*1080",
    "pixelResolution": "",
}))
MAX_PAGES = 5      # 每页20条,近期100条足够(freshness 再过滤过期)
PAGE_SIZE = 20


def _uuid(n: int = 32) -> str:
    cs = ("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
          + str(int(time.time() * 1000)))
    return "".join(random.choice(cs) for _ in range(n))


class ShowstartBeijingSource(BaseSource):
    name = "showstart_beijing"
    compliance = "mid"

    def __init__(self):
        super().__init__()
        self._token = ""

    def _headers(self, url: str, body: str) -> dict:
        o, ut, idt, uid, devno = self._token, "", "", "", ""
        trace = _uuid(32) + str(int(time.time() * 1000))
        raw = o + ut + idt + uid + "web" + devno + body + url + "999web" + trace
        sign = hashlib.md5(raw.encode("utf-8")).hexdigest()
        h = {
            "User-Agent": UA, "Referer": "https://www.showstart.com/",
            "Origin": "https://www.showstart.com",
            "CUSAT": o, "CUSUT": ut, "CUSIT": idt, "CUSID": uid, "CUSNAME": "",
            "CTERMINAL": "web", "CSAPPID": "web", "CDEVICENO": devno,
            "CVERSION": "999", "CDEVICEINFO": _DEV,
            "CRTRACEID": trace, "CRPSIGN": sign,
        }
        if body:
            h["Content-Type"] = "application/json;charset=UTF-8"
        return h

    def _get_token(self) -> bool:
        url = "/waf/gettoken"
        try:
            r = requests.post(API + url, headers=self._headers(url, ""),
                              data=b"", timeout=self.timeout)
            self._token = r.json()["result"]["accessToken"]["access_token"]
            return bool(self._token)
        except Exception as e:  # noqa: BLE001
            print(f"[showstart_beijing] 取匿名token失败: {e}")
            return False

    def _page(self, page_no: int) -> Optional[list]:
        url = "/web/activity/list"
        payload = {
            "pageNo": page_no, "pageSize": PAGE_SIZE, "cityCode": CITY_CODE,
            "activityIds": "", "coupon": "", "keyword": "", "organizerId": "",
            "performerId": "", "showStyle": "", "showTime": "", "showType": "",
            "siteId": "", "sortType": "1", "themeId": "", "timeRange": "",
            "tourId": "", "type": "", "tag": "",
        }
        body = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
        try:
            r = requests.post(API + url, headers=self._headers(url, body),
                              data=body.encode("utf-8"), timeout=self.timeout)
            return r.json()["result"]["result"]
        except Exception as e:  # noqa: BLE001
            print(f"[showstart_beijing] 抓第{page_no}页失败: {e}")
            return None

    def fetch(self) -> List[Event]:
        if not self._get_token():
            return []
        events: List[Event] = []
        seen = set()
        for pg in range(1, MAX_PAGES + 1):
            rows = self._page(pg)
            if not rows:
                break
            for it in rows:
                title = (it.get("title") or "").strip()
                if not title or title in seen:
                    continue
                seen.add(title)
                start = ""
                st = it.get("showTime") or ""      # "2026/07/18 20:00"
                if len(st) >= 10 and st[:10].count("/") == 2:
                    y, m, d = st[:10].split("/")
                    start = f"{y}-{m}-{d}"
                events.append(Event(
                    title=title[:60], type="演出", source=self.name,
                    official_url="https://www.showstart.com/event/%s" % it.get("id", ""),
                    venue=(it.get("siteName") or "").strip(),
                    start_date=start,
                    price_range=(it.get("price") or "").lstrip("¥"),
                    raw_text=f"{title} {st} {it.get('siteName','')} {it.get('performers','')}",
                ))
            if len(rows) < PAGE_SIZE:
                break
        print(f"[showstart_beijing] 解析到 {len(events)} 条")
        return events
