import asyncio
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from VIPMUSIC import app
from config import REACTION_BOT, BANNED_USERS, OWNER_ID, START_REACTIONS
from VIPMUSIC.utils.database import get_sudoers
from VIPMUSIC.utils.database.reactiondb import get_reaction_status, set_reaction_status

# ------------------------------
# 🔘 BUTTONS
# ------------------------------
def reaction_buttons(chat_id: int):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Enable", callback_data=f"reactionon_{chat_id}"),
                InlineKeyboardButton("🚫 Disable", callback_data=f"reactionoff_{chat_id}"),
            ]
        ]
    )

# ------------------------------
# ⚙️ /reaction command
# ------------------------------
@app.on_message(filters.command("reaction") & ~BANNED_USERS)
async def reaction_toggle(client, message):
    if message.chat.type not in ["group", "supergroup"]:
        return await message.reply_text("❌ This command can only be used in groups.")

    try:
        sudoers = await get_sudoers()
    except Exception:
        sudoers = []

    user_id = message.from_user.id if message.from_user else 0
    if user_id != OWNER_ID and user_id not in sudoers:
        return await message.reply_text("🚫 Only admins or sudo users can manage reactions.")

    chat_id = message.chat.id
    current_status = await get_reaction_status(chat_id)

    # No arguments → show buttons
    if len(message.command) == 1:
        status_text = "🟢 Enabled" if current_status else "🔴 Disabled"
        return await message.reply_text(
            f"**Reaction Bot is currently {status_text} for this chat.**\n\nUse the buttons below to toggle:",
            reply_markup=reaction_buttons(chat_id),
        )

    arg = message.command[1].lower()
    if arg == "on":
        await set_reaction_status(chat_id, True)
        return await message.reply_text("✅ Reaction Bot has been **enabled** for this chat.")
    elif arg == "off":
        await set_reaction_status(chat_id, False)
        return await message.reply_text("🚫 Reaction Bot has been **disabled** for this chat.")
    else:
        return await message.reply_text("Usage:\n`/reaction on` or `/reaction off`")

# ------------------------------
# 🔘 BUTTON CALLBACKS
# ------------------------------
@app.on_callback_query(filters.regex(r"^reactionon_(\d+)$"))
async def cb_enable_reaction(client, query):
    chat_id = int(query.data.split("_")[1])
    await set_reaction_status(chat_id, True)
    await query.message.edit_text(
        "✅ Reaction Bot **enabled** for this chat.",
        reply_markup=reaction_buttons(chat_id),
    )

@app.on_callback_query(filters.regex(r"^reactionoff_(\d+)$"))
async def cb_disable_reaction(client, query):
    chat_id = int(query.data.split("_")[1])
    await set_reaction_status(chat_id, False)
    await query.message.edit_text(
        "🚫 Reaction Bot **disabled** for this chat.",
        reply_markup=reaction_buttons(chat_id),
    )

# ------------------------------
# 💫 AUTO REACTOR
# ------------------------------
@app.on_message(filters.all & ~BANNED_USERS)
async def auto_reactor(client, message):
    if not REACTION_BOT:
        return  # globally off

    if message.chat.type not in ["group", "supergroup", "private"]:
        return

    chat_id = message.chat.id
    status = await get_reaction_status(chat_id)
    if not status:
        return

    if not message.from_user or message.from_user.is_self:
        return

    try:
        from VIPMUSIC.plugins.tools.reaction import next_emoji
        emoji = next_emoji(chat_id)
        await message.react(emoji)
        print(f"[ReactionBot] Reacted in {chat_id} with {emoji}")
    except Exception as e:
        print(f"[ReactionBot] Failed to react in {chat_id}: {e}")
