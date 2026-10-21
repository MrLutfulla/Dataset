import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand, BotCommandScopeDefault

from config import BOT_TOKEN
from database import init_db
from handlers import setup_routers

# Loglarni sozlash
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("VoiceDatasetBot")


async def set_bot_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="🏠 Asosiy menyu"),
        BotCommand(command="record", description="🎙 Ovoz yozish (to'plam tanlash)"),
        BotCommand(command="speakers", description="👤 Spikerlarim (odam almashtirish/qo'shish)"),
        BotCommand(command="collections", description="📂 Dataset to'plamlari"),
        BotCommand(command="mystats", description="📊 Mening hissam va statistikam"),
        BotCommand(command="admin", description="⚙️ Ustoz & Admin boshqaruv paneli"),
        BotCommand(command="help", description="ℹ️ Qo'llanma va yordam"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())


async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN aniqlanmadi! Iltimos, .env faylini tekshiring.")
        return

    logger.info("Ma'lumotlar bazasi initsializatsiya qilinmoqda...")
    await init_db()
    logger.info("Ma'lumotlar bazasi tayyor!")

    # Aiogram 3.x bot va dispatcher (SSL xatoliklarini oldini olish uchun xavfsiz connector)
    from aiogram.client.session.aiohttp import AiohttpSession
    session = AiohttpSession()
    session._connector_init['ssl'] = False

    bot = Bot(
        token=BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Routerni ulash
    dp.include_router(setup_routers())

    # Telegram komandalar menyusini o'rnatish
    await set_bot_commands(bot)

    logger.info("Bot muvaffaqiyatli ishga tushdi! Polling boshlanmoqda...")
    # Eski update larni tashlab yuborish
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
