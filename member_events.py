# member_events.py
import discord
from discord import AuditLogAction
import discord.utils


def format_dt(dt: discord.utils.snowflake_time) -> str:
    """把 Discord 的 datetime 格式化成简单可读的字符串。"""
    if dt is None:
        return "未知"
    # Discord 一般是 UTC 时间
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


async def handle_member_ban(
    guild: discord.Guild,
    user: discord.abc.User,
    get_log_channel,
    write_log,
):
    """
    Handle member ban events.
    Sends an embed using the member's avatar (no external images).
    """

    try:
        write_log(
            f"[EVENT] on_member_ban fired for {user} ({user.id}) in guild {guild.name} ({guild.id})"
        )
    except Exception:
        pass

    channel = get_log_channel(guild)
    if not channel:
        try:
            write_log(
                f"[WARN] on_member_ban: LOG_CHANNEL not found in guild {guild.id}"
            )
        except Exception:
            pass
        return

    # 原本的 ban 文案（不改）
    msg = f"🚫 {user.mention} 被此群拉黑了！好家伙，这是没看群规则吗？溜了溜了。"

    # 获取成员信息（可能缓存中还在）
    member = guild.get_member(user.id)
    if member:
        display_name = member.display_name
        avatar_url = member.display_avatar.url
        big_avatar_url = member.display_avatar.replace(size=1024).url
        joined_str = format_dt(member.joined_at)
    else:
        display_name = user.name
        avatar_url = user.display_avatar.url
        big_avatar_url = user.display_avatar.replace(size=1024).url
        joined_str = "未知"

    created_str = format_dt(user.created_at)

    # Embed
    description = (
        f"{msg}\n\n"
        f"频道昵称：**{display_name}**\n"
        f"账号创建时间：`{created_str}`\n"
        f"加入本服务器时间：`{joined_str}`"
    )

    embed = discord.Embed(
        title="🚫 成员被拉黑",
        description=description,
        color=0xE74C3C,
        timestamp=discord.utils.utcnow(),
    )

    # 服务器信息
    if guild.icon:
        embed.set_author(name=guild.name, icon_url=guild.icon.url)
    else:
        embed.set_author(name=guild.name)

    # 小头像（右边缩略图）
    embed.set_thumbnail(url=avatar_url)

    # 大头像作为主要图像
    embed.set_image(url=big_avatar_url)

    embed.set_footer(text="回收站监控日志 · BAN 记录")

    try:
        await channel.send(embed=embed)
        try:
            write_log(f"[OK] BAN embed sent for {user.id} in channel {channel.id}")
        except Exception:
            pass
    except Exception as e:
        try:
            write_log(f"[ERROR] Failed to send BAN embed: {e}")
        except Exception:
            print(e)


async def handle_member_remove(
    member: discord.Member,
    get_log_channel,
    write_log,
):
    """
    KICK / LEAVE embeds using member avatar.
    """

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
            write_log(
                f"[WARN] on_member_remove: LOG_CHANNEL not found in guild {guild.id}"
            )
        except Exception:
            pass
        return

    kicked = False
    banned = False
    moderator = None

    # 检查 audit log
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
            write_log(f"[ERROR] AUDIT_LOG_ERROR: {e}")
        except Exception:
            print(e)

    # ban 会触发 remove，不再二次发送
    if banned:
        try:
            write_log(
                f"[INFO] handle_member_remove: {member.id} left due to BAN"
            )
        except Exception:
            pass
        return

    # 成员昵称与头像
    display_name = member.display_name
    avatar_url = member.display_avatar.url
    big_avatar_url = member.display_avatar.replace(size=1024).url
    created_str = format_dt(member.created_at)
    joined_str = format_dt(member.joined_at)

    # ===== Kick Embed =====
    if kicked:
        if moderator:
            msg = (
                f"👢 {member.mention} 不守群规则。管理员 {moderator.mention} 把他踢出群聊了。"
            )
        else:
            msg = (
                f"👢 {member.mention} 不守群规则，管理员把他踢出去了。"
            )

        description = (
            f"{msg}\n\n"
            f"频道昵称：**{display_name}**\n"
            f"账号创建时间：`{created_str}`\n"
            f"加入本服务器时间：`{joined_str}`"
        )

        embed = discord.Embed(
            title="👢 成员被踢出",
            description=description,
            color=0xF39C12,
            timestamp=discord.utils.utcnow(),
        )

        if guild.icon:
            embed.set_author(name=guild.name, icon_url=guild.icon.url)
        else:
            embed.set_author(name=guild.name)

        embed.set_thumbnail(url=avatar_url)
        embed.set_image(url=big_avatar_url)
        embed.set_footer(text="回收站监控日志 · KICK 记录")

        try:
            await channel.send(embed=embed)
            try:
                write_log(
                    f"[OK] KICK embed sent for {member.id} in channel {channel.id}"
                )
            except Exception:
                pass
        except Exception as e:
            try:
                write_log(f"[ERROR] Failed to send KICK embed: {e}")
            except Exception:
                print(e)

        return

    # ===== Leave Embed =====
    # 原文案不改
    msg = f"👋 {member.mention} 哦豁，这位成员受不了这个群聊，连夜卷铺盖溜了。"

    description = (
        f"{msg}\n\n"
        f"频道昵称：**{display_name}**\n"
        f"账号创建时间：`{created_str}`\n"
        f"加入本服务器时间：`{joined_str}`"
    )

    embed = discord.Embed(
        title="🛫 成员离开",
        description=description,
        color=0x3498DB,
        timestamp=discord.utils.utcnow(),
    )

    if guild.icon:
        embed.set_author(name=guild.name, icon_url=guild.icon.url)
    else:
        embed.set_author(name=guild.name)

    embed.set_thumbnail(url=avatar_url)
    embed.set_image(url=big_avatar_url)
    embed.set_footer(text="回收站监控日志 · LEAVE 记录")

    try:
        await channel.send(embed=embed)
        try:
            write_log(
                f"[OK] LEAVE embed sent for {member.id} in channel {channel.id}"
            )
        except Exception:
            pass
    except Exception as e:
        try:
            write_log(f"[ERROR] Failed to send LEAVE embed: {e}")
        except Exception:
            print(e)
