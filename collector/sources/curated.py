"""上海重大活动 · 策展源 —— 人工维护的年度重磅活动清单(带真实日期)。

为什么需要它:
  免费爬虫给不出"未来的重大活动"(WAIC/进博会/大师赛等),还会混入过期、
  纯 B2B、不适合儿童的内容。本源是雷达的"可靠骨架"——少而精、有日期、已筛选。

数据状态(2026-06 联网核实):
  有 start 日期者为已核实;note 含"待官方确认"者为档期估计,以官方为准。
维护方式: 直接编辑下方 EVENTS 列表(每年更新档期即可)。
"""
from __future__ import annotations

from typing import List

from models import Event
from sources.base import BaseSource

# 每条: title/type/start/end/venue/kid/age/featured/url/note/tags
EVENTS = [
    {
        "title": "世界人工智能大会 WAIC 2026", "type": "展会",
        "start": "2026-07-17", "end": "2026-07-20", "venue": "世博展览馆",
        "kid": True, "age": "8岁+", "featured": True,
        "url": "https://www.worldaic.com.cn/",
        "note": "AI 科普展区适合大童", "tags": ["AI/科技"],
    },
    {
        "title": "中国国际工业博览会(工博会)2026", "type": "展会",
        "start": "2026-10-12", "end": "2026-10-16", "venue": "国家会展中心(虹桥)",
        "kid": True, "age": "8岁+", "featured": True,
        "url": "https://www.ciif-expo.com/",
        "note": "机器人/智能制造展区", "tags": ["科技/机器人"],
    },
    {
        "title": "第九届中国国际进口博览会(进博会)", "type": "展会",
        "start": "2026-11-05", "end": "2026-11-10", "venue": "国家会展中心(虹桥)",
        "kid": False, "age": "", "featured": True, "url": "https://www.ciie.org/",
        "note": "公众日需预约,以官方为准", "tags": [],
    },
    {
        "title": "上海劳力士大师赛(网球 ATP1000)2026", "type": "体育",
        "start": "2026-10-07", "end": "2026-10-19", "venue": "旗忠森林网球中心",
        "kid": True, "age": "全年龄", "featured": True,
        "url": "https://www.jussevent.com/", "note": "结束日期约,以官方为准",
        "tags": ["网球"],
    },
    {
        "title": "上海马拉松 2026", "type": "体育",
        "start": "2026-12-06", "end": "", "venue": "外滩金牛广场(起点)",
        "kid": True, "age": "全年龄", "featured": True,
        "url": "https://www.shang-ma.com/", "note": "可观赛/亲子跑", "tags": ["跑步"],
    },
    {
        "title": "上海书展", "type": "展会",
        "start": "", "end": "", "venue": "上海展览中心",
        "kid": True, "age": "全年龄", "featured": False,
        "url": "http://www.shbookfair.cn/",
        "note": "档期待官方确认(往年 8 月中旬),非常适合带娃", "tags": ["文化/亲子"],
    },
    {
        "title": "中国上海国际艺术节", "type": "演出",
        "start": "", "end": "", "venue": "多场馆",
        "kid": True, "age": "", "featured": False, "url": "",
        "note": "档期待官方确认(往年 10–11 月),含亲子板块", "tags": ["文化"],
    },
    {
        "title": "上海国际电影节(第28届)", "type": "演出",
        "start": "2026-06-12", "end": "2026-06-21", "venue": "全市影院",
        "kid": True, "age": "全年龄", "featured": True, "url": "https://www.siff.com/",
        "note": "含动画/亲子展映单元", "tags": ["电影"],
    },
    {
        "title": "上海旅游节", "type": "演出",
        "start": "", "end": "", "venue": "全市景点",
        "kid": True, "age": "全年龄", "featured": True, "url": "",
        "note": "档期待官方确认(往年 9 月中–10 月,大量景点半价)", "tags": ["文化/亲子"],
    },
    {
        "title": "上海迪士尼·万圣狂欢", "type": "演出",
        "start": "", "end": "", "venue": "上海迪士尼度假区",
        "kid": True, "age": "全年龄", "featured": True,
        "url": "https://www.shanghaidisneyresort.com/",
        "note": "档期待官方确认(往年 10 月中–11 月初周末)", "tags": ["乐园/亲子"],
    },
    {
        "title": "上海马戏城 杂技/马戏 驻场秀", "type": "演出",
        "start": "", "end": "", "venue": "上海马戏城",
        "kid": True, "age": "全年龄", "featured": False,
        "url": "https://www.shanghaimaxicheng.com/",
        "note": "ERA时空之旅常驻,节目/购票见官网", "tags": ["马戏"],
    },
    {
        "title": "上海儿童艺术剧场 亲子剧目", "type": "演出",
        "start": "", "end": "", "venue": "上海儿童艺术剧场(梅陇)",
        "kid": True, "age": "全年龄", "featured": False,
        "url": "https://www.shcat.com.cn/zh",
        "note": "常年亲子剧/木偶/音乐会,排期见官网", "tags": ["剧场/亲子"],
    },
    {
        "title": "上海天文馆", "type": "展会",
        "start": "", "end": "", "venue": "上海天文馆(临港)",
        "kid": True, "age": "全年龄", "featured": False,
        "url": "https://www.sstm-sam.org.cn/",
        "note": "常年开放,需官网预约;亲子科普顶流", "tags": ["科普/亲子"],
    },
    {
        "title": "上海自然博物馆", "type": "展会",
        "start": "", "end": "", "venue": "自然博物馆(静安雕塑公园)",
        "kid": True, "age": "全年龄", "featured": False,
        "url": "https://www.snhm.org.cn/",
        "note": "常年开放+当期特展,需预约;亲子科普", "tags": ["科普/亲子"],
    },
    {
        "title": "上海科技馆", "type": "展会",
        "start": "", "end": "", "venue": "上海科技馆(浦东)",
        "kid": True, "age": "全年龄", "featured": False,
        "url": "https://www.sstm.org.cn/",
        "note": "常年开放,亲子科普", "tags": ["科普/亲子"],
    },
    {
        "title": "上海玻璃博物馆 儿童艺术馆", "type": "展会",
        "start": "", "end": "", "venue": "玻璃博物馆(宝山)",
        "kid": True, "age": "全年龄", "featured": False,
        "url": "http://www.shmog.org/",
        "note": "玻璃主题亲子体验,常年开放", "tags": ["科普/亲子"],
    },
    {
        "title": "上海木偶剧团 亲子木偶剧", "type": "演出",
        "start": "", "end": "", "venue": "多剧场",
        "kid": True, "age": "全年龄", "featured": False,
        "url": "http://www.sh-puppet.com.cn/",
        "note": "常年亲子木偶/皮影,排期见官网", "tags": ["剧场/亲子"],
    },
    {
        "title": "世界移动通信大会 MWC上海 2026", "type": "展会",
        "start": "2026-06-24", "end": "2026-06-26", "venue": "上海新国际博览中心",
        "kid": False, "age": "", "featured": True,
        "url": "https://www.mwcshanghai.cn/", "note": "移动AI/6G/卫星通信",
        "tags": ["科技/通信"],
    },
    {
        "title": "ChinaJoy 2026(中国国际数码互动娱乐展)", "type": "展会",
        "start": "2026-07-31", "end": "2026-08-03", "venue": "上海新国际博览中心",
        "kid": True, "age": "青少年", "featured": True,
        "url": "https://www.chinajoy.net/", "note": "游戏/ACG,适合大童青少年",
        "tags": ["游戏/ACG"],
    },
    {
        "title": "华为全连接大会 HUAWEI CONNECT 2026", "type": "展会",
        "start": "2026-09-17", "end": "2026-09-19", "venue": "世博展览馆",
        "kid": False, "age": "", "featured": True,
        "url": "https://www.huawei.com/cn/events/huaweiconnect",
        "note": "档期以华为官方为准(往年9月中旬)", "tags": ["科技/AI"],
    },
    # —— 下半年已确认档期的年度大展 ——
    {
        "title": "CCG EXPO 中国国际动漫游戏博览会 2026", "type": "展会",
        "start": "2026-07-04", "end": "2026-07-06", "venue": "上海跨国采购会展中心",
        "kid": True, "age": "青少年", "featured": True, "url": "",
        "note": "动漫/游戏/ACG,适合大童青少年", "tags": ["动漫/ACG"],
    },
    {
        "title": "上海国际童书展 CCBF 2026", "type": "展会",
        "start": "2026-11-13", "end": "2026-11-15", "venue": "世博展览馆",
        "kid": True, "age": "全年龄", "featured": True,
        "url": "https://www.ccbookfair.com/cn", "note": "童书/绘本,强亲子",
        "tags": ["文化/亲子"],
    },
    {
        "title": "FHC 上海环球食品展 2026", "type": "展会",
        "start": "2026-11-10", "end": "2026-11-12", "venue": "上海新国际博览中心",
        "kid": False, "age": "", "featured": True,
        "url": "https://www.fhcchina.com/", "note": "进口食品/餐饮", "tags": ["食品"],
    },
    {
        "title": "上海国际婚纱礼服展(婚博会)2026", "type": "展会",
        "start": "2026-07-15", "end": "2026-07-17", "venue": "世博展览馆",
        "kid": False, "age": "", "featured": False, "url": "",
        "note": "一年多届,具体见婚博会官网", "tags": ["婚庆"],
    },
    # —— 年度锚点:2026 上海届已过/双年展,标注往年档期,提前规划 ——
    {
        "title": "上海车展(上海国际汽车工业展览会)", "type": "展会",
        "start": "", "end": "", "venue": "国家会展中心(虹桥)",
        "kid": True, "age": "全年龄", "featured": True, "url": "",
        "note": "双年展(逢单数年),下届 2027年4月25日–5月2日", "tags": ["汽车"],
    },
    {
        "title": "CMEF 中国国际医疗器械博览会(上海)", "type": "展会",
        "start": "", "end": "", "venue": "国家会展中心(虹桥)",
        "kid": False, "age": "", "featured": False, "url": "",
        "note": "上海春季届,往年约 4 月", "tags": ["医疗"],
    },
    {
        "title": "CBE 中国美容博览会(上海美博会)", "type": "展会",
        "start": "", "end": "", "venue": "国家会展中心(虹桥)",
        "kid": False, "age": "", "featured": False, "url": "",
        "note": "往年约 5 月", "tags": ["美妆"],
    },
    {
        "title": "HOTELEX 上海国际酒店及餐饮业博览会", "type": "展会",
        "start": "", "end": "", "venue": "上海新国际博览中心",
        "kid": False, "age": "", "featured": False, "url": "",
        "note": "往年约 3–4 月", "tags": ["酒店餐饮"],
    },
    {
        "title": "SEMICON China 国际半导体展", "type": "展会",
        "start": "", "end": "", "venue": "上海新国际博览中心",
        "kid": False, "age": "", "featured": False, "url": "",
        "note": "往年约 3 月", "tags": ["半导体"],
    },
    # —— 常驻剧场(官网为 SPA 抓不到排期,列为场馆入口,点击看官方排期)——
    {
        "title": "上海大剧院", "type": "演出",
        "start": "", "end": "", "venue": "人民大道300号(人民广场)",
        "kid": True, "age": "全年龄", "featured": False,
        "url": "https://www.shgtheatre.com/", "note": "歌剧/芭蕾/话剧,排期见官网",
        "tags": ["剧场"],
    },
    {
        "title": "上海东方艺术中心", "type": "演出",
        "start": "", "end": "", "venue": "丁香路425号(浦东)",
        "kid": True, "age": "全年龄", "featured": False,
        "url": "https://www.shoac.com.cn/", "note": "音乐会/歌剧/亲子,排期见官网",
        "tags": ["剧场"],
    },
    {
        "title": "凯迪拉克·上海音乐厅", "type": "演出",
        "start": "", "end": "", "venue": "延安东路523号",
        "kid": True, "age": "全年龄", "featured": False,
        "url": "https://www.shanghaiconcerthall.com.cn/",
        "note": "音乐会/亲子音乐会,排期见官网", "tags": ["剧场"],
    },
    # —— 常驻博物馆 / 美术馆 / 科普(亲子去处,直链官网看展讯/预约)——
    {
        "title": "上海博物馆", "type": "展会",
        "start": "", "end": "", "venue": "人民广场本馆 / 东馆(浦东)",
        "kid": True, "age": "全年龄", "featured": False,
        "url": "https://www.shanghaimuseum.net/", "note": "本馆+东馆,需预约;历史文物",
        "tags": ["博物馆/亲子"],
    },
    {
        "title": "浦东美术馆 MAP", "type": "展会",
        "start": "", "end": "", "venue": "陆家嘴滨江",
        "kid": True, "age": "全年龄", "featured": False,
        "url": "https://www.museumofartpd.org.cn/", "note": "江景大展,需预约",
        "tags": ["美术馆"],
    },
    {
        "title": "中华艺术宫", "type": "展会",
        "start": "", "end": "", "venue": "浦东(原世博中国馆)",
        "kid": True, "age": "全年龄", "featured": False,
        "url": "https://www.artmuseumonline.org/", "note": "常设免费,特展另购",
        "tags": ["美术馆"],
    },
    {
        "title": "上海当代艺术博物馆 PSA", "type": "展会",
        "start": "", "end": "", "venue": "黄浦滨江(原南市发电厂)",
        "kid": False, "age": "", "featured": False,
        "url": "https://www.powerstationofart.com/", "note": "当代艺术,常设免费",
        "tags": ["美术馆"],
    },
    {
        "title": "龙美术馆(西岸馆)", "type": "展会",
        "start": "", "end": "", "venue": "徐汇西岸",
        "kid": True, "age": "全年龄", "featured": False,
        "url": "http://www.thelongmuseum.org/", "note": "西岸艺术地标",
        "tags": ["美术馆"],
    },
    {
        "title": "上海世博会博物馆", "type": "展会",
        "start": "", "end": "", "venue": "黄浦(原世博园区)",
        "kid": True, "age": "全年龄", "featured": False,
        "url": "https://www.expo-museum.cn/", "note": "世博主题,免费需预约",
        "tags": ["博物馆/亲子"],
    },
    {
        "title": "上海海洋水族馆", "type": "展会",
        "start": "", "end": "", "venue": "陆家嘴",
        "kid": True, "age": "全年龄", "featured": False,
        "url": "https://www.sh-aquarium.com/", "note": "强亲子,海洋生物",
        "tags": ["亲子/科普"],
    },
    {
        "title": "上海野生动物园", "type": "展会",
        "start": "", "end": "", "venue": "浦东南汇",
        "kid": True, "age": "全年龄", "featured": False,
        "url": "https://www.shwzoo.com/", "note": "强亲子,野生动物",
        "tags": ["亲子"],
    },
    {
        "title": "上海动物园", "type": "展会",
        "start": "", "end": "", "venue": "长宁虹桥路",
        "kid": True, "age": "全年龄", "featured": False,
        "url": "https://www.shanghaizoo.cn/", "note": "强亲子,市区动物园",
        "tags": ["亲子"],
    },
    {
        "title": "上海海昌海洋公园", "type": "展会",
        "start": "", "end": "", "venue": "浦东临港",
        "kid": True, "age": "全年龄", "featured": False,
        "url": "https://www.haichangoceanpark.com/shanghai/", "note": "海洋动物+游乐,强亲子",
        "tags": ["亲子"],
    },
    {
        "title": "上海乐高探索中心", "type": "展会",
        "start": "", "end": "", "venue": "室内亲子乐园",
        "kid": True, "age": "低龄", "featured": False,
        "url": "https://www.legolanddiscoverycenter.cn/shanghai/", "note": "低龄室内亲子",
        "tags": ["亲子"],
    },
]


# 固定场馆(常年滚动排期,无单一日期)—— 命中即归"固定场馆",其余策展归"年度固定"
_VENUE_KW = ["天文馆", "自然博物馆", "科技馆", "玻璃博物馆", "马戏城",
             "儿童艺术剧场", "木偶剧团", "音乐厅", "大剧院", "东方艺术中心",
             "博物馆", "美术馆", "艺术宫", "水族馆", "动物园", "海洋公园",
             "乐高", "植物园", "科普中心"]


def _kind(title: str) -> str:
    return "固定场馆" if any(k in title for k in _VENUE_KW) else "年度固定"


class CuratedSource(BaseSource):
    name = "curated"
    compliance = "high"  # 人工策展,无抓取

    def fetch(self) -> List[Event]:
        events = [
            Event(
                title=e["title"], type=e["type"], source=self.name,
                official_url=e["url"], venue=e["venue"],
                start_date=e["start"], end_date=e["end"],
                kid_friendly=e["kid"], age_range=e["age"],
                featured=e["featured"], note=e["note"], tags=list(e["tags"]),
                kind=_kind(e["title"]), raw_text=e["title"],
            )
            for e in EVENTS
        ]
        print(f"[curated] 重大活动 {len(events)} 条")
        return events
