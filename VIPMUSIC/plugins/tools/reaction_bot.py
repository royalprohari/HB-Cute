import asyncio
import random
from typing import Dict, Set
from pyrogram import filters
from pyrogram.types import Message
from VIPMUSIC import app
from config import START_REACTIONS, OWNER_ID
from VIPMUSIC.utils.database import mongodb, get_sudoers

# ---------------- DB COLLECTIONS ----------------
STATUS_COLLECTION = mongodb["reaction_bot_status"]    # stores per-chat on/off docs: {"chat_id": 123, "enabled": True}
# optionally reuse your existing collection for reaction mentions; not needed here

# ---------------- EMOJI CONFIG ----------------
VALID_REACTIONS = [
    "❤️", "💖", "💘", "💞", "💓", "✨", "🔥", "💫",
    "💥", "🌸", "😍", "🥰", "💎", "🌙", "🌹", "😂",
    "😎", "🤩", "😘", "😉", "🤭", "💐", "😻", "🥳"
]

# Use START_REACTIONS from config if present and valid
SAFE_REACTIONS = [e for e in (START_REACTIONS or []) if e in VALID_REACTIONS]
if not SAFE_REACTIONS:
    SAFE_REACTIONS = VALID_REACTIONS.copy()

# Per-chat recent history to avoid frequent repetition
per_chat_recent: Dict[int, list] = {}
MAX_HISTORY = 6


def next_emoji_for_chat(chat_id: int) -> str:
    """Return an emoji for a chat avoiding recently used ones in that chat."""
    if chat_id not in per_chat_recent:
        per_chat_recent[chat_id] = []

    recent = per_chat_recent[chat_id]
    available = [e for e in SAFE_REACTIONS if e not in recent]

    if not available:
        # reset recent history when exhausted
        recent.clear()
        available = SAFE_REACTIONS.copy()

    emoji = random.choice(available)
    recent.append(emoji)
    if len(recent) > MAX_HISTORY:
        recent.pop(0)
    per_chat_recent[chat_id] = recent
    return emoji


# ---------------- IN-MEMORY STATUS CACHE ----------------
# chat_id -> bool
reaction_status: Dict[int, bool] = {}


async def load_statuses_on_startup():
    """Load per-chat statuses from DB into memory at startup."""
    try:
        docs = await STATUS_COLLECTION.find().to_list(None)
        for d in docs:
            cid = d.get("chat_id")
            enabled = bool(d.get("enabled"))
            if cid is not None:
                reaction_status[int(cid)] = enabled
        print(f"[ReactionBot] Loaded {len(reaction_status)} chat statuses from DB.")
    except Exception as e:
        print(f"[ReactionBot] Failed to load statuses: {e}")


# schedule load
asyncio.get_event_loop().create_task(load_statuses_on_startup())


# ---------------- HELPERS ----------------
async def is_admin_or_sudo(client, chat_id: int, user_id: int) -> bool:
    """Return True if user is owner, in sudoers, or an admin/creator in the chat."""
    # owner shortcut
    if user_id == OWNER_ID:
        return True

    # sudoers from DB
    try:
        sudoers = await get_sudoers()
        if user_id in sudoers:
            return True
    except Exception:
        # if DB read fails, keep going to chat admin check
        pass

    # chat admin check
    try:
        member = await client.get_chat_member(chat_id, user_id)
        if getattr(member, "status", None) in ("administrator", "creator", "owner"):
            return True
    except Exception:
        pass

    return False


async def set_status_in_db(chat_id: int, enabled: bool):
    """Upsert chat status in DB and update in-memory cache."""
    try:
        await STATUS_COLLECTION.update_one(
            {"chat_id": chat_id},
            {"$set": {"chat_id": chat_id, "enabled": bool(enabled)}},
            upsert=True,
        )
        reaction_status[chat_id] = bool(enabled)
    except Exception as e:
        print(f"[ReactionBot] Failed to set status in DB for {chat_id}: {e}")


async def remove_status_from_db(chat_id: int):
    """Remove chat status doc (used optionally when disabling)."""
    try:
        await STATUS_COLLECTION.delete_one({"chat_id": chat_id})
        reaction_status.pop(chat_id, None)
    except Exception as e:
        print(f"[ReactionBot] Failed to remove status from DB for {chat_id}: {e}")


# ---------------- COMMAND (groups & supergroups only) ----------------
@app.on_message(filters.command("reaction") & (filters.group | filters.supergroup))
async def reaction_toggle_command(client, message: Message):
    """
    Usage:
      /reaction           -> shows current state for this chat
      /reaction on        -> enable reactions in this chat (persisted)
      /reaction off       -> disable reactions in this chat (persisted)
    Only Admin/Owner/Sudoers may use this command.
    """
    chat_id = message.chat.id
    user = message.from_user
    user_id = user.id if user else None

    if not user_id:
        return await message.reply_text("Couldn't identify you. Try again.")

    if not await is_admin_or_sudo(client, chat_id, user_id):
        return await message.reply_text("Only Admins, Owner or Sudoers can use this command.")

    # no arg -> show current status
    if len(message.command) == 1:
        enabled = reaction_status.get(chat_id, False)
        state = "ON ✅" if enabled else "OFF ❌"
        return await message.reply_text(f"Reaction bot for this chat is **{state}**.")

    arg = message.command[1].lower()
    if arg not in ("on", "off"):
        return await message.reply_text("Usage:\n/reaction on — enable reactions in this chat\n/reaction off — disable reactions in this chat")

    if arg == "on":
        await set_status_in_db(chat_id, True)
        return await message.reply_text("✅ Reaction bot **ENABLED** for this chat. I will react to every message.")
    else:  # off
        await set_status_in_db(chat_id, False)
        # optionally keep record in DB (we set enabled False) — if you prefer removing doc, call remove_status_from_db
        return await message.reply_text("❌ Reaction bot **DISABLED** for this chat. I will stop reacting.")


# ---------------- MESSAGE HANDLER (react to every message if enabled) ----------------
@app.on_message((filters.text | filters.audio | filters.photo | filters.video | filters.document | filters.sticker | filters.voice | filters.animation) & (filters.group | filters.supergroup))
async def reaction_every_message(client, message: Message):
    """
    React to every message in a chat when the chat's reaction status is True.
    This handler reacts to most message types (text, media, stickers, etc.)
    """

    chat_id = message.chat.id

    # quick skip: if not enabled in memory -> skip
    if not reaction_status.get(chat_id, False):
        return

    # avoid reacting to commands (optional)
    if message.text and message.text.startswith("/"):
        return

    # avoid reacting to other bots messages
    if getattr(message.from_user, "is_bot", False):
        return

    try:
        emoji = next_emoji_for_chat(chat_id)
        await message.react(emoji)
        # debug
        print(f"[ReactionBot] Chat {chat_id} reacted with {emoji}")
    except Exception as e:
        # fallback: attempt simple heart once (but avoid infinite fallback)
        try:
            await message.react("❤️")
        except Exception:
            print(f"[ReactionBot] react failed in chat {chat_id}: {e}")


# End of file
