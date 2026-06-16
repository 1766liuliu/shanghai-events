// 云函数: getEvents —— 小程序读取活动列表 / 详情(支持筛选)
const cloud = require('wx-server-sdk')
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV })
const db = cloud.database()

exports.main = async (event) => {
  const { id, type, district, kidOnly, page = 0, pageSize = 20 } = event
  try {
    // 详情: 按 _id 取单条
    if (id) {
      const res = await db.collection('events').doc(id).get()
      return { ok: true, data: [res.data] }
    }
    // 列表: 多维筛选
    const query = {}
    if (type) query.type = type
    if (district) query.district = district
    if (kidOnly) query.kid_friendly = true
    const res = await db.collection('events')
      .where(query)
      .orderBy('start_date', 'asc')
      .skip(page * pageSize)
      .limit(pageSize)
      .get()
    return { ok: true, data: res.data }
  } catch (e) {
    return { ok: false, error: e.message }
  }
}
