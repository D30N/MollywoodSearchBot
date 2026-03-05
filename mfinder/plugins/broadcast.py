import asyncio
import datetime
import io
import time

from pyrogram import Client, filters
from pyrogram.enums import ChatAction
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from mfinder import ADMINS, LOGGER
from mfinder.db.broadcast_sql import clear_users, count_users, del_user, get_users

lock = asyncio.Lock()
success = 0
failed = 0
completed = 0
t_users = 0
brc_task = None
start_time = None


@Client.on_message(filters.private & filters.command("stats") & filters.user(ADMINS))
async def get_subscribers_count(bot, message):
    user_id = message.from_user.id
    wait_msg = "__Checking active users, this will take some time, please wait...__"
    msg = await message.reply_text(wait_msg)
    active, blocked, sts_list = await users_info(bot)
    stats_msg = f"**Stats**\nSubscribers: `{active}`\nBlocked / Deleted: `{blocked}`"
    log_file = io.BytesIO()
    log_file.name = f"{datetime.datetime.utcnow()}_status.txt"
    log_file.write(sts_list.encode())
    await msg.edit(stats_msg)
    if blocked > 0:
        await bot.send_document(
            user_id,
            document=log_file,
            caption="Status check completed. Failed users log.",
        )


@Client.on_message(
    filters.private & filters.command("broadcast") & filters.user(ADMINS)
)
async def send_text(bot, message):
    global brc_task
    user_id = message.from_user.id
    if lock.locked():
        await message.reply("Wait until the previous broadcast completes.")
    if message.reply_to_message:
        brc_task = asyncio.create_task(broadcast_message(bot, message, user_id))
    else:
        reply_error = (
            "`Use this command as a reply to any telegram message without any spaces.`"
        )
        msg = await message.reply_text(reply_error, message.id)
        await asyncio.sleep(8)
        await msg.delete()


async def broadcast_message(bot, message, user_id):
    global success, failed, completed, t_users, brc_task, start_time
    start_time = time.time()
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Progress", callback_data="brd_pgrs"),
                InlineKeyboardButton("Cancel", callback_data="brd_cncl"),
            ]
        ]
    )
    await bot.copy_message(
        chat_id=user_id,
        from_chat_id=message.chat.id,
        message_id=message.reply_to_message_id,
        reply_markup=message.reply_to_message.reply_markup,
    )
    mess = await message.reply_text(
        "__Started broadcast with above message...__",
        reply_markup=kb,
        quote=True,
    )
    users = await get_users()
    t_users = await count_users()
    log_file = io.BytesIO()
    log_file.name = f"{datetime.datetime.utcnow()}_broadcast.txt"
    bc_log = "Broadcast Log:\n"
    async with lock:
        try:
            for user in users:
                chat_id = int(user)
                try:
                    await bot.copy_message(
                        chat_id=chat_id,
                        from_chat_id=message.chat.id,
                        message_id=message.reply_to_message_id,
                        reply_markup=message.reply_to_message.reply_markup,
                    )
                    success += 1
                    LOGGER.info("Broadcast sent to %s", chat_id)
                except FloodWait as e:
                    LOGGER.warning(
                        "Floodwait while broadcasting, sleeping for %s", e.value
                    )
                    await asyncio.sleep(e.value)
                    await bot.copy_message(
                        chat_id=chat_id,
                        from_chat_id=message.chat.id,
                        message_id=message.reply_to_message_id,
                        reply_markup=message.reply_to_message.reply_markup,
                    )
                except asyncio.exceptions.CancelledError:
                    LOGGER.info("Broadcast task was cancelled.")
                    return
                except Exception as e:
                    failed += 1
                    LOGGER.info("Broadcast failed to %s : Reason: %s", chat_id, e)
                    bc_log += f"Broadcast failed to {chat_id} : Reason: {e}\n"
                    pass
                completed += 1
        except asyncio.exceptions.CancelledError:
            LOGGER.info("Broadcast task was cancelled.")
            return
        except Exception as e:
            LOGGER.warning(e)
            await bot.send_message(user_id, f"An error occurred: {e}")
            return
        finally:
            brc_task = None

    log_file.write(bc_log.encode())
    time_taken = datetime.timedelta(seconds=int(time.time() - start_time))
    await mess.delete()
    await bot.send_message(
        user_id,
        f"**Broadcast Completed**\n\n**Stats:**\nCompleted: {completed}/{t_users}\nSuccess: `{success}`\nFailed: `{failed}`\nCompleted in `{time_taken}` HH:MM:SS",
    )
    if failed > 0:
        await bot.send_document(
            user_id,
            document=log_file,
            caption="Failed users log.",
        )
    success = 0
    failed = 0
    completed = 0
    t_users = 0
    start_time = None


@Client.on_callback_query(filters.regex(r"^brd_pgrs$"))
async def brd_pgrs(bot, query):
    if brc_task and not brc_task.done():
        time_taken = datetime.timedelta(seconds=int(time.time() - start_time))
        await query.answer(
            f"Broadcast in progress...\nCompleted: {completed}/{t_users}\nSuccess: {success}\nFailed: {failed}\nTime taken: {time_taken} HH:MM:SS",
            show_alert=True,
        )
    else:
        await query.answer("No active broadcasts")


@Client.on_callback_query(filters.regex(r"^brd_cncl$"))
async def brd_cncl(bot, query):
    global brc_task
    user_id = query.from_user.id
    if brc_task and not brc_task.done():
        brc_task.cancel()
        time_taken = datetime.timedelta(seconds=int(time.time() - start_time))
        await query.message.edit(
            f"Broadcast process was cancelled. \n\n**Stats:**\nCompleted: `{completed}`/`{t_users}`\nSent to: `{success}`\nBlocked / Deleted: `{failed}`\nCompleted in `{time_taken}` HH:MM:SS"
        )
        LOGGER.info("User requested cancellation of broadcasting.. : %s", user_id)
    else:
        await query.message.edit("No active broadcast process to cancel.")
    try:
        await query.answer("")
    except Exception:
        pass


# SR
@Client.on_message(
    filters.private & filters.command("clearusers") & filters.user(ADMINS)
)
async def clear_users_(bot, update):
    clear_ms = await update.reply_text(
        "Please conifirm that you want to remove all users",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("✅ Yes", callback_data="clear_users_yes"),
                    InlineKeyboardButton("❌ No", callback_data="clear_users_no"),
                ]
            ]
        ),
    )
    try:
        clear_cb = await bot.listen_callback(update.chat.id, clear_ms.id, timeout=300)
    except TimeoutError:
        await clear_ms.reply_text("Request timed out, please /start again.", quote=True)
        return
    if clear_cb.data == "clear_users_no":
        await clear_ms.edit_text("Operation Cancelled")
        return

    await clear_ms.delete()
    await clear_users()
    await update.reply_text("All users deleted successfully")


async def users_info(bot):
    users = 0
    blocked = 0
    user_list = await get_users()
    sts_list = ""
    for user in user_list:
        user_id = int(user)
        name = bool()
        try:
            name = await bot.send_chat_action(user_id, ChatAction.TYPING)
        except FloodWait as e:
            await asyncio.sleep(e.value)
        except Exception as e:
            sts_list += f"User ID: {user_id} : Status: {e}\n"
        if bool(name):
            users += 1
        else:
            await del_user(user_id)
            LOGGER.info("Deleted inactive user id %s from broadcast list", user_id)
            blocked += 1
    return users, blocked, sts_list


@Client.on_callback_query(filters.regex(r"^clear_users_(yes|no)$"))
async def clear_users_cb(bot, query):
    await query.answer()
