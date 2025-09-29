import discord
from discord import ui, app_commands
from discord.ext import commands, tasks
from discord import TextChannel
import random, uuid, requests, asyncio, time, threading, os, platform, psutil
from flask import Flask
from datetime import datetime, timedelta
import aiohttp
import hashlib
import logging
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
from rich import box
from rich.table import Table
from rich.panel import Panel
from humanize import naturaltime
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from cryptography.fernet import Fernet
from loguru import logger
import httpx
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
# ---------------- CONFIG ----------------
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = 1405933240212258816
OWNER_ID = 1065954764019470420

# ---------------- PROXY CONFIG ----------------
PROXY_ENABLED = os.getenv("PROXY_ENABLED", "false").lower() == "true"
PROXY_LIST = os.getenv("PROXY_LIST", "").split(",") if os.getenv("PROXY_LIST") else []
MAX_RETRIES = 3
RETRY_DELAY = 2.0

# ---------------- Channel ล่าสุด ----------------
ALERT_CHANNEL_ID = 1415593892585406525
CHANNEL_UI_ID = 1415555699454246985
CHANNEL_STATUS_ID = 1415345695069835267
CHANNEL_GUIDE_ID = 1415555569753788426
STATUS_DASHBOARD_ID = 1417378674537267333  # สถานะเซิร์ฟเวอร์

# ---------------- ตัวแปรสำหรับ Bot Management ----------------
bot_start_time = datetime.utcnow()
console = Console()

# ---------------- Security และ Token Protection ----------------
BOT_FINGERPRINT = hashlib.sha256(f"{OWNER_ID}_{GUILD_ID}_NEKTRI_BOT".encode()).hexdigest()[:16]
AUTHORIZED_INSTANCE = True
LAST_HEARTBEAT = datetime.utcnow()

# ---------------- Enterprise-Level Logging ----------------
logger.remove()  # ลบ default handler
logger.add("logs/bot.log", rotation="1 MB", retention="7 days", level="INFO", 
          format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} | {message}")
logger.add("logs/error.log", rotation="1 MB", retention="7 days", level="ERROR",
          format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} | {message}")
