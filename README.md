# Telegram 自动签到脚本 (完美版 v3)

## 🚀 功能特性
- ✅ **10 个 Bot/频道自动签到**：内置你的专属签到列表，无需配置
- ✅ **防卡死设计**：全局超时控制、连接超时、自动断开
- ✅ **智能重试**：网络波动自动重试 3 次，Flood 限制自动等待
- ✅ **北京时间日志**：所有日志时间戳自动转换为北京时间 (UTC+8)
- ✅ **敏感信息脱敏**：日志自动过滤 Session、Token、IP 等敏感信息
- ✅ **自动运行**：每天北京时间 8:30 自动执行
- ✅ **环境兼容**：兼容 Python 3.11+ 和 Telethon 1.36+

## 📋 支持的签到列表
| Bot/频道用户名 | 签到命令 |
|---------------|----------|
| @sgkboxbot | /qd |
| @TBSGKBot | /sign |
| @xfhzjbot | /qd |
| @Kali_SGK_Bot | /checkin |
| @xdhz88bot | /qd |
| @Carll_Bomb_bot | /qd |
| @jdHappybot | /qd |
| @nb3344bot | /qd |
| @SGK76H | 签到 |
| @XFchart1 | 签到 | **(新增)** |

## ⚙️ 配置要求
在 GitHub Secrets (Settings → Secrets and variables → Actions) 中设置以下三个变量：

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `API_ID` | Telegram API ID (纯数字) | `12345678` |
| `API_HASH` | Telegram API Hash (字符串) | `a1b2c3d4e5f6...` |
| `SESSION` | Telegram Session 字符串 (长字符串) | `1B5...` |

### 如何获取配置信息？

#### 1. 获取 API ID 和 API Hash
1. 访问 [my.telegram.org](https://my.telegram.org)
2. 使用你的手机号登录
3. 点击 **"API development tools"**
4. 创建一个新的应用（如果还没有）
5. 记录 `api_id` (数字) 和 `api_hash` (字符串)

#### 2. 获取 Session 字符串
**推荐方法（本地生成，安全）：**
```bash
# 安装 Telethon
pip install telethon

# 创建文件 get_session.py
cat > get_session.py << 'EOF'
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

api_id = YOUR_API_ID # 替换为你的数字 ID
api_hash = 'YOUR_API_HASH' # 替换为你的 Hash 字符串

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print(client.session.save())
EOF

# 运行脚本
python get_session.py
```
运行后会输出一长串字符，**复制它**作为 `SESSION`。

**注意**：
- **绝对不要**将 `SESSION` 发送给任何人（包括 AI）
- **绝对不要**将 `SESSION` 直接写在代码或公开文档中
- **只**在 GitHub Secrets 中填写 `SESSION`

## 🔄 运行方式
- **自动运行**：每天北京时间 **08:30** 自动触发
- **手动运行**：进入 Actions 标签页 → "Telegram Auto Sign-in" → "Run workflow"

## 📊 查看结果
1. 进入 **Actions** 标签页
2. 点击最新的运行记录
3. 查看日志中的 `✅ 成功` 或 `❌ 失败` 状态
4. 日志时间均为 **北京时间**

## ⚠️ 注意事项
1. **账号安全**：确保 Telegram 账号已登录，建议开启两步验证
2. **频率限制**：脚本已内置防 Flood 机制，请勿频繁手动触发
3. **Session 过期**：如果提示 `AuthKeyUnregistered`，请重新生成 Session 并更新 Secrets
4. **公开仓库**：本仓库为公开项目，日志已做脱敏处理，但仍请妥善保管 Secrets

## 🐛 故障排查

| 错误信息 | 原因 | 解决方案 |
|---------|------|---------|
| `AuthKeyUnregisteredError` | Session 过期或失效 | 重新生成 Session 并更新 Secrets |
| `ApiIdInvalidError` | API_ID/Hash 错误 | 检查 my.telegram.org 配置 |
| `SessionPasswordNeededError` | 需要两步验证密码 | 本地登录开启验证后重新生成 Session |
| `FloodWaitError` | 触发频率限制 | 脚本会自动等待，无需操作 |
| `TimeoutError` | 网络超时 | 脚本会自动重试，如持续失败请检查网络 |
| `连接超时` | Telegram 服务器无响应 | 检查网络环境，稍后重试 |
| `凭证缺失` | Secrets 未配置 | 检查 Settings → Secrets 是否已设置三个变量 |

## 🛡️ 安全说明
- 所有敏感信息（API_ID, API_HASH, SESSION）均通过 **GitHub Secrets** 管理
- 代码中**绝不硬编码**任何密钥
- 日志输出自动**脱敏**，防止泄露敏感信息
- 建议定期更新 Session 字符串（每 3-6 个月）

---
**最后更新**：2026-04-24 
**版本**：v3.0 (完美版 - 新增 @XFchart1) 
**维护者**：wang1520166813