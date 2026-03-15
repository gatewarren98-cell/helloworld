import aiohttp
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.api.message_components import Image

# ！！请务必在此处填入你申请的 ALS API Key ！！
ALS_API_KEY = "b7bc7443be72109d3c31e3fc85d3183f"

@register("apex_query", "开发者", "Apex全功能极速查询插件", "1.1.0")
class ApexQueryPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    # ==========================
    # 1. 玩家数据查询
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
                    
                    level = global_data.get("level", "未知")
                    rank_name = rank_data.get("rankName", "未知")
                    rank_div = rank_data.get("rankDiv", "")
                    rank_score = rank_data.get("rankScore", 0)
                    legend_name = global_data.get("legend", "未知")

            msg = (
                f"🎮 𝗔𝗣𝗘𝗫 𝗟𝗘𝗚𝗘𝗡𝗗𝗦 𝗦𝗧𝗔𝗧𝗦\n"
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
    # 2. 地图轮换查询
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

                    pubs_current = pubs.get("current", {}).get("map", "未知")
                    pubs_timer = pubs.get("current", {}).get("remainingTimer", "未知")
                    pubs_next = pubs.get("next", {}).get("map", "未知")
                    pubs_img = pubs.get("current", {}).get("asset", "")

                    ranked_current = ranked.get("current", {}).get("map", "未知")
                    ranked_timer = ranked.get("current", {}).get("remainingTimer", "未知")
                    ranked_next = ranked.get("next", {}).get("map", "未知")

            msg = (
                f"🗺️ 𝗔𝗣𝗘𝗫 地图轮换\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🗡️ 【匹配模式】\n"
                f"➤ 当前: {pubs_current} ({pubs_timer})\n"
                f"➤ 下局: {pubs_next}\n\n"
                f"🏆 【排位赛】\n"
                f"➤ 当前: {ranked_current} ({ranked_timer})\n"
                f"➤ 下局: {ranked_next}\n"
                f"━━━━━━━━━━━━━━━"
            )

            res = event.make_result().message(msg)
            if pubs_img:
                res.chain.append(Image.fromURL(pubs_img))
            yield res
        except Exception as e:
            logger.error(f"地图查询异常: {e}")
            yield event.plain_result("❌ 地图获取异常，请检查后台日志。")

    # ==========================
    # 3. 猎杀者分数线查询 (Predator)
    # ==========================
    @filter.command("apex猎杀")
    async def query_apex_predator(self, event: AstrMessageEvent):
        url = f"https://api.mozambiquehe.re/predator?auth={ALS_API_KEY}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=False) as response:
                    data = await response.json()
                    if "Error" in data:
                        yield event.plain_result(f"❌ 查询失败：{data['Error']}")
                        return

                    pc = data.get("RP", {}).get("PC", {})
                    ps4 = data.get("RP", {}).get("PS4", {})

            msg = (
                f"👹 𝗔𝗣𝗘𝗫 猎杀者底分线\n"
                f"━━━━━━━━━━━━━━━\n"
                f"💻 【PC / Steam 端】\n"
                f"➤ 门槛分: {pc.get('val', '未知')} RP\n"
                f"➤ 大师人数: {pc.get('totalMastersAndPreds', '未知')} 人\n\n"
                f"🎮 【PS / Xbox 端】\n"
                f"➤ 门槛分: {ps4.get('val', '未知')} RP\n"
                f"➤ 大师人数: {ps4.get('totalMastersAndPreds', '未知')} 人\n"
                f"━━━━━━━━━━━━━━━"
            )
            yield event.plain_result(msg)
        except Exception as e:
            logger.error(f"猎杀查询异常: {e}")
            yield event.plain_result("❌ 数据获取异常，请检查后台日志。")

    # ==========================
    # 4. 游戏商店速览 (Store)
    # ==========================
    @filter.command("apex商店")
    async def query_apex_store(self, event: AstrMessageEvent):
        url = f"https://api.mozambiquehe.re/store?auth={ALS_API_KEY}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=False) as response:
                    data = await response.json()
                    if "Error" in data:
                        yield event.plain_result(f"❌ 查询失败：{data['Error']}")
                        return

            # 商店物品很多，为了防止刷屏，我们只取前 3 个捆绑包
            msg = f"🛒 𝗔𝗣𝗘𝗫 当前商店精选\n━━━━━━━━━━━━━━━\n"
            top_items = data[:3]
            img_url = ""

            for i, item in enumerate(top_items):
                title = item.get("title", "未知物品")
                price = item.get("pricing", [{}])[0].get("quantity", "未知价格")
                msg += f"📦 {title} - 💰 {price} 金币\n"
                if i == 0:
                    img_url = item.get("asset", "") # 抓取第一个物品的图片

            msg += f"━━━━━━━━━━━━━━━\n(仅展示前3件商品)"
            
            res = event.make_result().message(msg)
            if img_url:
                res.chain.append(Image.fromURL(img_url))
            yield res
        except Exception as e:
            logger.error(f"商店查询异常: {e}")
            yield event.plain_result("❌ 数据获取异常，请检查后台日志。")

    # ==========================
    # 5. 最新官方新闻 (News)
    # ==========================
    @filter.command("apex新闻")
    async def query_apex_news(self, event: AstrMessageEvent):
        url = f"https://api.mozambiquehe.re/news?auth={ALS_API_KEY}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=False) as response:
                    data = await response.json()
                    if "Error" in data:
                        yield event.plain_result(f"❌ 查询失败：{data['Error']}")
                        return

            msg = f"📰 𝗔𝗣𝗘𝗫 官方最新资讯\n━━━━━━━━━━━━━━━\n"
            # 取最新的 2 条新闻
            top_news = data[:2]
            img_url = ""

            for i, news in enumerate(top_news):
                title = news.get("title", "无标题")
                link = news.get("link", "")
                msg += f"🔹 {title}\n🔗 链接: {link}\n\n"
                if i == 0:
                    img_url = news.get("img", "")

            msg += f"━━━━━━━━━━━━━━━"
            
            res = event.make_result().message(msg)
            if img_url:
                res.chain.append(Image.fromURL(img_url))
            yield res
        except Exception as e:
            logger.error(f"新闻查询异常: {e}")
            yield event.plain_result("❌ 数据获取异常，请检查后台日志。")

    # ==========================
    # 6. EA 服务器状态 (Servers)
    # ==========================
    @filter.command("apex服务器")
    async def query_apex_servers(self, event: AstrMessageEvent):
        url = f"https://api.mozambiquehe.re/servers?auth={ALS_API_KEY}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=False) as response:
                    data = await response.json()
                    if "Error" in data:
                        yield event.plain_result(f"❌ 查询失败：{data['Error']}")
                        return

            # 辅助函数：只要该服务有一个地区 DOWN，就判定为异常
            def get_status(service_data):
                for region, info in service_data.items():
                    if info.get("Status") != "UP":
                        return "🔴 异常 (DOWN)"
                return "🟢 运行正常"

            ea_acc = get_status(data.get("EA_accounts", {}))
            ea_nova = get_status(data.get("EA_novafusion", {}))
            crossplay = get_status(data.get("ApexOauth_Crossplay", {}))

            msg = (
                f"📡 𝗘𝗔 服务器实时状态\n"
                f"━━━━━━━━━━━━━━━\n"
                f"🖥️ EA 账号服务: {ea_acc}\n"
                f"🎮 核心匹配服务: {ea_nova}\n"
                f"🔄 跨平台认证: {crossplay}\n"
                f"━━━━━━━━━━━━━━━\n"
                f"💡 如果核心异常，大概率会遇到卡大厅、无法匹配或无限转圈。"
            )
            yield event.plain_result(msg)
        except Exception as e:
            logger.error(f"服务器查询异常: {e}")
            yield event.plain_result("❌ 数据获取异常，请检查后台日志。")

    # ==========================
    # 7. 玩家战绩历史 (Match History)
    # ==========================
    @filter.command("apex历史")
    async def query_apex_history(self, event: AstrMessageEvent, player_name: str = ""):
        if not player_name:
            yield event.plain_result("❌ 请输入玩家ID，例如：/apex历史 ItzTimmy")
            return
            
        url = f"https://api.mozambiquehe.re/games?auth={ALS_API_KEY}&player={player_name}&platform=PC"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, ssl=False) as response:
                    # 返回的是一个列表
                    data = await response.json()
                    
                    # 拦截特殊的错误返回格式
                    if isinstance(data, dict) and "Error" in data:
                        yield event.plain_result(f"❌ 查询失败：{data['Error']}")
                        return
                        
                    if not data or len(data) == 0:
                        yield event.plain_result(f"⚠️ 未找到 {player_name} 的近期比赛记录。\n(注: 玩家需在游戏中打开 ALS Tracker 才能被记录)")
                        return

            msg = f"⚔️ {player_name} 的近期战绩\n━━━━━━━━━━━━━━━\n"
            # 提取最近的 3 场比赛
            top_matches = data[:3]
            
            for match in top_matches:
                legend = match.get("legendPlayed", "未知")
                mode = match.get("mode", "未知模式")
                br_score_change = match.get("brScoreChange", 0) # 排位分数变化
                
                # 判定分数增减
                rp_text = f"RP: +{br_score_change}" if br_score_change > 0 else f"RP: {br_score_change}"
                if br_score_change == 0:
                    rp_text = "(匹配或未变动)"
                
                msg += f"🦸 {legend} | 🕹️ {mode}\n📊 {rp_text}\n---\n"
                
            msg += f"💡 战绩数据由 ALS 实时网络提供。"
            yield event.plain_result(msg)

        except Exception as e:
            logger.error(f"历史记录查询异常: {e}")
            yield event.plain_result("❌ 数据获取异常，请检查后台日志。")
