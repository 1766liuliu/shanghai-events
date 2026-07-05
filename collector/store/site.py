"""在线托管版页面 —— 生成 site/ 目录(index.html + events.json)。

页面交互(三个维度):
  · 顶部"选项卡" = 形态(🎫近期 / 🎭演出 / 🔥年度展 / 🏛场馆 / 🏢行业),一次只看一区,直观;
  · 第二行"搜索框" = 关键字实时过滤(跨选项卡全局搜 标题/场馆/标签/在演节目);
  · 第三行"筛选" = 属性(全部/最新/亲子),在当前区内再筛。
数据由独立 events.json 提供(JS 实时 fetch),刷新即拉最新。
"演出"区收所有临时演出(演唱会/音乐会/相声/脱口秀/livehouse/话剧/音乐节),让文娱浮出长列表。
注:"档期待定的临时活动"已在采集层(freshness)丢弃,页面不再有"待核实"区。
"""
from __future__ import annotations

import datetime
import json
import os
from typing import List

from models import Event

# 输出到仓库根目录(GitHub Pages 从 main/root 提供;Actions 在此运行)
SITE_DIR = os.path.join(os.path.dirname(__file__), "..", "..")

PUBLIC_FIELDS = [
    "title", "type", "venue", "district", "start_date", "end_date",
    "open_ticket_time", "price_range", "kid_friendly", "age_range",
    "tags", "official_url", "featured", "note", "first_seen", "kind",
    "audience", "kid_unfit", "sessions",
]

# 场馆核心名(用于把"已抓到、在该场馆的活动"交叉引用到场馆卡片的"近期在演")
CORES = [
    "马戏城", "儿童艺术剧场", "木偶剧团", "天文馆", "自然博物馆", "科技馆",
    "玻璃博物馆", "大剧院", "东方艺术中心", "音乐厅", "上海博物馆", "浦东美术馆",
    "中华艺术宫", "当代艺术博物馆", "龙美术馆", "世博会博物馆", "海洋水族馆",
    "野生动物园", "汽车博物馆", "航海博物馆", "西岸美术馆", "文化广场",
    "宛平", "天蟾", "梅赛德斯", "虹口足球场", "西岸大剧院", "东方体育中心",
]

# 北京版场馆核心名(与上面 CORES 完全独立;每次调用只对同城市事件列表生效,不会串城)
CORES_BJ = [
    "国家大剧院", "保利剧院", "首都剧场", "德云社剧场", "国家体育场", "工人体育场",
    "Livehouse", "国家博物馆", "中国美术馆", "798艺术区", "天桥艺术中心",
    "老舍茶馆", "红剧场", "刘老根大舞台", "曹禺剧场",
    "国家话剧院", "世纪剧院",
    "北展剧场", "朝阳剧场", "首都博物馆", "故宫", "中国科学技术馆",
    "国家自然博物馆", "五棵松", "首都体育馆",
    "愚公移山", "疆进酒", "蜂巢剧场", "繁星戏剧村",
    "国家会议中心", "中国国际展览中心", "水立方", "北京天文馆",
    "鼓楼西剧场", "隆福剧场", "77剧场",
]