logger.add("logs/critical.log", rotation="500 KB", retention="14 days", level="CRITICAL",
          format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {module}:{function}:{line} | {message}")
logger.add("logs/performance.log", rotation="2 MB", retention="3 days", level="DEBUG",
          filter=lambda record: "PERF" in record["extra"],
          format="{time:YYYY-MM-DD HH:mm:ss} | PERFORMANCE | {message}")
logger.info(f"Bot initializing with fingerprint: {BOT_FINGERPRINT}")

# ---------------- Enhanced Status Tracking ----------------
active_ngl_sessions = {}
server_stats = {
    'uptime_start': bot_start_time,
    'commands_executed': 0,
    'messages_processed': 0,
    'errors_count': 0,
    'last_restart': None,
    'connection_retries': 0,
    'rate_limit_hits': 0,
    'last_error': None,
    'critical_errors': 0
}

# ---------------- Error Recovery Configuration ----------------
MAX_RECONNECT_ATTEMPTS = 10
RECONNECT_DELAY = 30  # seconds
ERROR_THRESHOLD = 50  # Max errors before alert
CRITICAL_ERROR_THRESHOLD = 5  # Max critical errors before restart
last_connection_attempt = datetime.utcnow()
connection_failures = 0

# ---------------- ห้องสำคัญไม่ให้ลบ ----------------
KEEP_CHANNELS = [
    ALERT_CHANNEL_ID,
    CHANNEL_UI_ID,
    CHANNEL_STATUS_ID,
    CHANNEL_GUIDE_ID
]

# ---------------- ข้อความสุ่ม ----------------
RANDOM_MESSAGES = [
"เงี่ยนพ่อมึงอะ","จับยัดนะควย","ลงสอตรี่หาพ่อมึงเถอะ","พ่อเเม่พี่ตายยัง",
    "กู  nektri ","พ่อมึงต่ายลูกอีเหี้ย","ไปต่ายเถอะ","หี","ลูกหมา","ลุกเม่ต่าย",
    "กูNEKTRI","มาดิสัส","อย่าเก่งเเต่ปาก","มึงโดนเเล้ว","บักควย","ลุกอีสัส",
    "สันด้านหมา","มึงไม่ดีเอง","เกิดมาหาพ่อมึงอะ","อีสานจัด","มาดิจะ","นัดตีป่าว",
    "ออกมากูรอละ","ใจ๋กากจัด","ว้าวๆๆๆบูห","เข้ามาดิ","ไปต่าย","สาธุ1111","ลูกกาก",
    "ปากเเตก","น่าโดนสนตีน","หมดหี","ขายหีหรอหรือหำ","รั่วไหม","หนูเงี่ยนอะเสี่ย",
    "ช่วยเย็ดหน่อย","เป็นเเฟนเเม่มึงได้ไหม","ควย","สัส","ปัญญาอ่อนจัด","มา",
    "ทำไรห","กูสั่งงาน","กลับมาละ","เแลกหใัเไหใ","เขียนหร","กกนห","ขอเย็ดเเม่มึฃ",
    "หำเข็ฃ","เเตกในปะ","ควยเเข็งจริงนะ","ไม่ไหวเเตกละ",'เอารูปเเม่มึงมาเเตกในละ',
    "เสี่ยงมาก","ไปไหน","ไปพ่องไหม","พ่อมึงไปไหน","ลูกอีปอบ","พ่อมึงสั่งสอนปะ",
    "รั่วหี","ไอ้สัด","ไอ้เหี้ย","มึงบักหำ","สันดานหมา","อีเหี้ยเอ๊ย","ไอ้สัสสัส",
    "มึงเน่า","หัวควย","มึงกาก","อีสัส","ไอ้บัดซบ","สันขวานหมา","ไอ้ลูกหมา","ควยมึง",
    "มึงสัสจริง","อีคนโง่","มึงไร้ค่า","ไอ้ควาย","กากสัส","สัดเหี้ย"
]

# ---------------- ENHANCED PROXY SYSTEM ----------------
@dataclass
class ProxyInfo:
    url: str
    proxy_type: str = "http"  # http, https, socks4, socks5
    working: bool = True
    last_used: float = 0
    error_count: int = 0
    success_count: int = 0
    response_time: float = 0.0  # Average response time in seconds
    quality_score: float = 100.0  # Quality score (0-100)
    last_health_check: float = 0
    consecutive_failures: int = 0
    total_usage: int = 0
    country: Optional[str] = None
    authentication: Optional[Dict[str, str]] = None  # {'username': 'xxx', 'password': 'xxx'}
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        total = self.success_count + self.error_count
        if total == 0:
            return 100.0
        return (self.success_count / total) * 100
    
    @property
    def is_healthy(self) -> bool:
        """Check if proxy is considered healthy"""
        return (self.working and 
                self.consecutive_failures < 3 and 
                self.quality_score > 30.0 and
                self.success_rate > 50.0)

class ProxyRotationStrategy(Enum):
    ROUND_ROBIN = "round_robin"
    WEIGHTED_RANDOM = "weighted_random"
    LEAST_USED = "least_used"
    FASTEST_FIRST = "fastest_first"
    QUALITY_BASED = "quality_based"
    
class ProxyManager:
    def __init__(self, rotation_strategy: ProxyRotationStrategy = ProxyRotationStrategy.QUALITY_BASED):
        self.proxies: List[ProxyInfo] = []
        self.current_index = 0
        self.session: Optional[aiohttp.ClientSession] = None
        self.rotation_strategy = rotation_strategy
        self.health_check_interval = 300  # 5 minutes
        self.min_proxies_threshold = 2  # Minimum working proxies
        self.health_check_task: Optional[asyncio.Task] = None
        self._initialize_proxies()
        
    def _initialize_proxies(self):
        """เริ่มต้น proxy list with enhanced detection"""
        if PROXY_LIST and PROXY_ENABLED:
            for proxy_url in PROXY_LIST:
                proxy_url = proxy_url.strip()
                if proxy_url:
                    proxy_info = self._parse_proxy_url(proxy_url)
                    self.proxies.append(proxy_info)
            logger.info(f"Initialized {len(self.proxies)} proxies with enhanced tracking")
        else:
            logger.info("No proxies configured, using direct connection")
    
    def start_health_checks(self):
        """เริ่มระบบตรวจสอบสุขภาพ (เรียกใน event loop)"""
        if self.proxies and not self.health_check_task:
            try:
                self.health_check_task = asyncio.create_task(self._periodic_health_check())
                logger.info("Proxy health check system started")
            except RuntimeError as e:
                logger.warning(f"Could not start health check task: {e}")
    
    def stop_health_checks(self):
        """หยุดระบบตรวจสอบสุขภาพ"""
        if self.health_check_task:
            self.health_check_task.cancel()
            self.health_check_task = None
    
    def _parse_proxy_url(self, proxy_url: str) -> ProxyInfo:
        """Parse proxy URL to extract type and authentication"""
        proxy_info = ProxyInfo(url=proxy_url)
        
        # Detect proxy type from URL
        if proxy_url.startswith('socks5://'):
            proxy_info.proxy_type = 'socks5'
        elif proxy_url.startswith('socks4://'):
            proxy_info.proxy_type = 'socks4'
        elif proxy_url.startswith('https://'):
            proxy_info.proxy_type = 'https'
        else:
            proxy_info.proxy_type = 'http'
        
        # Extract authentication if present
        if '@' in proxy_url:
            try:
                # Format: protocol://username:password@host:port
                parts = proxy_url.split('@')
                auth_part = parts[0].split('//')[-1]
                if ':' in auth_part:
                    username, password = auth_part.split(':', 1)
                    proxy_info.authentication = {'username': username, 'password': password}
            except:
                pass
        
        return proxy_info
    
    def get_next_proxy(self) -> Optional[str]:
        """รับ proxy ถัดไปตามกลยุทธ์ที่กำหนด - Enhanced Selection"""
        if not self.proxies:
            return None
        
        # หา proxy ที่ใช้งานได้และมีสุขภาพดี
        healthy_proxies = [p for p in self.proxies if p.is_healthy]
        
        if not healthy_proxies:
            # Reset proxies if none are healthy
            self._reset_failed_proxies()
            healthy_proxies = [p for p in self.proxies if p.working]
        
        if not healthy_proxies:
            logger.warning("No working proxies available")
            return None
        
        # เลือก proxy ตามกลยุทธ์
        selected_proxy = self._select_proxy_by_strategy(healthy_proxies)
        
        if selected_proxy:
            selected_proxy.last_used = time.time()
            selected_proxy.total_usage += 1
            return selected_proxy.url
        
        return None
    
    def _select_proxy_by_strategy(self, proxies: List[ProxyInfo]) -> Optional[ProxyInfo]:
        """เลือก proxy ตามกลยุทธ์ที่กำหนด"""
        if not proxies:
            return None
            
        if self.rotation_strategy == ProxyRotationStrategy.ROUND_ROBIN:
            # Round Robin แบบปกติ
            if self.current_index >= len(proxies):
                self.current_index = 0
            selected = proxies[self.current_index]
            self.current_index += 1
            return selected
            
        elif self.rotation_strategy == ProxyRotationStrategy.LEAST_USED:
            # เลือก proxy ที่ใช้น้อยที่สุด
            return min(proxies, key=lambda p: p.total_usage)
            
        elif self.rotation_strategy == ProxyRotationStrategy.FASTEST_FIRST:
            # เลือก proxy ที่เร็วที่สุด (response time ต่ำสุด)
            return min(proxies, key=lambda p: p.response_time or 999)
            
        elif self.rotation_strategy == ProxyRotationStrategy.QUALITY_BASED:
            # เลือกตามคะแนนคุณภาพ (weighted random)
            weights = [p.quality_score for p in proxies]
            total_weight = sum(weights)
            if total_weight == 0:
                return random.choice(proxies)
            
            rand_num = random.uniform(0, total_weight)
            current_weight = 0
            for proxy, weight in zip(proxies, weights):
                current_weight += weight
                if rand_num <= current_weight:
                    return proxy
            return proxies[-1]  # fallback
            
        elif self.rotation_strategy == ProxyRotationStrategy.WEIGHTED_RANDOM:
            # สุ่มแบบมีน้ำหนักตาม success rate
            weights = [p.success_rate for p in proxies]
            total_weight = sum(weights)
            if total_weight == 0:
                return random.choice(proxies)
            
            rand_num = random.uniform(0, total_weight)
            current_weight = 0
            for proxy, weight in zip(proxies, weights):
                current_weight += weight
                if rand_num <= current_weight:
                    return proxy
            return proxies[-1]  # fallback
        
        # Default fallback
        return random.choice(proxies)
    
    def _sanitize_proxy_url(self, proxy_url: str) -> str:
        """ทำความสะอาด proxy URL เพื่อป้องกันการรั่วไหล credentials"""
        try:
            import re
            # แทนที่ credentials ด้วย ****
            sanitized = re.sub(r'://([^:]+):([^@]+)@', r'://\1:****@', proxy_url)
            return sanitized
        except:
            # Fallback: แสดงแค่ host:port
            parts = proxy_url.split('@')
            if len(parts) > 1:
                return f"***@{parts[-1]}"
            return proxy_url.split('://')[0] + "://****"
    
    def mark_proxy_failed(self, proxy_url: str, response_time: float = 0):
        """ทำเครื่องหมาย proxy ที่ล้มเหลว - Enhanced Tracking"""
        for proxy in self.proxies:
            if proxy.url == proxy_url:
                proxy.error_count += 1
                proxy.consecutive_failures += 1
                
                # Update quality score based on failure
                proxy.quality_score = max(0, proxy.quality_score - 10)
                
                if proxy.error_count >= 3 or proxy.consecutive_failures >= 5:
                    proxy.working = False
                    sanitized_url = self._sanitize_proxy_url(proxy_url)
                    logger.warning(f"Proxy {sanitized_url} marked as failed (errors: {proxy.error_count}, consecutive: {proxy.consecutive_failures})")
                
                break
    
    def mark_proxy_success(self, proxy_url: str, response_time: float):
        """ทำเครื่องหมาย proxy ที่สำเร็จ - Enhanced Tracking"""
        for proxy in self.proxies:
            if proxy.url == proxy_url:
                proxy.success_count += 1
                proxy.consecutive_failures = 0  # Reset consecutive failures
                
                # Update response time (moving average)
                if proxy.response_time == 0:
                    proxy.response_time = response_time
                else:
                    proxy.response_time = (proxy.response_time * 0.7) + (response_time * 0.3)
                
                # Improve quality score based on success
                proxy.quality_score = min(100, proxy.quality_score + 2)
                
                # Update last health check
                proxy.last_health_check = time.time()
                
                break
    
    def _reset_failed_proxies(self):
        """รีเซ็ต proxy ที่ล้มเหลวเพื่อลองใหม่"""
        reset_count = 0
        for proxy in self.proxies:
            if not proxy.working and proxy.error_count < 10:  # Don't reset completely broken proxies
                proxy.working = True
                proxy.consecutive_failures = 0
                proxy.quality_score = min(proxy.quality_score + 20, 60)  # Partial recovery
                reset_count += 1
        
        if reset_count > 0:
            logger.info(f"Reset {reset_count} failed proxies for retry")
    
    async def _periodic_health_check(self):
        """ตรวจสอบสุขภาพของ proxy เป็นระยะ"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._health_check_all_proxies()
            except Exception as e:
                logger.error(f"Error in periodic health check: {e}")
                await asyncio.sleep(60)  # Wait before retrying
    
    async def _health_check_all_proxies(self):
        """ตรวจสอบสุขภาพของ proxy ทั้งหมด"""
        if not self.proxies:
            return
        
        logger.info(f"Starting health check for {len(self.proxies)} proxies")
        
        # Create tasks for parallel health checking
        tasks = []
        for proxy in self.proxies:
            if time.time() - proxy.last_health_check > 60:  # Check if not checked recently
                task = asyncio.create_task(self._test_single_proxy(proxy))
                tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            healthy_count = sum(1 for result in results if result is True)
            logger.info(f"Health check completed: {healthy_count}/{len(tasks)} proxies are healthy")
    
    async def _test_single_proxy(self, proxy: ProxyInfo) -> bool:
        """ทดสอบ proxy เดียว"""
        test_url = "https://httpbin.org/ip"  # Simple test endpoint
        start_time = time.time()
        
        try:
            connector_kwargs = {
                'limit': 10,
                'keepalive_timeout': 15,
                'enable_cleanup_closed': True
            }
            
            if proxy.proxy_type in ['socks4', 'socks5']:
                # SOCKS proxy support would need aiohttp-socks
                # For now, skip SOCKS proxies in health check
                return True
            
            connector = aiohttp.TCPConnector(**connector_kwargs)
            timeout = aiohttp.ClientTimeout(total=10, connect=5)
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                kwargs = {
                    "headers": {"User-Agent": self.get_random_user_agent()},
                    "timeout": aiohttp.ClientTimeout(total=8)
                }
                
                if proxy.url:
                    kwargs["proxy"] = proxy.url
                    if proxy.authentication:
                        kwargs["proxy_auth"] = aiohttp.BasicAuth(
                            proxy.authentication["username"],
                            proxy.authentication["password"]
                        )
                
                async with session.get(test_url, **kwargs) as response:
                    if response.status == 200:
                        response_time = time.time() - start_time
                        self.mark_proxy_success(proxy.url, response_time)
                        return True
                    else:
                        self.mark_proxy_failed(proxy.url, time.time() - start_time)
                        return False
        
        except Exception as e:
            response_time = time.time() - start_time
            self.mark_proxy_failed(proxy.url, response_time)
            logger.debug(f"Proxy {proxy.url} health check failed: {e}")
            return False
    
    def get_proxy_stats(self) -> Dict[str, Any]:
        """รับสถิติของ proxy ทั้งหมด"""
        if not self.proxies:
            return {"total": 0, "healthy": 0, "working": 0}
        
        total = len(self.proxies)
        healthy = sum(1 for p in self.proxies if p.is_healthy)
        working = sum(1 for p in self.proxies if p.working)
        
        avg_quality = sum(p.quality_score for p in self.proxies) / total if total > 0 else 0
        avg_response_time = sum(p.response_time for p in self.proxies if p.response_time > 0) / max(1, sum(1 for p in self.proxies if p.response_time > 0))
        
        return {
            "total": total,
            "healthy": healthy,
            "working": working,
            "average_quality_score": round(avg_quality, 2),
            "average_response_time": round(avg_response_time, 3),
            "rotation_strategy": self.rotation_strategy.value
        }
    
    def create_session(self, proxy_url: Optional[str] = None):
        """สร้าง session context manager พร้อม proxy - Enhanced with proper session management"""
        from contextlib import asynccontextmanager
        
        @asynccontextmanager
        async def session_context():
            connector_kwargs = {
                'limit': 100,
                'limit_per_host': 10,
                'keepalive_timeout': 30,
                'enable_cleanup_closed': True
            }
            
            # สำหรับ SOCKS proxy ต้องใช้ aiohttp-socks (ยังไม่ install)
            # ในตอนนี้จะ skip SOCKS และใช้ HTTP/HTTPS เท่านั้น
            connector = aiohttp.TCPConnector(**connector_kwargs)
            
            timeout = aiohttp.ClientTimeout(
                total=30,
                connect=10,
                sock_read=10
            )
            
            session_kwargs = {
                'connector': connector,
                'timeout': timeout,
                'headers': {
                    'User-Agent': self.get_random_user_agent()
                }
            }
            
            session = None
            try:
                session = aiohttp.ClientSession(**session_kwargs)
                yield session
            finally:
                if session and not session.closed:
                    await session.close()
        
        return session_context()
    
    def prepare_proxy_kwargs(self, proxy_url: Optional[str] = None) -> Dict[str, Any]:
        """เตรียม kwargs สำหรับการใช้ proxy ใน request"""
        kwargs = {}
        
        if not proxy_url:
            return kwargs
        
        # หา proxy info สำหรับการตรวจสอบ authentication
        proxy_info = None
        for p in self.proxies:
            if p.url == proxy_url:
                proxy_info = p
                break
        
        if not proxy_info:
            return kwargs
        
        # สำหรับ SOCKS proxy ให้ skip ในตอนนี้
        if proxy_info.proxy_type in ['socks4', 'socks5']:
            logger.debug(f"SOCKS proxy {self._sanitize_proxy_url(proxy_url)} not supported yet")
            return kwargs
        
        # สำหรับ HTTP/HTTPS proxy
        # Normalize HTTPS proxy to HTTP for aiohttp
        proxy_url_normalized = proxy_url
        if proxy_url.startswith('https://'):
            proxy_url_normalized = proxy_url.replace('https://', 'http://', 1)
            logger.debug("Normalized HTTPS proxy to HTTP for aiohttp compatibility")
        
        kwargs['proxy'] = proxy_url_normalized
        
        # เพิ่ม authentication ถ้ามี
        if proxy_info.authentication:
            kwargs['proxy_auth'] = aiohttp.BasicAuth(
                proxy_info.authentication["username"],
                proxy_info.authentication["password"]
            )
        
        return kwargs
    
    def get_random_user_agent(self, category: str = "random") -> str:
        """สุ่ม User-Agent เพื่อหลีกเลี่ยงการตรวจจับ - Professional Database อย่างละ 50 ตัว"""
        
        # === WINDOWS CHROME (50 ตัว) ===
        windows_chrome = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.84 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.99 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/95.0.4638.69 Safari/537.36",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.164 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36",
            "Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36"
        ]

        # === MACOS CHROME (50 ตัว) ===
        macos_chrome = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36"
        ]

        # === IPHONE SAFARI (50 ตัว) ===
        iphone_safari = [
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.5 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.3 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.2 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.4 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.3 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_8 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 13_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 13_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 13_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 13_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 13_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 13_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 13_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 12_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 12_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 12_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.1 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 12_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 12_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/12.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 11_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 11_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 11_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 11_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.0 Mobile/15E148 Safari/604.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E277 Safari/602.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 10_2 like Mac OS X) AppleWebKit/602.3.12 (KHTML, like Gecko) Version/10.0 Mobile/14C92 Safari/602.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 10_1 like Mac OS X) AppleWebKit/602.2.14 (KHTML, like Gecko) Version/10.0 Mobile/14B72 Safari/602.1",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 10_0 like Mac OS X) AppleWebKit/602.1.38 (KHTML, like Gecko) Version/10.0 Mobile/14A300 Safari/602.1"
        ]

        # === ANDROID CHROME (50 ตัว) ===
        android_chrome = [
            "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; SM-S911B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; Pixel 7 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; SM-A546B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; OnePlus 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; CPH2449) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; SM-A536B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; SM-T870) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; SM-T225) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; Pixel 6 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 11; Pixel 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; SM-A716B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; SM-A525F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; SM-N986B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; SM-N975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; OnePlus 10 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; OnePlus 9 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; Xiaomi 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; Xiaomi 12) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; Redmi Note 12 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; Redmi Note 11) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; POCO F5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; POCO F4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; Huawei P60 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; Huawei P50 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; Nokia G60) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; Nokia G50) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; Vivo V29) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; Vivo V23) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; OPPO Find X6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; OPPO Find X5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; Realme GT 3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; Realme GT 2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; Nothing Phone 2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; Nothing Phone 1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; Sony Xperia 1 V) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; Sony Xperia 1 IV) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; Motorola Edge 40) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; Motorola Edge 30) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; Fairphone 5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; Fairphone 4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 13; TCL 30 XE) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.66 Mobile Safari/537.36",
            "Mozilla/5.0 (Linux; Android 12; TCL 20 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.80 Mobile Safari/537.36"
        ]

        # เลือกตามหมวดหมู่หรือสุ่มทั้งหมด
        if category == "windows_chrome":
            return random.choice(windows_chrome)
        elif category == "macos_chrome":
            return random.choice(macos_chrome)
        elif category == "iphone_safari":
            return random.choice(iphone_safari)
        elif category == "android_chrome":
            return random.choice(android_chrome)
        else:
            # สุ่มจากทุกหมวดหมู่
            all_agents = windows_chrome + macos_chrome + iphone_safari + android_chrome
            return random.choice(all_agents)

# สร้าง instance
proxy_manager = ProxyManager()

COOLDOWN = 1  # 1 วินาที
stop_sending = False
last_sent = {}

# ---------------- 24/7 Optimization ----------------
# Rate limiting สำหรับป้องกันการใช้งานเกินขีดจำกัด
GLOBAL_RATE_LIMIT = 5  # สูงสุด 5 การร้องขอต่อนาที
GLOBAL_REQUEST_COUNT = {}
GLOBAL_REQUEST_RESET_TIME = time.time()

def check_global_rate_limit() -> bool:
    """ตรวจสอบ rate limit ระดับโลก"""
    global GLOBAL_REQUEST_COUNT, GLOBAL_REQUEST_RESET_TIME
    
    current_time = time.time()
    
    # Reset counter ทุก 1 นาที
    if current_time - GLOBAL_REQUEST_RESET_TIME > 60:
        GLOBAL_REQUEST_COUNT.clear()
        GLOBAL_REQUEST_RESET_TIME = current_time
    
    # นับจำนวนการใช้งานในนาทีปัจจุบัน
    current_minute = int(current_time // 60)
    request_count = GLOBAL_REQUEST_COUNT.get(current_minute, 0)
    
    if request_count >= GLOBAL_RATE_LIMIT:
        return False
    
    GLOBAL_REQUEST_COUNT[current_minute] = request_count + 1
    return True

# Memory optimization
async def cleanup_old_data():
    """ทำความสะอาดข้อมูลเก่าเพื่อประหยัด memory"""
    global last_sent, GLOBAL_REQUEST_COUNT
    
    current_time = time.time()
    
    # ลบข้อมูล last_sent ที่เก่าเกิน 1 ชั่วโมง
    expired_users = []
    for username, last_time in last_sent.items():
        if current_time - last_time > 3600:  # 1 ชั่วโมง
            expired_users.append(username)
    
    for username in expired_users:
        del last_sent[username]
    
    # ลบข้อมูล rate limit เก่า
    expired_minutes = []
    for minute_key in GLOBAL_REQUEST_COUNT.keys():
        if current_time // 60 - minute_key > 5:  # เก่าเกิน 5 นาที
            expired_minutes.append(minute_key)
    
    for minute_key in expired_minutes:
        del GLOBAL_REQUEST_COUNT[minute_key]
    
    logger.info(f"Cleaned up {len(expired_users)} old user records and {len(expired_minutes)} old rate limit records")

# ---------------- Auto-Moderation Channels ----------------
PROTECTED_CHANNELS = [
    ALERT_CHANNEL_ID,
    CHANNEL_UI_ID, 
    CHANNEL_STATUS_ID,
    CHANNEL_GUIDE_ID,
    STATUS_DASHBOARD_ID
]

# ช่องที่อนุญาตให้พูดคุยได้ (ไม่ลบข้อความ)
CHAT_ALLOWED_CHANNELS = [
    # เพิ่ม channel IDs ที่อนุญาตให้คุยทั่วไปตรงนี้
    # 1234567890123456789  # ตัวอย่าง Chat Channel
]

# ---------------- Enhanced Helper Functions ----------------
def random_device_id():
    return str(uuid.uuid4())

async def validate_ngl_username(username: str) -> bool:
    """ตรวจสอบว่า username มีอยู่จริงใน NGL หรือไม่"""
    try:
        url = f"https://ngl.link/{username}"
        async with aiohttp.ClientSession() as session:
            async with session.head(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                return response.status == 200
    except:
        return True  # ถ้าตรวจสอบไม่ได้ ให้ผ่านไป

def get_ngl_link_from_username(username: str) -> str:
    """แปลง username เป็น NGL link"""
    # ลบ @ ข้างหน้าถ้ามี
    username = username.lstrip('@')
    
    # ถ้าเป็น link เต็มแล้ว
    if username.startswith('https://ngl.link/'):
        return username
    
    # ถ้าเป็น ngl.link/username
    if username.startswith('ngl.link/'):
        return f"https://{username}"
    
    # ถ้าเป็น username เปล่า
    return f"https://ngl.link/{username}"

def extract_username_from_input(text: str) -> str:
    """แยก username จาก input ที่หลากหลาย"""
    text = text.strip()
    
    if text.startswith('https://ngl.link/'):
        return text.split('/')[-1]
    elif text.startswith('ngl.link/'):
        return text.split('/')[-1]
    else:
        return text.lstrip('@')

async def handle_discord_error(error: Exception, context: str = "Unknown"):
    """Centralized Discord error handling with automatic recovery"""
    global connection_failures, last_connection_attempt
    
    error_type = type(error).__name__
    error_msg = str(error)
    
    logger.error(f"Discord error in {context}: {error_type} - {error_msg}")
    
    # Handle specific Discord errors
    if "rate limit" in error_msg.lower():
        server_stats['rate_limit_hits'] += 1
        await alert_server(bot, f"Rate limit hit in {context}. Waiting...", "WARNING")
        await asyncio.sleep(60)  # Wait 1 minute for rate limit
        
    elif "connection" in error_msg.lower() or "disconnected" in error_msg.lower():
        connection_failures += 1
        server_stats['connection_retries'] += 1
        last_connection_attempt = datetime.utcnow()
        
        if connection_failures <= MAX_RECONNECT_ATTEMPTS:
            await alert_server(bot, f"Connection issue #{connection_failures}. Attempting reconnect...", "WARNING")
            await asyncio.sleep(RECONNECT_DELAY)
        else:
            await alert_server(bot, f"Max reconnection attempts reached. Initiating emergency restart...", "CRITICAL")
            await emergency_restart()
            
    elif "forbidden" in error_msg.lower() or "unauthorized" in error_msg.lower():
        await alert_server(bot, f"Permission error in {context}: {error_msg}", "ERROR")
        
    else:
        await alert_server(bot, f"Unexpected error in {context}: {error_type} - {error_msg}", "ERROR")
    
    server_stats['last_error'] = f"{context}: {error_msg}"
    
    # Check if we need to restart due to too many critical errors
    if server_stats['critical_errors'] >= CRITICAL_ERROR_THRESHOLD:
        await alert_server(bot, f"Critical error threshold reached ({CRITICAL_ERROR_THRESHOLD}). Initiating emergency restart...", "CRITICAL")
        await emergency_restart()

async def performance_monitor(func_name: str, start_time: float):
    """Monitor function performance"""
    end_time = time.time()
    duration = end_time - start_time
    
    if duration > 5.0:  # Log slow operations
        logger.bind(PERF=True).debug(f"Slow operation: {func_name} took {duration:.2f}s")
        
    if duration > 10.0:  # Alert for very slow operations
        await alert_server(bot, f"Performance warning: {func_name} took {duration:.2f}s", "WARNING")

def safe_task_wrapper(func):
    """Decorator to wrap async tasks with error handling"""
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            await performance_monitor(func.__name__, start_time)
            return result
        except Exception as e:
            await handle_discord_error(e, func.__name__)
            await performance_monitor(func.__name__, start_time)
    return wrapper

async def alert_server(bot, message: str, severity: str = "INFO"):
    """Enhanced alert system with severity levels and error handling"""
    try:
        channel = bot.get_channel(ALERT_CHANNEL_ID)
        if channel:
            # Choose emoji and color based on severity
            if severity == "CRITICAL":
                emoji = "🛑"
                color = discord.Color.red()
                server_stats['critical_errors'] += 1
            elif severity == "ERROR":
                emoji = "❌"
                color = discord.Color.orange()
                server_stats['errors_count'] += 1
            elif severity == "WARNING":
                emoji = "⚠️"
                color = discord.Color.yellow()
            else:
                emoji = "🟢"
                color = discord.Color.green()
            
            embed = discord.Embed(
                title=f"{emoji} [แจ้งเตือนระบบ - {severity}]",
                description=message,
                color=color,
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="🔍 ระดับความร้ายแรง", value=severity, inline=True)
            embed.add_field(name="🕰️ เวลา", value=datetime.utcnow().strftime("%H:%M:%S"), inline=True)
            
            await channel.send(embed=embed)
            
            # Log to file based on severity
            if severity == "CRITICAL":
                logger.critical(f"ALERT: {message}")
            elif severity == "ERROR":
                logger.error(f"ALERT: {message}")
            elif severity == "WARNING":
                logger.warning(f"ALERT: {message}")
            else:
                logger.info(f"ALERT: {message}")
                
    except Exception as e:
        # Fallback to console logging if Discord fails
        error_msg = f"❌ ไม่สามารถส่งแจ้งเตือนได้: {e}"
        print(error_msg)
        logger.error(error_msg)
        server_stats['last_error'] = str(e)

# ---------------- NGL Sending with Proxy & Bot Detection Avoidance ----------------
async def send_ngl_message(session: aiohttp.ClientSession, username: str, message: str, proxy_url: Optional[str] = None) -> bool:
    """ส่งข้อความ NGL ด้วย session และ proxy"""
    try:
        # สุ่มข้อมูลเพื่อหลีกเลี่ยงการตรวจจับ
        device_id = random_device_id()
        
        # สุ่ม headers เพิ่มเติม
        headers = {
            "Content-Type": "application/json",
            "Accept": "*/*",
            "Accept-Language": "th-TH,th;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Origin": "https://ngl.link",
            "Referer": f"https://ngl.link/{username}",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
        }
        
        payload = {
            "username": username,
            "question": message,
            "deviceId": device_id,
            "gameSlug": "",
            "referrer": ""
        }
        
        # เพิ่มความน่าเชื่อถือด้วยการรอสักครู่
        await asyncio.sleep(random.uniform(0.5, 1.5))
        
        kwargs = {
            "json": payload,
            "headers": headers,
            "timeout": aiohttp.ClientTimeout(total=15)
        }
        
        # ใช้ระบบ proxy ใหม่ที่ปลอดภัยและรองรับ authentication
        if proxy_url:
            proxy_kwargs = proxy_manager.prepare_proxy_kwargs(proxy_url)
            kwargs.update(proxy_kwargs)
            
        start_time = time.time()
        async with session.post("https://ngl.link/api/submit", **kwargs) as response:
            response_time = time.time() - start_time
            
            if response.status == 200:
                # Mark proxy as successful with response time
                if proxy_url:
                    proxy_manager.mark_proxy_success(proxy_url, response_time)
                
                # ตรวจสอบ response เพิ่มเติม
                try:
                    response_data = await response.json()
                    # NGL บางครั้งส่ง 200 แต่มี error message
                    if "error" not in str(response_data).lower():
                        return True
                except:
                    pass
                return True
            else:
                logger.warning(f"NGL response status: {response.status}")
                if proxy_url:
                    proxy_manager.mark_proxy_failed(proxy_url, response_time)
                return False
                
    except asyncio.TimeoutError:
        response_time = time.time() - start_time
        logger.warning(f"Timeout sending to {username}")
        if proxy_url:
            proxy_manager.mark_proxy_failed(proxy_url, response_time)
        return False
    except Exception as e:
        response_time = time.time() - start_time
        logger.error(f"Error sending NGL: {e}")
        if proxy_url:
            proxy_manager.mark_proxy_failed(proxy_url, response_time)
        return False

async def send_ngl(bot, username_input, amount, speed, message=None, is_random=True):
    global stop_sending, last_sent
    
    # ตรวจสอบ rate limit ระดับโลก
    if not check_global_rate_limit():
        channel = bot.get_channel(CHANNEL_STATUS_ID)
        await channel.send("❌ ระบบมีการใช้งานเกินขีดจำกัด กรุณารอสักครู่")
        return
    
    # แยก username จาก input
    username = extract_username_from_input(username_input)
    
    # ตรวจสอบ cooldown
    now = time.time()
    if username in last_sent and now - last_sent[username] < COOLDOWN:
        channel = bot.get_channel(CHANNEL_STATUS_ID)
        await channel.send(f"❌ {username} ต้องรออีก {round(COOLDOWN - (now - last_sent[username]))} วินาที")
        return

    stop_sending = False
    sent, fail = 0, 0
    start_time = time.time()
    channel = bot.get_channel(CHANNEL_STATUS_ID)
    current_proxy = None

    # ลบข้อความเก่าก่อนเริ่มส่งใหม่ (ยกเว้นข้อความสำคัญ)
    async for msg in channel.history(limit=50):
        if msg.author.id == bot.user.id and channel.id not in KEEP_CHANNELS:
            try:
                await msg.delete()
            except:
                pass  # ผ่านไปถ้าลบไม่ได้

    # ตรวจสอบ username ก่อน
    username_valid = await validate_ngl_username(username)
    ngl_link = get_ngl_link_from_username(username)
    
    if not username_valid:
        await channel.send(f"❌ ไม่พบผู้ใช้ {username} ใน NGL\n🔗 Link: {ngl_link}")
        return

    # เริ่มส่งข้อความ
    embed = discord.Embed(
        title="🚀 เริ่มระบบยิง NGL",
        color=discord.Color.blue(),
        timestamp=datetime.utcnow()
    )
    embed.add_field(name="🎯 เป้าหมาย", value=username, inline=True)
    embed.add_field(name="🔗 Link", value=ngl_link, inline=True)
    embed.add_field(name="🔢 จำนวน", value=amount, inline=True)
    embed.add_field(name="⚡ ความเร็ว", value=f"{speed}s", inline=True)
    embed.add_field(name="🔄 โหมด", value="สุ่มข้อความ" if is_random else "ข้อความกำหนด", inline=True)
    embed.add_field(name="🛡️ Proxy", value="เปิดใช้งาน" if PROXY_ENABLED else "ปิดใช้งาน", inline=True)
    
    status_message = await channel.send(embed=embed)

    # ใช้ session context manager เพื่อการจัดการ session อย่างถูกต้อง
    current_proxy = proxy_manager.get_next_proxy()
    
    try:
        async with proxy_manager.create_session(current_proxy) as session:
            for i in range(min(amount, 200)):
                if stop_sending:
                    break
                    
                # เลือกข้อความ
                if is_random:
                    text = random.choice(RANDOM_MESSAGES)
                else:
                    text = message if message else random.choice(RANDOM_MESSAGES)
                
                # ส่งข้อความ
                success = await send_ngl_message(session, username, text, current_proxy)
                
                if success:
                    sent += 1
                else:
                    fail += 1
                    # เปลี่ยน proxy ถ้าส่งไม่สำเร็จ - ให้สร้าง session ใหม่
                    if PROXY_ENABLED and fail % 3 == 0:
                        current_proxy = proxy_manager.get_next_proxy()
                        # ออกจาก session เก่าและสร้างใหม่ด้วย proxy ใหม่
                        break
                
                # อัปเดตสถานะ
                progress = f"📊 ความคืบหน้า: {i+1}/{amount}"
                success_rate = f"✅ สำเร็จ: {sent} ({round(sent/(i+1)*100)}%)"
                fail_rate = f"❌ ล้มเหลว: {fail}"
                recent_msg = f"📝 ข้อความล่าสุด: {text[:50]}..."
                proxy_info = f"🌐 Proxy: {current_proxy[-15:] if current_proxy else 'Direct'}"
                
                embed.description = f"{progress}\n{success_rate}\n{fail_rate}\n{recent_msg}\n{proxy_info}"
                await status_message.edit(embed=embed)
                
                # หน่วงเวลาแบบสุ่ม
                delay = speed * random.uniform(0.8, 1.4)
                await asyncio.sleep(delay)
            
            # หากต้อง proxy rotation ให้ลองอีกรอบด้วย session ใหม่
            if PROXY_ENABLED and fail % 3 == 0 and sent + fail < amount:
                async with proxy_manager.create_session(current_proxy) as retry_session:
                    remaining = amount - (sent + fail)
                    for j in range(remaining):
                        if stop_sending:
                            break
                        
                        if is_random:
                            text = random.choice(RANDOM_MESSAGES)
                        else:
                            text = message if message else random.choice(RANDOM_MESSAGES)
                        
                        success = await send_ngl_message(retry_session, username, text, current_proxy)
                        
                        if success:
                            sent += 1
                        else:
                            fail += 1
                        
                        # อัปเดตสถานะ
                        total_sent = sent + fail
                        progress = f"📊 ความคืบหน้า: {total_sent}/{amount}"
                        success_rate = f"✅ สำเร็จ: {sent} ({round(sent/total_sent*100) if total_sent > 0 else 0}%)"
                        fail_rate = f"❌ ล้มเหลว: {fail}"
                        recent_msg = f"📝 ข้อความล่าสุด: {text[:50]}..."
                        proxy_info = f"🌐 Proxy: {current_proxy[-15:] if current_proxy else 'Direct'} (Retry)"
                        
                        embed.description = f"{progress}\n{success_rate}\n{fail_rate}\n{recent_msg}\n{proxy_info}"
                        await status_message.edit(embed=embed)
                        
                        delay = speed * random.uniform(0.8, 1.4)
                        await asyncio.sleep(delay)
                        
                        if total_sent >= amount:
                            break

    except Exception as e:
        await alert_server(bot, f"เกิดข้อผิดพลาดร้ายแรงขณะยิง NGL: {e}", "ERROR")

    # สรุปผล
    duration = round(time.time() - start_time, 2)
    success_rate = round((sent / max(sent + fail, 1)) * 100, 1)
    
    final_embed = discord.Embed(
        title="✅ ยิง NGL เสร็จสิ้น",
        color=discord.Color.green(),
        timestamp=datetime.utcnow()
    )
    final_embed.add_field(name="🎯 เป้าหมาย", value=username, inline=True)
    final_embed.add_field(name="⏱️ เวลาที่ใช้", value=f"{duration} วินาที", inline=True)
    final_embed.add_field(name="✅ สำเร็จ", value=f"{sent} ข้อความ", inline=True)
    final_embed.add_field(name="❌ ล้มเหลว", value=f"{fail} ข้อความ", inline=True)
    final_embed.add_field(name="📊 อัตราสำเร็จ", value=f"{success_rate}%", inline=True)
    if sent + fail > 0:
        final_embed.add_field(name="⚡ ความเร็วเฉลี่ย", value=f"{round(duration/(sent+fail), 2)} s/msg", inline=True)
    
    await status_message.edit(embed=final_embed)
    
    # ส่งแจ้งเตือนไปยัง guide channel
    channel_success = bot.get_channel(CHANNEL_GUIDE_ID)
    if channel_success:
        await channel_success.send(f"📢 ยิง NGL ไปยัง {username} เสร็จสิ้น | สำเร็จ {sent}/{sent+fail} | เวลา {duration}s ✅")
    
    # อัปเดต last_sent เพื่อให้ cooldown ทำงาน
    last_sent[username] = time.time()

# ---------------- ฟังก์ชันตรวจสอบสิทธิ์ ----------------
def is_server_owner(interaction: discord.Interaction) -> bool:
    """ตรวจสอบว่าเป็นเจ้าของเซิร์ฟเวอร์หรือไม่ (เฉพาะเจ้าของเซิร์ฟเวอร์เท่านั้น)"""
    # ตรวจสอบ OWNER_ID ที่กำหนดไว้
    if interaction.user.id == OWNER_ID:
        return True

    # ตรวจสอบว่าเป็นเจ้าของเซิร์ฟเวอร์จริง
    if interaction.guild and interaction.guild.owner_id == interaction.user.id:
        return True

    return False

async def owner_only_check(interaction: discord.Interaction) -> bool:
    """Decorator check สำหรับคำสั่งเฉพาะเจ้าของ"""
    server_stats['commands_executed'] += 1
    if not is_server_owner(interaction):
        await interaction.response.send_message("❌ คำสั่งนี้ใช้ได้เฉพาะเจ้าของเซิร์ฟเวอร์เท่านั้น!", ephemeral=True)
        return False
    return True

# ---------------- Discord Bot ----------------
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------------- Slash Commands สำหรับจัดการบอท ----------------
@bot.tree.command(name="bot-status", description="ตรวจสอบสถานะบอทและเซิร์ฟเวอร์")
async def bot_status(interaction: discord.Interaction):
    if not await owner_only_check(interaction):
        return

    uptime = datetime.utcnow() - bot_start_time
    days = uptime.days
    hours, remainder = divmod(uptime.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    # ข้อมูลระบบ
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')

    embed = discord.Embed(
        title="🤖 สถานะบอทและเซิร์ฟเวอร์",
        color=discord.Color.green(),
        timestamp=datetime.utcnow()
    )

    embed.add_field(name="🟢 สถานะบอท", value="ออนไลน์", inline=True)
    embed.add_field(name="⏱️ Uptime", value=f"{days}d {hours}h {minutes}m {seconds}s", inline=True)
    embed.add_field(name="🏓 Ping", value=f"{round(bot.latency * 1000)}ms", inline=True)

    embed.add_field(name="💻 CPU", value=f"{cpu_percent}%", inline=True)
    embed.add_field(name="🧠 RAM", value=f"{memory.percent}% ({memory.used // 1024**3}GB/{memory.total // 1024**3}GB)", inline=True)
    embed.add_field(name="💾 Disk", value=f"{disk.percent}% ({disk.used // 1024**3}GB/{disk.total // 1024**3}GB)", inline=True)

    embed.add_field(name="🖥️ OS", value=platform.system(), inline=True)
    embed.add_field(name="🐍 Python", value=platform.python_version(), inline=True)
    embed.add_field(name="🔧 Discord.py", value=discord.__version__, inline=True)

    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="force-online", description="บังคับให้บอทออนไลน์ตลอดเวลา")
async def force_online(interaction: discord.Interaction):
    if not await owner_only_check(interaction):
        return

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="📊 เซิร์ฟเวอร์ออนไลน์ 24/7"
        ),
        status=discord.Status.online
    )

    embed = discord.Embed(
        title="✅ บังคับบอทออนไลน์สำเร็จ",
        description="บอทจะออนไลน์ตลอดเวลาและแสดงสถานะการเฝ้าระวัง",
        color=discord.Color.green()
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="server-check", description="ตรวจสอบการเชื่อมต่อเซิร์ฟเวอร์")
async def server_check(interaction: discord.Interaction, url: str | None = None):
    if not await owner_only_check(interaction):
        return

    await interaction.response.defer()

    # ถ้าไม่ใส่ URL จะเช็ค Flask server ของตัวเอง
    if url is None:
        url = "http://localhost:5000"

    if not url.startswith(('http://', 'https://')):
        url = f'https://{url}'

    try:
        start_time = asyncio.get_event_loop().time()
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                response_time = round((asyncio.get_event_loop().time() - start_time) * 1000)

                status_emoji = "🟢" if response.status == 200 else "🟡"
                status_color = discord.Color.green() if response.status == 200 else discord.Color.yellow()

                embed = discord.Embed(
                    title=f"{status_emoji} สถานะเซิร์ฟเวอร์",
                    color=status_color,
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="🌐 URL", value=url, inline=False)
                embed.add_field(name="📊 Status Code", value=response.status, inline=True)
                embed.add_field(name="⚡ Response Time", value=f"{response_time}ms", inline=True)

    except asyncio.TimeoutError:
        embed = discord.Embed(
            title="🔴 เซิร์ฟเวอร์ไม่ตอบสนอง",
            description="Request timeout - เซิร์ฟเวอร์ใช้เวลานานเกินไป",
            color=discord.Color.red()
        )
    except Exception as e:
        embed = discord.Embed(
            title="🔴 เกิดข้อผิดพลาด",
            description=f"Error: {str(e)}",
            color=discord.Color.red()
        )

    await interaction.followup.send(embed=embed)

@bot.tree.command(name="restart-bot", description="รีสตาร์ทบอทและเซอร์วิส")
async def restart_bot(interaction: discord.Interaction):
    if not await owner_only_check(interaction):
        return

    embed = discord.Embed(
        title="🔄 กำลังรีสตาร์ทบอท",
        description="บอทจะรีสตาร์ทใน 5 วินาที...",
        color=discord.Color.orange()
    )

    await interaction.response.send_message(embed=embed, ephemeral=True)

    # ส่งข้อความแจ้งเตือนไปยัง status channel
    status_channel = bot.get_channel(STATUS_DASHBOARD_ID)
    if status_channel and isinstance(status_channel, TextChannel):
        alert_embed = discord.Embed(
            title="🔄 รีสตาร์ทระบบ",
            description=f"Admin {interaction.user.mention} สั่งรีสตาร์ทบอท - รอสักครู่...",
            color=discord.Color.orange(),
            timestamp=datetime.utcnow()
        )
        await status_channel.send(embed=alert_embed)

    # รีสตาร์ทบอทหลังจาก 5 วินาที
    await asyncio.sleep(5)
    import os
    os._exit(0)  # ปิดบอทเพื่อให้ workflow supervisor รีสตาร์ทใหม่

# ---------------- Auto Keep-Alive และ Status Monitoring ----------------
@tasks.loop(minutes=2)  # ทุก 2 นาที
@safe_task_wrapper
async def keep_alive_task():
    """ฟังก์ชัน keep-alive เพื่อให้บอทออนไลน์ตลอดเวลา"""
    try:
        # อัพเดทสถานะบอท
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"📊 เซิร์ฟเวอร์ 24/7 | Uptime: {(datetime.utcnow() - bot_start_time).days}d"
            ),
            status=discord.Status.online
        )

        # ส่งสถานะไปยัง status channel
        status_channel = bot.get_channel(STATUS_DASHBOARD_ID)
        if status_channel and isinstance(status_channel, TextChannel):
            # คำนวณ uptime
            uptime = datetime.utcnow() - bot_start_time
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, _ = divmod(remainder, 60)

            # ข้อมูลระบบ
            cpu_percent = psutil.cpu_percent()
            memory = psutil.virtual_memory()

            # สร้าง embed สถานะ
            embed = discord.Embed(
                title="🟢 สถานะเซิร์ฟเวอร์ - ออนไลน์",
                color=discord.Color.green(),
                timestamp=datetime.utcnow()
            )

            embed.add_field(name="⏱️ Uptime", value=f"{days}d {hours}h {minutes}m", inline=True)
            embed.add_field(name="🏓 Ping", value=f"{round(bot.latency * 1000)}ms", inline=True)
            embed.add_field(name="💻 CPU", value=f"{cpu_percent}%", inline=True)
            embed.add_field(name="🧠 RAM", value=f"{memory.percent}%", inline=True)
            embed.add_field(name="🔋 Status", value="🟢 ปกติ", inline=True)
            embed.add_field(name="📡 Connected", value="✅ เชื่อมต่อแล้ว", inline=True)

            embed.set_footer(text="อัพเดทอัตโนมัติทุก 2 นาที")

            # ลบข้อความเก่าและส่งใหม่ (เก็บแค่ข้อความล่าสุด)
            async for message in status_channel.history(limit=10):
                if message.author == bot.user and message.embeds and message.embeds[0].title and "สถานะเซิร์ฟเวอร์" in message.embeds[0].title:
                    await message.delete()
                    break

            await status_channel.send(embed=embed)

    except Exception as e:
        await handle_discord_error(e, "keep_alive_task")
        logger.error(f"Keep-alive task error: {e}")

@tasks.loop(minutes=1)  # ทุก 1 นาที
@safe_task_wrapper
async def health_check():
    """ตรวจสอบสุขภาพเซิร์ฟเวอร์และส่งแจ้งเตือนหากมีปัญหา"""
    try:
        # ตรวจสอบ CPU และ Memory
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()

        # แจ้งเตือนหาก CPU หรือ Memory สูงเกินไป
        if cpu_percent > 80 or memory.percent > 85:
            alert_channel = bot.get_channel(ALERT_CHANNEL_ID)
            if alert_channel and isinstance(alert_channel, TextChannel):
                embed = discord.Embed(
                    title="⚠️ แจ้งเตือนประสิทธิภาพระบบ",
                    color=discord.Color.orange(),
                    timestamp=datetime.utcnow()
                )

                if cpu_percent > 80:
                    embed.add_field(name="🔥 CPU สูง", value=f"{cpu_percent}%", inline=True)

                if memory.percent > 85:
                    embed.add_field(name="🧠 RAM สูง", value=f"{memory.percent}%", inline=True)

                embed.set_footer(text="กรุณาตรวจสอบระบบ")
                await alert_channel.send(embed=embed)

    except Exception as e:
        await handle_discord_error(e, "health_check")
        logger.error(f"Health check error: {e}")

@keep_alive_task.before_loop
async def before_keep_alive():
    await bot.wait_until_ready()

@health_check.before_loop  
async def before_health_check():
    await bot.wait_until_ready()

# ---------------- Fake Activity Task ----------------
@tasks.loop(seconds=45)  # ทุก 45 วินาที
@safe_task_wrapper
async def fake_activity_task():
    """จำลองการใช้งานระบบเพื่อให้เซิร์ฟเวอร์ไม่หยุดทำงาน"""
    try:
        # 1. ส่ง HTTP request ไปยัง Flask server ของตัวเอง
        try:
            # ใช้ port ที่ถูกต้องสำหรับ Render.com
            port = os.environ.get('PORT', '10000')
            local_url = f"http://localhost:{port}/ping"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(local_url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    pass  # แค่ ping server เพื่อ keep alive
        except:
            pass  # ไม่ต้องแสดง error ถ้า ping ไม่ได้

        # 2. เปลี่ยนสถานะบอทเล็กน้อยเพื่อแสดงว่ากำลังทำงาน
        activities = [
            "📊 เซิร์ฟเวอร์ออนไลน์ 24/7",
            "🔥 พร้อมยิง NGL ตลอดเวลา",
            "⚡ ระบบรันตลอด 24 ชั่วโมง",
            "🚀 บอทพร้อมใช้งาน",
            "💪 ระบบแกร่งไม่มีหยุด"
        ]

        activity_name = random.choice(activities)
        await bot.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=activity_name
            ),
            status=discord.Status.online
        )

        # 3. เพิ่มการใช้งาน CPU เล็กน้อยเพื่อจำลองกิจกรรม
        random_calc = sum(range(random.randint(100, 500)))  # การคำนวณสั้น ๆ

    except Exception as e:
        await handle_discord_error(e, "fake_activity_task")
        logger.error(f"Fake activity task error: {e}")

@fake_activity_task.before_loop
async def before_fake_activity():
    await bot.wait_until_ready()

# ---------------- Enhanced UI Modals ----------------
class NGLConfigModal(ui.Modal):
    def __init__(self, preset_values: dict = None):
        super().__init__(title="⚙️ ตั้งค่า NGL - ระบบปรับแต่ง")
        
        preset = preset_values or {}
        
        self.username_input = ui.TextInput(
            label="🎯 ชื่อผู้ใช้ NGL หรือ Link",
            placeholder="username หรือ https://ngl.link/username",
            default=preset.get('username', ''),
            max_length=100
        )
        
        self.amount_input = ui.TextInput(
            label="🔢 จำนวนข้อความ (1-200)",
            placeholder="ใส่จำนวนข้อความที่ต้องการส่ง",
            default=str(preset.get('amount', 10)),
            max_length=3
        )
        
        self.speed_input = ui.TextInput(
            label="⚡ ความเร็ว (วินาที)",
            placeholder="ความล่าช้าระหว่างข้อความ (0.1-10)",
            default=str(preset.get('speed', 1.0)),
            max_length=4
        )
        
        self.custom_message_input = ui.TextInput(
            label="📝 ข้อความกำหนดเอง (ถ้าต้องการ)",
            placeholder="ปล่อยว่างไว้เพื่อใช้ข้อความสุ่ม",
            default=preset.get('message', ''),
            required=False,
            max_length=200
        )
        
        self.add_item(self.username_input)
        self.add_item(self.amount_input) 
        self.add_item(self.speed_input)
        self.add_item(self.custom_message_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            username = self.username_input.value.strip()
            if not username:
                await interaction.response.send_message("❌ กรุณาใส่ username!", ephemeral=True)
                return
                
            try:
                amount = int(self.amount_input.value.strip())
                amount = max(1, min(200, amount))
            except:
                amount = 10
                
            try:
                speed = float(self.speed_input.value.strip())
                speed = max(0.1, min(10.0, speed))
            except:
                speed = 1.0
                
            custom_message = self.custom_message_input.value.strip() if self.custom_message_input.value else None
            is_random = custom_message is None
            
            # แสดงการยืนยัน
            embed = discord.Embed(
                title="🚀 ยืนยันการยิง NGL",
                color=discord.Color.orange(),
                timestamp=datetime.utcnow()
            )
            embed.add_field(name="🎯 เป้าหมาย", value=username, inline=True)
            embed.add_field(name="🔢 จำนวน", value=f"{amount} ข้อความ", inline=True)
            embed.add_field(name="⚡ ความเร็ว", value=f"{speed} วินาที", inline=True)
            embed.add_field(name="📝 ข้อความ", value="สุ่มข้อความ" if is_random else f"กำหนดเอง: {custom_message[:50]}...", inline=False)
            embed.add_field(name="🛡️ ความปลอดภัย", value="ใช้ Proxy + Bot Detection Avoidance", inline=False)
            
            view = ConfirmationView(username, amount, speed, custom_message, is_random)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            
        except Exception as e:
            await interaction.response.send_message(f"❌ เกิดข้อผิดพลาด: {e}", ephemeral=True)

class ConfirmationView(ui.View):
    def __init__(self, username: str, amount: int, speed: float, message: Optional[str] = None, is_random: bool = True):
        super().__init__(timeout=60)
        self.username = username
        self.amount = amount
        self.speed = speed
        self.message = message
        self.is_random = is_random
    
    @ui.button(label="✅ ยืนยัน - เริ่มยิง", style=discord.ButtonStyle.green, emoji="🚀")
    async def confirm_shooting(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🚀 เริ่มยิง NGL แล้ว! ติดตามผลได้ที่ช่องสถานะ", ephemeral=True)
        await send_ngl(bot, self.username, self.amount, self.speed, self.message, self.is_random)
        self.stop()
    
    @ui.button(label="❌ ยกเลิก", style=discord.ButtonStyle.red, emoji="⏹️")
    async def cancel_shooting(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⏹️ ยกเลิกการยิงแล้ว", ephemeral=True)
        self.stop()

class QuickPresetModal(ui.Modal):
    def __init__(self):
        super().__init__(title="⚡ Quick Shot - ยิงด่วน")
        
        self.username_input = ui.TextInput(
            label="🎯 Username",
            placeholder="ใส่ username เท่านั้น",
            max_length=50
        )
        
        self.add_item(self.username_input)

    async def on_submit(self, interaction: discord.Interaction):
        username = self.username_input.value.strip()
        if not username:
            await interaction.response.send_message("❌ กรุณาใส่ username!", ephemeral=True)
            return
            
        # ใช้ค่าเริ่มต้น: 15 ข้อความ, 1 วินาที, สุ่มข้อความ
        await interaction.response.send_message(f"⚡ เริ่ม Quick Shot ไปยัง {username}!", ephemeral=True)
        await send_ngl(bot, username, 15, 1.0, None, True)

# ---------------- Enhanced Block Selection UI ----------------
class NGLControlView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @ui.button(label="🚀 ยิง NGL แบบกำหนดเอง", style=discord.ButtonStyle.primary, emoji="⚙️", row=0)
    async def custom_ngl(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(NGLConfigModal())
    
    @ui.button(label="⚡ ยิงด่วน (Quick Shot)", style=discord.ButtonStyle.green, emoji="🎯", row=0)
    async def quick_shot(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(QuickPresetModal())
    
    @ui.button(label="🔄 Preset: ปกติ", style=discord.ButtonStyle.secondary, emoji="📊", row=1)
    async def preset_normal(self, interaction: discord.Interaction, button: discord.ui.Button):
        preset_values = {'amount': 20, 'speed': 1.5}
        await interaction.response.send_modal(NGLConfigModal(preset_values))
    
    @ui.button(label="💥 Preset: หนัก", style=discord.ButtonStyle.secondary, emoji="🔥", row=1)
    async def preset_heavy(self, interaction: discord.Interaction, button: discord.ui.Button):
        preset_values = {'amount': 50, 'speed': 0.8}
        await interaction.response.send_modal(NGLConfigModal(preset_values))
    
    @ui.button(label="🐌 Preset: ช้า", style=discord.ButtonStyle.secondary, emoji="🛡️", row=1)
    async def preset_slow(self, interaction: discord.Interaction, button: discord.ui.Button):
        preset_values = {'amount': 10, 'speed': 3.0}
        await interaction.response.send_modal(NGLConfigModal(preset_values))

class ControlPanelView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @ui.button(label="⏹️ หยุดยิงทั้งหมด", style=discord.ButtonStyle.danger, emoji="🛑", row=0)
    async def emergency_stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        global stop_sending
        stop_sending = True
        
        embed = discord.Embed(
            title="🛑 หยุดยิงฉุกเฉิน",
            description="สั่งหยุดการยิง NGL ทั้งหมดแล้ว",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await alert_server(bot, f"ผู้ใช้ {interaction.user.mention} สั่งหยุดการยิง NGL ฉุกเฉิน", "WARNING")
    
    @ui.button(label="📊 ตรวจสอบสถานะ", style=discord.ButtonStyle.blurple, emoji="📈", row=0)
    async def check_status(self, interaction: discord.Interaction, button: discord.ui.Button):
        proxy_status = "🟢 เปิดใช้งาน" if PROXY_ENABLED else "🔴 ปิดใช้งาน"
        proxy_count = len(proxy_manager.proxies)
        working_proxies = sum(1 for p in proxy_manager.proxies if p.working)
        
        embed = discord.Embed(
            title="📊 สถานะระบบ NGL",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="🛡️ Proxy", value=proxy_status, inline=True)
        embed.add_field(name="🌐 Proxy ทั้งหมด", value=f"{proxy_count} ตัว", inline=True)
        embed.add_field(name="✅ Proxy ใช้งานได้", value=f"{working_proxies} ตัว", inline=True)
        embed.add_field(name="🚀 สถานะการยิง", value="ไม่ได้ยิง" if not stop_sending else "กำลังยิง", inline=True)
        
        # เพิ่มข้อมูลการยิงล่าสุด
        if last_sent:
            recent_targets = list(last_sent.keys())[-3:]  # 3 target ล่าสุด
            embed.add_field(name="🎯 เป้าหมายล่าสุด", value="\n".join(recent_targets) if recent_targets else "ไม่มี", inline=False)
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @ui.button(label="🔧 ตั้งค่า Proxy", style=discord.ButtonStyle.secondary, emoji="⚙️", row=1)  
    async def proxy_settings(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="🔧 การตั้งค่า Proxy",
            description="วิธีการตั้งค่า Proxy สำหรับระบบ",
            color=discord.Color.yellow()
        )
        embed.add_field(
            name="📝 วิธีตั้งค่า",
            value="""
            ตั้งค่าใน Environment Variables:
            ```
            PROXY_ENABLED=true
            PROXY_LIST=http://proxy1:port,http://proxy2:port
            ```
            """,
            inline=False
        )
        embed.add_field(
            name="💡 ข้อแนะนำ", 
            value="• ใช้ proxy หลายตัวเพื่อเพิ่มเสถียรภาพ\n• ตรวจสอบ proxy ก่อนใช้งาน\n• proxy ที่เสียจะถูกข้ามอัตโนมัติ",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    @ui.button(label="ℹ️ คู่มือการใช้งาน", style=discord.ButtonStyle.secondary, emoji="📖", row=1)
    async def user_guide(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="📖 คู่มือการใช้งาน NGL Bot",
            color=discord.Color.green()
        )
        embed.add_field(
            name="🚀 การยิง NGL",
            value="• **ยิงด่วน**: ใส่แค่ username\n• **กำหนดเอง**: ปรับแต่งทุกอย่าง\n• **Preset**: ใช้ค่าที่ตั้งไว้",
            inline=False
        )
        embed.add_field(
            name="🛡️ ความปลอดภัย",
            value="• ใช้ Proxy อัตโนมัติ\n• หลีกเลี่ยงการตรวจจับ\n• Rate limiting ป้องกัน ban",
            inline=False
        )
        embed.add_field(
            name="⚡ ความเร็ว",
            value="• 0.1-1.0s = เร็วมาก (เสี่ยง)\n• 1.0-2.0s = ปกติ (แนะนำ)\n• 2.0s+ = ช้า (ปลอดภัย)",
            inline=False
        )
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

# ---------------- on_ready ----------------
@bot.event
async def on_ready():
    print(f"Bot พร้อมใช้งาน: {bot.user}")
    try: 
        await bot.tree.sync()
        print("Slash Commands Synced ✅")
    except Exception as e: 
        print(f"❌ Slash Commands Sync Error: {e}")

    # เริ่ม keep-alive และ monitoring tasks
    if not keep_alive_task.is_running():
        keep_alive_task.start()
        print("✅ Keep-Alive Task เริ่มทำงาน")

    if not health_check.is_running():
        health_check.start()
        print("✅ Health Check Task เริ่มทำงาน")

    if not fake_activity_task.is_running():
        fake_activity_task.start()
        print("✅ Fake Activity Task เริ่มทำงาน - จำลองการใช้งานเพื่อ Keep-Alive")
        
    if not performance_monitor_task.is_running():
        performance_monitor_task.start()
        print("✅ Performance Monitor Task เริ่มทำงาน - ตรวจสอบประสิทธิภาพขั้นสูง")

    # เริ่มระบบตรวจสอบสุขภาพ Proxy (Professional Enhancement)
    if PROXY_ENABLED and proxy_manager.proxies:
        proxy_manager.start_health_checks()
        print("✅ Proxy Health Check System เริ่มทำงาน - ตรวจสอบ Proxy ขั้นสูง")

    # ตั้งสถานะเริ่มต้น
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="📊 เซิร์ฟเวอร์ออนไลน์ 24/7"
        ),
        status=discord.Status.online
    )

    # ลบข้อความเก่าในช่อง UI ก่อนส่งใหม่
    ui_channel = bot.get_channel(CHANNEL_UI_ID)
    if ui_channel and hasattr(ui_channel, 'send') and hasattr(ui_channel, 'history'):
        async for msg in ui_channel.history(limit=50):
            if msg.id not in KEEP_CHANNELS:
                try:
                    await msg.delete()
                except:
                    pass
        
        # สร้าง UI หลักด้วย embed สวยงาม
        main_embed = discord.Embed(
            title="🚀 ระบบยิง NGL - Premium Edition",
            description="ระบบยิง NGL ที่ทันสมัยและปลอดภัยที่สุด พร้อมการป้องกันการตรวจจับขั้นสูง",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        main_embed.add_field(
            name="✨ คุณสมบัติพิเศษ",
            value="🛡️ ระบบ Proxy อัตโนมัติ\n🤖 หลีกเลี่ยงการตรวจจับบอท\n⚡ ความเร็วสูงแต่ปลอดภัย\n📊 ติดตามสถานะแบบเรียลไทม์",
            inline=True
        )
        main_embed.add_field(
            name="🎯 วิธีใช้งาน",
            value="1️⃣ เลือกโหมดการยิง\n2️⃣ ใส่ข้อมูลเป้าหมาย\n3️⃣ ปรับแต่งการตั้งค่า\n4️⃣ เริ่มยิง!",
            inline=True
        )
        main_embed.add_field(
            name="⚠️ ข้อควรระวัง",
            value="• ใช้ความเร็วที่เหมาะสม\n• ตรวจสอบ proxy status\n• อย่าใช้งานเกินความจำเป็น",
            inline=False
        )
        main_embed.set_footer(text="Bot ทำงาน 24/7 | พัฒนาโดยระบบ AI ขั้นสูง")
        
        await ui_channel.send(embed=main_embed, view=NGLControlView())
        
        # ส่ง Control Panel ในข้อความแยก
        control_embed = discord.Embed(
            title="🎛️ แผงควบคุมระบบ",
            description="จัดการและตรวจสอบสถานะการทำงาน",
            color=discord.Color.orange()
        )
        await ui_channel.send(embed=control_embed, view=ControlPanelView())

    # ส่งข้อความแจ้งเตือนการเริ่มทำงาน
    alert_channel = bot.get_channel(ALERT_CHANNEL_ID)
    if alert_channel and hasattr(alert_channel, 'send'):
        startup_embed = discord.Embed(
            title="🟢 บอทเริ่มทำงาน",
            description="บอทพร้อมใช้งานและระบบ Keep-Alive ทำงานแล้ว",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        await alert_channel.send(embed=startup_embed)

# ---------------- Keep-Alive Flask Server สำหรับ Render.com ----------------
app = Flask(__name__)

# Disable Flask debug logs สำหรับ production
import logging
logging.getLogger('werkzeug').setLevel(logging.ERROR)

# Basic endpoints
@app.route('/')
def home():
    """Homepage สำหรับ cron-job.org และ monitoring"""
    return {
        "status": "Bot is running",
        "timestamp": datetime.utcnow().isoformat(),
        "uptime_seconds": (datetime.utcnow() - bot_start_time).total_seconds(),
        "message": "Discord Bot Active on Render.com"
    }

@app.route('/ping')
def ping():
    """Simple ping endpoint สำหรับ cron-job.org"""
    return {"status": "pong", "timestamp": datetime.utcnow().isoformat()}

@app.route('/keep-alive')
def keep_alive():
    """Keep-alive endpoint สำหรับ cron jobs"""
    return {
        "alive": True,
        "bot_ready": bot.is_ready() if 'bot' in globals() else False,
        "uptime": (datetime.utcnow() - bot_start_time).total_seconds()
    }

def run_flask():
    """รัน Flask server บน port ที่ Render.com กำหนด"""
    try:
        # Render.com จะส่ง PORT environment variable
        port = int(os.environ.get('PORT', 10000))  # Default port สำหรับ Render
        host = '0.0.0.0'  # Bind ทุก interfaces
        
        print(f"🌐 Starting Flask server on {host}:{port}")
        
        # รัน Flask โดยไม่แสดง debug logs
        app.run(
            host=host, 
            port=port, 
            debug=False,
            use_reloader=False,  # ป้องกัน double-loading
            threaded=True        # รองรับ multiple requests
        )
    except Exception as e:
        print(f"❌ Flask server error: {e}")
        logger.error(f"Flask server failed to start: {e}")

# ---------------- Auto-Restart และ Performance Monitoring ----------------
@tasks.loop(minutes=5)  # ตรวจสอบทุก 5 นาที
async def performance_monitor_task():
    """ตรวจสอบประสิทธิภาพและสถานะระบบขั้นสูง"""
    
    # ทำความสะอาดข้อมูลเก่า
    await cleanup_old_data()
    
    try:
        # ข้อมูลระบบปัจจุบัน
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # ตรวจสอบเงื่อนไขวิกฤต
        critical_conditions = []
        warnings = []
        
        if cpu_percent > 90:
            critical_conditions.append(f"CPU สูงมาก: {cpu_percent}%")
        elif cpu_percent > 80:
            warnings.append(f"CPU สูง: {cpu_percent}%")
            
        if memory.percent > 95:
            critical_conditions.append(f"RAM เต็มเกือบหมด: {memory.percent}%")
        elif memory.percent > 85:
            warnings.append(f"RAM สูง: {memory.percent}%")
            
        if disk.percent > 95:
            critical_conditions.append(f"Disk เต็มเกือบหมด: {disk.percent}%")
        elif disk.percent > 90:
            warnings.append(f"Disk เหลือน้อย: {disk.percent}%")
        
        # แจ้งเตือนตามระดับความร้ายแรง
        if critical_conditions:
            await alert_server(bot, f"🛑 สถานะวิกฤต:\n" + "\n".join(critical_conditions), "CRITICAL")
            
        if warnings:
            await alert_server(bot, f"⚠️ คำเตือน:\n" + "\n".join(warnings), "WARNING")
            
        # Log ข้อมูล performance
        logger.bind(PERF=True).debug(f"CPU: {cpu_percent}%, RAM: {memory.percent}%, Disk: {disk.percent}%")
        
        # เก็บสถิติ
        server_stats['last_cpu'] = cpu_percent
        server_stats['last_memory'] = memory.percent
        server_stats['last_disk'] = disk.percent
        
    except Exception as e:
        await handle_discord_error(e, "performance_monitor_task")

@performance_monitor_task.before_loop
async def before_performance_monitor():
    await bot.wait_until_ready()

async def emergency_restart():
    """ฟังก์ชันสำหรับการ restart ฉุกเฉิน"""
    try:
        await alert_server(bot, "🔄 เริ่มกระบวนการ restart ฉุกเฉิน...", "CRITICAL")
        
        # บันทึกสถิติก่อน restart
        server_stats['last_restart'] = datetime.utcnow()
        logger.critical("Emergency restart initiated")
        
        # แจ้งช่องหลักๆ
        for channel_id in [ALERT_CHANNEL_ID, CHANNEL_STATUS_ID]:
            channel = bot.get_channel(channel_id)
            if channel:
                await channel.send("🔄 **ระบบจะ restart ภายใน 10 วินาที**")
        
        await asyncio.sleep(10)
        
        # ปิดการเชื่อมต่อ Discord อย่างปลอดภัย
        await bot.close()
        
    except Exception as e:
        logger.critical(f"Emergency restart failed: {e}")

# ---------------- Enhanced Flask with Monitoring ----------------
@app.route('/health')
def health_check_endpoint():
    """Health check endpoint สำหรับระบบภายนอก"""
    try:
        uptime = (datetime.utcnow() - bot_start_time).total_seconds()
        return {
            "status": "healthy",
            "uptime_seconds": uptime,
            "bot_ready": bot.is_ready(),
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
            "errors_count": server_stats.get('errors_count', 0),
            "critical_errors": server_stats.get('critical_errors', 0),
            "commands_executed": server_stats.get('commands_executed', 0),
            "messages_processed": server_stats.get('messages_processed', 0),
            "render_info": {
                "port": os.environ.get('PORT', 'Not set'),
                "environment": os.environ.get('RENDER_ENVIRONMENT', 'Unknown')
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e), "timestamp": datetime.utcnow().isoformat()}, 500

@app.route('/metrics')
def metrics_endpoint():
    """Metrics endpoint สำหรับ monitoring tools"""
    try:
        return {
            "bot_uptime": (datetime.utcnow() - bot_start_time).total_seconds(),
            "commands_executed": server_stats['commands_executed'],
            "messages_processed": server_stats['messages_processed'],
            "errors_total": server_stats['errors_count'],
            "critical_errors": server_stats['critical_errors'],
            "rate_limit_hits": server_stats['rate_limit_hits'],
            "connection_retries": server_stats['connection_retries'],
            "last_error": server_stats.get('last_error', 'None'),
            "system_cpu": psutil.cpu_percent(),
            "system_memory": psutil.virtual_memory().percent,
            "system_disk": psutil.disk_usage('/').percent
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}, 500

# ---------------- Run Flask Server for Render.com ----------------
def start_flask_server():
    """เริ่ม Flask server ใน background thread"""
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.name = "FlaskServer"
    flask_thread.start()
    print("🌐 Flask server thread started")
    return flask_thread

# เริ่ม Flask server ทันที
flask_thread = start_flask_server()

# Enhanced bot startup with retry logic
async def start_bot_with_retry():
    """เริ่มบอทพร้อมระบบ retry และ recovery"""
    max_retries = 5
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"Starting bot (attempt {retry_count + 1}/{max_retries})...")
            if TOKEN:
                await bot.start(TOKEN)
            else:
                raise ValueError("DISCORD_TOKEN not found in environment variables")
            break
        except Exception as e:
            retry_count += 1
            logger.error(f"Bot start failed (attempt {retry_count}): {e}")
            
            if retry_count < max_retries:
                wait_time = min(30 * retry_count, 300)  # เพิ่มเวลารอแต่ไม่เกิน 5 นาที
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                logger.critical("Max retries reached. Bot failed to start.")
                raise

if TOKEN:
    try:
        # เริ่มบอทด้วยระบบ retry
        import asyncio
        asyncio.run(start_bot_with_retry())
    except KeyboardInterrupt:
        logger.info("Bot shutdown by user")
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        print(f"❌ ข้อผิดพลาดร้ายแรง: {e}")
else:
    print("❌ ไม่พบ DISCORD_TOKEN ในตัวแปรสภาพแวดล้อม!")
