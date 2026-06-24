# -*- coding: utf-8 -*-
"""沪上遛遛 · 每周精选邮件 —— 读 events.json → Chromium 渲染海报风 PDF → 邮件发送。

机密只从环境变量(GitHub Secrets)读,绝不写进代码/公开仓库:
  MAIL_USER = 发信邮箱(Gmail/QQ 等)   MAIL_PASS = 应用专用密码/授权码(非登录密码)
  MAIL_TO   = 收件人(逗号分隔)   MAIL_HOST = SMTP服务器(可选,默认按发信邮箱域名自动选)
未配置 MAIL_* 时只生成 PDF、不发信(便于本地测试)。
渲染用 Playwright(无头 Chromium),艺术字体走 Google Fonts。
"""
import base64
import datetime
import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from html import escape

ROOT = os.path.join(os.path.dirname(__file__), "..")
EVENTS = os.path.join(ROOT, "events.json")
OUT = os.path.join(ROOT, "data", "digest.pdf")
HERO = os.path.join(ROOT, "assets", "hero.jpg")
SITE = "https://1766liuliu.github.io/shanghai-events/"
SEC_COLOR = {"本周开票": "#4da3ff", "亲子精选": "#ff8a5b",
             "最新上架": "#4dd6a0", "重磅活动": "#ff5d8f"}


def _today():
    return datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).date()


def _days(s, today):
    try:
        return (datetime.date.fromisoformat(s) - today).days
    except Exception:  # noqa: BLE001
        return None


def _upcoming(e, today, win):
    s = e.get("start_date")
    d = _days(s, today) if s else None
    if d is not None and 0 <= d <= win:
        return True
    en = e.get("end_date")
    if d is not None and d < 0 and en and en >= today.isoformat():
        return True
    return False


def _fmtdate(e, today):
    s, en = e.get("start_date"), e.get("end_date")
    if not s:
        return "档期待定"
    d = _days(s, today)
    if d is not None and d < 0 and en and en >= today.isoformat():
        ep = en.split("-")
        return "演至 %d月%d日" % (int(ep[1]), int(ep[2]))
    p = s.split("-")
    base = "%d月%d日" % (int(p[1]), int(p[2]))
    if en and en != s:
        ep = en.split("-")
        base += ("–%d日" % int(ep[2])) if ep[1] == p[1] else ("–%d月%d日" % (int(ep[1]), int(ep[2])))
    return base


def select(data, today):
    evs = data.get("events", [])
    cut = (today - datetime.timedelta(days=6)).isoformat()
    kid = [e for e in evs if e.get("kid_friendly") and not e.get("kid_unfit") and _upcoming(e, today, 14)]
    new = [e for e in evs if e.get("first_seen", "") >= cut and _upcoming(e, today, 30)]
    feat = [e for e in evs if e.get("featured") and _upcoming(e, today, 30)]
    ticket = []
    for e in evs:
        ot = e.get("open_ticket_time")
        d = _days(ot, today) if ot else None
        if d is not None and 0 <= d <= 7:
            ticket.append(e)
    kd = lambda e: e.get("start_date") or "9999"  # noqa: E731
    return [
        ("本周开票", sorted(ticket, key=lambda e: e.get("open_ticket_time") or "")),
        ("亲子精选", sorted(kid, key=kd)[:8]),
        ("最新上架", sorted(new, key=kd)[:6]),
        ("重磅活动", sorted(feat, key=kd)[:6]),
    ]


SKYLINE = ('<svg class="sky" viewBox="0 0 800 84" preserveAspectRatio="none">'
           '<g fill="rgba(8,5,24,0.45)">'
           '<rect x="0" y="52" width="58" height="32"/><rect x="62" y="40" width="34" height="44"/>'
           '<rect x="102" y="58" width="44" height="26"/><rect x="150" y="32" width="26" height="52"/>'
           '<rect x="182" y="50" width="50" height="34"/><rect x="238" y="60" width="40" height="24"/>'
           '<rect x="300" y="46" width="30" height="38"/>'
           '<rect x="392" y="36" width="8" height="48"/><circle cx="396" cy="30" r="11"/><circle cx="396" cy="54" r="7"/>'
           '<rect x="430" y="42" width="46" height="42"/><rect x="482" y="28" width="24" height="56"/>'
           '<rect x="512" y="54" width="48" height="30"/><rect x="566" y="44" width="32" height="40"/>'
           '<rect x="604" y="58" width="46" height="26"/><rect x="656" y="38" width="26" height="46"/>'
           '<rect x="688" y="52" width="52" height="32"/><rect x="744" y="46" width="56" height="38"/>'
           '</g></svg>')

