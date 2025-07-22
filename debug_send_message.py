#!/usr/bin/env python3
"""
调试脚本：检查消息发送方法的正确性
"""

import sys
import os

# 模拟AstrBot环境
class MockLogger:
    def info(self, msg): print(f"[INFO] {msg}")
    def error(self, msg): print(f"[ERROR] {msg}")
    def debug(self, msg): print(f"[DEBUG] {msg}")
    def warning(self, msg): print(f"[WARNING] {msg}")

class MockComp:
    class Plain:
        def __init__(self, text):
            self.text = text
        def __repr__(self):
            return f"Plain('{self.text}')"

class MockContext:
    async def send_message(self, unified_msg_origin, message_chain):
        """模拟Context的send_message方法"""
        print(f"发送消息到: {unified_msg_origin}")
        print(f"消息链: {message_chain}")
        print(f"消息内容: {[str(msg) for msg in message_chain]}")
        return True

async def test_message_sending():
    """测试消息发送逻辑"""
    print("=== 测试AstrBot消息发送格式 ===")
    
    # 模拟数据
    context = MockContext()
    Comp = MockComp
    logger = MockLogger()
    
    # 测试数据
    target_groups = ["123456789", "987654321"]
    post = {
        'title': '测试帖子标题',
        'url': 'https://example.com/post/123'
    }
    
    print("1. 测试当前代码的消息发送逻辑:")
    
    for group_id in target_groups:
        try:
            message = f"🆕 Unikorn论坛新帖子\n\n📝 {post['title']}\n🔗 {post['url']}"
            
            # 构造消息链
            chain = [Comp.Plain(message)]
            
            # 根据AstrBot文档的建议格式构造unified_msg_origin
            unified_msg_origin = f"qq_group_{group_id}"
            
            # 使用context发送消息
            await context.send_message(unified_msg_origin, chain)
            logger.info(f"已向群 {group_id} 推送新帖子: {post['title']}")
            
        except Exception as e:
            logger.error(f"向群 {group_id} 推送消息失败: {e}")
    
    print("\n2. 测试可能的替代方案:")
    
    # 方案1: 使用broadcast方法
    if hasattr(context, 'broadcast'):
        print("测试broadcast方法...")
        message = f"🆕 Unikorn论坛新帖子\n\n📝 {post['title']}\n🔗 {post['url']}"
        try:
            # await context.broadcast(target_groups, [Comp.Plain(message)])
            print("broadcast方法可能的调用方式:")
            print(f"  context.broadcast({target_groups}, [Comp.Plain(message)])")
        except Exception as e:
            print(f"broadcast方法失败: {e}")
    
    # 方案2: 检查unified_msg_origin格式
    print("\n测试不同的unified_msg_origin格式:")
    formats = [
        f"qq_group_{target_groups[0]}",  # 当前使用的格式
        f"qq-group-{target_groups[0]}",  # 可能的替代格式
        f"group_{target_groups[0]}",     # 简化格式
        target_groups[0]                 # 直接使用群号
    ]
    
    for fmt in formats:
        print(f"  格式: {fmt}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_message_sending())
