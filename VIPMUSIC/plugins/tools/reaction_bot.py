import random
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from VIPMUSIC import app
from VIPMUSIC.utils.databases.reactiondb import is_reaction_on, reaction_on, reaction_off
from VIPMUSIC.misc import SUDOERS
from config import OWNER_ID, START_REACTIONS


print("[ReactionBot] Diagnostic plugin loaded!")


async def is_admin_or_sudo(client, message):
    if message.from_user is None:
        return False
    uid = message.from_user.id
    if uid == OWNER_ID or uid in SUDOERS:
        return True
    try:
        member = await message.chat.get_member(uid)
        return member.status in ("administrator", "creator")
    except Exception as e:
        print(f"[ReactionBot] Admin check error: {e}")
        return False


def reaction_buttons(status):
    if status:
        text = "✅ Reaction is currently *Enabled*"
        btn = [[InlineKeyboardButton("🛑 Disable", callback_data="reaction_disable")]]
    else:
        text = "❌ Reaction is currently *Disabled*"
        btn = [[InlineKeyboardButton("✅ Enable", callback_data="reaction_enable")]]
    return text, InlineKeyboardMarkup(btn)


# ------------------------------------------------------------
# GLOBAL MESSAGE LOGGER
# ------------------------------------------------------------
@app.on_message(filters.group)
async def all_message_logger(_, message):
    try:
        if message.text:
            print(f"[ReactionBot] MSG: {message.text}")
        else:
            print(f"[ReactionBot] MSG: (non-text)")
    except Exception as e:
        print(f"[ReactionBot] all_message_logger error: {e}")


# ------------------------------------------------------------
# COMMANDS
# ------------------------------------------------------------
@app.on_message(filters.command(["reactionon"], prefixes=["/", "!", "."]) & filters.group)
async def cmd_on(client, message):
    print("[ReactionBot] /reactionon triggered")
    try:
        if not await is_admin_or_sudo(client, message):
            print("[ReactionBot] Not admin or sudo.")
            return await message.reply_text("🚫 Permission denied.")
        await reaction_on(message.chat.id)
        await message.reply_text("✅ Reaction enabled for this group.")
        print("[ReactionBot] Reaction turned ON.")
    except Exception as e:
        print(f"[ReactionBot ERROR /reactionon]: {e}")


@app.on_message(filters.command(["reactionoff"], prefixes=["/", "!", "."]) & filters.group)
async def cmd_off(client, message):
    print("[ReactionBot] /reactionoff triggered")
    try:
        if not await is_admin_or_sudo(client, message):
            print("[ReactionBot] Not admin or sudo.")
            return await message.reply_text("🚫 Permission denied.")
        await reaction_off(message.chat.id)
        await message.reply_text("🛑 Reaction disabled for this group.")
        print("[ReactionBot] Reaction turned OFF.")
    except Exception as e:
        print(f"[ReactionBot ERROR /reactionoff]: {e}")


@app.on_message(filters.command(["reaction"], prefixes=["/", "!", "."]) & filters.group)
async def cmd_status(client, message):
    print("[ReactionBot] /reaction triggered")
    try:
        if not await is_admin_or_sudo(client, message):
            print("[ReactionBot] Not admin or sudo.")
            return await message.reply_text("🚫 Permission denied.")

        status = await is_reaction_on(message.chat.id)
        text, keyboard = reaction_buttons(status)
        await message.reply_text(text, reply_markup=keyboard)
        print(f"[ReactionBot] Sent status message (Enabled={status})")
    except Exception as e:
        print(f"[ReactionBot ERROR /reaction]: {e}")


@app.on_callback_query(filters.regex("^reaction_"))
async def callback_handler(client, cq):
    print(f"[ReactionBot] Callback: {cq.data} by {cq.from_user.id}")
    try:
        uid = cq.from_user.id
        member = await cq.message.chat.get_member(uid)
        if (
            uid != OWNER_ID
            and uid not in SUDOERS
            and member.status not in ("administrator", "creator")
        ):
            return await cq.answer("🚫 Not allowed.", show_alert=True)

        if cq.data == "reaction_enable":
            await reaction_on(cq.message.chat.id)
            text, kb = reaction_buttons(True)
            await cq.message.edit_text(text, reply_markup=kb)
            await cq.answer("✅ Reaction enabled!")

        elif cq.data == "reaction_disable":
            await reaction_off(cq.message.chat.id)
            text, kb = reaction_buttons(False)
            await cq.message.edit_text(text, reply_markup=kb)
            await cq.answer("🛑 Reaction disabled!")

    except Exception as e:
        print(f"[ReactionBot ERROR callback]: {e}")


# ------------------------------------------------------------
# REACTION LISTENER
# ------------------------------------------------------------
@app.on_message((filters.text | filters.caption) & filters.group)
async def react_listener(client, message):
    try:
        status = await is_reaction_on(message.chat.id)
        if not status:
            return
        if message.text and message.text.startswith(("/", "!", ".")):
            return
        emoji = random.choice(START_REACTIONS)
        await message.react(emoji)
    except Exception as e:
        print(f"[ReactionBot ERROR react_listener]: {e}")


@app.on_message(filters.command("reactiontest") & filters.group)
async def test(_, message):
    print("[ReactionBot] /reactiontest command triggered!")
    await message.reply_text("✅ Reaction test command works!")
