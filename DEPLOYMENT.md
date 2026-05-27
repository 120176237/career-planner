# 部署指南 - 职路星途抖音小程序

本指南详细说明如何将原H5项目完整迁移并部署到抖音小程序。

---

## 📋 部署前检查清单

- [ ] 已注册抖音小程序账号
- [ ] 已获取小程序 AppID
- [ ] 已安装字节跳动开发者工具
- [ ] 已规划后端部署方案（云开发 or 保留原服务）
- [ ] 已准备好AI API密钥（如使用）
- [ ] 已申请支付权限（如需）

---

## 🎯 部署方案选择

### 方案A：全云开发（推荐用于新项目）

| 组件 | 部署方式 |
|-----|---------|
| 前端 | 抖音小程序 |
| 后端 | 云函数 |
| 数据库 | 云数据库 |
| AI分析 | 云函数内实现 |

**适用场景：**
- 新项目或希望完全迁移到云开发
- 不需要复杂的AI分析能力
- 希望减少运维成本

### 方案B：混合部署（推荐）

| 组件 | 部署方式 |
|-----|---------|
| 前端 | 抖音小程序 |
| 后端API | 保留原FastAPI服务 |
| 数据库 | 保留原SQLite |
| 云函数 | 支付、咨询等 |

**适用场景：**
- 保留原有AI分析能力
- 已有服务器资源
- 平滑过渡

### 方案C：保留原服务

| 组件 | 部署方式 |
|-----|---------|
| 前端 | 抖音小程序 |
| 后端 | 原FastAPI服务 |
| 云函数 | 不使用 |

**适用场景：**
- 后端逻辑复杂
- 需要快速上线
- 后期再考虑迁移

---

## 🚀 方案B部署步骤（推荐）

### 第一步：配置小程序

1. **修改基础配置**

   编辑 `project.config.json`:
   ```json
   {
     "appid": "your-appid-here", // 替换为你的AppID
     "projectname": "职路星途"
   }
   ```

