import asyncio
import tomllib
from random import choice

from WechatAPI import WechatAPIClient
from database.XYBotDB import XYBotDB
from utils.decorators import *
from utils.plugin_base import PluginBase


class Leaderboard(PluginBase):
    description = "积分榜"
    author = "HenryXiaoYang"
    version = "1.0.0"

    def __init__(self):
        super().__init__()

        with open("plugins/Leaderboard/config.toml", "rb") as f:
            plugin_config = tomllib.load(f)

        config = plugin_config["Leaderboard"]

        self.enable = config["enable"]
        self.command = config["command"]
        self.max_count = config["max-count"]

        self.db = XYBotDB()

    @on_text_message
    async def handle_text(self, bot: WechatAPIClient, message: dict):
        if not self.enable:
            return

        content = str(message["Content"]).strip()
        command = content.split(" ")

        if command[0] not in self.command:
            return

        if "群" in command[0]:
            chatroom_members = await bot.get_chatroom_member_list(message["FromWxid"])
            data = []
            for member in chatroom_members:
                wxid = member["UserName"]
                points = self.db.get_points(wxid)
                if points == 0:
                    continue
                data.append((member["NickName"], points))

            data.sort(key=lambda x: x[1], reverse=True)
            data = data[:self.max_count]

            out_message = "-----WeBot积分群排行榜-----"
            rank_emojis = ["👑", "🥈", "🥉"]
            for rank, (nickname, points) in enumerate(data, start=1):
                emoji = rank_emojis[rank - 1] if rank <= 3 else ""
                random_emoji = choice(
                    ["😄", "😃", "😁", "😆", "😊", "😍", "😋", "😎", "🤗", "😺", "🥳", "🤩", "🎉", "⭐", "🎊", "🎈", "🌟", "✨", "🎶",
                     "❤️", "😛"])
                out_message += f"\n{emoji}{'' if emoji else str(rank) + '.'} {nickname}   {points}分  {random_emoji}"

        else:
            data = self.db.get_leaderboard(self.max_count)

            wxids = [i[0] for i in data]
            nicknames = []

            async def get_nicknames_chunk(chunk_wxids):
                return await bot.get_nickname(chunk_wxids)

            # 将wxids分成每组20个
            chunks = [wxids[i:i + 20] for i in range(0, len(wxids), 20)]
            # 使用信号量限制并发数为2
            sem = asyncio.Semaphore(2)

            async def worker(chunk):
                async with sem:
                    return await get_nicknames_chunk(chunk)

            # 并发执行所有请求
            tasks = [worker(chunk) for chunk in chunks]
            results = await asyncio.gather(*tasks)

            # 将所有结果合并到nicknames列表中
            for result in results:
                nicknames.extend(result)

            out_message = "-----WeBot积分排行榜-----"
            rank_emojis = ["👑", "🥈", "🥉"]
            for rank, (i, nickname) in enumerate(zip(data, nicknames), start=1):
                wxid, points = i
                nickname = nickname or wxid
                emoji = rank_emojis[rank - 1] if rank <= 3 else ""
                random_emoji = choice(
                    ["😄", "😃", "😁", "😆", "😊", "😍", "😋", "😎", "🤗", "😺", "🥳", "🤩", "🎉", "⭐", "🎊", "🎈", "🌟", "✨", "🎶",
                     "❤️", "😛"])
                out_message += f"\n{emoji}{'' if emoji else str(rank) + '.'} {nickname}   {points}分  {random_emoji}"

        await bot.send_text_message(message["FromWxid"], out_message)
