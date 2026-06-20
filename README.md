# UR空房监控机器人

自动监控UR租赁住宅的空房信息，发现新空房时通过Telegram通知。

## 功能

- 🔍 每5分钟检查一次指定UR物件的空房
- 📨 发现新空房时自动发送Telegram通知
- 📊 支持 `/status` 命令查询实时状态
- 🆓 完全免费运行（GitHub Actions）

## 部署

### 1. 创建Telegram Bot
1. 在Telegram中搜索 `@BotFather`
2. 发送 `/newbot` 创建新机器人
3. 获取Bot Token
4. 获取您的Chat ID

### 2. 配置GitHub Secrets
在仓库的 Settings → Secrets and variables → Actions 中添加：

- `TELEGRAM_BOT_TOKEN`: 您的Bot Token
- `TELEGRAM_CHAT_ID`: 您的Chat ID

### 3. 部署到GitHub
Fork此仓库，GitHub Actions会自动开始运行。

## 命令

- `/status` - 查看当前空房状态
- `/check` - 手动触发检查
- `/help` - 显示帮助信息

## 配置

修改 `src/config.py` 中的 `UR_TARGETS` 来监控其他物件。

## 注意事项

- 命令响应有0-5分钟延迟
- 使用Public仓库才能完全免费
- 监控时间：每天10:00-20:00

## 许可证

MIT
