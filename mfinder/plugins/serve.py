import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    CallbackQuery,
    LinkPreviewOptions,
)
from pyrogram.enums import ParseMode, ChatMemberStatus
from pyrogram.errors import UserNotParticipant
from pyrogram.errors.exceptions.bad_request_400 import MessageNotModified
from mfinder.db.files_sql import (
    get_filter_results,
    get_file_details,
    get_precise_filter_results,
)
from mfinder.db.settings_sql import (
    get_search_settings,
    get_admin_settings,
    get_link,
    get_channel,
)
from mfinder.db.ban_sql import is_banned
from mfinder.db.filters_sql import is_filter
from mfinder import LOGGER


@Client.on_message(
    ~filters.regex(r"^\/") & filters.text & filters.private & filters.incoming
)
async def filter_(bot, message):
    user_id = message.from_user.id

    if re.findall(r"((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
        return

    if await is_banned(user_id):
        await message.reply_text("You are banned. You can't use this bot.", quote=True)
        return

    force_sub = await get_channel()
    if force_sub:
        try:
            user = await bot.get_chat_member(int(force_sub), user_id)
            if user.status == ChatMemberStatus.BANNED:
                await message.reply_text("Sorry, you are Banned to use me.", quote=True)
                return
        except UserNotParticipant:
            link = await get_link()
            await message.reply_text(
                text="**ഈ bot ഉപയോഗിക്കണമെങ്കിൽ ഞങ്ങളുടെ updates ചാനലായ @MollywoodChanneI ൽ join ചെയ്യണം!**",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🤖 Join @MollywoodChanneI", url=link)]]
                ),
                parse_mode=ParseMode.MARKDOWN,
                quote=True,
            )
            return
        except Exception as e:
            LOGGER.warning(e)
            await message.reply_text(
                text="Something went wrong, please contact my support group",
                quote=True,
            )
            return

    admin_settings = await get_admin_settings()
    if admin_settings:
        if admin_settings.repair_mode:
            return

    fltr = await is_filter(message.text)
    if fltr:
        await message.reply_text(
            text=fltr.message,
            quote=True,
        )
        return

    if 2 < len(message.text) < 100:
        search = message.text
        page_no = 1
        me = bot.me
        username = me.username
        result, btn = await get_result(search, page_no, user_id, username)

        if result:
            if btn:
                await message.reply_text(
                    f"{result}",
                    reply_markup=InlineKeyboardMarkup(btn),
                    link_preview_options=LinkPreviewOptions(is_disabled=True),
                    quote=True,
                )
            else:
                await message.reply_text(
                    f"{result}",
                    link_preview_options=LinkPreviewOptions(is_disabled=True),
                    quote=True,
                )
        else:
            await message.reply_text(
                text="**NO RESULTS FOUND** 🧐\n \n Possible reasons: \n **1. Spelling തെറ്റായിരിക്കാം.** \n (സിനിമയുടെ പേര് മാത്രം കൃത്യമായി അയക്കുക.) \n **2. OTT ഇറങ്ങിയിട്ടുണ്ടാവില്ല.** \n (പുതിയ സിനിമകൾ OTT ഇറങ്ങിയ ശേഷം മാത്രമേ ബോട്ടിൽ കിട്ടുകയുള്ളൂ.) \n \n കൂടുതൽ സഹായത്തിന് /help അമർത്തുക. \n \n പരിശോധിച്ച് വീണ്ടും ശ്രമിക്കുക.",
                quote=True,
            )


@Client.on_callback_query(filters.regex(r"^(nxt_pg|prev_pg) \d+ \d+ .+$"))
async def pages(bot, query):
    user_id = query.from_user.id
    org_user_id, page_no, search = query.data.split(maxsplit=3)[1:]
    org_user_id = int(org_user_id)
    page_no = int(page_no)
    me = bot.me
    username = me.username

    result, btn = await get_result(search, page_no, user_id, username)

    if result:
        try:
            if btn:
                await query.message.edit(
                    f"{result}",
                    reply_markup=InlineKeyboardMarkup(btn),
                    link_preview_options=LinkPreviewOptions(is_disabled=True),
                )
            else:
                await query.message.edit(
                    f"{result}",
                    link_preview_options=LinkPreviewOptions(is_disabled=True),
                )
        except MessageNotModified:
            pass
    else:
        await query.message.reply_text(
            text="**NO RESULTS FOUND** 🧐\n \n Possible reasons: \n **1. Spelling തെറ്റായിരിക്കാം.** \n (സിനിമയുടെ പേര് മാത്രം കൃത്യമായി അയക്കുക.) \n **2. OTT ഇറങ്ങിയിട്ടുണ്ടാവില്ല.** \n (പുതിയ സിനിമകൾ OTT ഇറങ്ങിയ ശേഷം മാത്രമേ ബോട്ടിൽ കിട്ടുകയുള്ളൂ.) \n \n കൂടുതൽ സഹായത്തിന് /help അമർത്തുക. \n \n പരിശോധിച്ച് വീണ്ടും ശ്രമിക്കുക.",
            quote=True,
        )


