// 云函数: ticketWatch —— 监控关注活动的开票时间,触发"一次性订阅消息"提醒
// 建议配置定时触发器(如每小时)。需先在小程序后台申请"开票提醒"订阅消息模板,
// 把模板ID填到 TEMPLATE_ID,并按模板字段调整 data。
const cloud = require('wx-server-sdk')
cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV })
const db = cloud.database()
const _ = db.command

const TEMPLATE_ID = '' // TODO: 开票提醒订阅消息模板ID

exports.main = async () => {
  const now = new Date().toISOString().slice(0, 16).replace('T', ' ')
  const watches = await db.collection('watch')
    .where({ notifyOnSale: true, notified: _.neq(true) })
    .limit(100)
    .get()

  let sent = 0
  for (const w of watches.data) {
    const ev = await db.collection('events').doc(w.eventId).get().catch(() => null)
    if (!ev || !ev.data.open_ticket_time) continue
    if (ev.data.open_ticket_time <= now) {
      if (TEMPLATE_ID) {
        await cloud.openapi.subscribeMessage.send({
          touser: w._openid || w.openid,
          templateId: TEMPLATE_ID,
          page: `pages/detail/index?id=${w.eventId}`,
          data: {
            thing1: { value: String(ev.data.title).slice(0, 20) },
            time2: { value: ev.data.open_ticket_time },
          },
        }).catch((e) => console.error('推送失败', e))
      }
      await db.collection('watch').doc(w._id).update({ data: { notified: true } })
      sent++
    }
  }
  return { ok: true, sent }
}
