const REMIND_TMPL = '' // TODO: 开票提醒订阅消息模板ID

Page({
  data: { ev: null },

  onLoad(q) {
    this.eid = q.id
    wx.cloud
      .callFunction({ name: 'getEvents', data: { id: q.id } })
      .then((res) => {
        const list = (res.result && res.result.data) || []
        this.setData({ ev: list[0] || null })
      })
  },

  fav() {
    wx.cloud
      .database()
      .collection('favorites')
      .add({ data: { eventId: this.eid, createdAt: Date.now() } })
      .then(() => wx.showToast({ title: '已收藏' }))
      .catch(() => wx.showToast({ title: '收藏失败', icon: 'none' }))
  },

  remind() {
    if (!REMIND_TMPL) {
      wx.showToast({ title: '待配置订阅模板', icon: 'none' })
      return
    }
    wx.requestSubscribeMessage({ tmplIds: [REMIND_TMPL] }).then(() => {
      wx.cloud
        .database()
        .collection('watch')
        .add({ data: { eventId: this.eid, notifyOnSale: true } })
      wx.showToast({ title: '已订阅开票提醒' })
    })
  },

  buy() {
    const url = this.data.ev && this.data.ev.official_url
    if (!url) {
      wx.showToast({ title: '暂无购票链接', icon: 'none' })
      return
    }
    wx.setClipboardData({
      data: url,
      success: () => wx.showToast({ title: '购票链接已复制', icon: 'none' }),
    })
  },
})