async def get_result(search, page_no, user_id, username):
    search_settings = await get_search_settings(user_id)
    if search_settings:
        if search_settings.precise_mode:
            files, count = await get_precise_filter_results(query=search, page=page_no)
            precise_search = "Enabled"
        else:
            files, count = await get_filter_results(query=search, page=page_no)
            precise_search = "Disabled"
    else:
        files, count = await get_filter_results(query=search, page=page_no)
        precise_search = "Disabled"

    if search_settings:
        if search_settings.button_mode or search_settings.list_mode:
            button_mode = "ON"
        else:
            button_mode = "OFF"
    else:
        button_mode = "OFF"

    if search_settings:
        if search_settings.link_mode:
            link_mode = "ON"
        else:
            link_mode = "OFF"
    else:
        link_mode = "OFF"

    if button_mode == "ON" and link_mode == "OFF":
        search_md = "Button"
    elif button_mode == "OFF" and link_mode == "ON":
        search_md = "HyperLink"
    else:
        search_md = "Hyperlink"

    if files:
        btn = []
        index = (page_no - 1) * 10
        crnt_pg = index // 10 + 1
        tot_pg = (count + 10 - 1) // 10
        btn_count = 0
        result = f"**Search Query:** `{search}`\n**Total Results:** `{count}`\n**Page:** `{crnt_pg}/{tot_pg}`\n**Precise Search: **`{precise_search}`\n**Result Mode:** `{search_md}`\n"
        page = page_no
        for file in files:
            if button_mode == "ON":
                file_id = file.file_id
                filename = f"[{get_size(file.file_size)}]{file.file_name}"
                btn_kb = InlineKeyboardButton(
                    text=f"{filename}", callback_data=f"file {file_id}"
                )
                btn.append([btn_kb])
            else:
                index += 1
                btn_count += 1
                file_id = file.file_id
                filename = f"**{index}.** [{file.file_name}](https://t.me/{username}/?start={file_id}) - `[{get_size(file.file_size)}]`"
                result += "\n" + filename
            # else:
            #     index += 1
            #     btn_count += 1
            #     file_id = file.file_id
            #     filename = (
            #         f"**{index}.** `{file.file_name}` - `[{get_size(file.file_size)}]`"
            #     )
            #     result += "\n" + filename

            #     btn_kb = InlineKeyboardButton(
            #         text=f"{index}", callback_data=f"file {file_id}"
            #     )

            #     if btn_count == 1 or btn_count == 6:
            #         btn.append([btn_kb])
            #     elif 6 > btn_count > 1:
            #         btn[0].append(btn_kb)
            #     else:
            #         btn[1].append(btn_kb)

        nxt_kb = InlineKeyboardButton(
            text="Next >>",
            callback_data=f"nxt_pg {user_id} {page + 1} {search}",
        )
        prev_kb = InlineKeyboardButton(
            text="<< Previous",
            callback_data=f"prev_pg {user_id} {page - 1} {search}",
        )

        kb = []
        if crnt_pg == 1 and tot_pg > 1:
            kb = [nxt_kb]
        elif crnt_pg > 1 and crnt_pg < tot_pg:
            kb = [prev_kb, nxt_kb]
        elif tot_pg > 1:
            kb = [prev_kb]

        if kb:
            btn.append(kb)

        if button_mode and link_mode == "OFF":
            result = (
                result
                + "\n\n"
                + "__ആവശ്യമുള്ള file name ൽ ക്ലിക്ക് ചെയ്യുക.__"
            )
        elif link_mode == "ON":
            result = result + "\n\n" + " __ആവശ്യമുള്ള file name ൽ ക്ലിക്ക് ചെയ്യുക.__"

        return result, btn

    return None, None


@Client.on_callback_query(filters.regex(r"^file (.+)$"))
async def get_files(bot, query):
    user_id = query.from_user.id
    if isinstance(query, CallbackQuery):
        file_id = query.data.split()[1]
        await query.answer("Sending file...", cache_time=60)
        cbq = True
    elif isinstance(query, Message):
        file_id = query.text.split()[1]
        cbq = False
    filedetails = await get_file_details(file_id)
    admin_settings = await get_admin_settings()
    for files in filedetails:
        f_caption = files.caption
        if admin_settings.custom_caption:
            f_caption = admin_settings.custom_caption
        elif f_caption is None:
            f_caption = f"{files.file_name}"

        f_caption = "`" + f_caption + "`"

        if admin_settings.caption_uname:
            f_caption = f_caption + "\n" + admin_settings.caption_uname

        if cbq:
            msg = await query.message.reply_cached_media(
                file_id=file_id,
                caption=f_caption,
                parse_mode=ParseMode.MARKDOWN,
                quote=True,
            )
        else:
            msg = await query.reply_cached_media(
                file_id=file_id,
                caption=f_caption,
                parse_mode=ParseMode.MARKDOWN,
                quote=True,
            )

        if admin_settings.auto_delete:
            delay_dur = admin_settings.auto_delete
            delay = delay_dur / 60 if delay_dur > 60 else delay_dur
            delay = round(delay, 2)
            minsec = str(delay) + " mins" if delay_dur > 60 else str(delay) + " secs"
            disc = await bot.send_message(
                user_id,
                f"ഈ ഫയൽ എത്രയും വേഗം നിങ്ങളുടെ saved messages ലേക്ക് ഫോർവേഡ് ചെയ്ത് അവിടെ നിന്ന് ഡൗൺലോഡ് ചെയ്യുക, ഈ ചാറ്റിൽ നിന്നും {minsec} സമയത്തിനുള്ളിൽ ഡിലീറ്റ് ആവും.",
            )
            await asyncio.sleep(delay_dur)
            await disc.delete()
            await msg.delete()
            await bot.send_message(user_id, "File ഡിലീറ്റ് ചെയ്യപ്പെട്ടു!")


def get_size(size):
    units = ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB"]
    size = float(size)
    i = 0
    while size >= 1024.0 and i < len(units):
        i += 1
        size /= 1024.0
    return f"{size:.2f} {units[i]}"
