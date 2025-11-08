import random
from pyrogram import filters
from pyrogram.types import Message
from VIPMUSIC import app, SUDOERS
from config import REACTION_BOT  # 👈 import global toggle from config.py

# ---------------- EMOJI CONFIG ----------------
VALID_REACTIONS = [
    "❤️", "💖", "💘", "💞", "💓", "💫", "💥", "✨",
    "🌸", "🌹", "💎", "🌙", "🔥", "🥰", "😍",
    "😘", "😉", "🤩", "😂", "😎", "💐", "😻", "🥳"
]

# Track recently used emojis per chat
used_emojis = {}
MAX_HISTORY = 6  # don’t reuse last 6 emojis per chat


# ---------------- UTILS ----------------
def next_emoji(chat_id: int) -> str:
    """Return a random emoji not recently used in this chat."""
    if chat_id not in used_emojis:
        used_emojis[chat_id] = []

    available = [e for e in VALID_REACTIONS if e not in used_emojis[chat_id]]
    if not available:  # reset when all used
        used_emojis[chat_id].clear()
        available = VALID_REACTIONS.copy()

    emoji = random.choice(available)
    used_emojis[chat_id].append(emoji)
    if len(used_emojis[chat_id]) > MAX_HISTORY:
        used_emojis[chat_id].pop(0)
    return emoji


async def is_admin_or_sudo(chat_id: int, user_id: int) -> bool:
    """Check if user is admin, owner, or sudo."""
    if user_id in SUDOERS:
        return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in ["administrator", "creator"]
    except:
        return False


# ---------------- COMMAND HANDLER ----------------
@app.on_message(filters.command(["reaction"]) & (filters.group | filters.supergroup))
async def reaction_status_command(_, message: Message):
    """Show reaction bot state (from config)."""
    global REACTION_BOT

    user_id = message.from_user.id if message.from_user else None
    if not await is_admin_or_sudo(message.chat.id, user_id):
        return await message.reply_text("Only Admins, Owners or Sudoers can use this command!")

    # Check argument if provided
    if len(message.command) > 1:
        cmd = message.command[1].lower()
        if cmd == "on":
            REACTION_BOT = True
            return await message.reply_text("✅ Reaction Bot **Enabled** globally (config).")
        elif cmd == "off":
            REACTION_BOT = False
            return await message.reply_text("❌ Reaction Bot **Disabled** globally (config).")

    # If no argument, show current status
    state = "ON ✅" if REACTION_BOT else "OFF ❌"
    await message.reply_text(f"🎭 Reaction Bot is currently **{state}** (config controlled)")


# ---------------- REACTION HANDLER ----------------
@app.on_message(filters.text & (filters.group | filters.supergroup))
async def auto_react(_, message: Message):
    global REACTION_BOT
    chat_id = message.chat.id

    # Skip bot commands
    if message.text and message.text.startswith("/"):
        return

    # If globally disabled, skip reacting
    if not REACTION_BOT:
        return

    try:
        emoji = next_emoji(chat_id)
        await message.react(emoji)
        print(f"[ReactionBot] Reacted in {chat_id} with {emoji}")
    except Exception as e:
        print(f"[ReactionBot Error] {e}")
