import time
from private.secrets import BOT_ID, DISCORD_BOT_TOKEN, VC_CHANNEL_DICT, EGOSA_LIST
from ai.ai_client import AIClient
from ai.ai_client_provider import get_ai_client
from logging import getLogger, INFO, DEBUG
from urlextract import URLExtract
import logging
import discord
import random
import json
import sys


class ReplyTimer:
    
    def __init__(self):
        self.a1 = None
        self.a2 = None

    def get_before_time(self):
        return self.a1
    
    def is_replyable(self, limit=20):
        self.a2 = time.time()
        if self.a1 is None:
            self.a1 = self.a2
            return True
        delta = self.a2 - self.a1
        self.a1 = self.a2
        if delta > limit:
            return True
        return False

# ロガーの設定
logging.basicConfig(level=INFO)

logger = getLogger(__name__)
logger.setLevel(DEBUG)


intents = discord.Intents.default()
intents.message_content = True
discord_client = discord.Client(intents=intents)

ai_client: AIClient = None
url_extractor = URLExtract()
egosa_timer = ReplyTimer()
normal_reply_timer = ReplyTimer()

@discord_client.event
async def on_ready():
    logger.info(f"{discord_client.user} has connected to Discord!")
    if sys.argv[1] == "crawl":
        # sys.argv[1] ってここでも読めるのか？未テスト
        await crawl()


@discord_client.event
async def on_message(message):
    # 返事をしない場合は何もしない
    rate: int = VC_CHANNEL_DICT.get(str(message.channel.id), 0)
    if not _is_reply(message, rate):
        return

    # メンションであった場合、メンション文字列が混ざるのでこれは削除する
    chat_text: str = message.content.replace(ai_client.bot_id, "")

    # メッセージに画像が含まれる場合
    if len(message.attachments) > 0:
        # メンションでなければ無視
        if not discord_client.user in message.mentions:
            return
        content_type: str = message.attachments[0].content_type
        logger.info(f"{message.author} wants to send a message:")
        if content_type.startswith("image"):
            logger.info(f"{message.author} wants to send a message:")
            logger.info(f"{message.author} sent a image: {message.attachments[0].url}")
            logger.info(f"reply to {chat_text}")
            await message.channel.send(ai_client.generate_reply_to_including_image(chat_text))
            return
        else:
            # 画像以外は無視
            logger.info(f"{message.author} sent a {content_type}")
            return

    logger.info(f"{message.author} wants to send a message:")
    # メッセージにURLが含まれる場合
    urls: list[str] = url_extractor.find_urls(chat_text)
    if len(urls) > 0:
        # メンションでなければ無視
        if not discord_client.user in message.mentions:
            return
        logger.info(f"{message.author} sent a URL: {urls[0]}")
        for url in urls:
            chat_text = chat_text.replace(url, "")
        logger.info(f"reply to {chat_text}")
        await message.channel.send(ai_client.generate_reply_to_including_URL(chat_text))
        return

    # 返事をする
    
    logger.info(f"{message.author} wants to send a message:")
    reply = ai_client.generate_reply(chat_text, message.channel.id)
    logger.info(f"{message.author} sent a message: {chat_text}, response: {reply}")

    if len(reply) == 0:
        return
    
    await message.channel.send(reply)


# 返事をするか判断する
def _is_reply(message, rate: int = 40) -> bool:
    # 自分自身の投稿と、@everyoneへのメンションは無視する
    if (
        message.author == discord_client.user
        or message.mention_everyone
    ):
        return False

    # メンションには絶対に反応する
    if discord_client.user in message.mentions:
        return True

    # メンションであって、自分が含まれていない場合は無視する
    if len(message.mentions) > 0 and discord_client.user not in message.mentions:
        return False


    if ai_client.bot_id == BOT_ID['himari'] or ai_client.bot_id == BOT_ID['shiroko']:
        egosa_list = EGOSA_LIST['himari'] if ai_client.bot_id == BOT_ID['himari'] else EGOSA_LIST['shiroko'] # = ["himari", "himaranai"...]
        chat_text: str = message.content.replace(ai_client.bot_id, "")
        for eg in egosa_list:
            if chat_text.lower().find(eg) != -1:
                author = message.author # message may be changed before logging
                if not egosa_timer.is_replyable():
                    logger.info(f"{author} was not egosearched by {ai_client.bot_id}:")
                    logger.info(f"ignored naming: {eg}")
                    logger.info(f"ignored chat_text: {chat_text}")
                    break
                logger.info(f"{author} was successfully egosearched by {ai_client.bot_id}:")
                logger.info(f"naming: {eg}")
                logger.info(f"chat_text: {chat_text}")
                return True

    # 40% の確率で返事をする
    return random.randint(1, 100) < rate if normal_reply_timer.is_replyable(5) else False


# 全てのテキストチャンネルに投稿されたメッセージを収拾する
async def crawl():
    for channel in discord_client.get_all_channels():
        logger.info(f"Channel: {channel.name}")
        result: list[tuple[str, str]] = []
        if channel.type == discord.ChannelType.text:
            logger.info(f"TextChannel: {channel.name}")
            async for message in channel.history(limit=None):
                result.append((message.author.name, message.content))
            with open(f"./chat_log/{channel.name}.txt", "w") as f:
                json.dump(result, f, ensure_ascii=False)


def main():
    if len(sys.argv) <= 1:
        logger.info("no argument. you must specify 'crawl' or bot name.")
        return

    # 悲しいけど、ここでグローバル変数を書き換える
    global ai_client
    ai_client = get_ai_client(sys.argv[1])

    discord_client.run(DISCORD_BOT_TOKEN[sys.argv[1]])


if __name__ == "__main__":
    main()
