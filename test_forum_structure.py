#!/usr/bin/env python3
"""
测试论坛网页结构和筛选机制的脚本
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def analyze_forum_structure():
    """分析论坛网页结构"""
    print("=== 分析 Unikorn 论坛网页结构 ===\n")
    
    forum_url = "https://unikorn.axfff.com/forum"
    
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=30),
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    ) as session:
        try:
            async with session.get(forum_url) as response:
                if response.status != 200:
                    print(f"❌ 获取页面失败，状态码: {response.status}")
                    return
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                print("1. 页面基本信息")
                print("=" * 40)
                title = soup.find('title')
                print(f"页面标题: {title.text if title else '未找到'}")
                
                # 查找页面主要容器
                print(f"\n2. 主要容器结构")
                print("=" * 40)
                
                posts_container = soup.find('div', class_='posts-container')
                if posts_container:
                    print("✅ 找到 posts-container")
                    
                    page_title = posts_container.find('h1', class_='page-title')
                    if page_title:
                        print(f"页面标题: {page_title.text.strip()}")
                    
                    posts_list = posts_container.find('div', class_='posts-list')
                    if posts_list:
                        print(f"posts-list 内容: {len(posts_list.find_all())} 个子元素")
                        print(f"posts-list HTML: {str(posts_list)[:200]}...")
                else:
                    print("❌ 未找到 posts-container")
                
                # 查找所有可能的帖子链接
                print(f"\n3. 所有 <a> 标签分析")
                print("=" * 40)
                
                all_links = soup.find_all('a', href=True)
                print(f"总共找到 {len(all_links)} 个链接")
                
                for i, link in enumerate(all_links, 1):
                    href = link.get('href', '')
                    text = link.get_text(strip=True)
                    classes = link.get('class', [])
                    
                    print(f"{i:2d}. href='{href}' text='{text}' class={classes}")
                
                # 查找包含"发帖"的元素
                print(f"\n4. 发帖相关元素")
                print("=" * 40)
                
                post_buttons = soup.find_all(text=lambda t: t and '发帖' in t)
                for i, button_text in enumerate(post_buttons, 1):
                    parent = button_text.parent
                    print(f"{i}. 文本: '{button_text.strip()}'")
                    print(f"   父元素: {parent.name if parent else 'None'}")
                    print(f"   父元素类: {parent.get('class', []) if parent else []}")
                    print(f"   完整HTML: {str(parent)[:150]}...")
                    print()
                
                # 测试我们的筛选逻辑
                print(f"\n5. 测试筛选逻辑")
                print("=" * 40)
                
                # 测试文本筛选
                test_texts = [
                    "我要发帖",
                    "发帖",
                    "论坛文章",
                    "排序方式",
                    "上一页",
                    "下一页",
                    "登录",
                    "注册"
                ]
                
                excluded_keywords = [
                    '发帖', '登录', '注册', '排序', '筛选', '页', '菜单', 
                    '导航', '搜索', '设置', '帮助', '关于'
                ]
                
                def is_button_text(text):
                    if not text or len(text.strip()) < 2:
                        return True
                    
                    # 常见按钮文本模式
                    button_patterns = [
                        r'^(点击|按钮|确定|取消|提交|重置|保存|删除|编辑|修改|添加|新增)',
                        r'(发帖|登录|注册|搜索|筛选|排序|切换|展开|收起)$',
                        r'^(上一页|下一页|首页|末页|第\s*\d+\s*页)',
                        r'^(更多|查看|详情|展示|显示|隐藏)$'
                    ]
                    
                    import re
                    text_clean = text.strip()
                    for pattern in button_patterns:
                        if re.search(pattern, text_clean):
                            return True
                    
                    return False
                
                def is_excluded_content(text):
                    if not text:
                        return True
                    
                    text_lower = text.lower().strip()
                    return any(keyword.lower() in text_lower for keyword in excluded_keywords)
                
                print("测试按钮文本检测:")
                for text in test_texts:
                    is_button = is_button_text(text)
                    is_excluded = is_excluded_content(text)
                    print(f"  '{text}' -> 按钮: {is_button}, 排除: {is_excluded}")
                
                # 分析JavaScript加载的数据
                print(f"\n6. JavaScript数据分析")
                print("=" * 40)
                
                scripts = soup.find_all('script')
                nuxt_data = None
                for script in scripts:
                    if script.get('id') == '__NUXT_DATA__':
                        nuxt_data = script.string
                        break
                
                if nuxt_data:
                    print("✅ 找到 NUXT 数据")
                    print(f"数据长度: {len(nuxt_data)} 字符")
                    # 尝试查找与帖子相关的数据
                    if '"posts"' in nuxt_data or '"articles"' in nuxt_data:
                        print("✅ 数据中包含帖子信息")
                    else:
                        print("⚠️ 数据中未直接找到帖子信息")
                else:
                    print("❌ 未找到 NUXT 数据")
                
                print(f"\n7. 总结")
                print("=" * 40)
                print("🔍 发现的问题:")
                print("1. 这是一个 Nuxt.js SPA，帖子内容通过 JavaScript 动态加载")
                print("2. 静态HTML中只包含页面框架，没有实际帖子内容")
                print("3. '我要发帖' 按钮确实存在于静态HTML中")
                print("4. 需要等待 JavaScript 执行或使用API获取实际帖子数据")
                
                print(f"\n💡 建议的解决方案:")
                print("1. 增强按钮和导航元素的筛选逻辑")
                print("2. 添加对空内容的检测")
                print("3. 考虑使用 Selenium 或其他渲染引擎")
                print("4. 查找是否有直接的API端点")
                
        except Exception as e:
            print(f"❌ 分析过程中出错: {e}")

if __name__ == "__main__":
    asyncio.run(analyze_forum_structure())
