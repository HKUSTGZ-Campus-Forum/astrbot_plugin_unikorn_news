#!/usr/bin/env python3
"""
测试协议端API功能的模拟脚本
"""

import asyncio

class MockLogger:
    def info(self, msg): print(f"[INFO] {msg}")
    def error(self, msg): print(f"[ERROR] {msg}")

class MockClient:
    class API:
        async def call_action(self, action_name, **kwargs):
            """模拟协议端API调用"""
            print(f"🔧 API调用: {action_name}")
            print(f"   参数: {kwargs}")
            
            # 模拟不同API的返回值
            if action_name == 'get_group_info':
                return {
                    'group_id': kwargs.get('group_id', 12345),
                    'group_name': '测试群聊',
                    'member_count': 150
                }
            elif action_name == 'get_login_info':
                return {
                    'user_id': 123456789,
                    'nickname': 'UnikornBot'
                }
            elif action_name == 'send_group_msg':
                return {
                    'message_id': 98765
                }
            elif action_name == 'send_private_msg':
                return {
                    'message_id': 98766
                }
            elif action_name == 'delete_msg':
                return {
                    'retcode': 0
                }
            elif action_name == 'get_group_member_list':
                # 模拟群成员列表
                return [
                    {'user_id': 111, 'nickname': '群主', 'role': 'owner'},
                    {'user_id': 222, 'nickname': '管理员1', 'role': 'admin'},
                    {'user_id': 333, 'nickname': '管理员2', 'role': 'admin'},
                    {'user_id': 444, 'nickname': '成员1', 'role': 'member'},
                    {'user_id': 555, 'nickname': '成员2', 'role': 'member'},
                    {'user_id': 666, 'nickname': '成员3', 'role': 'member'},
                ]
            else:
                return {'retcode': 0, 'data': None}
    
    def __init__(self):
        self.api = self.API()

class MockMessageObj:
    def __init__(self, group_id="12345", message_id="54321"):
        self.group_id = group_id
        self.message_id = message_id

class MockAiocqhttpMessageEvent:
    def __init__(self, sender_id="999888777", platform_name="aiocqhttp"):
        self.bot = MockClient()
        self.message_obj = MockMessageObj()
        self._sender_id = sender_id
        self._platform_name = platform_name
    
    def get_platform_name(self):
        return self._platform_name
    
    def get_sender_id(self):
        return self._sender_id
    
    def plain_result(self, text):
        print(f"📨 回复消息: {text}")
        return text

