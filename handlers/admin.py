import os
import io
import csv
import json
import zipfile
import html
from pathlib import Path
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from config import BASE_DIR, AUDIOS_DIR
from audio_converter import center_and_pad_to_1sec, analyze_wav_quality
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
    get_speaker,
    get_speech_commands_export_data,
    get_scientific_quality_audit,
    get_flagged_recordings_for_admin,
    add_validation
)
from keyboards.inline import (
    get_admin_inline_keyboard,
    get_dataset_export_menu_keyboard,
    get_admin_users_menu_keyboard,
    get_user_role_toggle_keyboard,
    get_speaker_card_keyboard,
    get_category_selection_for_upload,
    get_flagged_review_keyboard
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
async def show_admin_panel(message: Message, state: FSMContext = None):
    if state:
        await state.clear()

    if not await is_admin(message.from_user.id):
        await message.answer(
            "⛔️ <b>Ruxsat cheklangan!</b>\n\n"
            "Ushbu bo'lim faqat bot administratorlari (ustoz va mas'ullar) uchun mo'ljallangan.\n\n"
            f"👤 Sizning Telegram ID: <code>{message.from_user.id}</code>\n"
            "Agar siz guruh koordinatori yoki ustoz bo'lsangiz, ID raqamingizni bosh adminga taqdim eting.",
            parse_mode="HTML"
        )
        return

    text = (
        "⚙️ <b>Ustoz & Administrator Boshqaruv Markazi</b>\n\n"
        "Quyidagi boshqaruv va ilmiy tahlil bo'limlaridan birini tanlang:\n\n"
        "• <b>📊 Jonli Statistika:</b> Jami foydalanuvchilar, jins/yosh nisbati, audio soatlari;\n"
        "• <b>🔬 Ilmiy Sifat Tahlili:</b> Inter-annotator kelishuv, SNR, demografik muvozanat;\n"
        "• <b>⚠️ Shubhali Audiolar:</b> Noto'g'ri/sifatsiz deb ovoz berilgan yozuvlarni nazorat qilish;\n"
        "• <b>📦 Datasetni ZIP Yuklash:</b> Google Speech Commands (1.0s) yoki Hugging Face formati;\n"
        "• <b>👥 Foydalanuvchilar & Guruhlar:</b> Demografik guruhlar, qidiruv va filtrlash;\n"
        "• <b>➕ Yangi To'plam / Matnlar:</b> Mavzu ochish va jumlalar kiritish."
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
    val_data = stats.get("validation_stats", {})
    val_text = (
        f"🎧 <b>Ovozlar tekshiruvi (Validatsiya):</b>\n"
        f"  • Jami tekshiruvlar: {val_data.get('total_validations', 0)} ta\n"
        f"  • ✅ To'g'ri (mos): {val_data.get('correct_cnt', 0)} ta\n"
        f"  • ❌ Noto'g'ri: {val_data.get('incorrect_cnt', 0)} ta\n"
        f"  • ⚠️ Sifatsiz/Shovqinli: {val_data.get('low_quality_cnt', 0)} ta\n\n"
    )

    text = (
        "📊 <b>DATASET TIZIMI JONLI STATISTIKASI:</b>\n\n"
        f"👥 <b>Foydalanuvchilar (Telegram):</b> {stats['total_users']} ta\n"
        f"🎙 <b>Ro'yxatdan o'tgan spikerlar:</b> {stats['total_speakers']} ta\n"
        f"<b>Jinslar taqsimoti:</b>\n{gender_info}\n"
        f"🏆 <b>To'liq yakunlangan sessiyalar:</b> {stats['completed_sessions']} ta\n"
        f"📁 <b>Datasetdagi jami tasdiqlangan ovozlar:</b> {stats['total_recordings']} ta (.wav)\n"
        f"⏱ <b>Umumiy audio davomiyligi:</b> {stats['total_duration']} sek (~{minutes} daqiqa)\n"
        f"⚠️ <b>Chala qolgan / bekor qilingan:</b> {stats['abandoned_sessions']} ta\n\n"
        f"{val_text}"
        f"<b>To'plamlar bo'yicha to'plangan ovozlar:</b>\n{cat_info}"
    )

    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_inline_keyboard())
    await callback.answer()


# ==================== ILMIY SIFAT TAHLILI (SCIENTIFIC QUALITY AUDIT) ====================

@router.callback_query(F.data == "admin_scientific_audit")
async def show_scientific_audit(callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    audit = await get_scientific_quality_audit()

    male_recs = audit["gender_stats"].get("male", {}).get("recordings", 0)
    female_recs = audit["gender_stats"].get("female", {}).get("recordings", 0)
    tot_rec = max(1, audit["total_recordings"])
    m_pct = round(male_recs / tot_rec * 100, 1)
    f_pct = round(female_recs / tot_rec * 100, 1)

    age_str = ""
    for grp, dt in audit["age_stats"].items():
        if grp:
            age_str += f"  • {grp}: {dt['speakers']} spiker ({dt['recordings']} audio)\n"
    if not age_str:
        age_str = "  • Hozircha ma'lumot yetarli emas\n"

    v_pct = round(audit["verified_count"] / tot_rec * 100, 1)
    acc_pct = round(audit["accepted_count"] / tot_rec * 100, 1)
    rej_pct = round(audit["rejected_count"] / tot_rec * 100, 1)
    unrev_pct = round(audit["unreviewed_count"] / tot_rec * 100, 1)

    text = (
        "🔬 <b>ILMIY DATASET SIFAT VA METRIKALAR TAHLILI</b>\n\n"
        "⚡️ <b>Akustik va Audio Ko'rsatkichlari:</b>\n"
        f"  • Format: <b>16 kHz, 16-bit PCM, Mono .WAV</b>\n"
        f"  • Jami audio vaqti: <b>{audit['total_seconds']} sek (~{audit['total_hours']} soat)</b>\n"
        f"  • O'rtacha buyruq davomiyligi: <b>{audit['avg_duration']} soniya</b>\n"
        f"  • Faol spikerlar soni: <b>{audit['active_speakers']} nafar</b>\n\n"
        "👥 <b>Demografik Muvozanat (Demographic Balance):</b>\n"
        f"  • Jinslar nisbati: 👨 <b>{m_pct}% Erkak</b> | 👩 <b>{f_pct}% Ayol</b>\n"
        f"  • Yosh guruhlari taqsimoti:\n{age_str}\n"
        "🎯 <b>Crowdsourced Validatsiya & Kelishuv Indeksi:</b>\n"
        f"  • Tekshiruvchilar soni: <b>{audit['total_validators']} kishi</b>\n"
        f"  • Jami berilgan baholar: <b>{audit['total_votes']} ta</b>\n"
        f"  • <b>Inter-Annotator Consensus:</b> <code>{audit['consensus_rate']}%</code> (Ilmiy kelishuv)\n\n"
        "📊 <b>Dataset Sifat Holati (Quality Breakdown):</b>\n"
        f"  • 🌟 <b>Verified (2+ tasdiqlangan):</b> {audit['verified_count']} ta ({v_pct}%)\n"
        f"  • ✅ <b>Accepted (1 tasdiqlangan):</b> {audit['accepted_count']} ta ({acc_pct}%)\n"
        f"  • ⚠️ <b>Unreviewed (tekshirilmagan):</b> {audit['unreviewed_count']} ta ({unrev_pct}%)\n"
        f"  • ❌ <b>Rejected (shubhali/rad etilgan):</b> {audit['rejected_count']} ta ({rej_pct}%)\n\n"
        "<i>Tizim AI/ML modellarini (Speech-to-Text / Keyword Spotting) o'qitish standartlariga to'liq mos keladi.</i>"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚠️ Shubhali audiolarni ko'rish", callback_data="admin_review_flagged")],
        [InlineKeyboardButton(text="⬅️ Admin Menyu", callback_data="admin_menu")]
    ])
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()


# ==================== SHUBHALI AUDIOLAR NAZORATI ====================

@router.callback_query(F.data == "admin_review_flagged")
async def show_review_flagged_audio(callback: CallbackQuery, bot: Bot):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    flagged = await get_flagged_recordings_for_admin(limit=1)
    if not flagged:
        await callback.message.edit_text(
            "✅ <b>Shubhali yoki sifatsiz deb belgilangan audilar yo'q!</b>\n\n"
            "Barcha yozilgan ovozlar to'g'ri o'qilgan yoki tekshiruvchilarda e'tiroz tug'dirmagan.",
            parse_mode="HTML",
            reply_markup=get_admin_inline_keyboard()
        )
        await callback.answer("Shubhali ovozlar yo'q")
        return

    rec = flagged[0]
    rec_id = rec["recording_id"]
    caption = (
        "⚠️ <b>Ustoz Nazorati: Shubhali Audio Ekspertizasi</b>\n\n"
        f"📖 <b>Kutilgan matn:</b> « {html.escape(rec['prompt_text'])} »\n"
        f"🏷 <b>Spiker ID:</b> <code>spk{rec['speaker_id']:03d}</code>\n"
        f"📂 <b>To'plam:</b> {html.escape(rec.get('category_title', ''))}\n"
        f"⏱ <b>Davomiyligi:</b> {rec['duration']} soniya\n\n"
        "📊 <b>Tekshiruvchilar baholari:</b>\n"
        f"  • ✅ To'g'ri: {rec['val_correct']} ta\n"
        f"  • ❌ Noto'g'ri: {rec['val_incorrect']} ta\n"
        f"  • ⚠️ Sifatsiz: {rec['val_low_quality']} ta\n\n"
        "<i>Ushbu ovoz haqiqatdan ham matnga to'g'ri keladimi? Yakuniy qarorni tanlang:</i>"
    )

    kb = get_flagged_review_keyboard(rec_id)
    file_id = rec.get("file_id")
    file_path = BASE_DIR / rec["file_path"]

    sent = False
    if file_id:
        try:
            await bot.send_voice(chat_id=callback.from_user.id, voice=file_id, caption=caption, parse_mode="HTML", reply_markup=kb)
            sent = True
        except Exception:
            sent = False

    if not sent and file_path.exists():
        await bot.send_voice(chat_id=callback.from_user.id, voice=FSInputFile(file_path), caption=caption, parse_mode="HTML", reply_markup=kb)

    await callback.answer("Shubhali audio yuklandi")


@router.callback_query(F.data.startswith("flag_resolve:"))
async def handle_flag_resolve(callback: CallbackQuery, bot: Bot):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    parts = callback.data.split(":")
    rec_id = int(parts[1])
    decision = parts[2]

    if decision == "approve":
        await add_validation(rec_id, callback.from_user.id, "correct")
        await callback.answer("✅ Ustoz tomonidan tasdiqlandi!")
    else:
        await add_validation(rec_id, callback.from_user.id, "incorrect")
        await callback.answer("🗑 Ovoz sifatsiz deb topildi va rad etildi!")

    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await show_review_flagged_audio(callback, bot)


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


@router.callback_query(F.data == "export_speech_commands_zip")
async def handle_export_speech_commands_zip(callback: CallbackQuery, bot: Bot):
    if not await is_admin(callback.from_user.id):
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    await callback.answer("Google Speech Commands (uz_robot_cmd) arxivlanmoqda...", show_alert=False)
    status_msg = await callback.message.answer(
        "⏳ <i>«uz_robot_cmd» (Google Speech Commands standarti) bo'yicha audio fayllar 1 soniyaga keltirilmoqda va arxivlanmoqda...</i>",
        parse_mode="HTML"
    )

    data = await get_speech_commands_export_data()
    items = data["items"]
    speakers = data["speakers"]

    if not items:
        await status_msg.edit_text(
            "ℹ️ <b>Google Speech Commands («uz_robot_cmd») bo'yicha audio yozuvlar topilmadi.</b>\n\n"
            "Ushbu to'plam faqat 20 ta standart robot buyruqlari (`🗣 Qisqa Buyruqlar`) bo'yicha to'liq yakunlangan sessiyalardan olinadi.\n\n"
            "Mavjud umumiy ASR (kitobiy) datasetini yuklab olish uchun <b>«📦 Barcha Datasetlar (Umumiy ZIP)»</b> tugmasidan foydalaning.",
            parse_mode="HTML"
        )
        return

    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = f"uz_robot_cmd_{timestamp_str}.zip"
    temp_zip_path = BASE_DIR / zip_filename

    # 1. speakers.csv
    spk_csv_out = io.StringIO()
    spk_writer = csv.writer(spk_csv_out)
    spk_writer.writerow(["speaker_id", "jins", "yosh_guruhi", "hudud", "qurilma"])
    for sp in speakers:
        spk_writer.writerow([
            sp["speaker_id"],
            sp["jins"],
            sp["yosh_guruhi"],
            sp["hudud"],
            sp["qurilma"]
        ])

    # 2. splits.csv
    splits_csv_out = io.StringIO()
    splits_writer = csv.writer(splits_csv_out)
    splits_writer.writerow(["audio_path", "speaker_id", "command", "class_name", "split"])

    val_list = []
    test_list = []

    temp_process_dir = BASE_DIR / "temp_1sec_cache"
    temp_process_dir.mkdir(exist_ok=True)

    try:
        with zipfile.ZipFile(temp_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for it in items:
                orig_file = BASE_DIR / it["original_file_path"]
                if not orig_file.exists():
                    continue

                cached_wav = temp_process_dir / it["filename"]
                center_and_pad_to_1sec(orig_file, cached_wav, target_samples=16000)

                arc_name = f"uz_robot_cmd/{it['folder_name']}/{it['filename']}"
                zipf.write(cached_wav, arcname=arc_name)

                splits_writer.writerow([
                    f"{it['folder_name']}/{it['filename']}",
                    it["speaker_id"],
                    it["command"],
                    it.get("class_name", it["command"]),
                    it["split"]
                ])

                if it["split"] == "val":
                    val_list.append(f"{it['folder_name']}/{it['filename']}")
                elif it["split"] == "test":
                    test_list.append(f"{it['folder_name']}/{it['filename']}")

            zipf.writestr("uz_robot_cmd/speakers.csv", ("\ufeff" + spk_csv_out.getvalue()).encode("utf-8"))
            zipf.writestr("uz_robot_cmd/splits.csv", ("\ufeff" + splits_csv_out.getvalue()).encode("utf-8"))
            zipf.writestr("uz_robot_cmd/validation_list.txt", "\n".join(val_list).encode("utf-8"))
            zipf.writestr("uz_robot_cmd/testing_list.txt", "\n".join(test_list).encode("utf-8"))

            # Validatsiya va sifat ma'lumotlari (Crowdsourced validation results)
            val_csv_out = io.StringIO()
            val_writer = csv.writer(val_csv_out)
            val_writer.writerow(["audio_path", "speaker_id", "command", "correct_votes", "incorrect_votes", "low_quality_votes", "quality_status"])
            for r_val in data.get("validations", []):
                val_writer.writerow([
                    r_val["audio_file"],
                    r_val["speaker_id"],
                    r_val["command"],
                    r_val["correct_votes"],
                    r_val["incorrect_votes"],
                    r_val["low_quality_votes"],
                    r_val["quality_status"]
                ])
            zipf.writestr("uz_robot_cmd/validations.csv", ("\ufeff" + val_csv_out.getvalue()).encode("utf-8"))

            readme_text = (
                "Google Speech Commands standarti (O'zbek tili - uz_robot_cmd)\n"
                "===========================================================\n"
                "1. Format: 16 kHz, 16-bit PCM, mono WAV, uzunligi roppa-rosa 1.0 soniya.\n"
                "2. Buyruq audio markazida joylashgan, oldi va ortida jimlik qoldirilgan.\n"
                "3. Fayl nomlari: spkXXX_buyruq_takror.wav\n"
                "4. speakers.csv: speaker_id, jins, yosh_guruhi, hudud, qurilma\n"
                "5. splits.csv: 80% train, 10% val, 10% test (speaker-disjoint)\n"
                "6. validations.csv: Crowdsourced audio tekshiruvlari va sifat ko'rsatkichlari\n"
                "7. validation_list.txt va testing_list.txt: rasmiy Speech Commands loaderlari uchun.\n"
            )
            zipf.writestr("uz_robot_cmd/README.txt", readme_text.encode("utf-8"))

        doc = FSInputFile(temp_zip_path, filename=zip_filename)
        caption = (
            "🤖 <b>uz_robot_cmd (Google Speech Commands) Tayyor!</b>\n\n"
            f"📁 <b>Audio fayllar soni:</b> {len(items)} ta\n"
            f"👥 <b>Diktorlar soni:</b> {len(speakers)} ta (speakers.csv)\n"
            "🎚 <b>Audio formati:</b> 16 kHz, 16-bit mono WAV, roppa-rosa 1.0s (buyruq markazda)\n"
            "⚖️ <b>Bo'linmalar:</b> 80% train / 10% val / 10% test (splits.csv)\n"
            "📂 <b>Tuzilma:</b> `uz_robot_cmd/[buyruq]/spkXXX_buyruq_01.wav`\n"
            "📄 <b>Fayllar:</b> `speakers.csv`, `splits.csv`, `validations.csv`, `validation_list.txt`, `testing_list.txt`"
        )
        await bot.send_document(chat_id=callback.from_user.id, document=doc, caption=caption, parse_mode="HTML")
        await status_msg.delete()
    finally:
        if temp_zip_path.exists():
            try:
                os.remove(temp_zip_path)
            except Exception:
                pass
        import shutil
        if temp_process_dir.exists():
            shutil.rmtree(temp_process_dir, ignore_errors=True)


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
        "speaker_id",
        "speaker_gender",
        "speaker_age",
        "speaker_age_group",
        "speaker_region",
        "speaker_device",
        "session_id",
        "duration_seconds",
        "file_size_bytes",
        "quality_status",
        "correct_votes",
        "incorrect_votes",
        "low_quality_votes",
        "created_at"
    ])

    jsonl_lines = []
    total_duration_sec = 0.0

    with zipfile.ZipFile(temp_zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for r in rows:
            rel_file = r["file_path"]
            full_audio_path = BASE_DIR / rel_file
            arc_name = f"audios/{Path(rel_file).name}"

            if full_audio_path.exists():
                zipf.write(full_audio_path, arcname=arc_name)

            dur = float(r.get("duration", 0.0))
            total_duration_sec += dur

            spk_tag = f"spk{r['speaker_id']:03d}"
            writer.writerow([
                r["recording_id"],
                arc_name,
                r["prompt_text"],
                r["category_code"],
                r["category_title"],
                spk_tag,
                r["speaker_gender"],
                r["speaker_age"],
                r.get("speaker_age_group", ""),
                r.get("speaker_region", ""),
                r.get("speaker_device", ""),
                r["session_id"],
                dur,
                r["file_size"],
                r.get("quality_status", "unreviewed"),
                r.get("val_correct", 0),
                r.get("val_incorrect", 0),
                r.get("val_low_quality", 0),
                r["created_at"]
            ])

            jsonl_lines.append(json.dumps({
                "recording_id": r["recording_id"],
                "audio_file": arc_name,
                "text": r["prompt_text"],
                "category": r["category_code"],
                "speaker": {
                    "id": spk_tag,
                    "gender": r["speaker_gender"],
                    "age": r["speaker_age"],
                    "age_group": r.get("speaker_age_group", ""),
                    "region": r.get("speaker_region", ""),
                    "device": r.get("speaker_device", "")
                },
                "duration": dur,
                "quality": {
                    "status": r.get("quality_status", "unreviewed"),
                    "correct_votes": r.get("val_correct", 0),
                    "incorrect_votes": r.get("val_incorrect", 0),
                    "low_quality_votes": r.get("val_low_quality", 0)
                },
                "created_at": r["created_at"]
            }, ensure_ascii=False))

        zipf.writestr("metadata.csv", ("\ufeff" + csv_output.getvalue()).encode("utf-8"))
        zipf.writestr("metadata.jsonl", "\n".join(jsonl_lines).encode("utf-8"))

        summary_meta = {
            "dataset_name": f"Uzbek Speech Corpus ({label})",
            "audio_format": "WAV 16kHz 16-bit PCM Mono",
            "total_recordings": len(rows),
            "total_duration_seconds": round(total_duration_sec, 2),
            "total_duration_minutes": round(total_duration_sec / 60, 2),
            "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        zipf.writestr("dataset_summary.json", json.dumps(summary_meta, indent=2, ensure_ascii=False).encode("utf-8"))

        readme_doc = (
            f"# O'zbek Tili Ovozli Dataseti ({label})\n\n"
            "## Texnik va Akustik Parametrlar:\n"
            "- Audio formati: 16 kHz, 16-bit PCM, Mono WAV\n"
            f"- Jami yozuvlar soni: {len(rows)} ta\n"
            f"- Umumiy audio davomiyligi: {round(total_duration_sec / 60, 2)} daqiqa\n"
            "- Metama'lumotlar: `metadata.csv` va `metadata.jsonl` (Common Voice / Hugging Face formati)\n"
            "- Validatsiya: Crowdsourced o'zaro tekshiruv va sifat ko'rsatkichlari kiritilgan\n"
        )
        zipf.writestr("README.md", readme_doc.encode("utf-8"))

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
        uname = f"@{html.escape(u['username'])}" if u["username"] else "Username yo'q"
        fname = html.escape(u.get('first_name') or '')
        text += (
            f"• <b>{fname}</b> ({uname})\n"
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
        label = "👶 O'smirlar (18 yoshgacha)"
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
        owner_uname = f"@{html.escape(sp['username'])}" if sp["username"] else html.escape(sp.get('user_first_name') or '')
        spk_name = html.escape(sp.get('name') or '')
        text += (
            f"• {g_icon} <b>{spk_name}</b> ({sp['age']} yosh)\n"
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
    uname = f"@{html.escape(u['username'])}" if u["username"] else "Username yo'q"
    fname = html.escape(u.get('first_name') or '')

    text = (
        "👤 <b>Foydalanuvchi Tafsilotlari:</b>\n\n"
        f"• <b>Ismi:</b> {fname}\n"
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
            f"🔍 <code>{html.escape(query)}</code> bo'yicha foydalanuvchi topilmadi.\n"
            "Foydalanuvchi avval botga /start bosgan bo'lishi kerak.\n\n"
            "Qaytadan ID yoki @username kiriting yoki /admin buyrug'ini bering:"
        )
        return

    u = users[0]
    await state.clear()

    role_badge = "👑 Administrator" if u["role"] in ("admin", "superadmin") else "👤 Oddiy foydalanuvchi"
    uname = f"@{html.escape(u['username'])}" if u["username"] else "Username yo'q"
    fname = html.escape(u.get('first_name') or '')

    text = (
        "👤 <b>Topilgan foydalanuvchi:</b>\n\n"
        f"• <b>Ismi:</b> {fname}\n"
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
