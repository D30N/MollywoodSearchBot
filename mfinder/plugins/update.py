import os
import sys
import subprocess
from pyrogram import Client, filters
from mfinder import ADMINS, LOGGER

# Repo root = two levels up from this file (mfinder/plugins/update.py -> repo/)
REPO_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)


@Client.on_message(filters.command("update") & filters.user(ADMINS))
async def update_bot(client, message):
    """Admin-only: git pull latest code from GitHub and restart the bot."""
    msg = await message.reply("Pulling latest code...⏳")
    try:
        proc = subprocess.run(
            ["git", "pull"],
            cwd=REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        output = (proc.stdout + "\n" + proc.stderr).strip()
        if len(output) > 3500:
            output = output[:3500] + "\n...[truncated]"
        LOGGER.info("git pull output: %s", output)
        await msg.edit(
            f"**Git pull done.**\n```\n{output}\n```\n\nRestarting bot..."
        )
    except subprocess.TimeoutExpired:
        await msg.edit("`git pull` timed out. Try again.")
        return
    except Exception as e:
        LOGGER.exception(e)
        await msg.edit(f"Update failed: `{e}`")
        return
    # Restart: re-execute this Python process so fresh code loads at start.
    try:
        os.chdir(REPO_DIR)
        os.execv(sys.executable, [sys.executable, "-m", "mfinder"])
    except Exception as e:
        await msg.edit(f"Pull done, but auto-restart failed: `{e}`\nUse /restart.")
