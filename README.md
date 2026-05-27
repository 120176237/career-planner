# 职路星途 - 抖音小程序版

基于原H5项目的完整抖音小程序迁移版本，保留原有业务逻辑，适配抖音生态。

## 📁 项目结构

```
职路星途_发布版_抖音版/
├── app.js                  # 小程序入口
├── app.json                # 小程序配置
├── app.ttss                # 全局样式
├── project.config.json     # 项目配置
├── sitemap.json            # 站点地图
├── pages/                  # 页面目录
│   ├── index/              # 首页
│   ├── quiz/               # 答题页
│   ├── result/             # 结果页
│   ├── payment/            # 支付页
│   └── vip-admin/          # VIP管理页
├── utils/                  # 工具函数
│   ├── api.js             # API请求
│   ├── util.js            # 通用工具
│   └── questions.js       # 题目配置
├── components/             # 组件目录
├── cloudfunctions/         # 云函数
│   ├── analyze/           # 分析云函数
│   ├── payment/           # 支付云函数
│   └── vip-consult/       # VIP咨询云函数
└── images/                # 图片资源
```

## 🚀 快速开始

### 前置条件

1. 下载并安装 [字节跳动开发者工具](https://developer.open-douyin.com/)
2. 注册抖音小程序账号
3. 获取小程序 AppID
4. 开通云开发服务

### 配置项目

1. 修改 `project.config.json` 中的 `appid` 为你的小程序 AppID
2. 修改 `app.js` 中的云环境ID:
   ```javascript
   tt.cloud.init({
     env: 'your-env-id' // 替换为你的云环境ID
   });
   ```
3. 如需使用外部API，修改 `utils/api.js` 中的 `BASE_URL`

### 部署云函数

1. 在开发者工具中打开云开发控制台
2. 创建云环境（如果没有）
3. 在 `cloudfunctions` 目录右键选择云函数，点击「上传并部署」

### 创建云数据库集合

在云开发控制台创建以下集合：

| 集合名称 | 说明 |
|---------|------|
| analysis_cache | 分析缓存 |
| analysis_records | 分析记录 |
| orders | 订单 |
| user_privileges | 用户权限 |
| vip_consults | VIP咨询 |

### 运行小程序

1. 在开发者工具中打开项目
2. 点击「编译」按钮
3. 在模拟器中预览

## 📱 功能特性

### 用户端功能

- ✅ 用户身份选择（30-40岁/应届生/家长）
- ✅ AI职业测评（轻量版/深度版/VIP版）
- ✅ 个性化行业推荐
- ✅ 深度分析报告
- ✅ 抖音支付
- ✅ 结果分享
- ✅ VIP咨询

### 管理功能

- VIP咨询管理
- 数据查看

## ☁️ 后端部署方案

### 方案一：云开发（推荐）

使用抖音云开发，无需搭建服务器。

**优点：**
- 无需服务器维护
- 与小程序深度集成
- 自动扩缩容
- 免费额度充足

**数据库对应关系：**

| 原SQLite表 | 云数据库集合 |
|-----------|------------|
| vip_consults | vip_consults |
| payments | orders |
| (缓存文件) | analysis_cache |

### 方案二：保留原Python服务

继续使用原有的 FastAPI 后端。

1. 部署原服务到服务器
2. 在小程序管理后台配置服务器域名白名单
3. 修改 `utils/api.js` 中的 `BASE_URL`
4. 云函数仅作为备选或不使用

**优点：**
- 保留原有AI分析能力
- 无需重写后端逻辑
- 可以复用缓存系统

## 🔧 API适配说明

### 原有API调用方式

```javascript
// H5方式
fetch('/api/analyze', {
  method: 'POST',
  body: JSON.stringify(data)
});
```

### 小程序调用方式

```javascript
// 方式1：云函数调用（推荐）
const cloud = require('../../utils/api');
await cloud.AnalyzeAPI.analyzeLight(data);

// 方式2：tt.request
tt.request({
  url: BASE_URL + '/api/analyze',
  method: 'POST',
  data: data,
  success: (res) => { /* ... */ }
});
```

## 💳 支付配置

### 抖音支付接入

1. 在抖音开放平台申请支付权限
2. 配置支付回调地址
3. 修改支付云函数中的逻辑

### 模拟支付（测试）

在 `pages/payment/payment.js` 中提供了模拟支付按钮，便于测试：

```javascript
// 模拟支付成功
simulatePayment: async function() {
  await PaymentAPI.simulatePayment(this.data.orderId);
  // ...
}
```

## 📊 数据迁移

### 从原SQLite迁移到云数据库

可以编写迁移脚本：

```javascript
// 迁移脚本示例
async function migrateFromSQLite() {
  // 1. 读取原 career.db
  // 2. 转换为云数据库格式
  // 3. 批量插入
}
```

### 缓存迁移

原缓存文件可以保留在服务器作为备选，新的缓存写入云数据库。

## 🔐 安全注意事项

1. **接口鉴权**：云函数通过 openid 自动鉴权
2. **数据加密**：敏感信息加密存储
3. **域名白名单**：只允许白名单域名访问
4. **支付验证**：服务端验证支付状态
5. **内容审核**：确保小程序内容符合抖音规范

## 🎨 样式适配

### 主要改动

1. `px` → `rpx` (响应式单位)
2. `class` → `ttss`
3. 新增移动端优化样式
4. 使用抖音UI规范

## 📝 注意事项

### 抖音审核规范

1. ❌ 移除所有外部链接跳转
2. ✅ 使用抖音登录
3. ✅ 使用抖音支付
4. ✅ 内容符合社区规范
5. ✅ 收集用户信息时明确告知

### 兼容性

- 支持抖音、抖音极速版、今日头条
- 不同版本UI略有调整

## 📚 相关文档

- [抖音小程序开发文档](https://developer.open-douyin.com/)
- [云开发文档](https://developer.open-douyin.com/docs/resource/zh-CN/mini-app/develop/cloud/guide/intro)
- [支付接入文档](https://developer.open-douyin.com/docs/resource/zh-CN/mini-app/develop/server/payment/payment-overview)

## 🔄 更新日志

### v1.0.0 (2026-05-14)
- 初始版本，从H5迁移
- 完成核心功能
- 支持云开发

## 💬 技术支持

如有问题，请参考原项目文档或联系开发团队。
