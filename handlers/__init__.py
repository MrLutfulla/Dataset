from aiogram import Router
from aiogram.types import Message
from database import is_admin
from keyboards.main_menu import get_main_keyboard
from handlers.start import router as start_router
from handlers.admin import router as admin_router
from handlers.speakers import router as speakers_router
from handlers.categories import router as categories_router
from handlers.validation import router as validation_router
from handlers.recording import router as recording_router

fallback_router = Router()


@fallback_router.message()
async def process_unhandled_message(message: Message):
    admin_status = await is_admin(message.from_user.id)
    kb = get_main_keyboard(is_admin=admin_status)
    await message.answer(
        "ℹ️ Buyruq tushunarsiz.\n\n"
        "Kerakli bo'limni tanlash uchun quyidagi menyu tugmalaridan foydalaning:",
        parse_mode="HTML",
        reply_markup=kb
    )


def setup_routers() -> Router:
    main_router = Router()
    # 1. Start va umumiy komandalar
    main_router.include_router(start_router)
    # 2. Admin boshqaruv paneli (yuqori ustuvorlikda)
    main_router.include_router(admin_router)
    # 3. Spikerlar va to'plamlar
    main_router.include_router(speakers_router)
    main_router.include_router(categories_router)
    # 4. Tekshiruv va ovoz yozish
    main_router.include_router(validation_router)
    main_router.include_router(recording_router)
    # 5. Faqat hech qaysi handler ushlay olmagan noma'lum xabarlar uchun oxirgi fallback
    main_router.include_router(fallback_router)
    return main_router
