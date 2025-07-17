# 安装和使用指南

## 🚀 安装步骤

1. **确保插件位于正确目录**
   ```
   AstrBot/data/plugins/astrbot_plugin_unikorn_news/
   ```

2. **安装依赖包**
   插件会自动安装所需的依赖包：
   - aiohttp>=3.8.0
   - beautifulsoup4>=4.10.0
   - lxml>=4.8.0

3. **重启AstrBot**
   重启AstrBot以加载新插件

## ⚙️ 配置插件

1. **打开AstrBot管理面板**
   - 在浏览器中访问AstrBot的Web管理界面
   - 通常是 `http://localhost:6185` (端口可能不同)

2. **找到插件设置**
   - 在左侧菜单中找到"插件管理"或"插件"
   - 找到"Unikorn论坛监控"插件
   - 点击"管理"或"配置"

3. **配置必要参数**
   - `target_groups`: **必须配置** - 输入要推送消息的QQ群号列表
     ```json
     ["123456789", "987654321"]
     ```
   - `check_interval`: 检查间隔（分钟），默认5分钟
   - `enable_notification`: 是否启用自动推送，默认true
   - `max_title_length`: 标题最大长度，默认50字符

4. **保存配置**
   点击保存按钮保存配置

## 🎯 使用方法

### 基本指令

在QQ中发送以下指令：

```
/unikorn                    # 显示帮助信息
/unikorn status            # 查看监控状态
/unikorn check             # 手动检查更新
/unikorn start             # 启动监控
/unikorn stop              # 停止监控
/unikorn posts             # 查看最新帖子
```

### 自动监控

配置完成后，插件会：
1. 自动每5分钟（或配置的间隔）检查论坛
2. 发现新帖子时自动推送到配置的QQ群
3. 避免重复推送已知的帖子

### 推送消息格式

```
🆕 Unikorn论坛新帖子

📝 [帖子标题]
🔗 [帖子链接]
```

## 🛠️ 故障排除

### 1. 插件无法加载
- 检查Python语法是否正确
- 确保所有依赖包已安装
- 查看AstrBot日志获取错误信息

### 2. 无法推送到QQ群
- 确保机器人已加入目标QQ群
- 检查群号配置是否正确
- 确认机器人在群里有发言权限

### 3. 检测不到新帖子
- 手动运行 `/unikorn check` 测试
- 检查网络连接
- 论坛网站结构可能发生变化

### 4. 推送频率问题
- 调整 `check_interval` 配置
- 不建议设置过短的间隔（<3分钟）

## 📝 注意事项

1. **合理设置检查间隔**：避免给目标网站造成过大压力
2. **权限确认**：确保机器人在目标群有发言权限
3. **网络稳定**：确保服务器网络稳定，能正常访问目标网站
4. **数据备份**：插件会自动保存已知帖子数据到 `data/unikorn_news_data.json`

## 🔧 高级配置

如果论坛网站结构发生变化，可能需要修改 `main.py` 中的网页解析逻辑：

```python
# 在 fetch_forum_posts 方法中调整选择器
post_elements = soup.find_all(['div', 'article', 'li'], class_=lambda x: x and any(
    keyword in str(x).lower() for keyword in ['post', 'topic', 'thread', 'item', 'article']
))
```

## 📞 支持

如有问题，请：
1. 查看AstrBot日志
2. 检查插件配置
3. 尝试手动执行检查指令
4. 联系插件开发者或AstrBot社区
