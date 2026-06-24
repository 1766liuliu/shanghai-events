# -*- coding: utf-8 -*-
"""沪上遛遛 · 每周精选邮件 —— 读 events.json → 生成 PDF → QQ 邮箱 SMTP 发给家人。

机密只从环境变量(GitHub Secrets)读,绝不写进代码/公开仓库:
  MAIL_USER = 发信邮箱(Gmail/QQ 等)   MAIL_PASS = 应用专用密码/授权码(非登录密码)
  MAIL_TO   = 收件人(逗号分隔)   MAIL_HOST = SMTP服务器(可选,默认按发信邮箱域名自动选)
未配置 MAIL_* 时只生成 PDF、不发信(便于本地测试)。
"""
import datetime
import json
import os
import smtplib
import ssl
from email.message import EmailMessage
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

ROOT = os.path.join(os.path.dirname(__file__), "..")
EVENTS = os.path.join(ROOT, "events.json")
OUT = os.path.join(ROOT, "data", "digest.pdf")
SITE = "https://c18531171777-creator.github.io/shanghai-events/"
FONT = "STSong-Light"
pdfmetrics.registerFont(UnicodeCIDFont(FONT))


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
    en = e.get("end_date")  # 在演(已开始未结束)
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
        ("亲子精选", sorted(kid, key=kd)[:10]),
        ("最新上架", sorted(new, key=kd)[:8]),
        ("重磅活动", sorted(feat, key=kd)[:6]),
    ]


def build_pdf(sections, today, gen):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    doc = SimpleDocTemplate(OUT, pagesize=A4, title="沪上遛遛 本周精选",
                            topMargin=18 * mm, bottomMargin=16 * mm,
                            leftMargin=16 * mm, rightMargin=16 * mm)
    H1 = ParagraphStyle("H1", fontName=FONT, fontSize=20, leading=26,
                        textColor=colors.HexColor("#7c3aed"))
    SUB = ParagraphStyle("SUB", fontName=FONT, fontSize=10, leading=14,
                         textColor=colors.grey)
    H2 = ParagraphStyle("H2", fontName=FONT, fontSize=14, leading=20,
                        textColor=colors.HexColor("#1f6feb"), spaceBefore=14, spaceAfter=4)
    IT = ParagraphStyle("IT", fontName=FONT, fontSize=12, leading=17, spaceBefore=13)
    META = ParagraphStyle("META", fontName=FONT, fontSize=9.5, leading=13,
                          textColor=colors.grey, leftIndent=14, spaceAfter=2)
    story = [Paragraph("沪上遛遛 · 本周精选", H1),
             Paragraph("%d年%d月%d日 · 上海亲子 / 演出 / 展会 / 赛事"
                       % (today.year, today.month, today.day), SUB),
             Spacer(1, 4)]
    seen, any_item = set(), False
    for name, items in sections:
        rows = [e for e in items if e.get("title") and e["title"] not in seen]
        if not rows:
            continue
        any_item = True
        story.append(Paragraph(name, H2))
        for e in rows:
            seen.add(e["title"])
            t = escape(e["title"])
            url = e.get("official_url", "")
            link = '<a href="%s" color="#1f6feb">%s</a>' % (escape(url), t) if url else t
            bullet = '<font color="#7c3aed">●</font> '
            story.append(Paragraph(bullet + link, IT))
            bits = [_fmtdate(e, today)]
            if e.get("venue") and e["venue"] != e["title"]:
                bits.append(escape(e["venue"]))
            if e.get("price_range"):
                bits.append(escape(e["price_range"]))
            ot = e.get("open_ticket_time")
            if name == "本周开票" and ot:
                bits.insert(0, "开票 " + escape(ot))
            story.append(Paragraph(" | ".join(bits), META))
    if not any_item:
        story.append(Paragraph("本周暂无精选(数据更新中,点下方在线版查看全部)。", IT))
    story.append(Spacer(1, 12))
    story.append(Paragraph("数据更新于 %s · 在线版 %s" % (escape(gen), SITE), SUB))
    doc.build(story)
    print("[digest] 已生成 PDF →", OUT)


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
    build_pdf(select(data, today), today, data.get("generatedAt", ""))
    send(today)


if __name__ == "__main__":
    main()
