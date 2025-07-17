#!/usr/bin/env python3
"""
Unikorn论坛监控插件测试脚本
用于测试网页抓取功能
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup

async def test_forum_fetch():
    """测试论坛页面抓取"""
    forum_url = "https://unikorn.axfff.com/forum"
    
    async with aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=30),
        headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    ) as session:
        try:
            print(f"正在获取页面: {forum_url}")
            async with session.get(forum_url) as response:
                if response.status != 200:
                    print(f"HTTP错误: {response.status}")
                    return
                
                html = await response.text()
                print(f"页面大小: {len(html)} 字符")
                
                soup = BeautifulSoup(html, 'html.parser')
                
                # 查找所有链接
                all_links = soup.find_all('a', href=True)
                print(f"找到 {len(all_links)} 个链接")
                
                # 过滤出可能的帖子链接
                posts = []
                for link in all_links:
                    href = link.get('href')
                    title = link.get_text(strip=True)
                    
                    if (href and title and 
                        ('/forum/' in href or '/post/' in href or '/thread/' in href) and
                        len(title) > 5 and len(title) < 200):
                        
                        if href.startswith('/'):
                            href = 'https://unikorn.axfff.com' + href
                        elif not href.startswith('http'):
                            href = 'https://unikorn.axfff.com/forum/' + href
                        
                        posts.append({
                            'title': title,
                            'url': href
                        })
                
                print(f"找到 {len(posts)} 个可能的帖子")
                
                # 显示前5个
                for i, post in enumerate(posts[:5], 1):
                    print(f"{i}. {post['title']}")
                    print(f"   {post['url']}")
                    print()
                
                if not posts:
                    print("未找到帖子链接，可能需要调整解析逻辑")
                    print("页面标题:", soup.title.string if soup.title else "无标题")
                    
                    # 显示页面结构分析
                    print("\n页面结构分析:")
                    for tag in ['article', 'div', 'section', 'li']:
                        elements = soup.find_all(tag)
                        if elements:
                            print(f"  {tag}: {len(elements)} 个")
                
        except Exception as e:
            print(f"抓取失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_forum_fetch())
