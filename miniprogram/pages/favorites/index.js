Page({
  data: { list: [], loading: true },

  onShow() {
    this.load()
  },

  async load() {
    this.setData({ loading: true })
    try {
      const favs = await wx.cloud.database().collection('favorites').get()
      const ids = (favs.data || []).map((f) => f.eventId)
      const evs = []
      for (const id of ids) {
        const r = await wx.cloud
          .callFunction({ name: 'getEvents', data: { id } })
          .catch(() => null)
        if (r && r.result && r.result.data[0]) evs.push(r.result.data[0])
      }
      this.setData({ list: evs, loading: false })
    } catch (e) {
      this.setData({ loading: false })
    }
  },

  open(e) {
    wx.navigateTo({ url: `/pages/detail/index?id=${e.currentTarget.dataset.id}` })
  },
})
