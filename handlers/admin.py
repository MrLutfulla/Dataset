import os
import io
import csv
import json
import zipfile
from pathlib import Path
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from config import BASE_DIR, AUDIOS_DIR
from database import (
    is_admin,
    get_overall_stats,
    get_all_users,
    find_users_by_query,
    get_user,
    set_user_role,
    get_categories,
    get_category,
    add_category,
    add_prompts_bulk,
    get_export_dataset_rows,
    get_speakers_by_filter,
    get_speaker
)
from keyboards.inline import (
    get_admin_inline_keyboard,
    get_dataset_export_menu_keyboard,
    get_admin_users_menu_keyboard,
    get_user_role_toggle_keyboard,
    get_speaker_card_keyboard,
    get_category_selection_for_upload
)

router = Router()


class AdminSG(StatesGroup):
    waiting_for_user_search = State()
    waiting_for_prompts_file = State()
    waiting_for_col_title = State()
    waiting_for_col_desc = State()
    waiting_for_col_prompts = State()


@router.message(F.text == "⚙️ Admin Panel")
@router.message(Command("admin"))
async def show_admin_panel(message: Message):
    if not await is_admin(message.from_user.id):
        await message.answer("⛔️ Kechirasiz, ushbu bo'lim faqat bot administratorlari (ustoz) uchun!")
        return

    text = (
        "⚙️ <b>Ustoz & Administrator Boshqaruv Markazi</b>\n\n"
        "Quyidagi boshqaruv bo'limlaridan birini tanlang:\n\n"
        "• <b>📊 Jonli Statistika:</b> Jami userlar, jinslar/yoshlar nisbati, audio soatlari;\n"
        "• <b>📦 Datasetni ZIP Yuklash:</b> Umumiy yoki to'plam/spiker bo'yicha alohida yuklash;\n"
        "• <b>👥 Foydalanuvchilar & Guruhlar:</b> Jins, yosh bo'yicha filtrlash, qidiruv va datasetlarini yuklash;\n"
        "• <b>➕ Yangi To'plam Yaratish:</b> Yangi mavzu ochish va ichiga so'z/matnlar kiritish;\n"
        "• <b>📝 Matnlar Qo'shish:</b> Mavjud to'plamlarga qo'shimcha jumlalar kiritish."
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_admin_inline_keyboard())


@router.callback_query(F.data == "admin_menu")
async def back_to_admin_menu(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return
    await state.clear()
    text = "⚙️ <b>Ustoz & Administrator Boshqaruv Markazi</b>"
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_inline_keyboard())
    await callback.answer()


# ==================== JONLI STATISTIKA ====================

