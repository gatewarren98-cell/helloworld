import os
import tempfile
import aiohttp
from jinja2 import Template
from playwright.async_api import async_playwright

from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.message_components import Image  # 引入 AstrBot 的图片组件

# ！！请务必在此处填入你申请的 ALS API Key ！！
ALS_API_KEY = "b7bc7443be72109d3c31e3fc85d3183f"

# ==========================================
# HTML / CSS 模板定义
# ==========================================
PLAYER_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { margin: 0; padding: 20px; display: inline-block; background-color: transparent; }
        .card { background: linear-gradient(135deg, #2b2b2b, #1a1a1a); border: 2px solid #cc2936; border-radius: 12px; padding: 20px 30px; width: 350px; color: #ecf0f1; font-family: 'Segoe UI', Tahoma, sans-serif; box-shadow: 0 10px 20px rgba(0,0,0,0.5); }
        .header { font-size: 24px; font-weight: bold; text-align: center; color: #e74c3c; border-bottom: 2px solid #444; padding-bottom: 15px; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 2px; }
        .info-row { display: flex; justify-content: space-between; margin: 12px 0; font-size: 18px; }
        .label { color: #95a5a6; }
        .value { font-weight: bold; color: #f1c40f; }
    </style>
</head>
<body>
    <div class="card" id="apex-card">
        <div class="header">Apex Legends Stats</div>
        <div class="info-row"><span class="label">玩家 ID:</span><span class="value">{{ player_name }}</span></div>
        <div class="info-row"><span class="label">当前等级:</span><span class="value">Lv.{{ level }}</span></div>
        <div class="info-row"><span class="label">大逃杀段位:</span><span class="value">{{ rank_name }} {{ rank_div }}</span></div>
        <div class="info-row"><span class="label">排位分数:</span><span class="value">{{ rank_score }} RP</span></div>
    </div>
</body>
</html>
"""

MAP_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { margin: 0; padding: 20px; display: inline-block; background-color: transparent; }
        .container { background: #1a1a1a; border: 2px solid #cc2936; border-radius: 12px; padding: 20px; width: 500px; color: #ecf0f1; font-family: 'Segoe UI', Tahoma, sans-serif; box-shadow: 0 10px 20px rgba(0,0,0,0.5); }
        .header { font-size: 24px; font-weight: bold; text-align: center; color: #e74c3c; border-bottom: 2px solid #444; padding-bottom: 10px; margin-bottom: 20px; letter-spacing: 2px; }
        .mode-section { position: relative; margin-bottom: 20px; border-radius: 8px; overflow: hidden; height: 120px; }
        .bg-image { position: absolute; top: 0; left: 0; width: 100%; height: 100%; object-fit: cover; opacity: 0.6; z-index: 1; }
        .content { position: relative; z-index: 2; padding: 15px; background: linear-gradient(90deg, rgba(0,0,0,0.9) 0%, rgba(0,0,0,0.4) 100%); height: 100%; box-sizing: border-box; }
        .mode-title { font-size: 18px; color: #f1c40f; font-weight: bold; margin-bottom: 5px; }
        .map-name { font-size: 22px; font-weight: bold; color: white; text-shadow: 1px 1px 3px black; }
        .timer { font-size: 14px; color: #2ecc71; margin-top: 5px; }
        .next-map { font-size: 12px; color: #bdc3c7; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="container" id="map-card">
        <div class="header">APEX 地图轮换</div>
        <div class="mode-section">
            <img class="bg-image" src="{{ pubs_img }}">
            <div class="content">
                <div class="mode-title">🗡️ 匹配模式 (Pubs)</div>
                <div class="map-name">{{ pubs_current }}</div>
                <div class="timer">剩余时间: {{ pubs_timer }}</div>
                <div class="next-map">下一张: {{ pubs_next }}</div>
            </div>
        </div>
        <div class="mode-section">
            <img class="bg-image" src="{{ ranked_img }}">
            <div class="content">
                <div class="mode-title">🏆 排位赛 (Ranked)</div>
                <div class="map-name">{{ ranked_current }}</div>
                <div class="timer">剩余时间: {{ ranked_timer }}</div>
                <div class="next-map">下一张: {{ ranked_next }}</div>
            </div>
        </div>
    </div>
</body>
</html>
"""

@register("apex_query", "开发者", "Apex图文查询与地图插件", "1.0.0")
class ApexQueryPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    # ==========================
    # 功能一：玩家数据查询
    # ==========================
    @filter.command("查apex")
    async def query_apex(self, event: AstrMessageEvent, player_name: str = ""):
        if not player_name:
            yield event.plain_result("❌ 请输入玩家ID，例如：/查apex ItzTimmy")
            return
            
        yield event.plain_result(f"⏳ 正在查询并渲染 {player_name} 的数据图片...")
        url = f"https://api.mozambiquehe.re/bridge?auth={ALS_API_KEY}&player={player_name}&platform=PC"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=False) as response:
                    data = await response.json()
                    if "Error" in data:
                        yield event.plain_result(f"❌ 查询失败：{data['Error']}")
                        return

                    global_data = data.get("global", {})
                    rank_data = global_data.get("rank", {})

            # 渲染 HTML
            html_content = Template(PLAYER_HTML_TEMPLATE).render(
                player_name=player_name,
                level=global_data.get("level", "未知"),
                rank_name=rank_data.get("rankName", "未知"),
                rank_div=rank_data.get("rankDiv", ""),
                rank_score=rank_data.get("rankScore", 0)
            )

            # 截图并发送
            image_path = await self._render_to_image(html_content, "#apex-card")
            yield event.chain([Image.fromFileSystem(image_path)])
            os.remove(image_path)  # 发送后清理临时图片

        except Exception as e:
            logger.error(f"Apex查询异常: {e}")
            yield event.plain_result("❌ 插件运行异常，请检查日志。")

    # ==========================
    # 功能二：地图轮换查询
    # ==========================
    @filter.command("apex地图")
    async def query_apex_map(self, event: AstrMessageEvent):
        yield event.plain_result("🗺️ 正在获取最新地图数据并渲染...")
        url = f"https://api.mozambiquehe.re/maprotation?version=2&auth={ALS_API_KEY}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=False) as response:
                    data = await response.json()
                    if "Error" in data:
                        yield event.plain_result(f"❌ 查询失败：{data['Error']}")
                        return

                    pubs = data.get("battle_royale", {})
                    ranked = data.get("ranked", {})

            # 渲染 HTML
            html_content = Template(MAP_HTML_TEMPLATE).render(
                pubs_current=pubs.get("current", {}).get("map", "未知"),
                pubs_timer=pubs.get("current", {}).get("remainingTimer", "未知"),
                pubs_img=pubs.get("current", {}).get("asset", ""),
                pubs_next=pubs.get("next", {}).get("map", "未知"),
                ranked_current=ranked.get("current", {}).get("map", "未知"),
                ranked_timer=ranked.get("current", {}).get("remainingTimer", "未知"),
                ranked_img=ranked.get("current", {}).get("asset", ""),
                ranked_next=ranked.get("next", {}).get("map", "未知")
            )

            # 截图并发送 (传入 wait_until 保证背景大图加载完毕)
            image_path = await self._render_to_image(html_content, "#map-card", wait_network=True)
            yield event.chain([Image.fromFileSystem(image_path)])
            os.remove(image_path)

        except Exception as e:
            logger.error(f"地图查询异常: {e}")
            yield event.plain_result("❌ 地图获取异常，请检查日志。")

    # ==========================
    # 辅助函数：调用无头浏览器截图
    # ==========================
    async def _render_to_image(self, html_content: str, selector: str, wait_network=False) -> str:
        async with async_playwright() as p:
            # 增加参数以适配 Docker 环境
            browser = await p.chromium.launch(args=['--no-sandbox', '--disable-setuid-sandbox'])
            page = await browser.new_page()
            
            if wait_network:
                await page.set_content(html_content, wait_until="networkidle")
            else:
                await page.set_content(html_content)
                
            element = await page.query_selector(selector)
            
            # 创建临时文件保存图片
            fd, path = tempfile.mkstemp(suffix=".png")
            os.close(fd)
            await element.screenshot(path=path, omit_background=True)
            
            await browser.close()
            return path
