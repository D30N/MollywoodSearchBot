from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


START_KB = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("🆘 Help", callback_data="help_cb"),
            InlineKeyboardButton(
                "👨‍💻 Source Code", url="https://github.com/EL-Coders/mediafinder"
            ),
        ]
    ]
)

HELP_KB = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("🔙 Back", callback_data="back_m"),
        ],
    ]
)


STARTMSG = "Hi **[{}](tg://user?id={})**, I am a media finder bot which finds media from my database channel. Just send query to find the media.\nSend /help for more or you can toggle your settings by sending /settings."


HELPMSG = """
**You can find the bot commands here.**
**User Commands:-**
/help - __Show this help message__
/settings - __Toggle settings of Precise Mode and Button Mode__
`Precise Mode:` 
- __If Enabled, bot will match the word & return results with only the exact match__
- __If Disabled, bot will match the word & return all the results containing the word__ 
`Result Mode:` 
- __If Button, bot will return results in button format__
- __If List, bot will return results in list format__
- __If HyperLink, bot will return results in hyperlink format__

**Admin Commands:-**
/logs - __Get logs as a file__
/server - __Get server stats__
/restart - __Restart the bot__
/stats - __Get bot user stats__
/broadcast - __Reply to a message to send that to all bot users__
/index - __Start indexing a database channel (bot must be admin of the channel if that is provate channel)__
__You can just forward the message from database channel for starting indexing, no need to use the /index command__
/delete - __Reply to a file to delete it from database__
/autodelete - __Set file auto delete time in seconds__
/repairmode - __Enable or disable repair mode - If on, bot will not send any files__
/customcaption - __Set custom caption for files__
/adminsettings - __Get current admin settings__
/ban - __Ban a user from bot__ - `/ban user_id`
/unban - __Unban a user from bot__ - `/unban user_id`
/addfilter - __Add a text filter__ - `/addfilter filter message` __or__ `/addfilter "filter multiple words" message` __(If a filter is there, bot will send the filter rather than file)__
/delfilter - __Delete a text filter__ - `/delfilter filter`
/listfilters - __List all filters currently added in the bot__
/forcesub - __Set force subscribe channel__ - `/forcesub channel_id` __Bot must be admin of that channel (Bot will create a new invite link for that channel)__
/checklink - __Check invite link for force subscribe channel__
/total - __Get count of total files in DB__
"""

SET_MSG = """
**Precise Mode:** 
• Enabled ആണെങ്കിൽ അയക്കുന്ന keyword ന് കൃത്യം match ആയ results ആവും കാണിക്കുക.
• Disabled ആണെങ്കിൽ അയക്കുന്ന keyword മായി സാമ്യമുള്ള results കാണിക്കും.

**Result Mode:**
• HyperLink (preferred) ആണെങ്കിൽ link രൂപത്തിലുള്ള result list കിട്ടും.
• Button ആണെങ്കിൽ ബട്ടൺ രൂപത്തിലാവും result list കിട്ടുക.

**താഴെ വലതു വശത്തെ ബട്ടനിൽ ക്ലിക്ക് ചെയ്ത് settings customize ചെയ്യാവുന്നതാണ്.**
"""

