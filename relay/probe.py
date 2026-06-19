# -*- coding: utf-8 -*-
"""上海家庭活动雷达 · 境内中继探测 v3(腾讯云 SCF · 纯标准库 · 无依赖/令牌)

v3 目标: 拿木偶排期页 perform.aspx + 一个详情页的精确结构(日期/地点/票价)。
关键改动: HTML 片段用 base64 回传 —— 纯 ASCII,聊天框不会再吃掉日期数字。
用法同前: 覆盖代码 → 部署 → 测试 → 把"返回结果"整段复制发回。
"""
import base64
import re
import ssl
import urllib.request

TARGETS = {
    "木偶_排期页": "http://www.sh-puppet.com.cn/perform.aspx",
    "木偶_详情样例": "http://www.sh-puppet.com.cn/perform_detail.aspx?id=792",
}
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
MARK = re.compile(
    r"(news_list|演出时间|演出地点|票价|场次|地点|时间|《|20\d{2}-\d{2}-\d{2}|\d{1,2}月\d{1,2}日)"
)


def _fetch(url):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15, context=ctx) as r:
        return r.geturl(), r.read()


def _decode(raw):
    m = re.search(rb'charset=["\']?\s*([a-zA-Z0-9\-]+)', raw[:3000])
    enc = m.group(1).decode("ascii", "ignore").lower() if m else "utf-8"
    if enc in ("gb2312", "gbk", "gb18030"):
        enc = "gb18030"
    try:
        return raw.decode(enc, "replace"), enc
    except Exception:  # noqa: BLE001
        return raw.decode("utf-8", "replace"), "utf-8?"


def _excerpt(html):
    m = MARK.search(html)
    i = max(0, (m.start() if m else 0) - 200)
    return html[i:i + 2000]


def main_handler(event, context):
    out = {}
    for name, url in TARGETS.items():
        try:
            final, raw = _fetch(url)
            html, enc = _decode(raw)
            frag = _excerpt(html)
            out[name] = {
                "URL": final,
                "编码": enc,
                "原始字节": len(raw),
                "b64": base64.b64encode(frag.encode("utf-8")).decode("ascii"),
            }
        except Exception as e:  # noqa: BLE001
            out[name] = {"错误": repr(e)}
    print("probe v3 done")
    return out
