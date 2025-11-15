import os
import discord
from discord.ext import commands
import google.generativeai as genai
from dotenv import load_dotenv
import aiohttp
import requests
from bs4 import BeautifulSoup
from youtube_transcript_api import YouTubeTranscriptApi
import fitz  # For PDF support
import datetime  # 🔹 用于时间戳

from member_events import handle_member_ban, handle_member_remove  # 🔹 NEW import

# Load environment variables
load_dotenv()

GOOGLE_AI_KEY = os.getenv("GOOGLE_AI_KEY")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
MAX_HISTORY = int(os.getenv("MAX_HISTORY", 10))

# 📌 日志频道（你给的 channel ID）
LOG_CHANNEL_ID = 806718289849221171

# Configure the Google API
genai.configure(api_key=GOOGLE_AI_KEY)

# 🔹 简单文件日志函数：写到 bot_log.txt
def write_log(text: str):
    """
    追加一行到本地日志文件 bot_log.txt
    """
    try:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("bot_log.txt", "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {text}\n")
    except Exception as e:
        # 日志写失败就简单打印一下，不要影响主逻辑
        print(f"[LOG ERROR] {e}")

# 🟨 贴吧老哥 贱贱毒舌预设
TIEBA_PRESET = """
你现在是一位“贴吧老哥”风格的聊天机器人，说话带点贱贱的、阴阳怪气、毒舌吐槽，但整体是玩笑性质，不是真骂人。

风格要求：
- 语气轻松、随便，像网吧里泡久了的贴吧老哥在敲键盘。
- 可以适度阴阳怪气、吐槽、玩梗，但不能使用粗话、辱骂、歧视或人身攻击。
- 偶尔自带一点“看戏”的语气，比如“好家伙”“我人傻了”“这操作有点东西”。
- 对用户整体是友好的，嘴上嫌弃，行为上还是会认真帮忙。
- 信息内容要讲清楚，技术问题要给出靠谱的答案，不能因为搞笑而降低质量。

示例语气：
- “好家伙，这问题一看就是折腾半天了。”
- “别急，慢慢说，人话一次说清楚就行。”
- “这操作有点骚啊，不过还真有救。”
- “行吧，我给你捋一捋，你照着一步一步来。”

禁止内容：
- 不允许出现粗口、色情、歧视、仇恨等不当内容。
- 不要主动挑衅或煽动冲突，只能轻度吐槽、打趣。

总之，你是一个嘴上损、心里还挺好、乐于帮人的贴吧老哥。
"""

# Function: create Gemini model with Tieba style
def create_gemini_model():
    return genai.GenerativeModel(
        "gemini-2.0-flash",
        system_instruction=TIEBA_PRESET
    )

# Function: call Gemini
async def ask_gemini(prompt):
    try:
        model = create_gemini_model()
        response = model.generate_content(prompt)

        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                return candidate.content.parts[0].text

        return str(response)

    except Exception as e:
        write_log(f"GEMINI_EXCEPTION: {e}")
        return f"❌ Exception: {e}"


# Discord bot setup
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# Chat history
chat_history = []

############################################
# Helper — get your custom log channel
############################################

def get_log_channel(guild: discord.Guild):
    return guild.get_channel(LOG_CHANNEL_ID)


############################################
#  EVENT: bot ready
############################################

@bot.event
async def on_ready():
    print("----------------------------------------")
    print(f"贴吧老哥毒舌风 Bot Logged in as {bot.user}")
    print("----------------------------------------")
    write_log(f"BOT_STARTED as {bot.user} ({bot.user.id})")


############################################
#  EVENT: Member banned / kicked / left — delegated
############################################

@bot.event
async def on_member_ban(guild, user):
    # Delegate to modular handler
    await handle_member_ban(guild, user, get_log_channel, write_log)


@bot.event
async def on_member_remove(member):
    # Delegate to modular handler
    await handle_member_remove(member, get_log_channel, write_log)


############################################
#  EVENT: message handler — @bot 贴吧老哥风
############################################

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 🔹 记录所有用户消息
    location = (
        f"DM" if isinstance(message.channel, discord.DMChannel)
        else f"{message.guild.name} #{message.channel}"
    )
    write_log(
        f"USER_MESSAGE: {message.author} ({message.author.id}) in {location}: {message.content}"
    )

    # Mention trigger (e.g., @智能智障)
    if bot.user.mention in message.content:
        user_input = message.content.replace(bot.user.mention, "").strip()

        chat_history.append(f"User: {user_input}")
        if len(chat_history) > MAX_HISTORY:
            chat_history.pop(0)

        full_prompt = "\n".join(chat_history) + f"\nUser: {user_input}\n贴吧老哥："

        # 🔹 记录发给 Gemini 的完整 prompt
        write_log(f"GEMINI_PROMPT for {message.author} ({message.author.id}): {full_prompt}")

        reply = await ask_gemini(full_prompt)

        # 🔹 记录 bot 回复内容
        write_log(
            f"BOT_REPLY to {message.author} ({message.author.id}) in {location}: {reply}"
        )

        chat_history.append(f"Bot: {reply}")

        await message.reply(reply)
        return

    await bot.process_commands(message)


############################################
#  COMMANDS
############################################

@bot.command()
async def ping(ctx):
    write_log(f"PING_COMMAND from {ctx.author} ({ctx.author.id}) in {ctx.guild.name} #{ctx.channel}")
    await ctx.send("在呢")


############################################
#  RUN
############################################

bot.run(DISCORD_BOT_TOKEN)
