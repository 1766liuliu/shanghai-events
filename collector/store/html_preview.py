"""HTML 预览导出 —— 生成可直接双击在浏览器查看的活动清单。

重磅活动置顶、倒计时、分类色条、亲子徽章、档期待核实标记。
"""
from __future__ import annotations

import datetime
import html
import os
from typing import List

from models import Event

DEFAULT_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "活动预览.html"
)

CAT_COLOR = {"体育": "#e4572e", "展会": "#1f6feb", "演出": "#9b51e0"}
DEFAULT_COLOR = "#16a34a"

HEAD = """<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>上海家庭活动雷达</title>
<style>
 *{box-sizing:border-box}
 body{font-family:-apple-system,"PingFang SC","Helvetica Neue",sans-serif;background:#f0f2f5;margin:0;color:#1a1a1a}
 .wrap{max-width:760px;margin:0 auto;padding:0 16px 48px}
 header{background:linear-gradient(135deg,#1f6feb,#7c3aed);color:#fff;padding:28px 24px;border-radius:0 0 20px 20px;margin:0 -16px 18px;box-shadow:0 6px 20px rgba(31,111,235,.25)}
 header h1{margin:0;font-size:23px;letter-spacing:.5px}
 header .sub{margin-top:8px;font-size:13px;opacity:.9}
 .filters{position:sticky;top:0;background:#f0f2f5;padding:12px 0;z-index:5;white-space:nowrap;overflow-x:auto}
 .filters button{border:0;background:#fff;color:#555;padding:7px 16px;border-radius:20px;margin-right:8px;font-size:13px;cursor:pointer;box-shadow:0 1px 3px rgba(0,0,0,.06)}
 .filters button.on{background:#1f6feb;color:#fff}
 .card{background:#fff;border-radius:14px;padding:16px 18px;margin-bottom:12px;border-left:4px solid #ccc;box-shadow:0 1px 4px rgba(0,0,0,.06);transition:transform .12s,box-shadow .12s}
 .card:hover{transform:translateY(-2px);box-shadow:0 6px 18px rgba(0,0,0,.10)}
 .top{display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap}
 .pill{font-size:12px;padding:2px 10px;border-radius:20px;font-weight:600}
 .cd{background:#fff0e6;color:#e4572e}
 .cd.soon{background:#e4572e;color:#fff}
 .kid{background:#fff3d6;color:#a86400}
 .feat{background:#fde8ff;color:#9b1ec0}
 .nw{background:#e6f7ed;color:#1a7f4b}
 .cat{color:#fff}
 .title{font-weight:600;font-size:16px;line-height:1.4}
 .title a{color:#1a1a1a;text-decoration:none}
 .title a:hover{color:#1f6feb}
 .meta{color:#777;font-size:13px;margin-top:8px;display:flex;gap:14px;flex-wrap:wrap}
 .note{color:#b08900;font-size:12px;margin-top:6px}
 .price{color:#e4572e;font-size:13px;margin-top:4px}
 .group{font-size:14px;font-weight:700;color:#666;margin:22px 4px 10px}
 .empty{padding:60px 0;text-align:center;color:#999}
 .snap{margin-top:12px;font-size:12px;opacity:.95;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
 .refresh{border:0;background:rgba(255,255,255,.22);color:#fff;padding:6px 16px;border-radius:16px;font-size:12px;cursor:pointer}
 .refresh:active{background:rgba(255,255,255,.42)}
</style></head><body><div class="wrap">
<header><h1>📡 上海家庭活动雷达</h1>
<div class="sub">共 __COUNT__ 条 · 🆕最新 __NEW__ · 🔥重磅 __FEAT__ · 👨‍👩‍👧亲子优先</div>
<div class="snap">📅 数据截至 __NOW__ · 离线快照
<button class="refresh" onclick="location.replace(location.href.split('?')[0]+'?t='+Date.now())" title="重新读取最新文件(绕过缓存)">🔄 刷新本页</button></div></header>
<div class="filters">
 <button class="on" onclick="flt(this,'all')">全部</button>
 <button onclick="flt(this,'new')">🆕 最新</button>
 <button onclick="flt(this,'feat')">🔥 重磅</button>
 <button onclick="flt(this,'kid')">👨‍👩‍👧 亲子</button>
 <button onclick="flt(this,'体育')">体育</button>
 <button onclick="flt(this,'展会')">展会</button>
 <button onclick="flt(this,'演出')">演出</button>
</div>
<div id="list">
"""

