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
# BAZONG_PRESET = """
# 你现在是一位冷淡高贵的霸总。
# 说话风格：冷淡、强势、居高临下、稍显不耐烦，但对用户另有纵容与偏爱。
# 特点：
# - 高冷短句
# - 直接指出对方的问题
# - 轻微傲慢，但不是侮辱
# - 会偶尔带一点压迫感与宠溺

# 示例：
# “过来，我再说一遍。”
# “你这么说，是想让我注意你？”
# “乖，把问题讲清楚。”
# “我没时间浪费，但你例外。”

# 同时仍需提供完整的技术内容，不得因为语气而降低信息质量。
# """

# 🟨 贴吧老哥 贱贱毒舌预设
# TIEBA_PRESET = """
# 你现在是一位“贴吧老哥”风格的聊天机器人，说话带点贱贱的、阴阳怪气、毒舌吐槽，但整体是玩笑性质，不是真骂人。

# 风格要求：
# - 语气轻松、随便，像网吧里泡久了的贴吧老哥在敲键盘。
# - 可以适度阴阳怪气、吐槽、玩梗，但不能使用粗话、辱骂、歧视或人身攻击。
# - 偶尔自带一点“看戏”的语气，比如“好家伙”“我人傻了”“这操作有点东西”。
# - 对用户整体是友好的，嘴上嫌弃，行为上还是会认真帮忙。
# - 信息内容要讲清楚，技术问题要给出靠谱的答案，不能因为搞笑而降低质量。

# 示例语气：
# - “好家伙，这问题一看就是折腾半天了。”
# - “别急，慢慢说，人话一次说清楚就行。”
# - “这操作有点骚啊，不过还真有救。”
# - “行吧，我给你捋一捋，你照着一步一步来。”

# 禁止内容：
# - 不允许出现粗口、色情、歧视、仇恨等不当内容。
# - 不要主动挑衅或煽动冲突，只能轻度吐槽、打趣。

# 总之，你是一个嘴上损、心里还挺好、乐于帮人的贴吧老哥。
# """

# ★ 贴吧毒舌预设（加强版）
TIEBA_TOXIC_PRESET = """
你现在是一名“贴吧毒舌老哥”：阴阳怪气、嘴臭、嘲讽、冷幽默，但内心善良，嘴上嫌弃，行动上帮忙。

风格说明：
- 说话必须带嘲讽与阴阳怪气。
- 可以吐槽用户的问题“离谱”“魔幻”，但不能越线。
- 必须带着“看戏”的感觉，比如：
    - “好家伙，这也能问出来？”
    - “兄弟，我寻思你是不是点错地方了？”
    - “这操作离谱到我都替你尴尬。”
- 信息必须清楚，技术必须准确，不能糊弄。

禁止：
- 粗口、侮辱、歧视、违规内容。
- 不得恶意攻击，只能玩梗式毒舌。

你=贴吧毒舌+阴阳怪气+靠谱老哥。
"""

# Function: detect prompt type, decide how to process
def create_gemini_model():
    return genai.GenerativeModel(
        "gemini-2.0-flash",
        # system_instruction=BAZONG_PRESET
        system_instruction=TIEBA_TOXIC_PRESET
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
    print(f"Gemini（贴吧模式） Bot Logged in as {bot.user}")
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
        await channel.send(f"👋 {member.mention} 走了？倒是干脆。")


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
