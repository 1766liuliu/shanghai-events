# 云后端（微信云开发 / CloudBase）

小程序的后端，跑在微信云开发环境里。包含三个云函数 + 四个数据库集合。

## 数据库集合（需在云开发控制台手动创建）

| 集合 | 用途 | 权限建议 |
|------|------|---------|
| `events` | 活动主表（采集层写入） | 所有人可读、仅管理端写 |
| `weekly` | 每周精选快照 | 所有人可读 |
| `favorites` | 用户收藏 | 仅创建者可读写 |
| `watch` | 开票提醒关注 | 仅创建者可读写 |

## 云函数

| 函数 | 作用 | 触发方式 |
|------|------|---------|
| `getEvents` | 列表/详情读取（支持类型/区域/亲子筛选） | 小程序调用 |
| `weeklyDigest` | 生成本周精选写入 weekly | 定时触发器（每周一早晨） |
| `ticketWatch` | 检查开票时间→发订阅消息 | 定时触发器（每小时） |

## 部署步骤

1. 微信开发者工具 → 云开发 → 开通环境，记下「环境 ID」。
2. 控制台「数据库」里新建上表四个集合并设权限。
3. `cloudfunctions/` 下每个函数右键「上传并部署：云端安装依赖」。
4. 给 `weeklyDigest` / `ticketWatch` 配置「定时触发器」(在函数的 `config.json` 或控制台)。
5. 把环境 ID 填到 `miniprogram/app.js` 的 `globalData.env`。
6. 申请「开票提醒」订阅消息模板，模板ID 填到 `ticketWatch/index.js` 和 `miniprogram/pages/detail/index.js`。

> 采集层(本机 Python)通过 `collector/store/cloudbase.py` 把活动写进 `events` 集合。
