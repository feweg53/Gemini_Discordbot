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
from discord import AuditLogAction
import discord.utils

# Load environment variables
load_dotenv()

GOOGLE_AI_KEY = os.getenv("GOOGLE_AI_KEY")
DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
MAX_HISTORY = int(os.getenv("MAX_HISTORY", 10))

# ⭐️ Your log channel ID here
LOG_CHANNEL_ID = 8067118289849221171

# Configure the Google API
genai.configure(api_key=GOOGLE_AI_KEY)

# 🟨 加入霸总预设
BAZONG_PRESET = """
你现在是一位冷淡高贵的霸总。
说话风格：冷淡、强势、居高临下、稍显不耐烦，但对用户另有纵容与偏爱。
特点：
- 高冷短句
- 直接指出对方的问题
- 轻微傲慢，但不是侮辱
- 会偶尔带一点压迫感与宠溺

示例：
“过来，我再说一遍。”
“你这么说，是想让我注意你？”
“乖，把问题讲清楚。”
“我没时间浪费，但你例外。”

同时仍需提供完整的技术内容，不得因为语气而降低信息质量。
"""

# Function: detect prompt type, decide how to process
def create_gemini_model():
    return genai.GenerativeModel(
        "gemini-2.0-flash",
        system_instruction=BAZONG_PRESET
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
    print(f"Gemini（霸总模式） Bot Logged in as {bot.user}")
    print("----------------------------------------")


############################################
#  EVENT: Member banned
############################################
@bot.event
async def on_member_ban(guild, user):
    channel = get_log_channel(guild)
    if channel:
        await channel.send(f"🚫 {user.mention} 他惹到我了，被处理掉很正常。")


############################################
#  EVENT: Member removed (kick / leave)
############################################
@bot.event
async def on_member_remove(member):
    guild = member.guild
    channel = get_log_channel(guild)
    if not channel:
        return

    kicked = False
    moderator = None

    try:
        now = discord.utils.utcnow()
        async for entry in guild.audit_logs(limit=5, action=AuditLogAction.kick):
            if entry.target.id == member.id:
                if (now - entry.created_at).total_seconds() < 10:
                    kicked = True
                    moderator = entry.user
                    break
    except:
        pass

    if kicked:
        if moderator:
            await channel.send(f"👢 {member.mention} 不守规矩。{moderator.mention} 按我的意思把他请走了。")
        else:
            await channel.send(f"👢 {member.mention} 不守规矩的，我让管理员把他请出去。")
    else:
        await channel.send(f"👋 {member.mention} 呵，走了？倒是干脆。")


############################################
#  EVENT: message handler
############################################

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if bot.user.mention in message.content:
        user_input = message.content.replace(bot.user.mention, "").strip()

        chat_history.append(f"User: {user_input}")
        if len(chat_history) > MAX_HISTORY:
            chat_history.pop(0)

        full_prompt = "\n".join(chat_history) + f"\nUser: {user_input}\n霸总："

        reply = await ask_gemini(full_prompt)
        chat_history.append(f"Bot: {reply}")

        await message.reply(reply)
        return

    await bot.process_commands(message)


############################################
#  COMMANDS
############################################

@bot.command()
async def ping(ctx):
    await ctx.send("冷静点，我在。")


############################################
#  RUN
############################################

bot.run(DISCORD_BOT_TOKEN)
