import tomllib
import traceback

import aiohttp
from loguru import logger

from WechatAPI import WechatAPIClient
from utils.decorators import *
from utils.plugin_base import PluginBase


class RandomPicture(PluginBase):
    description = "随机图片"
    author = "HenryXiaoYang"
    version = "1.0.0"

    def __init__(self):
        super().__init__()

        with open("plugins/RandomPicture/config.toml", "rb") as f:
            plugin_config = tomllib.load(f)

        config = plugin_config["RandomPicture"]

        self.enable = config["enable"]
        self.group_list = config["group_list"]
        self.command = config["command"]
        self.command_hs = config["command_hs"]
        self.command_bs = config["command_bs"]
        self.command_mn = config["command_mn"]
        self.command_boy = config["command_boy"]
        self.url_command = config["url_command"]
        self.url_hs = config["url_hs"]
        self.url_bs = config["url_bs"]
        self.url_mn = config["url_mn"]
        self.url_boy = config["url_boy"]

    @on_text_message
    async def handle_text(self, bot: WechatAPIClient, message: dict):
        if not self.enable:
            return

        if message.get("FromWxid") not in self.group_list and message["IsGroup"]:
            return

        content = str(message["Content"]).strip()
        command = content.split(" ")

        if not len(command):
            return

        if command[0] in self.command:
            api_url = self.url_command
        elif command[0] in self.command_hs:
            api_url = self.url_hs
        elif command[0] in self.command_bs:
            api_url = self.url_bs
        elif command[0] in self.command_mn:
            api_url = self.url_mn
        elif command[0] in self.command_boy:
            api_url = self.url_boy
        else:
            return

        logger.info("api_url：{}", api_url)

        try:
            conn_ssl = aiohttp.TCPConnector(ssl=False)

            if "type=text" in api_url:
                async with aiohttp.request("GET", url=api_url, connector=conn_ssl) as req:
                    pic_url = await req.text()
            else:
                pic_url = api_url

            async with aiohttp.request("GET", url=pic_url, connector=conn_ssl) as req:
                content = await req.read()

            await conn_ssl.close()

            await bot.send_image_message(message["FromWxid"], image=content)

        except Exception as error:
            out_message = f"-----WeBot-----\n出现错误❌！\n{error}"
            logger.error(traceback.format_exc())

            await bot.send_text_message(message["FromWxid"], out_message)
