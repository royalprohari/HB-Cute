from VIPMUSIC import app
from pyrogram import filters
import config

SUDOERS = list(map(int, config.SUDOERS))

# Only filters.group works for old Pyrogram versions
group_filter = filters.group

def is_authorized(_, __, message):
    user = message.from_user
    if not user:
        return False
    return user.id in SUDOERS or user.id == config.OWNER_ID or getattr(user, "is_chat_admin", False)

@app.on_message(filters.command("zzztest") & group_filter & filters.create(is_authorized))
async def zzz_test(_, message):
    await message.reply_text("✅ ZZZ Test works!")