TAIL = """</div>
<div class="empty" id="empty" style="display:none">该分类下暂无活动</div>
</div>
<script>
function flt(btn,key){
 document.querySelectorAll('.filters button').forEach(b=>b.classList.remove('on'));
 btn.classList.add('on');
 let shown=0;
 document.querySelectorAll('.card').forEach(c=>{
   const ok = key==='all' || (key==='new'? c.dataset.new==='1'
            : key==='feat'? c.dataset.feat==='1'
            : key==='kid'? c.dataset.kid==='1' : c.dataset.type===key);
   c.style.display = ok?'block':'none';
   if(ok) shown++;
 });
 document.querySelectorAll('.group').forEach(g=>g.style.display = key==='all'?'block':'none');
 document.getElementById('empty').style.display = shown? 'none':'block';
}
</script></body></html>"""


def _fmt_date(start: str, end: str) -> str:
    if not start:
        return "档期待定"
    try:
        s = datetime.date.fromisoformat(start)
    except ValueError:
        return start
    if end and end != start:
        try:
            e = datetime.date.fromisoformat(end)
            if e.month == s.month:
                return f"{s.month}月{s.day}–{e.day}日"
            return f"{s.month}月{s.day}日–{e.month}月{e.day}日"
        except ValueError:
            pass
    return f"{s.month}月{s.day}日"


def _countdown(start: str, end: str, today: datetime.date):
    if not start:
        return None
    try:
        d = (datetime.date.fromisoformat(start) - today).days
    except ValueError:
        return None
    if d < 0:
        # 可能进行中(结束日期未过)
        if end:
            try:
                if datetime.date.fromisoformat(end) >= today:
                    return ("进行中", True)
            except ValueError:
                pass
        return None
    if d == 0:
        return ("今天", True)
    if d == 1:
        return ("明天", True)
    return (f"{d}天后", d <= 14)


def _card(e: Event, today: datetime.date) -> str:
    color = CAT_COLOR.get(e.type, DEFAULT_COLOR)
    title = html.escape(e.title)
    if e.official_url:
        title = f'<a href="{html.escape(e.official_url)}" target="_blank">{title}</a>'

    cutoff = (today - datetime.timedelta(days=6)).isoformat()
    is_new = bool(e.first_seen and e.first_seen >= cutoff)
    pills = [f'<span class="pill cat" style="background:{color}">{e.type}</span>']
    if is_new:
        pills.append('<span class="pill nw">🆕 最新</span>')
    if e.featured:
        pills.append('<span class="pill feat">🔥 重磅</span>')
    cd = _countdown(e.start_date, e.end_date, today)
    if cd:
        pills.append(f'<span class="pill cd {"soon" if cd[1] else ""}">{cd[0]}</span>')
    if e.kid_friendly:
        label = "👨‍👩‍👧 亲子" + (f" {e.age_range}" if e.age_range else "")
        pills.append(f'<span class="pill kid">{html.escape(label)}</span>')

    meta = [f"📅 {_fmt_date(e.start_date, e.end_date)}"]
    if e.venue:
        meta.append(f"📍 {html.escape(e.venue)}")
    note = f'<div class="note">⚠ {html.escape(e.note)}</div>' if e.note else ""
    price = f'<div class="price">{html.escape(e.price_range)}</div>' if e.price_range else ""

    return (
        f'<div class="card" style="border-left-color:{color}" '
        f'data-type="{e.type}" data-kid="{1 if e.kid_friendly else 0}" '
        f'data-feat="{1 if e.featured else 0}" data-new="{1 if is_new else 0}">'
        f'<div class="top">{"".join(pills)}</div>'
        f'<div class="title">{title}</div>'
        f'<div class="meta">{"  ".join(meta)}</div>{note}{price}</div>'
    )


def save(events: List[Event], path: str = DEFAULT_PATH) -> None:
    path = os.path.abspath(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    today = datetime.date.today()

    # 排序: 重磅优先 → 有日期早的优先 → 无日期最后
    events = sorted(events, key=lambda e: (not e.featured, e.start_date or "9999-99-99"))
    dated = [e for e in events if e.start_date]
    undated = [e for e in events if not e.start_date]

    body = []
    if dated:
        body.append('<div class="group">📌 有确定档期</div>')
        body += [_card(e, today) for e in dated]
    if undated:
        body.append('<div class="group">🎪 常态演出 / 档期待核实</div>')
        body += [_card(e, today) for e in undated]

    feat = sum(1 for e in events if e.featured)
    cutoff = (today - datetime.timedelta(days=6)).isoformat()
    n_new = sum(1 for e in events if e.first_seen and e.first_seen >= cutoff)
    head = (
        HEAD.replace("__COUNT__", str(len(events)))
        .replace("__FEAT__", str(feat))
        .replace("__NEW__", str(n_new))
        .replace("__NOW__", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(head + "\n".join(body) + TAIL)
    print(f"[html_preview] 已生成 → {path}")
