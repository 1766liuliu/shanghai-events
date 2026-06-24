# -*- coding: utf-8 -*-
"""上海家庭活动雷达 · 境内中继(腾讯云 SCF · 纯标准库 · 无第三方依赖)

职责: 在境内抓 儿艺 + 木偶 的演出排期 → 生成事件列表 → 提交回 GitHub 仓库的
      data/cn_events.json。GitHub Actions 下次跑 main.py 会自动读入(见
      collector/sources/cnrelay.py),全程不碰中国网络。

安全: GitHub 令牌从环境变量 GH_TOKEN 读取(在 SCF「环境变量」里配置,绝不写进代码)。
      · 未设 GH_TOKEN → 只抓取、不提交,返回样例供人工核对解析是否正确(验证模式);
      · 已设 GH_TOKEN → 抓取后用 GitHub Contents API 提交 cn_events.json(上线模式)。
"""
import base64
import datetime
import json
import os
import re
import ssl
import urllib.parse
import urllib.request

GH_TOKEN = os.environ.get("GH_TOKEN", "")
GH_REPO = os.environ.get("GH_REPO", "1766liuliu/shanghai-events")
GH_PATH = "data/cn_events.json"
GH_BRANCH = "main"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
      "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TODAY = datetime.date.today()


def _ctx():
    c = ssl.create_default_context()
    c.check_hostname = False
    c.verify_mode = ssl.CERT_NONE
    return c


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20, context=_ctx()) as r:
        return r.read()


def _decode(raw):
    m = re.search(rb'charset=["\']?\s*([a-zA-Z0-9\-]+)', raw[:3000])
    enc = m.group(1).decode("ascii", "ignore").lower() if m else "utf-8"
    if enc in ("gb2312", "gbk", "gb18030"):
        enc = "gb18030"
    try:
        return raw.decode(enc, "replace")
    except Exception:  # noqa: BLE001
        return raw.decode("utf-8", "replace")


def _strip(s):
    return re.sub(r"\s+", " ", re.sub(r"(?s)<[^>]+>", " ", s)).strip()


def _infer_date(text):
    """'7月27日 10:00...' → 'YYYY-MM-DD'(年份推断: 月份≥本月用今年,否则明年)。"""
    m = re.search(r"(\d{1,2})\s*月\s*(\d{1,2})\s*日", text)
    if not m:
        return ""
    mo, da = int(m.group(1)), int(m.group(2))
    yr = TODAY.year if mo >= TODAY.month else TODAY.year + 1
    try:
        return datetime.date(yr, mo, da).isoformat()
    except ValueError:
        return ""


# ---------------- 上海儿童艺术剧场 ----------------
def scrape_shcat():
    base = "https://www.shcat.com.cn"
    html = _decode(_get(base + "/zh/programs?status=ongoing"))
    out = []
    for blk in re.split(r'class="border-b-brand text-brand flex flex-col', html)[1:]:
        ma = re.search(r'<a class="text-lg" href="(/zh/programs/\d+)">([^<]+)</a>', blk)
        if not ma:
            continue
        href, title = ma.group(1), _strip(ma.group(2))
        d = re.search(r"(\d{4}-\d{2}-\d{2})(?:\s*-\s*(\d{4}-\d{2}-\d{2}))?", blk)
        start = d.group(1) if d else ""
        end = d.group(2) if (d and d.group(2) and d.group(2) != start) else ""
        loc = re.search(r"地点\s*[|｜]\s*([^\n<｜]+)", blk)
        age = re.search(r"适龄观众\s*[|｜]\s*([^\n<｜]+)", blk)
        venue = "上海儿童艺术剧场"
        if loc:
            venue += "·" + _strip(loc.group(1))
        out.append({
            "title": title, "type": "演出", "source": "shcat",
            "official_url": base + href, "venue": venue,
            "start_date": start, "end_date": end,
            "age_range": _strip(age.group(1)) if age else "",
            "kid_friendly": True,
        })
    return out


# ---------------- 上海木偶剧团 ----------------
def scrape_puppet():
    base = "http://www.sh-puppet.com.cn/"
    html = _decode(_get(base + "perform.aspx"))
    out = []
    for blk in re.split(r'class="\s*program border-bottom"', html)[1:]:
        ma = re.search(r'href="(perform_detail\.aspx\?id=\d+)"\s+title="([^"]+)"', blk)
        if not ma:
            continue
        href, title = ma.group(1), _strip(ma.group(2))
        t = re.search(r'class="performTime"[^>]*>([^<]+)<', blk)
        start = _infer_date(t.group(1)) if t else ""
        loc = re.search(r"icon-location\.png[^>]*>\s*([^<]+)<", blk)
        price = re.search(r"icon-price\.png[^>]*>\s*([^<]+)<", blk)
        venue = "上海木偶剧团"
        if loc:
            venue += "·" + _strip(loc.group(1))
        out.append({
            "title": title, "type": "演出", "source": "sh-puppet",
            "official_url": urllib.parse.urljoin(base, href), "venue": venue,
            "start_date": start,
            "price_range": _strip(price.group(1)) if price else "",
            "kid_friendly": True,
        })
    return out


# ---------------- 提交回 GitHub ----------------
def _commit(events):
    api = "https://api.github.com/repos/%s/contents/%s" % (GH_REPO, GH_PATH)
    hdr = {"Authorization": "Bearer " + GH_TOKEN, "User-Agent": "radar-relay",
           "Accept": "application/vnd.github+json"}
    sha = None
    try:
        req = urllib.request.Request(api + "?ref=" + GH_BRANCH, headers=hdr)
        with urllib.request.urlopen(req, timeout=20, context=_ctx()) as r:
            sha = json.load(r).get("sha")
    except Exception:  # noqa: BLE001
        pass  # 文件首次创建时不存在,无 sha
    body = json.dumps(events, ensure_ascii=False, indent=2).encode("utf-8")
    payload = {
        "message": "中继更新 cn_events.json (%d条) %s" % (
            len(events), datetime.datetime.now().strftime("%Y-%m-%d %H:%M")),
        "content": base64.b64encode(body).decode("ascii"),
        "branch": GH_BRANCH,
    }
    if sha:
        payload["sha"] = sha
    req = urllib.request.Request(
        api, data=json.dumps(payload).encode("utf-8"),
        headers={**hdr, "Content-Type": "application/json"}, method="PUT")
    with urllib.request.urlopen(req, timeout=30, context=_ctx()) as r:
        return r.status


def main_handler(event, context):
    events, errors = [], {}
    for fn in (scrape_shcat, scrape_puppet):
        try:
            events += fn()
        except Exception as e:  # noqa: BLE001
            errors[fn.__name__] = repr(e)
    result = {"抓取条数": len(events), "错误": errors, "样例": events[:6]}
    if not GH_TOKEN:
        result["提交状态"] = "验证模式(未设GH_TOKEN,只抓取不提交)"
    elif not events:
        # 失败不空覆盖:两站都抓挂时,保留仓库里上次的好数据,绝不用空列表覆盖
        result["提交状态"] = "本次0条,跳过提交(保留上次数据)"
    else:
        try:
            result["提交状态"] = _commit(events)
        except Exception as e:  # noqa: BLE001
            result["提交状态"] = "提交失败: " + repr(e)
    print(json.dumps(result, ensure_ascii=False)[:200])
    return result
