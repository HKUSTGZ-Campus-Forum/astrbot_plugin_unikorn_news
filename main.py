import asyncio
import json
import os
import re
from datetime import datetime
from typing import Dict, List, Set, Optional
import aiohttp
from bs4 import BeautifulSoup

from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult, MessageChain
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
                
                # 检查是否为Nuxt.js或类似的SPA应用
                if self._is_spa_application(soup):
                    logger.warning("检测到SPA应用，帖子内容可能通过JavaScript动态加载")
                
                # 首先检查帖子容器是否为空
                if self._is_posts_container_empty(soup):
                    logger.warning("帖子容器为空，可能没有帖子数据或需要JavaScript渲染")
                    return []
                
                # 首先尝试识别常见的论坛结构
                # 1. 尝试查找明确的帖子容器
                post_containers = self._find_post_containers(soup)
                
                if post_containers:
                    logger.info(f"找到 {len(post_containers)} 个帖子容器")
                    for container in post_containers:
                        post_data = self._extract_post_from_container(container)
                        if post_data and self._is_valid_post(post_data):
                            posts.append(post_data)
                
                # 2. 如果没有找到明确的容器，使用改进的通用方法
                if not posts:
                    logger.info("未找到明确的帖子容器，使用通用方法")
                    posts = self._extract_posts_generic(soup)
                
                # 3. 过滤和验证帖子
                filtered_posts = []
                for post in posts:
                    if self._is_valid_post(post) and not self._is_excluded_content(post):
                        filtered_posts.append(post)
                
                # 去重
                unique_posts = self._deduplicate_posts(filtered_posts)
                
                logger.info(f"获取到 {len(unique_posts)} 个有效帖子")
                return unique_posts
                
        except Exception as e:
            logger.error(f"获取论坛帖子失败: {e}")
            return []

    def _is_spa_application(self, soup: BeautifulSoup) -> bool:
        """检测是否为单页应用"""
        # 查找常见的SPA框架标识
        spa_indicators = [
            'nuxt', 'vue', 'react', 'angular', '__NUXT_DATA__', 
            'data-nuxt-', 'ng-app', 'reactroot'
        ]
        
        html_content = str(soup).lower()
        return any(indicator in html_content for indicator in spa_indicators)
    
    def _is_posts_container_empty(self, soup: BeautifulSoup) -> bool:
        """检查帖子容器是否为空"""
        # 查找帖子列表容器
        posts_containers = soup.find_all(['div', 'ul', 'section'], 
                                       class_=re.compile(r'(posts?[-_]?(list|container|wrapper)|forum[-_]?posts?|topic[-_]?list)', re.I))
        
        if not posts_containers:
            return True
        
        for container in posts_containers:
            # 获取容器内的文本内容（排除HTML标签）
            text_content = container.get_text(strip=True)
            
            # 如果容器有意义的文本内容，说明不为空
            if text_content and len(text_content) > 10:
                # 但要排除只包含导航/按钮文字的情况
                if not self._is_only_navigation_content(text_content):
                    return False
        
        return True
    
    def _is_only_navigation_content(self, text: str) -> bool:
        """检查文本是否只包含导航/按钮内容"""
        navigation_patterns = [
            r'^(上一页|下一页|首页|末页|第\s*\d+\s*页|共\s*\d+\s*页|页码|分页)+$',
            r'^(发帖|我要发帖|新建|添加|创建|登录|注册|搜索|筛选|排序)+$',
            r'^(加载中|loading|暂无数据|没有更多|到底了)+$'
        ]
        
        text_clean = re.sub(r'\s+', '', text).lower()
        return any(re.search(pattern, text, re.I) for pattern in navigation_patterns)

    def _find_post_containers(self, soup: BeautifulSoup) -> List:
        """查找帖子容器元素"""
        containers = []
        
        # 常见的帖子容器选择器
        selectors = [
            # 基于类名的选择器
            '[class*="post"]:not([class*="button"]):not([class*="btn"])',
            '[class*="topic"]:not([class*="button"]):not([class*="btn"])',
            '[class*="thread"]:not([class*="button"]):not([class*="btn"])',
            '[class*="article"]:not([class*="button"]):not([class*="btn"])',
            '[class*="item"]:not([class*="nav"]):not([class*="menu"])',
            # 基于数据属性的选择器
            '[data-post-id]',
            '[data-topic-id]',
            '[data-thread-id]',
            # 结构化选择器
            'article[id*="post"]',
            'div[id*="post"]',
            'li[id*="post"]',
        ]
        
        for selector in selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    logger.debug(f"选择器 '{selector}' 找到 {len(elements)} 个元素")
                    containers.extend(elements)
                    if len(containers) >= 10:  # 限制数量避免过多
                        break
            except Exception as e:
                logger.debug(f"选择器 '{selector}' 执行失败: {e}")
        
        return containers

    def _extract_post_from_container(self, container) -> Optional[Dict]:
        """从容器中提取帖子信息"""
        try:
            # 查找标题链接
            title_link = None
            
            # 优先查找明确的标题链接
            title_selectors = [
                'a[class*="title"]',
                'a[class*="subject"]',
                'a[class*="topic"]',
                'h1 a', 'h2 a', 'h3 a', 'h4 a',
                '.title a', '.subject a', '.topic a',
            ]
            
            for selector in title_selectors:
                try:
                    link = container.select_one(selector)
                    if link and link.get('href'):
                        title_link = link
                        break
                except:
                    continue
            
            # 如果没找到，查找第一个有效链接
            if not title_link:
                links = container.find_all('a', href=True)
                for link in links:
                    if self._looks_like_post_link(link):
                        title_link = link
                        break
            
            if not title_link:
                return None
            
            title = title_link.get_text(strip=True)
            href = title_link.get('href')
            
            # 标准化URL
            if href.startswith('/'):
                href = 'https://unikorn.axfff.com' + href
            elif not href.startswith('http'):
                href = 'https://unikorn.axfff.com/forum/' + href
            
            # 提取额外信息
            post_data = {
                'title': title,
                'url': href,
                'id': href,
                'container_class': container.get('class', []),
                'container_id': container.get('id', ''),
            }
            
            # 尝试提取发布时间
            time_element = container.select_one('[class*="time"], [class*="date"], time')
            if time_element:
                post_data['timestamp'] = time_element.get_text(strip=True)
            
            return post_data
            
        except Exception as e:
            logger.debug(f"从容器提取帖子信息失败: {e}")
            return None

    def _extract_posts_generic(self, soup: BeautifulSoup) -> List[Dict]:
        """通用的帖子提取方法"""
        posts = []
        
        # 查找所有链接
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            if self._looks_like_post_link(link):
                href = link.get('href')
                title = link.get_text(strip=True)
                
                # 标准化URL
                if href.startswith('/'):
                    href = 'https://unikorn.axfff.com' + href
                elif not href.startswith('http'):
                    href = 'https://unikorn.axfff.com/forum/' + href
                
                posts.append({
                    'title': title,
                    'url': href,
                    'id': href,
                    'link_class': link.get('class', []),
                    'parent_class': link.parent.get('class', []) if link.parent else [],
                })
        
        return posts

    def _looks_like_post_link(self, link) -> bool:
        """判断链接是否看起来像帖子链接"""
        href = link.get('href', '')
        title = link.get_text(strip=True)
        
        # URL模式检查
        url_patterns = [
            '/post/', '/topic/', '/thread/', '/discussion/',
            '/p/', '/t/', '/d/', '/forum/',
            r'/\d+/', r'id=\d+', r'tid=\d+', r'pid=\d+'
        ]
        
        import re
        url_matches = any(re.search(pattern, href) for pattern in url_patterns)
        
        # 标题检查
        title_valid = (
            title and 
            len(title) > 5 and 
            len(title) < 200 and
            not self._is_button_text(title)
        )
        
        return url_matches and title_valid

    def _is_button_text(self, text: str) -> bool:
        """判断文本是否为按钮文本"""
        if not text or len(text.strip()) < 2:
            return True
            
        # 获取用户配置的排除关键词
        excluded_keywords = self.config.get("excluded_keywords", [])
        
        # 精确匹配的按钮文本模式（完全匹配）
        exact_button_patterns = [
            # 发帖相关
            r'^我要发帖$', r'^发布帖子$', r'^新建帖子$', r'^创建帖子$', r'^写帖子$', r'^发帖$',
            # 用户操作
            r'^登录$', r'^注册$', r'^退出$', r'^登出$', r'^注销$',
            # 导航按钮  
            r'^首页$', r'^主页$', r'^返回$', r'^上一页$', r'^下一页$', r'^末页$', r'^尾页$',
            # 分页相关
            r'^第\s*\d+\s*页$', r'^共\s*\d+\s*页$', r'^页码\s*\d+$',
            # 功能按钮
            r'^搜索$', r'^查找$', r'^筛选$', r'^过滤$', r'^排序$', r'^切换$',
            r'^展开$', r'^收起$', r'^更多$', r'^详情$', r'^查看$',
            # 表单按钮
            r'^提交$', r'^确定$', r'^取消$', r'^重置$', r'^保存$', r'^删除$',
            r'^编辑$', r'^修改$', r'^添加$', r'^新增$',
            # 英文按钮
            r'^post$', r'^new post$', r'^create$', r'^login$', r'^register$',
            r'^search$', r'^more$', r'^next$', r'^prev$', r'^home$',
        ]
        
        # 默认包含关键词（更保守的策略，避免误判正常帖子）
        default_button_keywords = [
            '回复', '编辑', '删除', '举报', '点赞', '收藏',
            '提交', '确定', '取消', '关闭',
            'reply', 'edit', 'delete', 'report', 'like', 'save',
            'submit', 'ok', 'cancel', 'close',
        ]
        
        text_clean = text.strip()
        
        # 首先检查精确匹配模式
        for pattern in exact_button_patterns:
            if re.search(pattern, text_clean, re.IGNORECASE):
                return True
        
        # 然后检查包含关键词
        all_keywords = default_button_keywords + excluded_keywords
        text_lower = text_clean.lower()
        
        for keyword in all_keywords:
            if keyword.lower() in text_lower:
                return True
        
        # 检查是否为纯数字、符号或单字符
        if re.match(r'^[\d\s\-_\+\.]+$|^.$', text_clean):
            return True
        
        return False

    def _is_valid_post(self, post_data: Dict) -> bool:
        """验证是否为有效帖子"""
        if not post_data:
            return False
        
        title = post_data.get('title', '')
        url = post_data.get('url', '')
        
        # 基本检查
        if not title or not url:
            return False
        
        # 使用配置的标题长度限制
        min_length = self.config.get("min_title_length", 5)
        max_length = self.config.get("max_title_length", 50) * 4  # 用于验证的最大长度比显示长度更长
        
        if len(title) < min_length or len(title) > max_length:
            if self.config.get("debug_mode", False):
                logger.debug(f"标题长度不符合要求: '{title}' (长度: {len(title)})")
            return False
        
        # URL有效性检查
        if not url.startswith('http'):
            return False
        
        return True

    def _is_excluded_content(self, text: str) -> bool:
        """检查内容是否应被排除（改进版）"""
        if not text:
            return True
        
        # 获取用户配置的排除关键词
        user_excluded = self.config.get("excluded_keywords", [])
        
        # 严格匹配的排除模式（避免误判正常帖子）
        strict_exclusion_patterns = [
            # 导航类（完全匹配）
            r'^(首页|主页|上一页|下一页|末页|尾页)$',
            # 分页类
            r'^(第\s*\d+\s*页|共\s*\d+\s*页|页码).*$',
            # 功能类（完全匹配）
            r'^(登录|注册|搜索|筛选|排序|设置|帮助|关于我们|联系我们)$',
            r'^(排序方式|筛选条件|搜索结果).*$',
            # 菜单类
            r'^(菜单|导航|面包屑).*$',
        ]
        
        text_clean = text.strip()
        
        # 检查严格匹配模式
        for pattern in strict_exclusion_patterns:
            if re.search(pattern, text_clean, re.IGNORECASE):
                return True
        
        # 检查用户自定义的排除关键词（如果用户明确配置了）
        if user_excluded:
            text_lower = text_clean.lower()
            for keyword in user_excluded:
                if keyword.lower() in text_lower:
                    return True
        
        return False

    def _deduplicate_posts(self, posts: List[Dict]) -> List[Dict]:
        """去重帖子列表"""
        seen_urls = set()
        seen_titles = set()
        unique_posts = []
        
        for post in posts:
            url = post['url']
            title = post['title']
            
            # 基于URL去重
            if url in seen_urls:
                continue
            
            # 基于标题去重（处理相同标题不同URL的情况）
            title_normalized = title.lower().strip()
            if title_normalized in seen_titles:
                continue
            
            seen_urls.add(url)
            seen_titles.add(title_normalized)
            unique_posts.append(post)
        
        return unique_posts

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
                        # 构造消息链 - 使用正确的MessageChain方式
                        message_chain = MessageChain().message(message)
                        
                        # 构造unified_msg_origin
                        unified_msg_origin = f"qq_group_{group_id}"
                        
                        # 使用context发送消息
                        await self.context.send_message(unified_msg_origin, message_chain)
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
        admin_qq_list = self.config.get("admin_qq_list", [])
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
            "/unikorn groupmembers - 获取群成员统计\n"
            "/unikorn debug - 调试帖子筛选机制"
        )
        
        message = "🦄 Unikorn论坛监控插件\n\n" + basic_commands
        
        if is_admin and event.get_platform_name() == "aiocqhttp":
            message += admin_commands
        elif admin_qq_list and event.get_platform_name() == "aiocqhttp":
            message += "\n\n💡 提示: 您不在管理员列表中，无法使用高级功能"
        elif event.get_platform_name() != "aiocqhttp":
            message += "\n\n💡 提示: 协议端API功能仅在QQ平台(aiocqhttp)可用"
            
        yield event.plain_result(message)

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

    @filter.command("unikorn", "recall")
    async def recall_command(self, event: AstrMessageEvent):
        """撤回最后一条机器人消息（仅管理员）- 展示aiocqhttp协议端API的使用"""
        try:
            # 检查是否为aiocqhttp平台
            if event.get_platform_name() != "aiocqhttp":
                yield event.plain_result("❌ 此功能仅支持QQ平台（aiocqhttp）")
                return
            
            # 检查管理员权限（这里简化处理，实际应该使用AstrBot的权限系统）
            admin_qq_list = self.config.get("admin_qq_list", [])
            sender_id = event.get_sender_id()
            
            if admin_qq_list and sender_id not in admin_qq_list:
                yield event.plain_result("❌ 仅管理员可以使用此功能")
                return
            
            # 导入aiocqhttp相关类型
            from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
            
            # 确认这是aiocqhttp事件
            if not isinstance(event, AiocqhttpMessageEvent):
                yield event.plain_result("❌ 无法获取协议端客户端")
                return
            
            # 获取协议端客户端
            client = event.bot
            
            # 这里演示几个常用的协议端API调用
            yield event.plain_result("🔍 正在演示协议端API调用...")
            
            # 1. 获取群信息
            if event.message_obj.group_id:
                try:
                    group_info_payload = {
                        "group_id": int(event.message_obj.group_id)
                    }
                    group_info = await client.api.call_action('get_group_info', **group_info_payload)
                    logger.info(f"群信息: {group_info}")
                    
                    yield event.plain_result(f"📋 当前群信息:\n"
                                           f"群号: {group_info.get('group_id', 'N/A')}\n"
                                           f"群名: {group_info.get('group_name', 'N/A')}\n"
                                           f"成员数: {group_info.get('member_count', 'N/A')}")
                except Exception as e:
                    logger.error(f"获取群信息失败: {e}")
                    yield event.plain_result(f"❌ 获取群信息失败: {str(e)}")
            
            # 2. 获取机器人自身信息
            try:
                login_info = await client.api.call_action('get_login_info')
                logger.info(f"登录信息: {login_info}")
                
                yield event.plain_result(f"🤖 机器人信息:\n"
                                       f"QQ号: {login_info.get('user_id', 'N/A')}\n"
                                       f"昵称: {login_info.get('nickname', 'N/A')}")
            except Exception as e:
                logger.error(f"获取登录信息失败: {e}")
                yield event.plain_result(f"❌ 获取登录信息失败: {str(e)}")
            
            # 3. 发送一条测试消息，然后演示撤回
            try:
                # 构造发送消息的参数
                if event.message_obj.group_id:
                    send_payload = {
                        "group_id": int(event.message_obj.group_id),
                        "message": "🧪 这是一条测试消息，3秒后将被撤回..."
                    }
                    send_result = await client.api.call_action('send_group_msg', **send_payload)
                else:
                    send_payload = {
                        "user_id": int(event.get_sender_id()),
                        "message": "🧪 这是一条测试消息，3秒后将被撤回..."
                    }
                    send_result = await client.api.call_action('send_private_msg', **send_payload)
                
                logger.info(f"发送消息结果: {send_result}")
                message_id = send_result.get('message_id')
                
                if message_id:
                    # 等待3秒
                    await asyncio.sleep(3)
                    
                    # 撤回消息
                    recall_payload = {
                        "message_id": message_id
                    }
                    recall_result = await client.api.call_action('delete_msg', **recall_payload)
                    logger.info(f"撤回消息结果: {recall_result}")
                    
                    yield event.plain_result("✅ 协议端API调用演示完成！测试消息已撤回。")
                else:
                    yield event.plain_result("❌ 无法获取消息ID，撤回演示失败")
                    
            except Exception as e:
                logger.error(f"发送/撤回消息失败: {e}")
                yield event.plain_result(f"❌ 消息操作失败: {str(e)}")
            
        except Exception as e:
            logger.error(f"协议端API调用失败: {e}")
            yield event.plain_result(f"❌ 协议端API调用失败: {str(e)}")

    @filter.command("unikorn", "groupmembers")
    async def group_members_command(self, event: AstrMessageEvent):
        """获取群成员列表（仅管理员）- 展示更多协议端API"""
        try:
            # 检查平台和权限
            if event.get_platform_name() != "aiocqhttp":
                yield event.plain_result("❌ 此功能仅支持QQ平台（aiocqhttp）")
                return
                
            admin_qq_list = self.config.get("admin_qq_list", [])
            sender_id = event.get_sender_id()
            
            if admin_qq_list and sender_id not in admin_qq_list:
                yield event.plain_result("❌ 仅管理员可以使用此功能")
                return
                
            if not event.message_obj.group_id:
                yield event.plain_result("❌ 此功能仅在群聊中可用")
                return
            
            from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
            
            if not isinstance(event, AiocqhttpMessageEvent):
                yield event.plain_result("❌ 无法获取协议端客户端")
                return
            
            client = event.bot
            
            # 获取群成员列表
            group_id = int(event.message_obj.group_id)
            member_list_payload = {
                "group_id": group_id
            }
            
            member_list = await client.api.call_action('get_group_member_list', **member_list_payload)
            logger.info(f"群成员数量: {len(member_list) if member_list else 0}")
            
            if member_list:
                # 统计不同角色的成员
                owners = [m for m in member_list if m.get('role') == 'owner']
                admins = [m for m in member_list if m.get('role') == 'admin']
                members = [m for m in member_list if m.get('role') == 'member']
                
                message = f"👥 群成员统计 (群号: {group_id}):\n\n"
                message += f"👑 群主: {len(owners)} 人\n"
                message += f"🛡️ 管理员: {len(admins)} 人\n"
                message += f"👤 普通成员: {len(members)} 人\n"
                message += f"📊 总计: {len(member_list)} 人"
                
                yield event.plain_result(message)
            else:
                yield event.plain_result("❌ 获取群成员列表失败")
                
        except Exception as e:
            logger.error(f"获取群成员列表失败: {e}")
            yield event.plain_result(f"❌ 获取群成员列表失败: {str(e)}")

    @filter.command("unikorn", "debug")
    async def debug_command(self, event: AstrMessageEvent):
        """调试帖子筛选机制（仅管理员）"""
        try:
            # 检查权限
            admin_qq_list = self.config.get("admin_qq_list", [])
            sender_id = event.get_sender_id()
            
            if admin_qq_list and sender_id not in admin_qq_list:
                yield event.plain_result("❌ 仅管理员可以使用此功能")
                return
            
            yield event.plain_result("🔍 开始调试帖子筛选机制...")
            
            # 临时启用调试模式
            original_debug = self.config.get("debug_mode", False)
            self.config["debug_mode"] = True
            
            try:
                # 获取原始帖子数据
                if not self.session:
                    yield event.plain_result("❌ HTTP会话未初始化")
                    return
                
                async with self.session.get(self.forum_url) as response:
                    if response.status != 200:
                        yield event.plain_result(f"❌ 获取论坛页面失败，状态码: {response.status}")
                        return
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # 分析网页结构
                    debug_info = []
                    debug_info.append("📊 网页结构分析:")
                    debug_info.append(f"总链接数: {len(soup.find_all('a', href=True))}")
                    debug_info.append(f"总元素数: {len(soup.find_all())}")
                    
                    # 查找潜在的帖子容器
                    containers = self._find_post_containers(soup)
                    debug_info.append(f"潜在帖子容器: {len(containers)}")
                    
                    # 获取所有链接进行分析
                    all_links = soup.find_all('a', href=True)
                    valid_links = []
                    invalid_links = []
                    
                    for link in all_links:
                        href = link.get('href', '')
                        title = link.get_text(strip=True)
                        
                        if self._looks_like_post_link(link):
                            valid_links.append({'title': title, 'href': href})
                        else:
                            invalid_links.append({'title': title, 'href': href})
                    
                    debug_info.append(f"疑似帖子链接: {len(valid_links)}")
                    debug_info.append(f"排除的链接: {len(invalid_links)}")
                    
                    # 显示前几个有效链接
                    debug_info.append("\n📝 前5个疑似帖子:")
                    for i, link in enumerate(valid_links[:5], 1):
                        debug_info.append(f"{i}. {link['title'][:30]}...")
                        debug_info.append(f"   URL: {link['href']}")
                    
                    # 显示前几个被排除的链接
                    debug_info.append("\n❌ 前5个被排除的链接:")
                    for i, link in enumerate(invalid_links[:5], 1):
                        debug_info.append(f"{i}. {link['title'][:30]}...")
                        debug_info.append(f"   URL: {link['href']}")
                    
                    # 测试完整的筛选流程
                    posts = await self.fetch_forum_posts()
                    debug_info.append(f"\n✅ 最终筛选结果: {len(posts)} 个有效帖子")
                    
                    if posts:
                        debug_info.append("\n📋 最终帖子列表:")
                        for i, post in enumerate(posts[:3], 1):
                            debug_info.append(f"{i}. {post['title']}")
                    
                    # 配置信息
                    debug_info.append(f"\n⚙️ 当前筛选配置:")
                    debug_info.append(f"最小标题长度: {self.config.get('min_title_length', 5)}")
                    debug_info.append(f"严格过滤: {self.config.get('strict_filtering', True)}")
                    debug_info.append(f"排除关键词: {len(self.config.get('excluded_keywords', []))}")
                    
                    yield event.plain_result("\n".join(debug_info))
                    
            finally:
                # 恢复原始调试模式设置
                self.config["debug_mode"] = original_debug
                
        except Exception as e:
            logger.error(f"调试功能失败: {e}")
            yield event.plain_result(f"❌ 调试失败: {str(e)}")

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
