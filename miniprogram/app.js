App({
  globalData: {
    env: 'YOUR_CLOUD_ENV', // TODO: 填微信云开发环境 ID
  },
  onLaunch() {
    if (!wx.cloud) {
      console.error('请使用 2.2.3 以上基础库以使用云能力')
      return
    }
    wx.cloud.init({ env: this.globalData.env, traceUser: true })
  },
})
