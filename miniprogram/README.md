# 小程序前端（微信小程序）

## 页面

| 页面 | 路径 | 功能 |
|------|------|------|
| 发现 | `pages/list` | 活动列表 + 类型/亲子筛选 |
| 详情 | `pages/detail` | 详情 + 收藏 + 开票提醒 + 复制购票链接 |
| 收藏 | `pages/favorites` | 我的收藏 |

## 运行

1. 微信开发者工具 → 导入项目，目录选 `miniprogram/`。
2. 填 AppId（`project.config.json` 的 `appid`，或导入时填）。
3. 把云开发环境 ID 填到 `app.js` 的 `globalData.env`。
4. 编译预览。数据为空时先跑采集层 + 部署云函数写入 `events` 集合。

## 待配置

- `app.js`：云开发环境 ID
- `pages/detail/index.js`：开票提醒订阅消息模板 ID（`REMIND_TMPL`）

> 个人号阶段订阅消息为「一次性订阅」，用户每次点「开票提醒」授权一次推送。
