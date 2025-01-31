from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# use the same format for name & user_id placeholders
START_MSG = """
Hi [{}](tg://user?id={}), this is a Malayalam-Movie-Search Bot. 🎉

• Bot എങ്ങനെയാണ് ഉപയോഗിക്കേണ്ടത് എന്നറിയാൻ /help അമർത്തുക.

NB: ഈ bot ഉപയോഗിക്കാൻ ആദ്യം @MollywoodChanneI ൽ join ചെയ്യണം.
"""

HELP_MSG = """
Welcome to Malayalam-Movie-Search Bot. ✨

ആവശ്യമുള്ള സിനിമയുടെ പേര് സ്പെല്ലിങ് തെറ്റാതെ അയക്കുക. 
Simple ⚡

(2015 മുതൽ DVD/OTT ഇറങ്ങിയ എല്ലാ മലയാളം സിനിമകളും ഇതിൽ ലഭ്യമാണ്. കൂടാതെ, Malayalam Dubbed സിനിമകളും 1960-80 കാലഘട്ടത്തെ ചില evergreen സിനിമകളും ചേർത്തിട്ടുണ്ട്.)

• Results വരുന്ന list customize ചെയ്യാൻ /settings അമർത്തുക 

NB: ഈ bot ഉപയോഗിക്കാൻ ആദ്യം @MollywoodChanneI subscribe ചെയ്യണം.
"""

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
        ]
    ]
)
