#!/usr/bin/env python3
"""
测试修复后的消息发送代码
"""

import asyncio

# 模拟AstrBot环境
class MockLogger:
    def info(self, msg): print(f"[INFO] {msg}")
    def error(self, msg): print(f"[ERROR] {msg}")

class MockMessageChain:
    def __init__(self):
        self._messages = []
    
    def message(self, text):
        self._messages.append(text)
        return self
    
    def __repr__(self):
        return f"MessageChain({self._messages})"

class MockContext:
    async def send_message(self, unified_msg_origin, message_chain):
        """模拟Context的send_message方法"""
        print(f"✅ 发送消息到: {unified_msg_origin}")
        print(f"   消息链: {message_chain}")
        return True

async def test_fixed_message_sending():
    """测试修复后的消息发送逻辑"""
    print("=== 测试修复后的AstrBot消息发送格式 ===")
    
    # 模拟数据
    context = MockContext()
    MessageChain = MockMessageChain
    logger = MockLogger()
    
    # 测试数据
    target_groups = ["410015005", "987654321"]
    new_posts = [
        {
            'title': '测试帖子标题1',
            'url': 'https://example.com/post/123'
        },
        {
            'title': '这是一个很长的标题，应该会被截断显示',
            'url': 'https://example.com/post/456'
        }
    ]
    max_title_length = 50
    
    print("测试修复后的消息发送逻辑:")
    
    for post in new_posts:
        title = post['title']
        if len(title) > max_title_length:
            title = title[:max_title_length] + "..."
        
        message = f"🆕 Unikorn论坛新帖子\n\n📝 {title}\n🔗 {post['url']}"
        
        # 发送到每个配置的群
        for group_id in target_groups:
            try:
                # 构造消息链 - 使用正确的MessageChain方式
                message_chain = MessageChain().message(message)
                
                # 构造unified_msg_origin
                unified_msg_origin = f"qq_group_{group_id}"
                
                # 使用context发送消息
                await context.send_message(unified_msg_origin, message_chain)
                logger.info(f"已向群 {group_id} 推送新帖子: {title}")
            except Exception as e:
                logger.error(f"向群 {group_id} 推送消息失败: {e}")
        
        print()

if __name__ == "__main__":
    asyncio.run(test_fixed_message_sending())
