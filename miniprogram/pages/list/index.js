Page({
  data: { events: [], kidOnly: false, type: '', loading: true },

  onShow() {
    this.load()
  },

  load() {
    this.setData({ loading: true })
    wx.cloud
      .callFunction({
        name: 'getEvents',
        data: { kidOnly: this.data.kidOnly, type: this.data.type },
      })
      .then((res) => {
        const data = (res.result && res.result.data) || []
        this.setData({ events: data, loading: false })
      })
      .catch(() => this.setData({ loading: false }))
  },

  setType(e) {
    this.setData({ type: e.currentTarget.dataset.type }, () => this.load())
  },

  toggleKid() {
    this.setData({ kidOnly: !this.data.kidOnly }, () => this.load())
  },

  openDetail(e) {
    wx.navigateTo({ url: `/pages/detail/index?id=${e.currentTarget.dataset.id}` })
  },

  goFav() {
    wx.navigateTo({ url: '/pages/favorites/index' })
  },
})
