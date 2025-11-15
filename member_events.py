# member_events.py
import discord
from discord import AuditLogAction
import discord.utils


def format_dt(dt):
    if dt is None:
        return "未知"
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def days_in_server(joined_at):
    if joined_at is None:
        return "未知"
    now = discord.utils.utcnow()
    delta = now - joined_at
    return f"{delta.days} 天"


# 固定大图
BAN_BIG_IMAGE = "https://i.imgflip.com/44yl6z.jpg"
KICK_BIG_IMAGE = "https://pic2.zhimg.com/v2-c446dd39e3b7a7c3bde56560daf1291f_r.jpg"
LEAVE_BIG_IMAGE = "https://i.imgur.com/l1DM8Wo.jpg"


async def handle_member_ban(guild, user, get_log_channel, write_log):

    try:
        write_log(f"[EVENT] on_member_ban fired for {user} ({user.id}) in guild {guild.name} ({guild.id})")
    except Exception:
        pass

    channel = get_log_channel(guild)
    if not channel:
        try:
            write_log(f"[WARN] on_member_ban: No LOG_CHANNEL for guild {guild.id}")
        except Exception:
            pass
        return

    # 查操作管理员
    moderator = None
    try:
        now = discord.utils.utcnow()
        async for entry in guild.audit_logs(limit=6, action=AuditLogAction.ban):
            if entry.target.id != user.id:
                continue
            if (now - entry.created_at).total_seconds() > 10:
                continue
            moderator = entry.user
            break
    except Exception as e:
        try:
            write_log(f"[ERROR] BAN AUDIT_LOG: {e}")
        except Exception:
            print(e)

    # 文案（保留你原来的）
    msg = f"🚫 {user.mention} 被此群拉黑了！好家伙，这是没看群规则吗？溜了溜了。"

    # 获取成员信息
    member = guild.get_member(user.id)
    if member:
        display_name = member.display_name
        avatar_url = member.display_avatar.url
        joined_str = format_dt(member.joined_at)
        stay_days = days_in_server(member.joined_at)
    else:
        display_name = user.name
        avatar_url = user.display_avatar.url
        joined_str = "未知"
        stay_days = "未知"

    created_str = format_dt(user.created_at)

    description = (
        f"{msg}\n\n"
        f"频道昵称：**{display_name}**\n"
        f"账号创建时间：`{created_str}`\n"
        f"加入本服务器时间：`{joined_str}`\n"
        f"驻站时长：`{stay_days}`"
    )

    embed = discord.Embed(
        title="🚫 震惊：一位太空人被本群拉黑！",
        description=description,
        color=0xE74C3C,  # 红色
        timestamp=discord.utils.utcnow(),
    )

    if guild.icon:
        embed.set_author(name=guild.name, icon_url=guild.icon.url)
    else:
        embed.set_author(name=guild.name)

    embed.set_thumbnail(url=avatar_url)
    embed.set_image(url=BAN_BIG_IMAGE)

    footer = "回收站监控日志 · BAN 记录"
    if moderator:
        footer += f" · 操作管理员：{moderator.display_name}"
    embed.set_footer(text=footer)

    try:
        await channel.send(embed=embed)
    except Exception as e:
        try:
            write_log(f"[ERROR] BAN embed send failed: {e}")
        except Exception:
            print(e)