async def test_aiocqhttp_api_features():
    """测试协议端API功能"""
    print("=== 测试 AstrBot aiocqhttp 协议端 API 功能 ===\n")
    
    logger = MockLogger()
    
    # 模拟配置
    config = {
        'admin_qq_list': ['999888777', '111222333'],
        'target_groups': ['12345', '67890']
    }
    
    # 测试数据
    admin_event = MockAiocqhttpMessageEvent("999888777", "aiocqhttp")
    normal_event = MockAiocqhttpMessageEvent("444555666", "aiocqhttp")
    telegram_event = MockAiocqhttpMessageEvent("999888777", "telegram")
    
    print("1. 测试协议端API演示功能 (/unikorn recall)")
    print("=" * 50)
    
    async def test_recall_command(event, test_name):
        print(f"\n{test_name}:")
        print(f"发送者: {event.get_sender_id()}, 平台: {event.get_platform_name()}")
        
        # 检查平台
        if event.get_platform_name() != "aiocqhttp":
            print("❌ 此功能仅支持QQ平台（aiocqhttp）")
            return
        
        # 检查管理员权限
        admin_qq_list = config.get("admin_qq_list", [])
        sender_id = event.get_sender_id()
        
        if admin_qq_list and sender_id not in admin_qq_list:
            print("❌ 仅管理员可以使用此功能")
            return
        
        print("✅ 权限验证通过")
        
        # 模拟协议端API调用
        client = event.bot
        
        # 1. 获取群信息
        try:
            group_info = await client.api.call_action('get_group_info', group_id=int(event.message_obj.group_id))
            print(f"✅ 群信息获取成功: {group_info}")
        except Exception as e:
            print(f"❌ 获取群信息失败: {e}")
        
        # 2. 获取登录信息
        try:
            login_info = await client.api.call_action('get_login_info')
            print(f"✅ 登录信息获取成功: {login_info}")
        except Exception as e:
            print(f"❌ 获取登录信息失败: {e}")
        
        # 3. 发送并撤回消息
        try:
            # 发送消息
            send_result = await client.api.call_action('send_group_msg', 
                                                     group_id=int(event.message_obj.group_id),
                                                     message="🧪 这是一条测试消息，3秒后将被撤回...")
            print(f"✅ 消息发送成功: {send_result}")
            
            message_id = send_result.get('message_id')
            if message_id:
                # 模拟等待3秒
                print("⏳ 等待3秒...")
                await asyncio.sleep(1)  # 简化为1秒
                
                # 撤回消息
                recall_result = await client.api.call_action('delete_msg', message_id=message_id)
                print(f"✅ 消息撤回成功: {recall_result}")
            
        except Exception as e:
            print(f"❌ 消息操作失败: {e}")
    
    # 测试不同情况
    await test_recall_command(admin_event, "管理员用户 + QQ平台")
    await test_recall_command(normal_event, "普通用户 + QQ平台")  
    await test_recall_command(telegram_event, "管理员用户 + Telegram平台")
    
    print("\n\n2. 测试群成员统计功能 (/unikorn groupmembers)")
    print("=" * 50)
    
    async def test_group_members_command(event, test_name):
        print(f"\n{test_name}:")
        
        # 检查平台和权限
        if event.get_platform_name() != "aiocqhttp":
            print("❌ 此功能仅支持QQ平台（aiocqhttp）")
            return
            
        admin_qq_list = config.get("admin_qq_list", [])
        sender_id = event.get_sender_id()
        
        if admin_qq_list and sender_id not in admin_qq_list:
            print("❌ 仅管理员可以使用此功能")
            return
        
        if not event.message_obj.group_id:
            print("❌ 此功能仅在群聊中可用")
            return
        
        print("✅ 权限验证通过")
        
        client = event.bot
        group_id = int(event.message_obj.group_id)
        
        try:
            # 获取群成员列表
            member_list = await client.api.call_action('get_group_member_list', group_id=group_id)
            print(f"✅ 获取到群成员列表，共 {len(member_list)} 人")
            
            # 统计不同角色
            owners = [m for m in member_list if m.get('role') == 'owner']
            admins = [m for m in member_list if m.get('role') == 'admin']
            members = [m for m in member_list if m.get('role') == 'member']
            
            print(f"👑 群主: {len(owners)} 人")
            print(f"🛡️ 管理员: {len(admins)} 人")
            print(f"👤 普通成员: {len(members)} 人")
            print(f"📊 总计: {len(member_list)} 人")
            
        except Exception as e:
            print(f"❌ 获取群成员列表失败: {e}")
    
    await test_group_members_command(admin_event, "管理员用户测试群成员统计")
    await test_group_members_command(normal_event, "普通用户测试群成员统计")
    
    print("\n\n3. 测试帮助指令显示 (/unikorn)")
    print("=" * 50)
    
    def test_help_command(event, test_name):
        print(f"\n{test_name}:")
        
        admin_qq_list = config.get("admin_qq_list", [])
        sender_id = event.get_sender_id()
        is_admin = sender_id in admin_qq_list if admin_qq_list else False
        
        basic_commands = (
            "📋 基本指令:\n"
            "/unikorn status - 查看监控状态\n"
            "/unikorn check - 手动检查更新\n"
            "/unikorn start - 启动监控\n"
            "/unikorn stop - 停止监控\n"
            "/unikorn posts - 查看最新帖子"
        )
        
        admin_commands = (
            "\n\n🔧 管理员指令 (需配置admin_qq_list):\n"
            "/unikorn recall - 协议端API演示（消息撤回等）\n"
            "/unikorn groupmembers - 获取群成员统计"
        )
        
        message = "🦄 Unikorn论坛监控插件\n\n" + basic_commands
        
        if is_admin and event.get_platform_name() == "aiocqhttp":
            message += admin_commands
            status = "✅ 显示管理员指令"
        elif admin_qq_list and event.get_platform_name() == "aiocqhttp":
            message += "\n\n💡 提示: 您不在管理员列表中，无法使用高级功能"
            status = "⚠️ 显示权限提示"
        elif event.get_platform_name() != "aiocqhttp":
            message += "\n\n💡 提示: 协议端API功能仅在QQ平台(aiocqhttp)可用"
            status = "⚠️ 显示平台提示"
        else:
            status = "📋 仅显示基本指令"
        
        print(f"状态: {status}")
        print(f"帮助内容:\n{message}")
    
    test_help_command(admin_event, "管理员查看帮助 (QQ平台)")
    test_help_command(normal_event, "普通用户查看帮助 (QQ平台)")
    test_help_command(telegram_event, "管理员查看帮助 (Telegram平台)")
    
    print("\n\n✅ 协议端API功能测试完成！")

if __name__ == "__main__":
    asyncio.run(test_aiocqhttp_api_features())
