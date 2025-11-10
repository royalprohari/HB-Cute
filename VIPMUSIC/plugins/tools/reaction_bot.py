# VIPMUSIC/plugins/tools/reaction_bot.py
from pyrogram import filters
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from VIPMUSIC import app
from VIPMUSIC.misc import SUDOERS
from VIPMUSIC.utils.databases.reactiondb import is_reaction_on, reaction_on, reaction_off
from config import START_REACTIONS
import random

print("[ReactionBot] Plugin loaded!")

# -------------------------------
# COMMANDS FOR OWNER / SUDO / ADMIN
# -------------------------------

# /reactionon command - Enable auto-reactions
@app.on_message(filters.command("reactionon", prefixes=["/", ".", "!", "#"]) & 
                (filters.user(SUDOERS) | filters.me | filters.group))
async def enable_reaction_cmd(client, message: Message):
    chat_id = message.chat.id
    # Only allow Owner / Sudo / Admin
    member = await client.get_chat_member(chat_id, message.from_user.id)
    if not (message.from_user.id in SUDOERS or member.status in ["administrator", "creator"]):
        return await message.reply_text("❌ You are not allowed to do this!")

    await reaction_on(chat_id)
    await message.reply_text("✅ Reactions are now ENABLED in this chat.")

# /reactionoff command - Disable auto-reactions
@app.on_message(filters.command("reactionoff", prefixes=["/", ".", "!", "#"]) &
                (filters.user(SUDOERS) | filters.me | filters.group))
async def disable_reaction_cmd(client, message: Message):
    chat_id = message.chat.id
    member = await client.get_chat_member(chat_id, message.from_user.id)
    if not (message.from_user.id in SUDOERS or member.status in ["administrator", "creator"]):
        return await message.reply_text("❌ You are not allowed to do this!")

    await reaction_off(chat_id)
    await message.reply_text("❌ Reactions are now DISABLED in this chat.")

# /reaction command - show enable/disable buttons
@app.on_message(filters.command("reaction", prefixes=["/", ".", "!", "#"]) &
                (filters.user(SUDOERS) | filters.me | filters.group))
async def reaction_buttons_cmd(client, message: Message):
    chat_id = message.chat.id
    status = "ENABLED" if await is_reaction_on(chat_id) else "DISABLED"

    keyboard = [
        [InlineKeyboardButton("✅ Enable", callback_data=f"reaction_enable"),
         InlineKeyboardButton("❌ Disable", callback_data=f"reaction_disable")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text(
        f"💫 Reaction status in this chat: {status}",
        reply_markup=reply_markup
    )

# -------------------------------
# CALLBACK QUERY HANDLERS
# -------------------------------

@app.on_callback_query(filters.regex("^reaction_enable$"))
async def callback_enable_reaction(client, callback: CallbackQuery):
    chat_id = callback.message.chat.id
    member = await client.get_chat_member(chat_id, callback.from_user.id)
    if not (callback.from_user.id in SUDOERS or member.status in ["administrator", "creator"]):
        return await callback.answer("❌ You are not allowed!", show_alert=True)

    await reaction_on(chat_id)
    await callback.answer("✅ Reactions ENABLED")
    await callback.message.edit_text("💫 Reaction status: ENABLED")

@app.on_callback_query(filters.regex("^reaction_disable$"))
async def callback_disable_reaction(client, callback: CallbackQuery):
    chat_id = callback.message.chat.id
    member = await client.get_chat_member(chat_id, callback.from_user.id)
    if not (callback.from_user.id in SUDOERS or member.status in ["administrator", "creator"]):
        return await callback.answer("❌ You are not allowed!", show_alert=True)

    await reaction_off(chat_id)
    await callback.answer("❌ Reactions DISABLED")
    await callback.message.edit_text("💫 Reaction status: DISABLED")

# -------------------------------
# AUTO-REACTION HANDLER
# -------------------------------

@app.on_message(filters.group)
async def auto_react_messages(client, message: Message):
    chat_id = message.chat.id
    if await is_reaction_on(chat_id):
        try:
            emoji = random.choice(START_REACTIONS)
            await message.reply_text(emoji)
        except:
            pass  # Avoid bot crash if cannot send message
