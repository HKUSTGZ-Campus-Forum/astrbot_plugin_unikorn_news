# Unikorn论坛监控插件

这是一个AstrBot插件，用于监控Unikorn论坛的更新并自动推送新帖子到指定的QQ群。

## 功能特性

- 🔄 自动监控Unikorn论坛更新（默认每5分钟检查一次）
- 📱 自动推送新帖子到指定QQ群
- ⚙️ 可配置检查间隔和目标群
- 📋 支持手动检查和管理监控状态
- 💾 自动保存已知帖子，避免重复推送
- 🔧 协议端API演示功能（仅QQ平台管理员可用）

## 配置说明

插件支持以下配置项：

- `check_interval`: 检查间隔（分钟），默认5分钟
- `target_groups`: 目标QQ群号列表
- `enable_notification`: 是否启用自动推送
- `max_title_length`: 标题最大长度，超出会截断
- `admin_qq_list`: 管理员QQ列表（用于协议端API功能）

## 使用方法

### 基本指令

- `/unikorn` - 显示帮助信息
- `/unikorn status` - 查看监控状态
- `/unikorn check` - 手动检查更新
- `/unikorn start` - 启动监控
- `/unikorn stop` - 停止监控
- `/unikorn posts` - 查看最新帖子

### 高级指令（仅QQ平台管理员）

- `/unikorn recall` - 协议端API演示（消息发送/撤回等）
- `/unikorn groupmembers` - 获取群成员统计

### 配置步骤

1. 在AstrBot管理面板中找到"Unikorn论坛监控"插件
2. 点击"管理"进入配置页面
3. 设置`target_groups`为要推送的QQ群号列表
4. （可选）设置`admin_qq_list`为管理员QQ号列表，以使用高级功能
5. 调整其他配置项（可选）
6. 保存配置并重启插件

### 使用协议端API功能

1. 确保使用的是QQ平台（aiocqhttp）
2. 在配置中添加管理员QQ号到`admin_qq_list`
3. 使用`/unikorn recall`或`/unikorn groupmembers`测试功能
4. 查看详细使用说明：[AIOCQHTTP_API_GUIDE.md](AIOCQHTTP_API_GUIDE.md)

## 依赖包

- aiohttp>=3.8.0
- beautifulsoup4>=4.10.0
- lxml>=4.8.0

## 注意事项

- 需要确保机器人在目标QQ群中
- 建议不要设置过短的检查间隔，避免给服务器造成压力
- 如果网站结构发生变化，可能需要更新插件代码

## 版本历史

- v1.0.0: 初始版本，支持基本的论坛监控和推送功能
