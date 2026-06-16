// 云函数: weeklyDigest —— 生成"本周精选"(建议配置定时触发器,每周一早晨)
// 取未来 7 天活动,亲子优先排序,写入 weekly 集合,供小程序/推送使用。
const cloud = require('wx-server-sdk')
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV })
const db = cloud.database()
const _ = db.command

const fmt = (d) => d.toISOString().slice(0, 10)

exports.main = async () => {
  const today = new Date()
  const in7 = new Date(today.getTime() + 7 * 86400000)
  try {
    const res = await db.collection('events')
      .where({ start_date: _.gte(fmt(today)).and(_.lte(fmt(in7))) })
      .limit(100)
      .get()
    // 亲子优先 → 价格友好
    const picks = res.data.sort((a, b) => {
      if (!!b.kid_friendly !== !!a.kid_friendly) return (b.kid_friendly ? 1 : 0) - (a.kid_friendly ? 1 : 0)
      return (a.price_min ?? 9999) - (b.price_min ?? 9999)
    })
    await db.collection('weekly').add({
      data: { generatedAt: fmt(today), count: picks.length, items: picks.slice(0, 20) },
    })
    return { ok: true, count: picks.length }
  } catch (e) {
    return { ok: false, error: e.message }
  }
}
