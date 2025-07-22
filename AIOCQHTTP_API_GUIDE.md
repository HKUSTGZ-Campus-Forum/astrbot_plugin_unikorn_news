# AstrBot aiocqhttp 协议端 API 使用指南

## 概述

AstrBot 支持直接调用 aiocqhttp 协议端的 API，这允许你使用更底层的 QQ 机器人功能。本插件演示了如何在实际项目中使用这些 API。

## 🔧 新增功能

### 1. 协议端 API 演示功能

#### `/unikorn recall` - API 调用演示
这个指令演示了多个常用的协议端 API：

- **获取群信息** - `get_group_info`
- **获取机器人信息** - `get_login_info`  
- **发送消息** - `send_group_msg` / `send_private_msg`
- **撤回消息** - `delete_msg`

#### `/unikorn groupmembers` - 群成员统计
使用 `get_group_member_list` API 获取群成员信息并进行统计。

## 💡 实现原理

### 1. 平台检测
```python
if event.get_platform_name() != "aiocqhttp":
    yield event.plain_result("❌ 此功能仅支持QQ平台（aiocqhttp）")
    return
```

### 2. 获取协议端客户端
```python
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent

if isinstance(event, AiocqhttpMessageEvent):
    client = event.bot  # 获取协议端客户端
```

### 3. 调用协议端 API
```python
# 基本调用格式
result = await client.api.call_action('api_name', **parameters)

# 具体示例
group_info = await client.api.call_action('get_group_info', group_id=12345)
send_result = await client.api.call_action('send_group_msg', 
                                         group_id=12345, 
                                         message="Hello World")
```

## 📋 常用 API 列表

### 消息相关
- `send_private_msg` - 发送私聊消息
- `send_group_msg` - 发送群消息  
- `delete_msg` - 撤回消息
- `get_msg` - 获取消息详情

### 群管理
- `get_group_info` - 获取群信息
- `get_group_list` - 获取群列表
- `get_group_member_info` - 获取群成员信息
- `get_group_member_list` - 获取群成员列表
- `set_group_kick` - 踢出群成员
- `set_group_ban` - 禁言群成员

### 用户信息
- `get_login_info` - 获取登录账号信息
- `get_stranger_info` - 获取陌生人信息
- `get_friend_list` - 获取好友列表

## ⚙️ 配置说明

在 `_conf_schema.json` 中新增了管理员配置：

```json
{
  "admin_qq_list": {
    "description": "管理员QQ列表",
    "type": "list", 
    "default": [],
    "hint": "可以使用高级功能的管理员QQ号列表"
  }
}
```

## 🚀 使用步骤

### 1. 配置管理员
在 AstrBot 管理面板中配置 `admin_qq_list`：
```json
["12345678", "87654321"]
```

### 2. 测试功能
在 QQ 群中发送：
- `/unikorn` - 查看所有可用指令
- `/unikorn recall` - 测试协议端 API（仅管理员）
- `/unikorn groupmembers` - 获取群成员统计（仅管理员）

### 3. 查看日志
在 AstrBot 日志中查看 API 调用结果：
```
[INFO] 群信息: {'group_id': 12345, 'group_name': '测试群', ...}
[INFO] 发送消息结果: {'message_id': 123}
[INFO] 撤回消息结果: {'retcode': 0}
```

## 🔗 API 文档参考

- **NapCat API**: https://napcat.apifox.cn/
- **Lagrange API**: https://lagrange-onebot.apifox.cn/
- **AstrBot 官方文档**: https://docs.astrbot.app/dev/star/plugin.html

## ⚠️ 注意事项

1. **平台限制**: 协议端 API 仅在 aiocqhttp 平台可用
2. **权限管理**: 敏感操作建议添加管理员验证
3. **错误处理**: API 调用可能失败，需要适当的异常处理
4. **频率限制**: 避免频繁调用 API，可能被风控
5. **数据格式**: 不同协议端 API 返回的数据格式可能略有差异

## 🎯 扩展建议

基于协议端 API，你可以实现更多高级功能：

1. **群管理机器人** - 自动踢人、禁言等
2. **消息统计** - 分析群聊活跃度
3. **自动回复** - 基于特定条件的智能回复
4. **数据采集** - 收集群信息用于分析
5. **安全防护** - 检测并处理恶意消息

## 📝 代码示例

### 自定义消息撤回功能
```python
@filter.command("recall_last")
async def recall_last_message(self, event: AstrMessageEvent):
    if event.get_platform_name() == "aiocqhttp":
        from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
        
        if isinstance(event, AiocqhttpMessageEvent):
            client = event.bot
            
            # 撤回指定消息
            await client.api.call_action('delete_msg', 
                                       message_id=target_message_id)
```

### 群成员管理
```python
@filter.command("kick_user")  
async def kick_user(self, event: AstrMessageEvent, user_id: str):
    if event.get_platform_name() == "aiocqhttp":
        from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
        
        if isinstance(event, AiocqhttpMessageEvent):
            client = event.bot
            
            # 踢出群成员
            await client.api.call_action('set_group_kick',
                                       group_id=int(event.message_obj.group_id),
                                       user_id=int(user_id))
```

通过这些示例，你可以根据需要实现更多自定义功能！
