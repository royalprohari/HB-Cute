# VIPMUSIC/plugins/tools/reaction_bot.py
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from VIPMUSIC import app
from VIPMUSIC.misc import SUDOERS, OWNER_ID
from VIPMUSIC.utils.databases.reactiondb import is_reaction_on, reaction_on, reaction_off
from config import START_REACTIONS

print("[ReactionBot] Plugin loaded!")

# --- Custom filter for SUDO/OWNER/Admin ---
def sudo_filter(_, __, message: Message):
    user_id = message.from_user.id if message.from_user else None
    if not user_id:
        return False
    # Owner, Sudo, or chat admin
    if user_id in SUDOERS or user_id == OWNER_ID:
        return True
    chat_member = message.chat.get_member(user_id)
    if chat_member and chat_member.status in ["administrator", "creator"]:
        return True
    return False

# --- /reactionon command ---
@app.on_message(filters.command("reactionon") & filters.group)
async def reaction_on_cmd(client, message: Message):
    if not sudo_filter(None, None, message):
        return await message.reply_text("❌ You are not authorized to use this command!")
    await reaction_on(message.chat.id)
    await message.reply_text("✅ Reactions are now enabled for this chat.")

# --- /reactionoff command ---
@app.on_message(filters.command("reactionoff") & filters.group)
async def reaction_off_cmd(client, message: Message):
    if not sudo_filter(None, None, message):
        return await message.reply_text("❌ You are not authorized to use this command!")
    await reaction_off(message.chat.id)
    await message.reply_text("❌ Reactions are now disabled for this chat.")

# --- /reaction command with enable/disable buttons ---
@app.on_message(filters.command("reaction") & filters.group)
async def reaction_button_cmd(client, message: Message):
    if not sudo_filter(None, None, message):
        return await message.reply_text("❌ You are not authorized to use this command!")

    status = await is_reaction_on(message.chat.id)
    status_text = "✅ Enabled" if status else "❌ Disabled"

    keyboard = [
        [
            InlineKeyboardButton("Enable ✅", callback_data="reaction_enable"),
            InlineKeyboardButton("Disable ❌", callback_data="reaction_disable")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(f"💫 Current Reaction Status: {status_text}", reply_markup=reply_markup)

# --- Callback query for buttons ---
@app.on_callback_query(filters.regex("^reaction_"))
async def reaction_button_callback(client, callback_query: CallbackQuery):
    if not sudo_filter(None, None, callback_query.message):
        return await callback_query.answer("❌ Not authorized!", show_alert=True)

    if callback_query.data == "reaction_enable":
        await reaction_on(callback_query.message.chat.id)
        await callback_query.message.edit_text("✅ Reactions are now ENABLED!")
    elif callback_query.data == "reaction_disable":
        await reaction_off(callback_query.message.chat.id)
        await callback_query.message.edit_text("❌ Reactions are now DISABLED!")
    await callback_query.answer()  # remove "loading" circle

# --- Example /zzztest command (to check commands are working) ---
@app.on_message(filters.command("zzztest") & filters.group)
async def zzz_test_cmd(client, message: Message):
    await message.reply_text("✅ /zzztest command works!")

# --- Auto react handler ---
@app.on_message(filters.group)
async def auto_react(_, message: Message):
    if not await is_reaction_on(message.chat.id):
        return
    # react only to messages with text
    if not message.text:
        return
    import random
    emoji = random.choice(START_REACTIONS)
    try:
        await message.react(emoji)
    except:
        pass