PAGE = """<!doctype html><html lang="zh"><head><meta charset="utf-8">
<style>
@import url('https://fonts.googleapis.com/css2?family=ZCOOL+KuaiLe&family=Noto+Sans+SC:wght@400;500;700&display=swap');
@page{size:A4;margin:0}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Noto Sans SC',sans-serif;color:#fff;-webkit-print-color-adjust:exact;print-color-adjust:exact;
 background:linear-gradient(158deg,#140c33 0%,#291552 30%,#561f63 62%,#9c2f4c 100%)}
.hero{height:332px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:0 40px;background:__HEROBG__}
.brand{font-family:'ZCOOL KuaiLe',cursive;font-size:84px;line-height:1;letter-spacing:9px;text-shadow:0 4px 28px rgba(0,0,0,.75)}
.tag{margin-top:16px;font-size:16px;letter-spacing:5px;color:#ffe2b3;font-weight:500;text-shadow:0 2px 12px rgba(0,0,0,.7)}
.dt{margin-top:10px;font-size:13px;letter-spacing:3px;color:rgba(255,255,255,.88);text-shadow:0 2px 12px rgba(0,0,0,.7)}
.wrap{padding:18px 28px 26px}
.sec{margin-top:20px;border-radius:16px;padding:14px 14px 4px;border:1px solid rgba(255,255,255,.09)}
.sh{display:inline-block;font-family:'ZCOOL KuaiLe',cursive;font-size:23px;letter-spacing:2px;color:#fff;padding:7px 22px;border-radius:30px;margin-bottom:13px}
.cols{column-count:2;column-gap:13px}
.it{break-inside:avoid;-webkit-column-break-inside:avoid;page-break-inside:avoid;background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.13);border-radius:12px;padding:12px 14px;margin:0 0 12px}
.itt{font-size:14.5px;font-weight:700;line-height:1.45}
.itt a{color:#fff;text-decoration:none}
.itm{margin-top:6px;font-size:11.5px;color:rgba(255,255,255,.8);line-height:1.5}
.ft{text-align:center;padding:18px 20px 30px;font-size:11px;letter-spacing:1px;color:rgba(255,255,255,.55)}
.ft a{color:rgba(255,255,255,.8)}
</style></head><body>
<div class="hero"><div class="brand">沪上遛遛</div>
<div class="tag">上海亲子 · 演出 · 展会 · 赛事</div>
<div class="dt">__DATE__</div></div>
<div class="wrap">__CONTENT__</div>
<div class="ft">数据更新于 __GEN__ &nbsp;·&nbsp; 在线版 <a href="__SITE__">1766liuliu.github.io/shanghai-events</a></div>
</body></html>"""


TEX = {
    "本周开票": "repeating-linear-gradient(45deg,rgba(77,163,255,.12) 0 2px,transparent 2px 13px)",
    "亲子精选": "radial-gradient(rgba(255,138,91,.17) 1.4px,transparent 1.6px)",
    "最新上架": ("repeating-linear-gradient(0deg,rgba(77,214,160,.11) 0 1px,transparent 1px 16px),"
                 "repeating-linear-gradient(90deg,rgba(77,214,160,.11) 0 1px,transparent 1px 16px)"),
    "重磅活动": "repeating-linear-gradient(-45deg,rgba(255,93,143,.12) 0 2px,transparent 2px 13px)",
}


