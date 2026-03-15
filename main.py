import aiohttp
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.message_components import Image

# ！！请务必在此处填入你申请的 ALS API Key ！！
ALS_API_KEY = "b7bc7443be72109d3c31e3fc85d3183f"

@register("apex_query", "开发者", "Apex原生轻量级查询插件", "1.0.0")
class ApexQueryPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    # ==========================
    # 功能一：玩家数据查询 (纯文本排版)
    # ==========================
    @filter.command("查apex")
    async def query_apex(self, event: AstrMessageEvent, player_name: str = ""):
        if not player_name:
            yield event.plain_result("❌ 请输入玩家ID，例如：/查apex ItzTimmy")
            return
            
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
                    
                    # 提取数据
                    level = global_data.get("level", "未知")
                    rank_name = rank_data.get("rankName", "未知")
                    rank_div = rank_data.get("rankDiv", "")
                    rank_score = rank_data.get("rankScore", 0)
                    
                    # 也可以提取玩家当前选择的传奇
                    legend_name = global_data.get("legend", "未知")

            # 仿 Discord Embed 风格的纯文本排版
            msg = (
                f"🎮 𝗔𝗣𝗘𝗫 𝗟𝗘𝗚𝗘𝗡𝗗𝗦 𝗦𝗧𝗔𝗧𝗦 🎮\n"
                f"━━━━━━━━━━━━━━━\n"
                f"👤 玩家: {player_name}\n"
                f"🔰 等级: Lv.{level}\n"
                f"🏆 段位: {rank_name} {rank_div} ({rank_score} RP)\n"
                f"🦸 传奇: {legend_name}\n"
                f"━━━━━━━━━━━━━━━"
            )
            yield event.plain_result(msg)

        except Exception as e:
            logger.error(f"Apex查询异常: {e}")
            yield event.plain_result("❌ 插件网络请求异常，请检查后台日志。")

    # ==========================
    # 功能二：地图轮换查询 (原生文本 + 网络图片)
    # ==========================
    @filter.command("apex地图")
    async def query_apex_map(self, event: AstrMessageEvent):
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

                    # 提取匹配数据
                    pubs_current = pubs.get("current", {}).get("map", "未知")
                    pubs_timer = pubs.get("current", {}).get("remainingTimer", "未知")
                    pubs_next = pubs.get("next", {}).get("map", "未知")
                    pubs_img = pubs.get("current", {}).get("asset", "") # 官方提供的地图图片 URL

                    # 提取排位数据
                    ranked_current = ranked.get("current", {}).get("map", "未知")
                    ranked_timer = ranked.get("current", {}).get("remainingTimer", "未知")
                    ranked_next = ranked.get("next", {}).get("map", "未知")

            # 构造消息文本
            msg = (
                f"🗺️ 𝗔𝗣𝗘𝗫 地图轮换 🗺️\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🗡️ 【匹配模式】\n"
                f"➤ 当前: {pubs_current} ({pubs_timer})\n"
                f"➤ 下一轮: {pubs_next}\n\n"
                f"🏆 【排位模式】\n"
                f"➤ 当前: {ranked_current} ({ranked_timer})\n"
                f"➤ 下一轮: {ranked_next}\n"
                f"━━━━━━━━━━━━━━━"
            )

            # 使用 AstrBot V4 构建消息：文本 + 直接发送网络图片URL
            res = event.make_result().message(msg)
            
            # 如果 API 返回了图片 URL，直接让机器人发送这张图，无需自己渲染
            if pubs_img:
                res.chain.append(Image.fromURL(pubs_img))
                
            yield res

        except Exception as e:
            logger.error(f"地图查询异常: {e}")
            yield event.plain_result("❌ 地图获取异常，请检查后台日志。")