INDEX_HTML = r"""<!doctype html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="apple-mobile-web-app-capable" content="yes">
<title>1766一起遛遛</title>
<style>
 :root{--bg:#f0f2f5;--card:#fff;--text:#1a1a1a;--muted:#6b7280;--hint:#9aa0a6;--line:#e6e9ee;--tab:#e9ecf1;--tabtx:#555;--fltr:#fff;--fltrtx:#555;
  --cd:#fff0e6;--cdtx:#e4572e;--kid:#fff3d6;--kidtx:#9a6a00;--feat:#fbe6ff;--feattx:#9b1ec0;--nw:#e6f7ed;--nwtx:#1a7f4b;--note:#9a7400;--price:#e4572e;
  --prog:#f1f8f3;--progtx:#23503a;--progb:#1a7f4b;--proglk:#1a6fc0;--more:#eef2ff;--moretx:#1f6feb;--date:#eaf1ff;--datetx:#2563c9;--vic:#eaf1ff;--hl:#fff7ed;--hltx:#b45309;--hlb:#fde6c8}
 @media(prefers-color-scheme:dark){:root{--bg:#15171a;--card:#1e2126;--text:#e9eaec;--muted:#9aa0a6;--hint:#71767d;--line:#2b2f36;--tab:#262a31;--tabtx:#b8bcc2;--fltr:#1e2126;--fltrtx:#b8bcc2;
  --cd:#3a2417;--cdtx:#ff9d77;--kid:#362c12;--kidtx:#f0c674;--feat:#33203a;--feattx:#e8a0f5;--nw:#12301f;--nwtx:#5fc98a;--note:#e0b15a;--price:#ff9d77;
  --prog:#16241c;--progtx:#c3e6d1;--progb:#5fc98a;--proglk:#82bbf2;--more:#222b3b;--moretx:#82bbf2;--date:#1b2433;--datetx:#82bbf2;--vic:#1b2433;--hl:#33270f;--hltx:#f0b86e;--hlb:#574023}}
 *{box-sizing:border-box}
 body{font-family:-apple-system,"PingFang SC","Helvetica Neue",sans-serif;background:var(--bg);margin:0;color:var(--text);-webkit-font-smoothing:antialiased}
 .wrap{max-width:760px;margin:0 auto;padding:0 16px 48px}
 header{background:linear-gradient(135deg,#1f6feb,#7c3aed);color:#fff;padding:22px;border-radius:0 0 22px 22px;margin:0 -16px}
 header h1{margin:0;font-size:21px;font-weight:700}
 header .sub{margin-top:7px;font-size:12px;opacity:.92}
 header .tag{margin-top:6px;font-size:13px;opacity:.95;font-weight:600}
 .snap{margin-top:10px;font-size:12px;opacity:.95;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
 .refresh{border:0;background:rgba(255,255,255,.22);color:#fff;padding:6px 16px;border-radius:16px;font-size:12px;cursor:pointer}
 .refresh:active{background:rgba(255,255,255,.42)}
 .controls{position:sticky;top:0;background:var(--bg);z-index:5;padding-top:10px;margin:0 -16px;padding-left:16px;padding-right:16px}
 .tabs{display:flex;gap:6px;margin-bottom:8px}
 .tab{flex:1;border:0;background:var(--tab);color:var(--tabtx);padding:10px 2px;border-radius:12px;font-size:13.5px;font-weight:600;cursor:pointer;white-space:nowrap}
 .tab.on{background:#1f6feb;color:#fff}
 .search{width:100%;border:1px solid var(--line);background:var(--fltr);color:var(--text);border-radius:12px;padding:9px 14px;font-size:14px;margin-bottom:8px;-webkit-appearance:none;outline:none}
 .search:focus{border-color:#1f6feb}
 .filters{white-space:nowrap;overflow-x:auto;padding-bottom:10px}
 .filters button{background:var(--fltr);color:var(--fltrtx);padding:7px 16px;border-radius:20px;margin-right:8px;font-size:13px;cursor:pointer;border:1px solid var(--line)}
 .filters button.on{background:var(--text);color:var(--bg);border-color:var(--text)}
 .card{background:var(--card);border-radius:16px;padding:15px 16px;margin:12px 0 0;border-left:4px solid #ccc}
 .card.featured{box-shadow:inset 0 0 0 1.5px var(--feattx)}
 .row{display:flex;gap:13px;align-items:flex-start}
 .datebox{flex:none;width:50px;text-align:center;background:var(--date);color:var(--datetx);border-radius:12px;padding:7px 0}
 .datebox .dm{display:block;font-size:12px;line-height:1.3}
 .datebox .dd{display:block;font-size:23px;font-weight:700;line-height:1.05}
 .datebox.now{background:var(--nw);color:var(--nwtx)}
 .vic{flex:none;width:46px;height:46px;border-radius:50%;background:var(--vic);display:flex;align-items:center;justify-content:center;font-size:22px}
 .body{flex:1;min-width:0}
 .top{display:flex;align-items:center;gap:6px;margin-bottom:7px;flex-wrap:wrap}
 .pill{font-size:12px;padding:2px 10px;border-radius:20px;font-weight:600}
 .cd{background:var(--cd);color:var(--cdtx)}.cd.soon{background:#e4572e;color:#fff}
 .kid{background:var(--kid);color:var(--kidtx)}.feat{background:var(--feat);color:var(--feattx)}
 .nw{background:var(--nw);color:var(--nwtx)}.cat{color:#fff}
 .morep{font-size:12px;padding:2px 9px;border-radius:20px;font-weight:600;background:var(--tab);color:var(--tabtx);border:0;cursor:pointer}
 .title{font-weight:600;font-size:16.5px;line-height:1.45}
 .title a{color:var(--text);text-decoration:none}
 .meta{color:var(--muted);font-size:13px;margin-top:7px;line-height:1.6}
 .note{color:var(--note);font-size:12px;margin-top:6px}
 .price{color:var(--price);font-size:13px;margin-top:4px;font-weight:600}
 .prog{margin-top:11px;font-size:13px;color:var(--progtx);background:var(--prog);border-radius:10px;padding:9px 11px}
 .prog b{color:var(--progb)}
 .prog .pi{display:flex;justify-content:space-between;gap:10px;margin-top:5px;align-items:flex-start}
 .prog .pi a{color:var(--proglk);text-decoration:none;flex:1;min-width:0;word-break:break-word;line-height:1.5}
 .prog .pi a::before{content:"•";color:var(--progb);margin-right:6px;font-weight:700}
 .prog .pi .pd{flex:none;color:var(--hint)}
 .empty{padding:56px 0;text-align:center;color:var(--hint)}
 .health{margin-top:14px;font-size:12px;color:var(--hltx);background:var(--hl);border:1px solid var(--hlb);border-radius:10px;padding:8px 12px;line-height:1.5}
 .more{display:block;width:100%;margin-top:12px;border:0;background:var(--more);color:var(--moretx);padding:12px;border-radius:12px;font-size:14px;font-weight:600;cursor:pointer}
 .srchinfo{font-size:13px;color:var(--moretx);background:var(--more);border-radius:10px;padding:9px 13px;margin-top:4px;font-weight:600}
 .citysw{display:flex;gap:6px;margin-top:11px}
 .cbtn{border:0;background:rgba(255,255,255,.18);color:#fff;padding:6px 15px;border-radius:14px;font-size:12.5px;font-weight:700;cursor:pointer}
 .cbtn.on{background:rgba(255,255,255,.95);color:#1f6feb}
</style></head><body><div class="wrap">
<header><h1>🗺️ 1766一起遛遛</h1>
<div class="tag" id="tag">上海亲子 · 演出 · 展会 · 赛事——日更雷达</div>
<div class="citysw" id="citysw">
 <button class="cbtn on" data-c="上海" onclick="setCity('上海')">📍 上海</button>
 <button class="cbtn" data-c="北京" onclick="setCity('北京')">📍 北京</button>
</div>
<div class="sub" id="sub">加载中…</div>
<div class="snap"><span id="snap"></span></div></header>
<div class="controls">
 <div class="tabs">
  <button class="tab on" data-t="live" onclick="setTab(this,'live')">🎫 近期</button>
  <button class="tab" data-t="show" onclick="setTab(this,'show')">🎭 演出</button>
  <button class="tab" data-t="annual" onclick="setTab(this,'annual')">🔥 年度展</button>
  <button class="tab" data-t="venue" onclick="setTab(this,'venue')">🏛 场馆</button>
  <button class="tab" data-t="b2b" onclick="setTab(this,'b2b')">🏢 行业</button>
 </div>
 <input id="q" class="search" type="search" placeholder="🔍 搜活动名 / 场馆 / 关键词" oninput="apply()" autocomplete="off">
 <div class="filters">
  <button class="on" data-k="all" onclick="setF(this,'all')">全部</button>
  <button data-k="new" onclick="setF(this,'new')">🆕 最新</button>
  <button data-k="kid" onclick="setF(this,'kid')">👨‍👩‍👧 亲子</button>
 </div>
</div>
<div id="srchInfo" class="srchinfo" style="display:none"></div>
<div id="list"><div class="empty">加载中…</div></div>
<button class="more" id="moreBtn" style="display:none" onclick="showFar=true;apply()"></button>
<div class="health" id="health" style="display:none"></div>
</div>
<script>
const CAT={'体育':'#e4572e','展会':'#1f6feb','演出':'#9b51e0'},DEF='#16a34a',NEW_DAYS=7;
const KMAP={'年度固定':'annual','固定场馆':'venue','临时':'live'};
const CITY_FILE={'上海':'events.json','北京':'events_beijing.json'};
const CITY_TAG={'上海':'上海亲子 · 演出 · 展会 · 赛事——日更雷达','北京':'北京亲子 · 演出 · 展会 · 赛事——日更雷达'};
let curTab='live',curF='all',NEWCUT='',showFar=false,curCity='上海';
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));}
function fmtDate(s,e){if(!s)return '档期待定';const d=s.split('-');if(d.length<3)return s;const m=+d[1],day=+d[2];
 if(e&&e!==s){const x=e.split('-');if(x.length===3){const em=+x[1],ed=+x[2];return em===m?`${m}月${day}–${ed}日`:`${m}月${day}日–${em}月${ed}日`;}}
 return `${m}月${day}日`;}
function cd(s,e,t){if(!s)return null;const sd=new Date(s+'T00:00:00');if(isNaN(sd))return null;
 const diff=Math.round((sd-t)/864e5);
 if(diff<0){if(e){const ed=new Date(e+'T00:00:00');if(!isNaN(ed)&&ed>=t)return['进行中',true];}return null;}
 if(diff===0)return['今天',true];if(diff===1)return['明天',true];return[diff+'天后',diff<=14];}
function subcat(ev){const s=((ev.title||'')+' '+((ev.tags||[]).join(' '))).toLowerCase();
 if(/相声|脱口秀|曲艺|滑稽|栋笃笑/.test(s))return '相声脱口秀';
 if(/livehouse|音乐现场|乐队/.test(s))return 'Livehouse';
 if(/演唱会/.test(s))return '演唱会';
 if(/音乐节/.test(s))return '音乐节';
 if(/音乐会|交响|钢琴|独奏|协奏|室内乐|合唱|乐团|爵士/.test(s))return '音乐会';
 if(/京剧|越剧|昆曲|戏曲|沪剧|评弹|黄梅|豫剧|粤剧/.test(s))return '戏曲';
 if(/儿童|亲子|绘本|宝贝|亲亲|童趣/.test(s))return '亲子剧';
 if(/话剧|音乐剧|舞台剧|舞剧|歌剧|沉浸|默剧|马戏|杂技|魔术/.test(s))return '话剧歌舞';
 return '其他';}
function card(ev,t){const color=CAT[ev.type]||DEF,kind=(ev.audience==='B2B')?'b2b':(ev.kind==='临时'&&ev.type==='演出')?'show':(KMAP[ev.kind]||'live');
 let title=esc(ev.title);if(ev.official_url)title=`<a href="${esc(ev.official_url)}" target="_blank" rel="noopener">${title}</a>`;
 const isNew=!!(ev.first_seen&&ev.first_seen>=NEWCUT);
 let pills=[`<span class="pill cat" style="background:${color}">${esc(ev.type)}</span>`];
 const c=cd(ev.start_date,ev.end_date,t);if(c)pills.push(`<span class="pill cd ${c[1]?'soon':''}">${c[0]}</span>`);
 if(ev.kid_friendly){const lab='👨‍👩‍👧 亲子'+(ev.age_range?(' '+ev.age_range):'');pills.push(`<span class="pill kid">${esc(lab)}</span>`);}
 if(isNew)pills.push('<span class="pill nw">🆕 最新</span>');
 if(ev.featured)pills.push('<span class="pill feat">🔥 重磅</span>');
 let ph=pills.slice(0,5).join('');
 if(pills.length>5)ph+=`<button class="morep" onclick="this.nextElementSibling.style.display='inline';this.remove()">+${pills.length-5}</button><span style="display:none">${pills.slice(5).join('')}</span>`;
 let days=9999,edays=-99999;
 if(ev.start_date){const sd=new Date(ev.start_date+'T00:00:00');if(!isNaN(sd))days=Math.round((sd-t)/864e5);}
 if(ev.end_date){const ed=new Date(ev.end_date+'T00:00:00');if(!isNaN(ed))edays=Math.round((ed-t)/864e5);}
 const ongoing=(days<0&&edays>=0);
 let badge='';
 if(kind!=='venue'){
  if(days>=0&&ev.start_date){const d=ev.start_date.split('-');badge=`<div class="datebox"><span class="dm">${+d[1]}月</span><span class="dd">${+d[2]}</span></div>`;}
  else if(ongoing){const e=ev.end_date.split('-');badge=`<div class="datebox now"><span class="dm">演至</span><span class="dd" style="font-size:15px">${+e[1]}/${+e[2]}</span></div>`;}
  else if(ev.start_date){const d=ev.start_date.split('-');badge=`<div class="datebox"><span class="dm">${+d[1]}月</span><span class="dd">${+d[2]}</span></div>`;}
  else badge='<div class="datebox"><span class="dd" style="font-size:17px">📅</span><span class="dm">待定</span></div>';
 }
 let meta=ev.venue?`📍 ${esc(ev.venue)}`:'';
 if(ev.sessions&&ev.sessions.length>1)meta+=(meta?'<br>':'')+`🎬 多场次 ${ev.sessions.map(d=>esc(d.slice(5))).join('、')}`;
 const note=ev.note?`<div class="note">⚠ ${esc(ev.note)}</div>`:'';
 const price=ev.price_range?`<div class="price">${esc(ev.price_range)}</div>`:'';
 let prog='';
 if(ev.programs&&ev.programs.length){prog='<div class="prog"><b>🎭 近期在演</b>'+ev.programs.map(p=>`<div class="pi"><a href="${esc(p.u||'#')}" target="_blank" rel="noopener">${esc(p.t)}</a><span class="pd">${p.d?esc(p.d.slice(5)):''}</span></div>`).join('')+'</div>';}
 const inner=`<div class="top">${ph}</div><div class="title">${title}</div><div class="meta">${meta}</div>${note}${price}${prog}`;
 const sdata=esc((ev.title+' '+(ev.venue||'')+' '+(ev.type||'')+' '+((ev.tags||[]).join(' '))+' '+((ev.programs||[]).map(p=>p.t).join(' '))).toLowerCase());
 const attrs=`style="border-left-color:${color}" data-kind="${kind}" data-type="${esc(ev.type)}" data-subcat="${esc(subcat(ev))}" data-kid="${ev.kid_friendly?1:0}" data-new="${isNew?1:0}" data-unfit="${ev.kid_unfit?1:0}" data-days="${days}" data-search="${sdata}"`;
 if(kind==='venue')return `<div class="card${ev.featured?' featured':''}" ${attrs}>${inner}</div>`;
 return `<div class="card${ev.featured?' featured':''}" ${attrs}><div class="row">${badge}<div class="body">${inner}</div></div></div>`;}
function mark(sel,btn){document.querySelectorAll(sel+' button').forEach(b=>b.classList.remove('on'));btn.classList.add('on');}
function renderFilters(){const box=document.querySelector('.filters');
 if(curTab==='show'){
   const cnt={};document.querySelectorAll('.card').forEach(c=>{if(c.dataset.kind==='show'){const k=c.dataset.subcat;cnt[k]=(cnt[k]||0)+1;}});
   const order=['演唱会','音乐会','话剧歌舞','亲子剧','相声脱口秀','Livehouse','戏曲','音乐节','其他'];
   let h='<button class="on" data-k="all" onclick="setF(this,\'all\')">全部</button>';
   order.forEach(k=>{if(cnt[k])h+='<button data-k="sub:'+k+'" onclick="setF(this,\'sub:'+k+'\')">'+k+' '+cnt[k]+'</button>';});
   box.innerHTML=h;
 }else{
   box.innerHTML='<button class="on" data-k="all" onclick="setF(this,\'all\')">全部</button>'+
     '<button data-k="new" onclick="setF(this,\'new\')">🆕 最新</button>'+
     '<button data-k="kid" onclick="setF(this,\'kid\')">👨‍👩‍👧 亲子</button>';
 }}
function setTab(b,t){curTab=t;curF='all';showFar=false;document.getElementById('q').value='';mark('.tabs',b);renderFilters();apply();}
function setF(b,f){curF=f;document.getElementById('q').value='';mark('.filters',b);apply();}
function setCity(c){if(c===curCity)return;curCity=c;
 document.querySelectorAll('.citysw button').forEach(b=>b.classList.toggle('on',b.dataset.c===c));
 document.getElementById('tag').textContent=CITY_TAG[c];
 curTab='live';curF='all';showFar=false;document.getElementById('q').value='';
 document.querySelectorAll('.tabs button').forEach(b=>b.classList.toggle('on',b.dataset.t==='live'));
 load();}
function apply(){let n=0,far=0;
 const q=(document.getElementById('q').value||'').trim().toLowerCase();
 document.querySelector('.tabs').style.opacity=q?'.4':'1';
 document.querySelector('.filters').style.opacity=q?'.4':'1';
 document.querySelectorAll('.card').forEach(c=>{
   let ok;
   if(q){ok=c.dataset.search.indexOf(q)>=0;}
   else{
     let tabOk;
     if(curTab==='live')tabOk=(c.dataset.kind==='live'||c.dataset.kind==='show');
     else tabOk=(c.dataset.kind===curTab);
     let fOk;
     if(curF==='all')fOk=true;
     else if(curF==='new')fOk=c.dataset.new==='1';
     else if(curF==='kid')fOk=(c.dataset.kid==='1'&&c.dataset.unfit!=='1');
     else if(curF.indexOf('sub:')===0)fOk=(c.dataset.subcat===curF.slice(4));
     else fOk=true;
     let winOk=true;
     if(curTab==='live'&&tabOk&&fOk&&(+c.dataset.days)>30){winOk=showFar;if(!showFar)far++;}
     ok=tabOk&&fOk&&winOk;
   }
   c.style.display=ok?'block':'none';if(ok)n++;});
 const et=document.getElementById('emptyTip');et.style.display=n?'none':'block';
 if(!n)et.textContent=q?('没有匹配「'+q+'」的活动'):'该分类下暂无活动';
 const si=document.getElementById('srchInfo');
 if(q){si.style.display='block';si.textContent='🔍 全局搜索「'+q+'」· 找到 '+n+' 条(跨所有分类)';}else si.style.display='none';
 const mb=document.getElementById('moreBtn');
 if(!q&&curTab==='live'&&!showFar&&far>0){mb.style.display='block';mb.textContent='📅 查看更远的 '+far+' 个活动';}else mb.style.display='none';}
function render(data){const evts=(data.events||[]).slice();
 const t=new Date();t.setHours(0,0,0,0);
 const cc=new Date(t);cc.setDate(cc.getDate()-(NEW_DAYS-1));NEWCUT=cc.toISOString().slice(0,10);
 const nNew=evts.filter(e=>e.first_seen&&e.first_seen>=NEWCUT).length;
 const h=data.health||{},hn=Object.keys(h),hbad=hn.filter(n=>h[n].status!=='ok');
 document.getElementById('snap').textContent='📅 数据更新于 '+(data.generatedAt||'')+' · 源 ✅'+(hn.length-hbad.length)+(hbad.length?' ⚠️'+hbad.length:'');
 const hd=document.getElementById('health');
 if(hbad.length){hd.style.display='block';hd.innerHTML='⚠️ 数据源异常(已用上次数据顶替,不影响展示): '+hbad.map(n=>esc(n)+'·'+esc(h[n].status)).join('、');}
 else{hd.style.display='none';}
 const showN=evts.filter(e=>e.kind==='临时'&&e.type==='演出'&&e.audience!=='B2B').length;
 const b2bN=evts.filter(e=>e.audience==='B2B').length;
 document.getElementById('sub').textContent='演出'+showN+' · 年度'+evts.filter(e=>e.kind==='年度固定').length+' · 场馆'+evts.filter(e=>e.kind==='固定场馆').length+' · 行业'+b2bN+' · 🆕'+nNew;
 const ord={'临时':0,'年度固定':1,'固定场馆':2};
 const TS=new Date(t.getTime()-t.getTimezoneOffset()*6e4).toISOString().slice(0,10);
 function sv(e){const s=e.start_date,en=e.end_date;if(s&&s>=TS)return s;if(en&&en>=TS)return '~'+en;return s||'9998';}
 evts.sort((a,b)=>{const o=(ord[a.kind]||0)-(ord[b.kind]||0);if(o)return o;
  if(a.kind==='固定场馆'){const pa=(a.programs&&a.programs.length)?1:0,pb=(b.programs&&b.programs.length)?1:0;if(pa!==pb)return pb-pa;return 0;}
  const x=sv(a),y=sv(b);return x<y?-1:x>y?1:0;});
 document.getElementById('list').innerHTML=evts.map(e=>card(e,t)).join('')+'<div class="empty" id="emptyTip" style="display:none">该分类下暂无活动</div>';
 renderFilters();apply();}
async function load(){document.getElementById('list').innerHTML='<div class="empty">加载中…</div>';
 try{const r=await fetch(CITY_FILE[curCity]+'?t='+Date.now(),{cache:'no-store'});render(await r.json());}
 catch(e){document.getElementById('list').innerHTML='<div class="empty">加载失败,请检查网络后点刷新</div>';}}
load();
</script></body></html>
"""