@router.callback_query(F.data == "admin_stats")
async def show_admin_stats(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    stats = await get_overall_stats()
    gender_info = ""
    for g, cnt in stats["gender_dist"].items():
        icon = "👨 Erkak" if g == "male" else "👩 Ayol"
        gender_info += f"  • {icon}: {cnt} ta\n"
    if not gender_info:
        gender_info = "  • Ma'lumot yo'q\n"

    cat_info = ""
    for c in stats["cat_dist"]:
        cat_info += f"  • {c['title']}: {c['cnt']} ta WAV audio\n"
    if not cat_info:
        cat_info = "  • Hozircha tasdiqlangan ovozlar yo'q\n"

    minutes = round(stats["total_duration"] / 60, 1)

    text = (
        "📊 <b>DATASET TIZIMI JONLI STATISTIKASI:</b>\n\n"
        f"👥 <b>Foydalanuvchilar (Telegram):</b> {stats['total_users']} ta\n"
        f"🎙 <b>Ro'yxatdan o'tgan spikerlar:</b> {stats['total_speakers']} ta\n"
        f"<b>Jinslar taqsimoti:</b>\n{gender_info}\n"
        f"🏆 <b>To'liq yakunlangan sessiyalar:</b> {stats['completed_sessions']} ta\n"
        f"📁 <b>Datasetdagi jami tasdiqlangan ovozlar:</b> {stats['total_recordings']} ta (.wav)\n"
        f"⏱ <b>Umumiy audio davomiyligi:</b> {stats['total_duration']} sek (~{minutes} daqiqa)\n"
        f"⚠️ <b>Chala qolgan / bekor qilingan:</b> {stats['abandoned_sessions']} ta\n\n"
        f"<b>To'plamlar bo'yicha to'plangan ovozlar:</b>\n{cat_info}"
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_inline_keyboard())
    await callback.answer()


# ==================== DATASET ZIP YUKLASH (MENYU VA FILTRLAR) ====================

@router.callback_query(F.data == "admin_export_menu")
async def show_export_menu(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    categories = await get_categories()
    text = (
        "📦 <b>Datasetni ZIP Ko'rinishida Yuklab Olish:</b>\n\n"
        "Barcha audio fayllar standart <b>16kHz mono .WAV</b> formatida, "
        "har birining metama'lumoti (spiker, yosh, jins, o'qilgan matn) esa "
        "<b>metadata.csv</b> hamda <b>metadata.jsonl</b> da to'liq arxivlanadi.\n\n"
        "Qaysi to'plamni yuklamoqchisiz? Tanlang:"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_dataset_export_menu_keyboard(categories))
    await callback.answer()


@router.callback_query(F.data.startswith("export_zip:"))
async def handle_export_zip(callback: CallbackQuery, bot: Bot):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    action = callback.data.split(":")[1]
    cat_id = None
    user_id = None
    speaker_id = None
    title_label = "Umumiy Barcha Dataset"

    if action == "all":
        title_label = "Barcha To'plamlar (Umumiy)"
    elif action.startswith("cat_"):
        cat_id = int(action.split("_")[1])
        c = await get_category(cat_id)
        title_label = f"To'plam: {c['title']}" if c else "To'plam"
    elif action.startswith("user_"):
        user_id = int(action.split("_")[1])
        u = await get_user(user_id)
        title_label = f"Foydalanuvchi: {u.get('first_name')}" if u else "Foydalanuvchi"
    elif action.startswith("speaker_"):
        speaker_id = int(action.split("_")[1])
        sp = await get_speaker(speaker_id)
        title_label = f"Spiker: {sp.get('name')} ({sp.get('age')} yosh)" if sp else "Spiker"

    await generate_and_send_zip(callback, bot, cat_id=cat_id, user_id=user_id, speaker_id=speaker_id, label=title_label)


async def generate_and_send_zip(callback: CallbackQuery, bot: Bot, cat_id=None, user_id=None, speaker_id=None, label="Dataset"):
    await callback.answer("Arxivlanmoqda, kuting...", show_alert=False)
    status_msg = await callback.message.answer(f"⏳ <i>«{label}» dataseti arxivlanmoqda va metama'lumotlar (.wav) tayyorlanmoqda...</i>", parse_mode="HTML")

    rows = await get_export_dataset_rows(category_id=cat_id, user_id=user_id, speaker_id=speaker_id)
    if not rows:
        await status_msg.edit_text(
            f"⚠️ <b>«{label}» bo'yicha eksport qilish uchun to'liq yakunlangan sessiyalar topilmadi!</b>\n\n"
            "Foydalanuvchilar kamida 1 ta to'liq sessiyani (5 ta matn) yakunlashi kerak.",
            parse_mode="HTML"
        )
        return

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"dataset_{timestamp_str}.zip"
    temp_zip_path = BASE_DIR / zip_filename

    csv_output = io.StringIO()
    writer = csv.writer(csv_output)
    writer.writerow([
        "recording_id",
        "audio_file",
        "prompt_text",
        "category_code",
        "category_title",
        "speaker_name",
        "speaker_gender",
        "speaker_age",
        "telegram_user_id",
        "session_id",
        "duration_seconds",
        "file_size_bytes",
        "created_at"
    ])

    jsonl_lines = []

    with zipfile.ZipFile(temp_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for r in rows:
            rel_file = r["file_path"]
            full_audio_path = BASE_DIR / rel_file
            arc_name = f"audios/{Path(rel_file).name}"

            if full_audio_path.exists():
                zipf.write(full_audio_path, arcname=arc_name)

            writer.writerow([
                r["recording_id"],
                arc_name,
                r["prompt_text"],
                r["category_code"],
                r["category_title"],
                r["speaker_name"],
                r["speaker_gender"],
                r["speaker_age"],
                r["telegram_user_id"],
                r["session_id"],
                r["duration"],
                r["file_size"],
                r["created_at"]
            ])

            jsonl_lines.append(json.dumps({
                "recording_id": r["recording_id"],
                "audio_file": arc_name,
                "text": r["prompt_text"],
                "category": r["category_code"],
                "speaker": {
                    "name": r["speaker_name"],
                    "gender": r["speaker_gender"],
                    "age": r["speaker_age"]
                },
                "duration": r["duration"],
                "created_at": r["created_at"]
            }, ensure_ascii=False))

        zipf.writestr("metadata.csv", ("\ufeff" + csv_output.getvalue()).encode("utf-8"))
        zipf.writestr("metadata.jsonl", "\n".join(jsonl_lines).encode("utf-8"))

    try:
        doc = FSInputFile(temp_zip_path, filename=zip_filename)
        caption = (
            f"📦 <b>{label} Arxiv Muvaffaqiyatli Tayyorlandi!</b>\n\n"
            f"📁 <b>Jami WAV fayllar:</b> {len(rows)} ta (16kHz mono)\n"
            f"📑 <b>Format:</b> Common Voice / Hugging Face standarti\n"
            f"📄 <b>Tarkibi:</b> `audios/` (.wav) + `metadata.csv` + `metadata.jsonl`\n"
            f"⏰ <b>Vaqt:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        await bot.send_document(chat_id=callback.from_user.id, document=doc, caption=caption, parse_mode="HTML")
        await status_msg.delete()
    finally:
        if temp_zip_path.exists():
            try:
                os.remove(temp_zip_path)
            except Exception:
                pass


# ==================== FOYDALANUVCHILAR VA GURUHLAR ====================

@router.callback_query(F.data == "admin_users_menu")
async def show_admin_users_menu(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return
    await state.clear()
    text = (
        "👥 <b>Foydalanuvchilar va Guruhlar Boshqaruvi:</b>\n\n"
        "Foydalanuvchi va spikerlarni jins yoki yosh toifalari bo'yicha ko'rishingiz, "
        "ularning alohida yig'gan datasetini ZIP qilib yuklab olishingiz mumkin.\n\n"
        "Quyidagi filtrlardan birini tanlang:"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_users_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "admin_list_all_users")
async def list_all_users_cb(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    users = await get_all_users(limit=20)
    text = "👥 <b>Barcha Ro'yxatdan O'tgan Foydalanuvchilar:</b>\n\n"
    buttons = []

    for u in users:
        role_badge = "👑 Admin" if u["role"] in ("admin", "superadmin") else "👤 User"
        uname = f"@{u['username']}" if u["username"] else "Username yo'q"
        text += (
            f"• <b>{u['first_name']}</b> ({uname})\n"
            f"  ID: <code>{u['user_id']}</code> | Roli: <b>{role_badge}</b>\n"
            f"  Spikerlar: {u['speakers_count']} ta | Yakunlangan: {u['completed_sessions']} ta\n\n"
        )
        buttons.append([
            InlineKeyboardButton(text=f"👤 {u['first_name']} ({u['user_id']})", callback_data=f"view_user:{u['user_id']}")
        ])

    buttons.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_users_menu")])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("admin_filter:"))
async def handle_speaker_filters(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    filter_type = callback.data.split(":")[1]
    gender = None
    min_age = None
    max_age = None
    label = ""

    if filter_type == "gender_male":
        gender = "male"
        label = "👨 Erkak Spikerlar"
    elif filter_type == "gender_female":
        gender = "female"
        label = "👩 Ayol Spikerlar"
    elif filter_type == "age_teen":
        max_age = 17
        label = "👶 O'smirlar (<18 yosh)"
    elif filter_type == "age_youth":
        min_age = 18
        max_age = 25
        label = "🧑 Yoshlar (18-25 yosh)"
    elif filter_type == "age_adult":
        min_age = 26
        max_age = 40
        label = "👨‍💼 O'rta Yosh (26-40 yosh)"
    elif filter_type == "age_senior":
        min_age = 41
        label = "🧓 Katta Yosh (40+ yosh)"

    speakers = await get_speakers_by_filter(gender=gender, min_age=min_age, max_age=max_age)

    if not speakers:
        text = f"📂 <b>{label}:</b>\n\nUshbu filtr bo'yicha hali birorta spiker topilmadi."
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_users_menu")]])
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
        await callback.answer()
        return

    text = f"📂 <b>{label} ro'yxati ({len(speakers)} ta):</b>\n\n"
    buttons = []

    for sp in speakers[:15]:
        g_icon = "👨" if sp["gender"] == "male" else "👩"
        owner_uname = f"@{sp['username']}" if sp["username"] else sp["user_first_name"]
        text += (
            f"• {g_icon} <b>{sp['name']}</b> ({sp['age']} yosh)\n"
            f"  Telegram: {owner_uname} (ID: <code>{sp['user_id']}</code>)\n"
            f"  Tasdiqlangan ovozlar: <b>{sp['recordings_count']} ta</b> | Sessiyalar: <b>{sp['completed_sessions']} ta</b>\n\n"
        )
        buttons.append([
            InlineKeyboardButton(text=f"📥 {sp['name']} datasetini yuklash", callback_data=f"export_zip:speaker_{sp['id']}")
        ])

    buttons.append([InlineKeyboardButton(text="⬅️ Ortga", callback_data="admin_users_menu")])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))
    await callback.answer()


@router.callback_query(F.data.startswith("view_user:"))
async def view_user_detail(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    user_id = int(callback.data.split(":")[1])
    u = await get_user(user_id)
    if not u:
        await callback.answer("Foydalanuvchi topilmadi!", show_alert=True)
        return

    role_badge = "👑 Administrator" if u["role"] in ("admin", "superadmin") else "👤 Oddiy foydalanuvchi"
    uname = f"@{u['username']}" if u["username"] else "Username yo'q"

    text = (
        "👤 <b>Foydalanuvchi Tafsilotlari:</b>\n\n"
        f"• <b>Ismi:</b> {u['first_name']}\n"
        f"• <b>Username:</b> {uname}\n"
        f"• <b>Telegram ID:</b> <code>{u['user_id']}</code>\n"
        f"• <b>Hozirgi roli:</b> {role_badge}\n"
        f"• <b>Qo'shilgan vaqti:</b> {u['created_at']}\n\n"
        "Quyidagi amallardan birini tanlang:"
    )
    kb = get_user_role_toggle_keyboard(u["user_id"], u["role"])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "admin_search_user")
async def prompt_search_user(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    await state.set_state(AdminSG.waiting_for_user_search)
    text = (
        "🔍 <b>Foydalanuvchi Qidiruvi:</b>\n\n"
        "Iltimos, izlanayotgan foydalanuvchining <b>Telegram ID sini</b> yoki <b>@username</b>ini chatga yozing:"
    )
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.message(AdminSG.waiting_for_user_search)
async def process_user_search(message: Message, state: FSMContext):
    query = message.text.strip()
    users = await find_users_by_query(query)

    if not users:
        await message.answer(
            f"🔍 <code>{query}</code> bo'yicha foydalanuvchi topilmadi.\n"
            "Foydalanuvchi avval botga /start bosgan bo'lishi kerak.\n\n"
            "Qaytadan ID yoki @username kiriting yoki /admin buyrug'ini bering:"
        )
        return

    u = users[0]
    await state.clear()

    role_badge = "👑 Administrator" if u["role"] in ("admin", "superadmin") else "👤 Oddiy foydalanuvchi"
    uname = f"@{u['username']}" if u["username"] else "Username yo'q"

    text = (
        "👤 <b>Topilgan foydalanuvchi:</b>\n\n"
        f"• <b>Ismi:</b> {u['first_name']}\n"
        f"• <b>Username:</b> {uname}\n"
        f"• <b>Telegram ID:</b> <code>{u['user_id']}</code>\n"
        f"• <b>Hozirgi roli:</b> {role_badge}\n"
        f"• <b>Qo'shilgan vaqti:</b> {u['created_at']}\n\n"
        "Quyidagi amallardan birini tanlang:"
    )
    kb = get_user_role_toggle_keyboard(u["user_id"], u["role"])
    await message.answer(text, parse_mode="HTML", reply_markup=kb)


@router.callback_query(F.data.startswith("set_role:"))
async def handle_set_role(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    parts = callback.data.split(":")
    target_id = int(parts[1])
    new_role = parts[2]

    if target_id == callback.from_user.id and new_role == "user":
        await callback.answer("O'zingizning admin rolingizni o'chira olmaysiz!", show_alert=True)
        return

    await set_user_role(target_id, new_role)
    target_user = await get_user(target_id)

    role_badge = "👑 Administrator" if new_role == "admin" else "👤 Oddiy foydalanuvchi"
    await callback.message.edit_text(
        f"✅ <b>Foydalanuvchi roli yangilandi!</b>\n\n"
        f"• <b>ID:</b> <code>{target_id}</code>\n"
        f"• <b>Ismi:</b> {target_user.get('first_name')}\n"
        f"• <b>Yangi roli:</b> {role_badge}",
        parse_mode="HTML",
        reply_markup=get_user_role_toggle_keyboard(target_id, new_role)
    )
    await callback.answer("Rol saqlandi!")


# ==================== YANGI TO'PLAM YARATISH (ADMIN UCHUN) ====================

@router.callback_query(F.data == "admin_create_collection")
async def start_create_collection(callback: CallbackQuery, state: FSMContext):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    await state.set_state(AdminSG.waiting_for_col_title)
    text = (
        "➕ <b>Yangi To'plam Yaratish (1-qadam / 3)</b>\n\n"
        "Iltimos, yangi to'plamning <b>Nomini</b> kiriting:\n"
        "<i>Masalan: Tibbiyot terminlari, Shevalar, Bolalar ertaklari yoki Smart-uy buyruqlari</i>"
    )
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.message(AdminSG.waiting_for_col_title)
async def process_col_title(message: Message, state: FSMContext):
    title = message.text.strip()
    if len(title) < 3 or len(title) > 60:
        await message.answer("Iltimos, 3 tadan 60 tagacha belgidan iborat nom kiriting:")
        return

    await state.update_data(title=title)
    await state.set_state(AdminSG.waiting_for_col_desc)
    await message.answer(
        f"📁 To'plam nomi: <b>{title}</b>\n\n"
        "<b>2-qadam / 3:</b> Ushbu to'plam uchun qisqa <b>tavsif yoki yo'riqnoma</b> kiriting:\n"
        "<i>Masalan: Tibbiyot sohasiga oid atamalarni xolis va aniq o'qish</i>",
        parse_mode="HTML"
    )


@router.message(AdminSG.waiting_for_col_desc)
async def process_col_desc(message: Message, state: FSMContext):
    desc = message.text.strip()
    await state.update_data(description=desc)
    await state.set_state(AdminSG.waiting_for_col_prompts)

    data = await state.get_data()
    title = data["title"]

    await message.answer(
        f"📁 To'plam: <b>{title}</b>\n"
        f"📝 Tavsif: <i>{desc}</i>\n\n"
        "<b>3-qadam / 3:</b> Endi ushbu to'plam uchun <b>matnlar yoki so'zlarni</b> yuklang:\n\n"
        "1. 📄 <b>.txt fayl qilib yuborish</b> (har bir qator alohida matn);\n"
        "2. ✍️ <b>Matn xabar sifatida yozish</b> (har bir jumla yangi qatordan).\n\n"
        "<i>Matnlarni yuboring:</i>",
        parse_mode="HTML"
    )


@router.message(AdminSG.waiting_for_col_prompts)
async def process_col_prompts(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    title = data["title"]
    desc = data["description"]

    lines = []
    if message.document:
        doc = message.document
        if not doc.file_name.endswith((".txt", ".csv")):
            await message.answer("⚠️ Iltimos, faqat `.txt` yoki `.csv` formatdagi fayl yuboring!")
            return

        file_obj = await bot.get_file(doc.file_id)
        file_bytes = await bot.download_file(file_obj.file_path)
        content = file_bytes.read().decode("utf-8", errors="ignore")
        lines = [line.strip() for line in content.splitlines() if line.strip()]

    elif message.text:
        lines = [line.strip() for line in message.text.splitlines() if line.strip()]

    if not lines:
        await message.answer("⚠️ Hech qanday matn topilmadi. Qaytadan yuboring:")
        return

    # Yangi to'plamni bazaga qo'shamiz
    cat_id = await add_category(code="", title=title, description=desc)
    added_count = await add_prompts_bulk(cat_id, lines)
    await state.clear()

    await message.answer(
        f"🎉 <b>Yangi To'plam Muvaffaqiyatli Yaratildi!</b>\n\n"
        f"📁 <b>Nomi:</b> {title}\n"
        f"📝 <b>Tavsif:</b> {desc}\n"
        f"📚 <b>Yuklangan matnlar soni:</b> {added_count} ta\n\n"
        "Endi ushbu to'plam barcha foydalanuvchilar uchun ovoz yozish ro'yxatida faol!",
        parse_mode="HTML",
        reply_markup=get_admin_inline_keyboard()
    )


# ==================== MAVJUD TO'PLAMGA MATN QO'SHISH ====================

@router.callback_query(F.data == "admin_upload_prompts")
async def choose_category_for_upload(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    categories = await get_categories()
    text = (
        "📝 <b>Mavjud To'plamga Matnlar Qo'shish:</b>\n\n"
        "Qaysi to'plamga yangi matnlar qo'shmoqchisiz? Tanlang:"
    )
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_category_selection_for_upload(categories))
    await callback.answer()


@router.callback_query(F.data.startswith("upload_to_cat:"))
async def ask_for_prompts(callback: CallbackQuery, state: FSMContext):
    cat_id = int(callback.data.split(":")[1])
    cat = await get_category(cat_id)

    await state.set_state(AdminSG.waiting_for_prompts_file)
    await state.update_data(target_category_id=cat_id, category_title=cat["title"])

    text = (
        f"📥 <b>To'plam: {cat['title']}</b>\n\n"
        "Matnlarni ikki xil usulda yuklashingiz mumkin:\n"
        "1. 📄 <b>.txt fayl qilib yuborish:</b> Har bir matn alohida qatorda;\n"
        "2. ✍️ <b>Xabar sifatida yozish:</b> Jumlalarni har birini yangi qatordan yozing.\n\n"
        "<i>Matnlarni yuboring:</i>"
    )
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.message(AdminSG.waiting_for_prompts_file)
async def process_prompts_input(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    cat_id = data["target_category_id"]
    cat_title = data["category_title"]

    lines = []
    if message.document:
        doc = message.document
        if not doc.file_name.endswith((".txt", ".csv")):
            await message.answer("⚠️ Iltimos, faqat `.txt` yoki `.csv` formatdagi fayl yuboring!")
            return

        file_obj = await bot.get_file(doc.file_id)
        file_bytes = await bot.download_file(file_obj.file_path)
        content = file_bytes.read().decode("utf-8", errors="ignore")
        lines = [line.strip() for line in content.splitlines() if line.strip()]

    elif message.text:
        lines = [line.strip() for line in message.text.splitlines() if line.strip()]

    if not lines:
        await message.answer("⚠️ Hech qanday matn topilmadi. Qaytadan yuboring:")
        return

    added_count = await add_prompts_bulk(cat_id, lines)
    await state.clear()

    await message.answer(
        f"🎉 <b>Muvaffaqiyatli saqlandi!</b>\n\n"
        f"📁 <b>To'plam:</b> {cat_title}\n"
        f"📝 <b>Qo'shilgan yangi matnlar soni:</b> {added_count} ta\n\n"
        "Matnlar bazaga qo'shildi.",
        parse_mode="HTML",
        reply_markup=get_admin_inline_keyboard()
    )
