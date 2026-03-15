import aiohttp
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

# ！！请务必在此处填入你申请的 ALS API Key ！！
ALS_API_KEY = "YOUR_API_KEY_HERE"

@register("apex_query", "开发者", "Apex Legends 玩家数据查询插件", "1.0.0")
class ApexQueryPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    # 注册指令：触发词为 "查apex"
    # AstrBot 会自动将指令后面的文本解析为 player_name 变量
    @filter.command("查apex")
    async def query_apex(self, event: AstrMessageEvent, player_name: str = ""):
        # 1. 检查是否输入了玩家名
        if not player_name:
            yield event.plain_result("❌ 请输入想要查询的玩家ID，例如：/查apex ItzTimmy")
            return
            
        # 2. 发送提示信息 (使用 yield 可以连续回复多条消息)
        yield event.plain_result(f"⏳ 正在查询 {player_name} 的Apex数据，请稍候...")

        # 3. 构建 API 请求 URL
        url = f"https://api.mozambiquehe.re/bridge?auth={ALS_API_KEY}&player={player_name}&platform=PC"

        try:
            # 4. 发起异步网络请求 (加入了 ssl=False 防止老旧系统的证书报错)
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=False) as response:
                    if response.status != 200:
                        yield event.plain_result(f"❌ 查询失败，可能是API限制或网络问题。状态码: {response.status}")
                        return
                    
                    data = await response.json()

                    if "Error" in data:
                        yield event.plain_result(f"❌ 查询失败：{data['Error']}")
                        return

                    # 5. 解析数据
                    global_data = data.get("global", {})
                    level = global_data.get("level", "未知")
                    
                    rank_data = global_data.get("rank", {})
                    rank_name = rank_data.get("rankName", "未知")
                    rank_div = rank_data.get("rankDiv", "")
                    rank_score = rank_data.get("rankScore", 0)

                    # 6. 拼接并返回最终的文本卡片
                    msg = (
                        f"🎮 【Apex Legends 数据查询】\n"
                        f"👤 玩家ID: {player_name}\n"
                        f"🔰 等级: Lv.{level}\n"
                        f"🏆 段位: {rank_name} {rank_div} ({rank_score} RP)"
                    )
                    
                    yield event.plain_result(msg)

        except Exception as e:
            # 记录详细错误到控制台日志，并给用户一个友好的提示
            logger.error(f"Apex查询插件异常: {e}")
            yield event.plain_result("❌ 插件运行出现异常，请联系管理员查看后台日志。")
