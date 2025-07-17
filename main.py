import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Set, Optional
import aiohttp
from bs4 import BeautifulSoup

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger, AstrBotConfig
import astrbot.api.message_components as Comp

@register("unikorn_news", "Assistant", "监听Unikorn论坛更新，自动推送新帖子到QQ群", "1.0.0", "https://github.com/Soulter/astrbot_plugin_unikorn_news")
class UnikornNewsPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.config = config
        self.forum_url = "https://unikorn.axfff.com/forum"
        self.check_task = None
        self.known_posts: Set[str] = set()
        # 数据文件存储在data目录下，避免插件更新时被覆盖
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
        os.makedirs(data_dir, exist_ok=True)
        self.data_file = os.path.join(data_dir, "unikorn_news_data.json")
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def initialize(self):
        """插件初始化方法"""
        try:
            logger.info("Unikorn News Plugin 初始化中...")
            
            # 创建HTTP会话
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30),
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            )
            
            # 加载已知帖子
            await self.load_known_posts()
            
            # 如果启用了通知功能，启动定时检查任务
            if self.config.get("enable_notification", True):
                await self.start_monitoring()
                
            logger.info("Unikorn News Plugin 初始化完成")
        except Exception as e:
            logger.error(f"Unikorn News Plugin 初始化失败: {e}")

    async def load_known_posts(self):
        """加载已知的帖子ID"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.known_posts = set(data.get('known_posts', []))
                logger.info(f"已加载 {len(self.known_posts)} 个已知帖子")
            else:
                logger.info("数据文件不存在，将创建新的数据文件")
        except Exception as e:
            logger.error(f"加载已知帖子失败: {e}")

    async def save_known_posts(self):
        """保存已知的帖子ID"""
        try:
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            data = {
                'known_posts': list(self.known_posts),
                'last_update': datetime.now().isoformat()
            }
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存已知帖子失败: {e}")

    async def fetch_forum_posts(self) -> List[Dict]:
        """获取论坛帖子列表"""
        try:
            if not self.session:
                logger.error("HTTP会话未初始化")
                return []
                
            async with self.session.get(self.forum_url) as response:
                if response.status != 200:
                    logger.error(f"获取论坛页面失败，状态码: {response.status}")
                    return []
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                posts = []
                
                # 尝试解析帖子信息（需要根据实际网页结构调整）
                # 由于网站可能使用JavaScript动态加载内容，我们先尝试获取静态内容
                post_elements = soup.find_all(['div', 'article', 'li'], class_=lambda x: x and any(
                    keyword in str(x).lower() for keyword in ['post', 'topic', 'thread', 'item', 'article']
                ))
                
                for element in post_elements:
                    # 查找标题链接
                    title_link = element.find('a', href=True)
                    if title_link and title_link.get('href'):
                        title = title_link.get_text(strip=True)
                        if title and len(title) > 3:  # 过滤掉太短的标题
                            href = title_link.get('href')
                            # 确保链接是完整的URL
                            if href.startswith('/'):
                                href = 'https://unikorn.axfff.com' + href
                            elif not href.startswith('http'):
                                href = 'https://unikorn.axfff.com/forum/' + href
                            
                            posts.append({
                                'title': title,
                                'url': href,
                                'id': href  # 使用URL作为唯一标识
                            })
                
                # 如果没有找到帖子，尝试其他方法
                if not posts:
                    # 查找所有链接，过滤出可能的帖子链接
                    all_links = soup.find_all('a', href=True)
                    for link in all_links:
                        href = link.get('href')
                        title = link.get_text(strip=True)
                        
                        # 过滤出论坛帖子链接
                        if (href and title and 
                            ('/forum/' in href or '/post/' in href or '/thread/' in href) and
                            len(title) > 5 and len(title) < 200):
                            
                            if href.startswith('/'):
                                href = 'https://unikorn.axfff.com' + href
                            elif not href.startswith('http'):
                                href = 'https://unikorn.axfff.com/forum/' + href
                            
                            posts.append({
                                'title': title,
                                'url': href,
                                'id': href
                            })
                
                # 去重
                seen_urls = set()
                unique_posts = []
                for post in posts:
                    if post['url'] not in seen_urls:
                        seen_urls.add(post['url'])
                        unique_posts.append(post)
                
                logger.info(f"获取到 {len(unique_posts)} 个帖子")
                return unique_posts
                
        except Exception as e:
            logger.error(f"获取论坛帖子失败: {e}")
            return []

    async def check_for_new_posts(self):
        """检查新帖子"""
        try:
            posts = await self.fetch_forum_posts()
            new_posts = []
            
            for post in posts:
                if post['id'] not in self.known_posts:
                    new_posts.append(post)
                    self.known_posts.add(post['id'])
            
            if new_posts:
                logger.info(f"发现 {len(new_posts)} 个新帖子")
                await self.notify_new_posts(new_posts)
                await self.save_known_posts()
            else:
                logger.debug("没有发现新帖子")
                
        except Exception as e:
            logger.error(f"检查新帖子失败: {e}")

    async def notify_new_posts(self, new_posts: List[Dict]):
        """通知新帖子"""
        try:
            target_groups = self.config.get("target_groups", [])
            max_title_length = self.config.get("max_title_length", 50)
            
            if not target_groups:
                logger.warning("未配置目标QQ群，无法推送新帖子")
                return
            
            for post in new_posts:
                title = post['title']
                if len(title) > max_title_length:
                    title = title[:max_title_length] + "..."
                
                message = f"🆕 Unikorn论坛新帖子\n\n📝 {title}\n🔗 {post['url']}"
                
                # 发送到每个配置的群
                for group_id in target_groups:
                    try:
                        # 构造消息链
                        chain = [Comp.Plain(message)]
                        
                        # 根据AstrBot文档的建议格式构造unified_msg_origin
                        unified_msg_origin = f"qq_group_{group_id}"
                        
                        # 使用context发送消息
                        await self.context.send_message(unified_msg_origin, chain)
                        logger.info(f"已向群 {group_id} 推送新帖子: {title}")
                    except Exception as e:
                        logger.error(f"向群 {group_id} 推送消息失败: {e}")
                        
        except Exception as e:
            logger.error(f"通知新帖子失败: {e}")

    async def start_monitoring(self):
        """启动监控任务"""
        if self.check_task and not self.check_task.done():
            logger.warning("监控任务已在运行")
            return
            
        interval = self.config.get("check_interval", 5) * 60  # 转换为秒
        logger.info(f"启动Unikorn论坛监控，检查间隔: {interval/60} 分钟")
        
        self.check_task = asyncio.create_task(self._monitoring_loop(interval))

    async def _monitoring_loop(self, interval: int):
        """监控循环"""
        while True:
            try:
                await self.check_for_new_posts()
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                logger.info("监控任务已取消")
                break
            except Exception as e:
                logger.error(f"监控循环出错: {e}")
                await asyncio.sleep(interval)

    @filter.command("unikorn")
    async def unikorn_command(self, event: AstrMessageEvent):
        """Unikorn论坛监控管理指令"""
        yield event.plain_result("🦄 Unikorn论坛监控插件\n\n"
                                "📋 可用指令:\n"
                                "/unikorn status - 查看监控状态\n"
                                "/unikorn check - 手动检查更新\n"
                                "/unikorn start - 启动监控\n"
                                "/unikorn stop - 停止监控\n"
                                "/unikorn posts - 查看最新帖子")

    @filter.command("unikorn", "status")
    async def status_command(self, event: AstrMessageEvent):
        """查看监控状态"""
        is_running = self.check_task and not self.check_task.done()
        status = "运行中" if is_running else "已停止"
        interval = self.config.get("check_interval", 5)
        target_groups = self.config.get("target_groups", [])
        
        message = (f"📊 Unikorn论坛监控状态\n\n"
                  f"🔄 状态: {status}\n"
                  f"⏰ 检查间隔: {interval} 分钟\n"
                  f"👥 目标群: {len(target_groups)} 个\n"
                  f"📚 已知帖子: {len(self.known_posts)} 个")
        
        yield event.plain_result(message)

    @filter.command("unikorn", "check")
    async def manual_check_command(self, event: AstrMessageEvent):
        """手动检查更新"""
        yield event.plain_result("🔍 正在检查Unikorn论坛更新...")
        
        try:
            await self.check_for_new_posts()
            yield event.plain_result("✅ 检查完成！如有新帖子会自动推送到配置的群。")
        except Exception as e:
            logger.error(f"手动检查失败: {e}")
            yield event.plain_result(f"❌ 检查失败: {str(e)}")

    @filter.command("unikorn", "start")
    async def start_command(self, event: AstrMessageEvent):
        """启动监控"""
        try:
            await self.start_monitoring()
            yield event.plain_result("✅ Unikorn论坛监控已启动")
        except Exception as e:
            logger.error(f"启动监控失败: {e}")
            yield event.plain_result(f"❌ 启动失败: {str(e)}")

    @filter.command("unikorn", "stop")
    async def stop_command(self, event: AstrMessageEvent):
        """停止监控"""
        if self.check_task and not self.check_task.done():
            self.check_task.cancel()
            yield event.plain_result("⏹️ Unikorn论坛监控已停止")
        else:
            yield event.plain_result("ℹ️ 监控未在运行")

    @filter.command("unikorn", "posts")
    async def posts_command(self, event: AstrMessageEvent):
        """查看最新帖子"""
        yield event.plain_result("📖 正在获取最新帖子...")
        
        try:
            posts = await self.fetch_forum_posts()
            if not posts:
                yield event.plain_result("❌ 未能获取到帖子，可能网站结构发生了变化")
                return
            
            # 显示最多5个最新帖子
            display_posts = posts[:5]
            max_title_length = self.config.get("max_title_length", 50)
            
            message = "📚 Unikorn论坛最新帖子:\n\n"
            for i, post in enumerate(display_posts, 1):
                title = post['title']
                if len(title) > max_title_length:
                    title = title[:max_title_length] + "..."
                message += f"{i}. {title}\n🔗 {post['url']}\n\n"
            
            if len(posts) > 5:
                message += f"... 还有 {len(posts) - 5} 个帖子"
                
            yield event.plain_result(message)
            
        except Exception as e:
            logger.error(f"获取帖子失败: {e}")
            yield event.plain_result(f"❌ 获取失败: {str(e)}")

    async def terminate(self):
        """插件销毁方法"""
        try:
            if self.check_task and not self.check_task.done():
                self.check_task.cancel()
                try:
                    await self.check_task
                except asyncio.CancelledError:
                    pass
            
            if self.session and not self.session.closed:
                await self.session.close()
                
            await self.save_known_posts()
            logger.info("Unikorn News Plugin 已清理完成")
        except Exception as e:
            logger.error(f"插件清理失败: {e}")
