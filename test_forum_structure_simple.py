#!/usr/bin/env python3
"""
使用内置库分析论坛网页结构的脚本
"""

import urllib.request
import urllib.error
import re
from html import unescape

def analyze_forum_structure():
    """分析论坛网页结构"""
    print("=== 分析 Unikorn 论坛网页结构 ===\n")
    
    forum_url = "https://unikorn.axfff.com/forum"
    
    try:
        # 创建请求
        req = urllib.request.Request(
            forum_url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status != 200:
                print(f"❌ 获取页面失败，状态码: {response.status}")
                return
            
            html = response.read().decode('utf-8')
            
            print("1. 页面基本信息")
            print("=" * 40)
            
            # 查找页面标题
            title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE)
            if title_match:
                print(f"页面标题: {unescape(title_match.group(1))}")
            
            # 查找论坛文章标题
            page_title_match = re.search(r'class="page-title"[^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
            if page_title_match:
                print(f"论坛标题: {unescape(re.sub(r'<[^>]*>', '', page_title_match.group(1)).strip())}")
            
            print(f"\n2. 寻找所有链接")
            print("=" * 40)
            
            # 查找所有 <a> 标签
            link_pattern = r'<a\s+[^>]*href=["\'](.*?)["\'][^>]*>(.*?)</a>'
            links = re.findall(link_pattern, html, re.IGNORECASE | re.DOTALL)
            
            print(f"总共找到 {len(links)} 个链接")
            
            for i, (href, text) in enumerate(links[:20], 1):  # 只显示前20个
                clean_text = unescape(re.sub(r'<[^>]*>', '', text).strip())
                if clean_text:  # 只显示有文本的链接
                    print(f"{i:2d}. href='{href}' text='{clean_text[:50]}{'...' if len(clean_text) > 50 else ''}'")
            
            if len(links) > 20:
                print(f"... 还有 {len(links) - 20} 个链接")
            
            print(f"\n3. 查找发帖相关内容")
            print("=" * 40)
            
            # 查找包含"发帖"的内容
            post_pattern = r'[^>]*发帖[^<]*'
            post_matches = re.findall(post_pattern, html, re.IGNORECASE)
            
            print(f"包含'发帖'的文本: {len(post_matches)} 个")
            for i, match in enumerate(post_matches, 1):
                clean_match = unescape(re.sub(r'<[^>]*>', '', match).strip())
                if clean_match:
                    print(f"{i}. '{clean_match}'")
            
            # 查找"我要发帖"按钮
            post_button_pattern = r'<a[^>]*href=["\'][^"\']*postMessage[^"\']*["\'][^>]*>(.*?)</a>'
            post_button_matches = re.findall(post_button_pattern, html, re.IGNORECASE | re.DOTALL)
            
            print(f"\n发帖按钮: {len(post_button_matches)} 个")
            for i, match in enumerate(post_button_matches, 1):
                clean_match = unescape(re.sub(r'<[^>]*>', '', match).strip())
                print(f"{i}. '{clean_match}'")
            
            print(f"\n4. 查找帖子容器")
            print("=" * 40)
            
            # 查找posts-list容器
            posts_list_pattern = r'<div[^>]*class="posts-list"[^>]*>(.*?)</div>'
            posts_list_matches = re.findall(posts_list_pattern, html, re.IGNORECASE | re.DOTALL)
            
            if posts_list_matches:
                print(f"找到 posts-list 容器: {len(posts_list_matches)} 个")
                for i, content in enumerate(posts_list_matches, 1):
                    clean_content = re.sub(r'<[^>]*>', '', content).strip()
                    print(f"{i}. 内容长度: {len(content)} 字符")
                    print(f"   清理后内容: '{clean_content[:100]}{'...' if len(clean_content) > 100 else ''}'")
                    
                    # 检查是否为空或只包含注释
                    if not clean_content or clean_content.isspace():
                        print("   ❌ 容器为空")
                    elif "<!--" in content and "-->" in content:
                        print("   ⚠️ 容器主要包含HTML注释")
            else:
                print("❌ 未找到 posts-list 容器")
            
            print(f"\n5. 分页信息")
            print("=" * 40)
            
            # 查找分页信息
            pagination_pattern = r'第\s*(\d+)\s*页[^第]*共\s*(\d+)\s*页'
            pagination_matches = re.findall(pagination_pattern, html, re.IGNORECASE)
            
            if pagination_matches:
                current_page, total_pages = pagination_matches[0]
                print(f"当前页: {current_page}, 总页数: {total_pages}")
            else:
                print("未找到分页信息")
            
            print(f"\n6. JavaScript 数据分析")
            print("=" * 40)
            
            # 查找NUXT数据
            nuxt_data_pattern = r'<script[^>]*id="__NUXT_DATA__"[^>]*>(.*?)</script>'
            nuxt_data_matches = re.findall(nuxt_data_pattern, html, re.IGNORECASE | re.DOTALL)
            
            if nuxt_data_matches:
                data = nuxt_data_matches[0].strip()
                print(f"✅ 找到 NUXT 数据，长度: {len(data)} 字符")
                
                # 检查是否包含帖子相关数据
                if '"posts"' in data.lower() or '"articles"' in data.lower():
                    print("✅ 数据中可能包含帖子信息")
                else:
                    print("⚠️ 数据中未发现明显的帖子信息")
                    
                # 显示数据的开头部分
                print(f"数据开头: {data[:200]}...")
            else:
                print("❌ 未找到 NUXT 数据")
            
            print(f"\n7. 筛选逻辑测试")
            print("=" * 40)
            
            # 测试我们的筛选关键词
            excluded_keywords = [
                '发帖', '登录', '注册', '排序', '筛选', '页', '菜单', 
                '导航', '搜索', '设置', '帮助', '关于'
            ]
            
            def is_excluded_content(text):
                if not text:
                    return True
                text_lower = text.lower().strip()
                return any(keyword.lower() in text_lower for keyword in excluded_keywords)
            
            test_texts = [
                "我要发帖",
                "论坛文章", 
                "排序方式：",
                "上一页",
                "下一页",
                "首页",
                "登录",
                "这是一个真实的帖子标题"
            ]
            
            print("筛选关键词测试:")
            for text in test_texts:
                excluded = is_excluded_content(text)
                status = "❌ 被排除" if excluded else "✅ 通过"
                print(f"  '{text}' -> {status}")
            
            print(f"\n8. 总结")
            print("=" * 40)
            print("🔍 主要发现:")
            print("1. 这是一个 Nuxt.js 单页应用")
            print("2. 帖子列表容器为空，内容通过 JavaScript 动态加载")
            print("3. 存在'我要发帖'按钮，会被当前筛选机制误判")
            print("4. 分页显示'第1页，共1页'，说明可能没有帖子数据")
            
            print(f"\n💡 问题原因:")
            print("- 静态HTML中没有真实帖子内容")
            print("- 当前的BeautifulSoup只能解析静态HTML")
            print("- '我要发帖'按钮被误认为是帖子链接")
            
            print(f"\n🔧 解决方案:")
            print("1. 改进筛选逻辑，更好地识别按钮和导航元素")
            print("2. 检查帖子容器是否为空")
            print("3. 考虑使用Selenium等工具处理JavaScript渲染")
            print("4. 寻找可能的API端点直接获取数据")
                
    except urllib.error.URLError as e:
        print(f"❌ 网络请求失败: {e}")
    except Exception as e:
        print(f"❌ 分析过程中出错: {e}")

if __name__ == "__main__":
    analyze_forum_structure()