def _herobg():
    try:
        with open(HERO, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        return ("linear-gradient(180deg,rgba(16,9,38,.42),rgba(16,9,38,.88)),"
                "url(data:image/jpeg;base64,%s) center/cover" % b64)
    except Exception:  # noqa: BLE001
        return "linear-gradient(158deg,#140c33,#3a1c66 55%,#7c2a73)"


def build_html(sections, today, gen):
    seen, blocks = set(), []
    for name, items in sections:
        rows = [e for e in items if e.get("title") and e["title"] not in seen]
        if not rows:
            continue
        col = SEC_COLOR.get(name, "#9aa0ff")
        its = []
        for e in rows:
            seen.add(e["title"])
            t = escape(e["title"])
            url = e.get("official_url", "")
            title = '<a href="%s">%s</a>' % (escape(url), t) if url else t
            bits = [_fmtdate(e, today)]
            if e.get("venue") and e["venue"] != e["title"]:
                bits.append(escape(e["venue"]))
            if e.get("price_range"):
                bits.append(escape(e["price_range"]))
            ot = e.get("open_ticket_time")
            if name == "本周开票" and ot:
                bits.insert(0, "开票 " + escape(ot))
            its.append('<div class="it" style="border-left:4px solid %s">'
                       '<div class="itt">%s</div><div class="itm">%s</div></div>'
                       % (col, title, " · ".join(bits)))
        size = "background-size:15px 15px;" if name == "亲子精选" else ""
        blocks.append('<div class="sec" style="background-image:%s;%s">'
                      '<span class="sh" style="background:%s;box-shadow:0 7px 22px %s66">%s（%d）</span>'
                      '<div class="cols">%s</div></div>'
                      % (TEX.get(name, ""), size, col, col, name, len(rows), "".join(its)))
    content = "".join(blocks) or '<div class="it">本周暂无精选,点下方在线版查看全部。</div>'
    datestr = "%d年%d月%d日 · 本周精选" % (today.year, today.month, today.day)
    html = PAGE
    for k, v in (("__HEROBG__", _herobg()), ("__DATE__", datestr), ("__CONTENT__", content),
                 ("__GEN__", escape(gen)), ("__SITE__", SITE)):
        html = html.replace(k, v)
    return html


def render_pdf(html):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page()
        pg.set_content(html, wait_until="networkidle")
        try:
            pg.evaluate("document.fonts.ready")
        except Exception:  # noqa: BLE001
            pass
        pg.pdf(path=OUT, format="A4", print_background=True,
               margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
        b.close()
    print("[digest] 已渲染海报 PDF →", OUT)


def send(today):
    user, pw, to = (os.environ.get("MAIL_USER"), os.environ.get("MAIL_PASS"),
                    os.environ.get("MAIL_TO"))
    if not (user and pw and to):
        print("[digest] 未配置 MAIL_USER/MAIL_PASS/MAIL_TO,只生成 PDF 不发信")
        return
    recipients = [x.strip() for x in to.replace(";", ",").split(",") if x.strip()]
    msg = EmailMessage()
    msg["Subject"] = "沪上遛遛 · 本周精选（%d/%d）" % (today.month, today.day)
    msg["From"] = user
    msg["To"] = ", ".join(recipients)
    msg.set_content("本周上海亲子 / 演出 / 展会 / 赛事精选见附件 PDF。\n在线版:" + SITE)
    with open(OUT, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf",
                           filename="沪上遛遛_本周精选_%s.pdf" % today.strftime("%Y%m%d"))
    host = os.environ.get("MAIL_HOST") or {
        "gmail.com": "smtp.gmail.com", "qq.com": "smtp.qq.com",
        "163.com": "smtp.163.com", "126.com": "smtp.126.com",
        "foxmail.com": "smtp.qq.com", "outlook.com": "smtp-mail.outlook.com",
    }.get(user.split("@")[-1].lower(), "smtp.gmail.com")
    with smtplib.SMTP_SSL(host, 465, context=ssl.create_default_context()) as s:
        s.login(user, pw)
        s.send_message(msg)
    print("[digest] 已通过 %s 发送给:" % host, ", ".join(recipients))


def main():
    today = _today()
    with open(EVENTS, encoding="utf-8") as f:
        data = json.load(f)
    render_pdf(build_html(select(data, today), today, data.get("generatedAt", "")))
    send(today)


if __name__ == "__main__":
    main()
