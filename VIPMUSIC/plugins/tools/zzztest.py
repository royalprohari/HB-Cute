from VIPMUSIC import app
from pyrogram import filters
from VIPMUSIC.misc import SUDOERS

print("[ReactionBot] Plugin loaded!")

@app.on_message(filters.command("zzztest", prefixes="/") & SUDOERS)
async def zzztest_cmd(_, message):
    print("[ReactionBot] /zzztest command triggered!")
    await message.reply_text("✅ ZZZ Test command works!")

@app.on_message(filters.command("reactiontest", prefixes="/") & SUDOERS)
async def reactiontest_cmd(_, message):
    print("[ReactionBot] /reactiontest command triggered!")
    await message.reply_text("✅ Reaction test command works!")