2. **配置服务器域名**

   在[抖音开放平台](https://developer.open-douyin.com/)配置域名白名单：
   - request合法域名：`https://your-api-domain.com`
   - uploadFile合法域名：（如需要）
   - downloadFile合法域名：（如需要）

3. **修改API地址**

   编辑 `utils/api.js`:
   ```javascript
   const BASE_URL = 'https://your-api-domain.com'; // 替换为你的API域名
   ```

### 第二步：部署后端服务

1. **确保原服务正常运行**

   原服务部署步骤：
   ```bash
   cd 职路星途_发布版_20260514
   pip install -r requirements.txt
   python server.py
   ```

2. **配置域名和HTTPS**

   - 使用 Nginx 或其他反向代理
   - 配置 SSL 证书（Let's Encrypt 免费）
   - 确保 API 可以通过 HTTPS 访问

3. **配置CORS**

   确保后端允许小程序域名访问：
   ```python
   # 在 server.py 中已配置，无需修改
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # 生产环境应该限制
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

### 第三步：部署支付和咨询云函数

1. **开通云开发**

   在开发者工具中：
   - 点击「云开发」按钮
   - 创建云环境（如：`zhiluxingtu-prod`）
   - 免费版足够初期使用

2. **修改云环境ID**

   编辑 `app.js`:
   ```javascript
   tt.cloud.init({
     env: 'zhiluxingtu-prod', // 替换为你的环境ID
     traceUser: true
   });
   ```

3. **创建数据库集合**

   在云开发控制台创建：
   - `orders`
   - `user_privileges`
   - `vip_consults`

4. **上传云函数**

   在开发者工具中：
   - 右键 `cloudfunctions/analyze`
   - 选择「上传并部署：云端安装依赖」
   - 重复此步骤部署 `payment` 和 `vip-consult`

### 第四步：测试

1. **在开发者工具中测试**

   - 打开小程序
   - 选择用户类型
   - 完成测评
   - 检查结果是否正常显示

2. **真机测试**

   - 点击「预览」
   - 使用抖音扫码
   - 在真机上测试完整流程

---

## ☁️ 方案A部署步骤（全云开发）

### 第一步：完整云开发配置

1. **开通云开发环境**（同上）

2. **上传所有云函数**

   部署 `analyze`, `payment`, `vip-consult`

3. **创建完整的数据库集合**

   | 集合 | 索引建议 |
   |-----|---------|
   | analysis_cache | cacheKey, version, userType |
   | analysis_records | openid, createdAt |
   | orders | orderId, openid |
   | user_privileges | openid, validUntil |
   | vip_consults | consultId, openid |

### 第二步：迁移行业数据库

将原 `server.py` 中的行业数据复制到云函数中。

### 第三步：实现AI分析

**选项1：使用云函数+HTTP调用AI**

```javascript
// 在云函数中调用AI API
const aiResponse = await cloud.callFunction({
  name: 'ai-analyze',
  data: prompt
});
```

**选项2：使用本地算法**

将评分算法移植到云函数中（已在示例中实现）。

---

## 💳 支付配置（正式上线前）

### 申请支付权限

1. 在抖音开放平台提交支付申请
2. 提供相关资质
3. 等待审核通过

### 配置支付

1. 获取支付密钥
2. 在云函数中配置
3. 实现支付回调处理
4. 测试支付流程

### 支付安全注意事项

- ⚠️ 金额在服务端校验
- ⚠️ 订单在服务端创建
- ⚠️ 支付结果在服务端验证
- ⚠️ 保存完整的支付记录

---

## 🔒 安全配置

### 配置云数据库权限

在云开发控制台设置各集合的权限：

| 集合 | 权限 | 说明 |
|-----|------|------|
| analysis_cache | 所有用户可读，仅创建者可写 | 缓存可以共享 |
| orders | 所有用户不可读写 | 敏感数据 |
| user_privileges | 仅创建者可读写 | 用户权限 |
| vip_consults | 仅创建者可读写 | 咨询数据 |

### 配置云函数安全

- 验证 openid
- 输入参数校验
- 操作权限检查

---

## 📱 小程序发布流程

### 1. 提交审核

1. 在开发者工具点击「上传」
2. 填写版本号和备注
3. 在开放平台提交审核
4. 等待审核通过（1-3个工作日）

### 2. 审核注意事项

✅ 确保内容符合抖音社区规范
✅ 移除外部链接
✅ 明确的隐私政策
✅ 真实的功能描述
✅ 必要的类目选择

### 3. 正式发布

审核通过后，点击「发布」即可。

---

## 🔄 数据迁移方案

### 从原SQLite迁移到云数据库

编写迁移脚本：

```python
# migration.py
import sqlite3
import json
from datetime import datetime

# 连接SQLite
conn = sqlite3.connect('career.db')
cursor = conn.cursor()

# 迁移VIP咨询
cursor.execute('SELECT * FROM vip_consults')
rows = cursor.fetchall()

# 转换为云数据库格式并导出
# ...
```

### 从文件缓存迁移到云数据库

解析原缓存JSON文件，写入云数据库。

---

## 📊 监控与维护

### 云开发监控

在云开发控制台查看：
- 云函数调用次数
- 数据库读写次数
- 错误日志
- 性能数据

### 小程序后台

在开放平台查看：
- 用户数据
- 访问分析
- 转化漏斗
- 异常监控

---

## 🚨 常见问题

### Q: AI分析功能怎么处理？

A: 
- 方案1：保留原服务，小程序通过API调用
- 方案2：将AI分析逻辑移植到云函数
- 方案3：使用第三方AI服务

### Q: 缓存怎么办？

A:
- 可以两层缓存：云数据库+原服务缓存
- 或者全部迁移到云数据库

### Q: 支付必须接入抖音支付吗？

A:
- 是的，小程序内支付必须使用抖音支付
- 可以暂时用模拟支付测试

### Q: 审核需要注意什么？

A:
- 不要有外部链接
- 内容合规
- 类目选择准确
- 提供必要的资质

---

## 📚 相关资源

- [抖音小程序文档](https://developer.open-douyin.com/)
- [云开发文档](https://developer.open-douyin.com/docs/resource/zh-CN/mini-app/develop/cloud/guide/intro)
- [支付接入](https://developer.open-douyin.com/docs/resource/zh-CN/mini-app/develop/server/payment/payment-overview)
- [社区规范](https://developer.open-douyin.com/docs/resource/zh-CN/mini-app/operation/settle/service-specification/standard-intro)

---

## 💡 最佳实践

1. **渐进式迁移**：先迁移前端，后端保持不变
2. **保留原服务**：作为备份和降级方案
3. **充分测试**：真机测试非常重要
4. **监控数据**：上线后密切关注数据
5. **快速迭代**：根据反馈优化

---

如有部署问题，请参考原项目文档或联系技术支持。
