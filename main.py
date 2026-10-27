import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand, BotCommandScopeDefault, BotCommandScopeChat

from config import BOT_TOKEN, ADMIN_IDS
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
    # 1. Oddiy foydalanuvchilar menyusi (Admin va Ustoz buyruqlari umuman ko'rinmaydi)
    user_commands = [
        BotCommand(command="start", description="🏠 Asosiy menyu"),
        BotCommand(command="record", description="🎙 Ovoz yozish"),
        BotCommand(command="validate", description="🎧 Ovoz tekshirish va baholash"),
        BotCommand(command="speakers", description="👤 Spikerlarim"),
        BotCommand(command="collections", description="📂 Dataset to'plamlari"),
        BotCommand(command="mystats", description="📊 Mening hissam"),
        BotCommand(command="help", description="ℹ️ Qo'llanma va yordam"),
    ]
    await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())

    # 2. Faqat administratorlar uchun maxsus menyu (Admin paneli faqat ularga ko'rinadi)
    admin_commands = [
        BotCommand(command="start", description="🏠 Asosiy menyu"),
        BotCommand(command="record", description="🎙 Ovoz yozish"),
        BotCommand(command="validate", description="🎧 Ovoz tekshirish va baholash"),
        BotCommand(command="speakers", description="👤 Spikerlarim"),
        BotCommand(command="collections", description="📂 Dataset to'plamlari"),
        BotCommand(command="mystats", description="📊 Mening hissam"),
        BotCommand(command="admin", description="⚙️ Ustoz & Admin boshqaruv paneli"),
        BotCommand(command="help", description="ℹ️ Qo'llanma va yordam"),
    ]
    for admin_id in ADMIN_IDS:
        try:
            await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=admin_id))
        except Exception as e:
            logger.warning(f"Admin {admin_id} uchun shaxsiy komandalarni o'rnatishda xatolik: {e}")

    # 3. Bot haqida ma'lumotlar tablosi (foydalanuvchi botga kirganda ko'rinadigan qism)
    try:
        desc = (
            "🎙 O'zbek tili Ovozli Dataset Yig'ish Tizimi\n\n"
            "Sun'iy intellekt modellarini o'qitish uchun ovozlar platformasi.\n\n"
            "📂 Dataset To'plamlari:\n"
            "• 📖 Kitobiy / Neytral: ASR/STT uchun xolis o'qish\n"
            "• 😊 Quvnoq / Xursand: Ko'tarinki kayfiyatdagi ovoz\n"
            "• 😢 Yig'lamsirab / Mahzun: Hissiyotli g'amgin ovoz\n"
            "• 😠 G'azab / Asabiy: Jiddiylik va g'azab ohangi\n"
            "• 🗣 Buyruqlar: Smart-uy va robot yordamchilar\n\n"
            "🎧 Boshqa ishtirokchilar ovozini tekshirish va baholash.\n\n"
            "Boshlash uchun pastdagi «Boshlash» (Start) ni bosing!"
        )
        short_desc = "O'zbek tili sun'iy intellekt modellarini o'qitish uchun ovozli dataset yig'ish va xolis tekshirish boti."
        await bot.set_my_description(description=desc)
        await bot.set_my_short_description(short_description=short_desc)
    except Exception as e:
        logger.warning(f"Bot tavsifini o'rnatishda xatolik: {e}")


async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN aniqlanmadi! Iltimos, .env faylini tekshiring.")
        return

    logger.info("Ma'lumotlar bazasi initsializatsiya qilinmoqda...")
    await init_db()
    logger.info("Ma'lumotlar bazasi tayyor!")

    # Aiogram 3.x bot va dispatcher (SSL va Windows tarmoq muammolarini bartaraf etuvchi barqaror sozlamalar)
    import socket
    from aiogram.client.session.aiohttp import AiohttpSession
    session = AiohttpSession()
    session._connector_init['ssl'] = False
    session._connector_init['family'] = socket.AF_INET
    session._connector_init['limit'] = 50
    session._connector_init['keepalive_timeout'] = 30

    bot = Bot(
        token=BOT_TOKEN,
        session=session,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Routerni ulash
    dp.include_router(setup_routers())

    # Eski update larni tozalab, barqaror polling boshlash (avtomatik qayta ulanish bilan)
    while True:
        try:
            logger.info("Telegram bilan aloqa o'rnatilmoqda...")
            try:
                await set_bot_commands(bot)
            except Exception as cmd_err:
                logger.warning(f"Komandalar menyusini o'rnatishda vaqtincha xatolik: {cmd_err}")

            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("Bot muvaffaqiyatli ishga tushdi! Polling boshlanmoqda...")
            await dp.start_polling(
                bot,
                polling_timeout=20,
                handle_signals=False if sys.platform == "win32" else True
            )
            break
        except (KeyboardInterrupt, SystemExit):
            logger.info("Bot to'xtatildi.")
            break
        except Exception as e:
            logger.error(f"Tarmoq uzilishi yoki ulanish xatoligi: {e}. 5 soniyadan so'ng qayta ulanadi...")
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