def save(events: List[Event], health: dict = None, city: str = "上海") -> None:
    """city 留空默认"上海"(与既有调用 100% 兼容,写 events.json);
    city="北京" 时写独立的 events_beijing.json,场馆交叉引用改用 CORES_BJ,
    与上海的 events/CORES 互不读取、互不覆盖。"""
    os.makedirs(SITE_DIR, exist_ok=True)
    with open(os.path.join(SITE_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(INDEX_HTML)
    out_name = "events.json" if city == "上海" else "events_beijing.json"
    cores = CORES if city == "上海" else CORES_BJ
    # 交叉引用:给固定场馆附"近期在演"(用已抓到、发生在该场馆的活动)。
    # 按"最长核心名"归属,避免"西岸大剧院"被并进"上海大剧院"等串场。
    shows = [e for e in events if e.kind != "固定场馆" and e.venue]

    def _best_core(text: str):
        ms = [c for c in cores if c in text]
        return max(ms, key=len) if ms else None

    show_core = {id(s): _best_core(s.venue) for s in shows}

    def _programs(v: Event):
        vcore = _best_core(v.title)
        if not vcore:
            return []
        m = sorted(
            [s for s in shows if show_core[id(s)] == vcore],
            key=lambda s: s.start_date or "9999",
        )
        return [
            {"t": s.title, "d": s.start_date, "u": s.official_url}
            for s in m[:5]
        ]

    recs = []
    for e in events:
        rec = {k: e.to_dict()[k] for k in PUBLIC_FIELDS}
        if e.kind == "固定场馆":
            rec["programs"] = _programs(e)
        recs.append(rec)

    payload = {
        "generatedAt": datetime.datetime.now(
            datetime.timezone(datetime.timedelta(hours=8))
        ).strftime("%Y-%m-%d %H:%M") + " 北京时间",
        "count": len(events),
        "health": health or {},
        "events": recs,
    }
    with open(os.path.join(SITE_DIR, out_name), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    print(f"[site] 已生成 index.html + {out_name}({len(events)} 条,{city},仓库根)")
