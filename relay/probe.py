# -*- coding: utf-8 -*-
"""上海家庭活动雷达 · 境内中继探测 v5(腾讯云 SCF · 纯标准库)

主攻文化上海云: 拿回主页真实 HTML(看重定向/脚本写法/内嵌数据/接口主机),
顺带给大河票务最后一次机会(http + 长超时)。HTML 用 base64 回传。
"""
import base64
import re
import ssl
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def _ctx():
    c = ssl.create_default_context()
    c.check_hostname = False
    c.verify_mode = ssl.CERT_NONE
    return c


def _get(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Referer": url})
    with urllib.request.urlopen(req, timeout=timeout, context=_ctx()) as r:
        return r.geturl(), r.read()


def _decode(raw):
    m = re.search(rb'charset=["\']?\s*([a-zA-Z0-9\-]+)', raw[:3000])
    enc = m.group(1).decode("ascii", "ignore").lower() if m else "utf-8"
    if enc in ("gb2312", "gbk", "gb18030"):
        enc = "gb18030"
    try:
        return raw.decode(enc, "replace")
    except Exception:  # noqa: BLE001
        return raw.decode("utf-8", "replace")


def _b64(s):
    return base64.b64encode(s.encode("utf-8")).decode("ascii")


def probe_dahepiao():
    try:
        final, raw = _get("http://www.dahepiao.com/", timeout=22)
    except Exception as e:  # noqa: BLE001
        return {"错误": repr(e)}
    html = _decode(raw)
    mk = re.search(r"(演出|话剧|上海|\d+\s*元|\d{4}-\d{2}-\d{2})", html)
    i = max(0, (mk.start() if mk else 0) - 200)
    return {"最终URL": final, "HTML字节": len(raw), "片段_b64": _b64(html[i:i + 1500])}


def probe_culturalcloud():
    try:
        final, raw = _get("https://www.culturalcloud.net/", timeout=15)
    except Exception as e:  # noqa: BLE001
        return {"错误": repr(e)}
    html = _decode(raw)
    scripts = re.findall(r"<script\b[^>]*>", html, re.I)
    hosts = sorted(set(re.findall(r"https?://[a-zA-Z0-9.\-]+", html)))
    paths = sorted(set(re.findall(r'["\'](/[A-Za-z0-9_][A-Za-z0-9_/\-]{3,40})["\']', html)))
    return {
        "最终URL": final,
        "HTML字节": len(raw),
        "script标签数": len(scripts),
        "script标签样例": scripts[:12],
        "页面内主机": hosts[:25],
        "页面内路径样例": paths[:25],
        "HTML头部_b64": _b64(html[:3500]),
    }


def main_handler(event, context):
    out = {"文化上海云": probe_culturalcloud(), "大河票务": probe_dahepiao()}
    print("probe v5 done")
    return out
