import asyncio

import uvloop

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from pyrogram import Client, __version__, idle
from pyrogram.raw.all import layer

from mfinder import API_HASH, APP_ID, BOT_TOKEN


async def main():
    plugins = dict(root="mfinder/plugins")
    app = Client(
        name="mfinder",
        api_id=APP_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
        plugins=plugins,
        workers=500,
    )
    async with app:
        me = await app.get_me()
        print(
            f"{me.first_name} - @{me.username} - Pyrogram v{__version__} (Layer {layer}) - Started..."
        )
        await idle()
        print(f"{me.first_name} - @{me.username} - Stopped !!!")


if __name__ == "__main__":
    loop.run_until_complete(main())