async def handle_member_remove(member, get_log_channel, write_log):

    guild = member.guild

    try:
        write_log(
            f"[EVENT] on_member_remove fired for {member} ({member.id}) in guild {guild.name} ({guild.id})"
        )
    except Exception:
        pass

    channel = get_log_channel(guild)
    if not channel:
        try:
            write_log(f"[WARN] on_member_remove: No LOG_CHANNEL for guild {guild.id}")
        except Exception:
            pass
        return

    kicked = False
    banned = False
    moderator = None

    # 查审计日志
    try:
        now = discord.utils.utcnow()
        async for entry in guild.audit_logs(limit=6):
            if entry.target.id != member.id:
                continue
            if (now - entry.created_at).total_seconds() > 10:
                continue
            if entry.action == AuditLogAction.kick:
                kicked = True
                moderator = entry.user
                break
            elif entry.action == AuditLogAction.ban:
                banned = True
                moderator = entry.user
                break
    except Exception as e:
        try:
            write_log(f"[ERROR] AUDIT_LOG: {e}")
        except Exception:
            print(e)

    # ban 导致的 remove 不处理，由 handle_member_ban 负责
    if banned:
        try:
            write_log(f"[INFO] handle_member_remove: {member.id} left due to BAN")
        except Exception:
            pass
        return

    # 成员信息
    display_name = member.display_name
    avatar_url = member.display_avatar.url
    created_str = format_dt(member.created_at)
    joined_str = format_dt(member.joined_at)
    stay_days_str = days_in_server(member.joined_at)

    # 计算驻站天数整数，用来生成吐槽
    if member.joined_at is not None:
        now = discord.utils.utcnow()
        stay_days_int = (now - member.joined_at).days
    else:
        stay_days_int = None

    # ===== Kick =====
    if kicked:
        if moderator:
            msg = f"👢 {member.mention} 不守群规则。管理员 {moderator.mention} 把他踢出群聊了。"
        else:
            msg = f"👢 {member.mention} 不守群规则，管理员把他踢出去了。"

        description = (
            f"{msg}\n\n"
            f"频道昵称：**{display_name}**\n"
            f"账号创建时间：`{created_str}`\n"
            f"加入本服务器时间：`{joined_str}`\n"
            f"驻站时长：`{stay_days_str}`"
        )

        embed = discord.Embed(
            title="👢 一位太空人不知道犯了什么错被踢出",
            description=description,
            color=0xF39C12,  # 黄色
            timestamp=discord.utils.utcnow(),
        )

        if guild.icon:
            embed.set_author(name=guild.name, icon_url=guild.icon.url)
        else:
            embed.set_author(name=guild.name)

        embed.set_thumbnail(url=avatar_url)
        embed.set_image(url=KICK_BIG_IMAGE)

        footer = "回收站监控日志 · KICK 记录"
        if moderator:
            footer += f" · 操作管理员：{moderator.display_name}"
        embed.set_footer(text=footer)

        try:
            await channel.send(embed=embed)
        except Exception as e:
            try:
                write_log(f"[ERROR] send KICK embed: {e}")
            except Exception:
                print(e)

        return

    # ===== Leave =====
    msg = f"👋 {member.mention} 哦豁，这位成员受不了这个群聊，连夜卷铺盖溜了。"

    # 根据驻站天数生成 贴吧老哥风 吐槽
    if stay_days_int is None:
        leave_comment = "来去无踪，连系统都搞不清楚你在这儿待了多久。"
    elif stay_days_int < 1:
        leave_comment = "这都没待满一天，进门看一眼就闪人了，属于路过打卡型。"
    elif stay_days_int < 7:
        leave_comment = "不到一周就跑路，估计是被这里的画风吓到了。"
    elif stay_days_int < 30:
        leave_comment = "混了几周就溜了，典型短期旅客，缘分浅浅。"
    elif stay_days_int < 180:
        leave_comment = "好歹也是老熟人了，说走就走，这洒脱劲儿我服了。"
    else:
        leave_comment = "资深废品都选择退站了，时代确实变了。"

    description = (
        f"{msg}\n\n"
        f"频道昵称：**{display_name}**\n"
        f"账号创建时间：`{created_str}`\n"
        f"加入本服务器时间：`{joined_str}`\n"
        f"驻站时长：`{stay_days_str}`\n"
        f"吐槽：{leave_comment}"
    )

    embed = discord.Embed(
        title="🛫 一位太空人连夜卷铺盖跑路",
        description=description,
        color=0x588BA8,  # 群主题色
        timestamp=discord.utils.utcnow(),
    )

    if guild.icon:
        embed.set_author(name=guild.name, icon_url=guild.icon.url)
    else:
        embed.set_author(name=guild.name)

    embed.set_thumbnail(url=avatar_url)
    embed.set_image(url=LEAVE_BIG_IMAGE)
    embed.set_footer(text="回收站监控日志 · LEAVE 记录")

    try:
        await channel.send(embed=embed)
    except Exception as e:
        try:
            write_log(f"[ERROR] send LEAVE embed: {e}")
        except Exception:
            print(e)
