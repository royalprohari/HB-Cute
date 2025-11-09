import random
from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from VIPMUSIC import app
from config import BANNED_USERS, START_REACTIONS
from VIPMUSIC.utils.database.reactiondb import get_reaction_status, set_reaction_status

# --- REACTIONS HANDLER ---
@app.on_message(filters.command("reaction") & ~filters.edited & ~BANNED_USERS)
async def reaction_command(_, message):
    chat_id = message.chat.id
    status = get_reaction_status(chat_id)
    text = f"🎭 **Reaction Bot Status:** {'✅ Enabled' if status else '❌ Disabled'}"

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ Enable", callback_data=f"reaction_enable:{chat_id}"),
                InlineKeyboardButton("🚫 Disable", callback_data=f"reaction_disable:{chat_id}"),
            ]
        ]
    )

    await message.reply_text(
        text,
        reply_markup=keyboard,
    )

@app.on_callback_query(filters.regex(r"reaction_(enable|disable):"))
async def reaction_toggle(_, query):
    chat_id = int(query.data.split(":")[1])
    action = query.data.split(":")[0].split("_")[1]

    if action == "enable":
        set_reaction_status(chat_id, True)
        await query.message.edit_text("✅ **Reactions have been Enabled.**")
    else:
        set_reaction_status(chat_id, False)
        await query.message.edit_text("🚫 **Reactions have been Disabled.**")

    await query.answer("Status updated!", show_alert=False)

# /reaction on | /reaction off (text command)
@app.on_message(filters.command(["reactionon", "reactionoff", "reaction_on", "reaction_off"]) & ~filters.edited)
async def reaction_toggle_cmd(_, message):
    chat_id = message.chat.id
    cmd = message.command[0].lower()

    if "on" in cmd:
        set_reaction_status(chat_id, True)
        await message.reply_text("✅ Reactions turned **ON** successfully.")
    else:
        set_reaction_status(chat_id, False)
        await message.reply_text("🚫 Reactions turned **OFF** successfully.")

# Automatic reaction system
@app.on_message(filters.group & ~filters.command(["reaction", "reactionon", "reactionoff"]) & ~filters.edited)
async def auto_react(_, message):
    chat_id = message.chat.id
    if not get_reaction_status(chat_id):
        return

    if message.from_user:
        emoji = random.choice(START_REACTIONS)
        username = message.from_user.first_name
        try:
            await message.react(emoji)
            print(f"[Reaction] Reacted with {emoji} to {username}")
        except Exception as e:
            print(f"[Reaction Error] {e}")
