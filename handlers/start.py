from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from database import get_or_create_user, get_user_stats, is_admin, get_speaker
from keyboards.main_menu import get_main_keyboard

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = await get_or_create_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )
    admin_status = await is_admin(message.from_user.id)
    kb = get_main_keyboard(is_admin=admin_status)

    speaker_info = "Belgilanmagan (avval spiker qo'shing)"
    if user.get("active_speaker_id"):
        sp = await get_speaker(user["active_speaker_id"])
        if sp:
            g_icon = "👨" if sp["gender"] == "male" else "👩"
            speaker_info = f"{g_icon} {sp['name']} ({sp['age']} yosh)"

    text = (
        f"Assalomu alaykum, <b>{message.from_user.first_name}</b>!\n\n"
        "🎙 <b>O'zbek tili Ovozli Dataset Yig'ish Botiga</b> xush kelibsiz!\n\n"
        "Ushbu bot ovozni matnga aylantirish (Speech-to-Text), sun'iy intellekt "
        "til modellarini o'qitish va ovozdagi hissiyotlar hamda yosh/jinsni aniqlash uchun "
        "yuqori sifatli dataset yig'ishga xizmat qiladi.\n\n"
        "📌 <b>Imkoniyatlar:</b>\n"
        "• Bitta profildan bir nechta spikerlar (oila a'zolari, do'stlar) nomidan ovoz yozish;\n"
        "• Turli toifalar (kitobiy, quvnoq, xafa, asabiy, buyruqlar);\n"
        "• To'liq yakunlangan sessiyalarni sifatli arxivlash.\n\n"
        f"👤 <b>Hozirgi faol spiker:</b> {speaker_info}\n\n"
        "Boshlash uchun pastdagi <b>🎙 Ovoz yozish</b> yoki <b>👤 Spikerlarim</b> tugmasini bosing!"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=kb)


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
        "4. <b>📦 Sessiya qoidasi:</b> Har bir to'plamdagi barcha buyruqlar (20 ta buyruq) to'liq ketma-ket o'qiladi. Barcha ovozlar toza 16kHz WAV formatida saqlanadi!\n\n"
        "⚙️ <b>Tezkor buyruqlar:</b>\n"
        "/record — Ovoz yozishni boshlash (to'plam tanlash)\n"
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
        f"⏱ <b>Umumiy audio davomiyligi:</b> {stats['total_duration']} soniya\n\n"
        "<i>Sun'iy intellektimiz rivojiga qo'shayotgan hissangiz uchun rahmat!</i>"
    )
    await message.answer(text, parse_mode="HTML")
