import os
import shutil
import subprocess
import sys
import tempfile
from pyrogram import Client, filters
from mfinder import ADMINS, LOGGER

# Repo root = two levels up from this file (mfinder/plugins/update.py -> repo/)
REPO_DIR = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)


def _write_askpass_script():
    """Create a temp SSH_ASKPASS helper that prints $GIT_SSH_PASSWORD.

    Lets `git pull` feed an SSH key passphrase to ssh without a terminal,
    so the command never hangs on a password prompt.
    """
    fd, path = tempfile.mkstemp(prefix="git-askpass-")
    try:
        with os.fdopen(fd, "w") as f:
            f.write("#!/bin/sh\n")
            f.write('echo "$GIT_SSH_PASSWORD"\n')
        os.chmod(path, 0o700)
        return path
    except Exception:
        try:
            os.unlink(path)
        except OSError:
            pass
        raise


@Client.on_message(filters.command("update") & filters.user(ADMINS))
async def update_bot(client, message):
    """Admin-only: git pull latest code from GitHub and restart the bot.

    If the git remote needs an SSH key passphrase, put it in .env as
    SSH_PASSWORD and it will be supplied to ssh non-interactively.
    """
    msg = await message.reply("Pulling latest code...⏳")
    askpass_path = None
    try:
        env = os.environ.copy()
        cmd = ["git", "pull"]
        ssh_password = os.environ.get("SSH_PASSWORD", "").strip()
        if ssh_password:
            # Detach from any controlling terminal and feed the passphrase
            # via SSH_ASKPASS so `git pull` never blocks on a prompt.
            askpass_path = _write_askpass_script()
            env["GIT_SSH_PASSWORD"] = ssh_password
            env["SSH_ASKPASS"] = askpass_path
            env["SSH_ASKPASS_REQUIRE"] = "force"
            env["DISPLAY"] = ":0"
            env["GIT_TERMINAL_PROMPT"] = "0"
            if shutil.which("setsid"):
                cmd = ["setsid"] + cmd
        proc = subprocess.run(
            cmd,
            cwd=REPO_DIR,
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
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
    finally:
        if askpass_path:
            try:
                os.unlink(askpass_path)
            except OSError:
                pass
    # Restart: re-execute this Python process so fresh code loads at start.
    try:
        os.chdir(REPO_DIR)
        os.execv(sys.executable, [sys.executable, "-m", "mfinder"])
    except Exception as e:
        await msg.edit(f"Pull done, but auto-restart failed: `{e}`\nUse /restart.")
