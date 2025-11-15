# member_events.py
import discord
from discord import AuditLogAction
import discord.utils

async def handle_member_ban(guild: discord.Guild,
                            user: discord.abc.User,
                            get_log_channel,
                            write_log):
    """
    Handle member ban events.
    - Sends a Tieba-laoge style ban message to the log channel.
    - Uses get_log_channel(guild) and write_log(text) from the main bot.
    """
    # Log event
    try:
        write_log(f"[EVENT] on_member_ban fired for {user} ({user.id}) in guild {guild.name} ({guild.id})")
    except Exception:
        pass

    channel = get_log_channel(guild)
    if not channel:
        try:
            write_log(f"[WARN] on_member_ban: LOG_CHANNEL not found in guild {guild.id}")
        except Exception:
            pass
        return

    msg = f"🚫 {user.mention} 好家伙，这是把管理员得罪干净了？溜了溜了。"

    try:
        await channel.send(msg)
        try:
            write_log(f"[OK] BAN message sent for {user.id} in channel {channel.id}")
        except Exception:
            pass
    except Exception as e:
        try:
            write_log(f"[ERROR] Failed to send BAN message in channel {channel.id}: {e}")
        except Exception:
            print(e)


async def handle_member_remove(member: discord.Member,
                               get_log_channel,
                               write_log):
    """
    Handle member remove events:
      - If recent audit log shows BAN  -> do nothing (on_member_ban already handles message)
      - If recent audit log shows KICK -> send kick message
      - Else -> treat as voluntary leave and send leave message
    """
    guild = member.guild

    try:
        write_log(f"[EVENT] on_member_remove fired for {member} ({member.id}) in guild {guild.name} ({guild.id})")
    except Exception:
        pass

    channel = get_log_channel(guild)
    if not channel:
        try:
            write_log(f"[WARN] on_member_remove: LOG_CHANNEL not found in guild {guild.id}")
        except Exception:
            pass
        return

    kicked = False
    banned = False
    moderator = None

    # Look at recent audit log entries for this member
    try:
        now = discord.utils.utcnow()

        # Check last few actions (ban & kick)
        async for entry in guild.audit_logs(limit=6):
            # Only care about this member
            if entry.target.id != member.id:
                continue

            # Only consider very recent actions (e.g., within 10 seconds)
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
            write_log(f"[ERROR] AUDIT_LOG_ERROR in handle_member_remove: {e}")
        except Exception:
            print(f"AUDIT_LOG_ERROR in handle_member_remove: {e}")

    # If banned: do not send leave/kick message – on_member_ban already handles it
    if banned:
        try:
            write_log(
                f"[INFO] handle_member_remove: {member.id} left due to BAN, no leave message sent."
            )
        except Exception:
            pass
        return

    # If kicked: send kick message
    if kicked:
        try:
            if moderator:
                msg = (
                    f"👢 {member.mention} 不守规矩。{moderator.mention} 按我的意思把他请走了。"
                )
            else:
                msg = (
                    f"👢 {member.mention} 不守规矩的，我让管理员把他请出去。"
                )

            await channel.send(msg)

            try:
                write_log(
                    f"[OK] KICK message sent for {member.id} in channel {channel.id}"
                )
            except Exception:
                pass

        except Exception as e:
            try:
                write_log(f"[ERROR] Failed to send KICK message: {e}")
            except Exception:
                print(e)

        return

    # Neither ban nor kick -> treat as leave
    msg = f"👋 {member.mention} 哦豁，这位受不了自己溜了？挺干脆的哈。"

    try:
        await channel.send(msg)
        try:
            write_log(
                f"[OK] LEAVE message sent for {member.id} in channel {channel.id}"
            )
        except Exception:
            pass
    except Exception as e:
        try:
            write_log(f"[ERROR] Failed to send LEAVE message: {e}")
        except Exception:
            print(e)
