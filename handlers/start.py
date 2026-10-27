import html
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from database import (
    get_or_create_user,
    get_user_stats,
    is_admin,
    get_speaker,
    get_speakers_by_user,
    cancel_session
)
from keyboards.main_menu import get_main_keyboard
from handlers.speakers import AddSpeakerSG

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    # Har qanday eski holat yoki chala sessiyani tozalaymiz
    data = await state.get_data()
    session_id = data.get("session_id")
    if session_id:
        await cancel_session(session_id)
    await state.clear()

    user = await get_or_create_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )
    admin_status = await is_admin(message.from_user.id)
    speakers = await get_speakers_by_user(message.from_user.id)

    # 1. Agar foydalanuvchida hali birorta ham spiker bo'lmasa, darhol ro'yxatdan o'tkazamiz
    if not speakers:
        await state.set_state(AddSpeakerSG.waiting_for_name)
        user_name = html.escape(message.from_user.first_name or "Ismingiz")
        text = (
            f"Assalomu alaykum, <b>{user_name}</b>!\n\n"
            "🎙 <b>O'zbek tili Ovozli Dataset Yig'ish Botiga xush kelibsiz!</b>\n\n"
            "Ovoz yozish va sun'iy intellekt modellarini o'qitishda ishtirok etish uchun "
            "avval <b>boshlang'ich diktor (spiker) profilingizni</b> ro'yxatdan o'tkazamiz.\n\n"
            "📝 <b>1-qadam (1/5):</b> Iltimos, o'zingizning <b>Ismingizni</b> (yoki laqab/taxallusingizni) yozib yuboring:\n"
            f"<i>Masalan: {user_name}</i>"
        )
        await message.answer(text, parse_mode="HTML")
        return

    # 2. Agar foydalanuvchida spiker mavjud bo'lsa, asosiy menyuni chiqaramiz
    kb = get_main_keyboard(is_admin=admin_status)

    active_sp = None
    if user.get("active_speaker_id"):
        active_sp = await get_speaker(user["active_speaker_id"])
    if not active_sp and speakers:
        active_sp = speakers[0]

    g_icon = "👨" if active_sp and active_sp.get("gender") in ("male", "erkak") else "👩"
    spk_tag = f"spk{active_sp['id']:03d}" if active_sp else "spk001"
    speaker_info = f"{g_icon} {active_sp['name']} ({active_sp['age']} yosh, <code>{spk_tag}</code>)"

    text = (
        f"Assalomu alaykum, <b>{html.escape(message.from_user.first_name or 'Foydalanuvchi')}</b>!\n\n"
        "🎙 <b>O'zbek tili Ovozli Dataset Yig'ish Tizimi</b>\n\n"
        f"👤 <b>Hozirgi faol spiker:</b> {speaker_info}\n\n"
        "Quyidagi menyu tugmalaridan birini tanlang:\n"
        "• <b>🎙 Ovoz yozish:</b> 20 ta robot buyruqlarini ketma-ket yozish;\n"
        "• <b>🎧 Ovoz tekshirish:</b> Boshqa ishtirokchilar ovozini tinglab baholash;\n"
        "• <b>👤 Spikerlarim:</b> Oila a'zolaringiz yoki do'stlaringiz nomidan yangi spikerlar qo'shish;\n"
        "• <b>📊 Mening hissam:</b> Siz kiritgan ovozlar va tekshiruvlar statistikasi."
    )
    await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.message(F.text == "🏠 Asosiy menyu")
@router.message(Command("cancel"))
async def cmd_cancel_and_home(message: Message, state: FSMContext):
    data = await state.get_data()
    session_id = data.get("session_id")
    if session_id:
        await cancel_session(session_id)
    await state.clear()
    admin_status = await is_admin(message.from_user.id)
    kb = get_main_keyboard(is_admin=admin_status)
    await message.answer("🏠 Asosiy menyudasiz. Kerakli bo'limni tanlang:", reply_markup=kb)


@router.message(Command("help"))
async def cmd_help(message: Message):
    admin_status = await is_admin(message.from_user.id)
    kb = get_main_keyboard(is_admin=admin_status)

    text = (
        "📖 <b>Botdan foydalanish bo'yicha qo'llanma:</b>\n\n"
        "1. <b>👤 Spikerlarim:</b> Ovoz yozayotgan insonning ismi, jinsi va yoshini kiriting. "
        "Bitta telefondan istalgancha odam uchun alohida profil ochishingiz mumkin.\n"
        "2. <b>📂 To'plamlar:</b> Qaysi yo'nalishda (kitobiy, hissiyotli yoki buyruqlar) ovoz yozishni ko'rishingiz mumkin.\n"
        "3. <b>🎙 Ovoz yozish:</b> Bosganda to'plamni tanlaysiz va berilgan matnlarni ketma-ket mikrofon orqali o'qib yuborasiz.\n"
        "4. <b>🎧 Ovoz tekshirish:</b> Boshqa ishtirokchilar yozgan ovozlarni anonim tarzda tinglab, matnga mosligi va sifatini baholaysiz.\n"
        "5. <b>📦 Sessiya qoidasi:</b> Har bir to'plamdagi barcha buyruqlar (20 ta buyruq) to'liq ketma-ket o'qiladi. Barcha ovozlar toza 16kHz WAV formatida saqlanadi!\n\n"
        "⚙️ <b>Tezkor buyruqlar:</b>\n"
        "/record — Ovoz yozishni boshlash\n"
        "/validate — Ovoz tekshirish va baholash\n"
        "/speakers — Spikerlar boshqaruvi\n"
        "/collections — To'plamlar ro'yxati\n"
        "/mystats — Shaxsiy hissa statistikasi\n"
    )
    if admin_status:
        text += "/admin — Ustoz va admin boshqaruv paneli\n"

    await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.message(F.text == "📊 Mening hissam")
@router.message(Command("mystats"))
async def cmd_my_stats(message: Message):
    stats = await get_user_stats(message.from_user.id)
    text = (
        f"📊 <b>{message.from_user.first_name}ning hissasi:</b>\n\n"
        f"👥 <b>Yaratilgan spikerlar soni:</b> {stats['speakers_count']} ta\n"
        f"🏆 <b>To'liq yakunlangan sessiyalar:</b> {stats['completed_sessions']} ta\n"
        f"🎙 <b>Tasdiqlangan ovozlar:</b> {stats['total_recordings']} ta\n"
        f"🎧 <b>Tekshirib baholangan ovozlar:</b> {stats.get('validated_count', 0)} ta\n"
        f"⏱ <b>Umumiy audio davomiyligi:</b> {stats['total_duration']} soniya\n\n"
        "<i>Sun'iy intellektimiz rivojiga qo'shayotgan hissangiz uchun rahmat!</i>"
    )
    await message.answer(text, parse_mode="HTML")
