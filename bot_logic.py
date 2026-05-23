import os
import logging
import re
import traceback
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes, ConversationHandler
)
import database as db
import ai_responder
import logger
import notifier

# Conversation States
REGISTER_ID, REGISTER_FACULTY = range(2)

def setup_bot_handlers(app):
    # Registration Flow
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(start_reset_id, pattern="^reset_id$")
        ],
        states={
            REGISTER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_id)],
            REGISTER_FACULTY: [CallbackQueryHandler(receive_faculty, pattern="^reg_fac_")],
        },
        fallbacks=[CommandHandler("start", start), CommandHandler("faculty", change_faculty)],
        name="registration_conv",
        persistent=False
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("faculty", change_faculty))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.REPLY & (filters.ChatType.GROUPS | filters.ChatType.SUPERGROUP), handle_admin_reply))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    student = db.get_student(user_id)
    
    if student:
        context.user_data['student_id'] = student['student_id']
        context.user_data['faculty_id'] = student['faculty_id']

        # Student registered but has no faculty — ask them to pick one
        if not student['faculty_id']:
            faculties = [f for f in db.get_all_faculties() if f['is_active']]
            keyboard = [[InlineKeyboardButton(f['name'], callback_data=f"reg_fac_{f['id']}")] for f in faculties]
            keyboard.append([InlineKeyboardButton("👤 Adminstrator (Umumiy)", callback_data="reg_fac_none")])
            await update.message.reply_text(
                f"Assalomu alaykum! 🎓 Sizning ID: {student['student_id']}\n\n"
                "Fakultetingiz hali tanlanmagan. Iltimos, fakultetingizni tanlang:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return ConversationHandler.END

        fac = db.get_faculty(student['faculty_id'])
        context.user_data['faculty_name'] = fac['name'] if fac else "Umumiy"
        
        kb = [[InlineKeyboardButton("🔄 Boshqa ID bilan kirish", callback_data="reset_id")]]
        await update.message.reply_text(
            f"Assalomu alaykum! UzNPUU botiga qayta xush kelibsiz! 🎓\n\n"
            f"Sizning ID: {student['student_id']}\n"
            f"Fakultet: {context.user_data.get('faculty_name', 'Umumiy')}\n\n"
            "Savolingizni yozishingiz mumkin ✍️",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return ConversationHandler.END

async def start_reset_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    conn = db.get_conn()
    conn.execute("DELETE FROM students WHERE telegram_id=?", (str(user_id),))
    conn.commit()
    conn.close()
    
    context.user_data.clear()
    
    await query.message.reply_text(
        "Eski ma'lumotlaringiz tizimdan o'chirildi.\n\n"
        "Iltimos, yangi **6 xonali talaba ID raqamingizni** kiriting (masalan: 123456):",
        parse_mode='Markdown'
    )
    return REGISTER_ID

    await update.message.reply_text(
        "Assalomu alaykum! UzNPUU botiga xush kelibsiz! 🎓\n\n"
        "Botdan foydalanish uchun ro'yxatdan o'tishingiz kerak.\n"
        "Iltimos, **6 xonali talaba ID raqamingizni** kiriting (masalan: 123456):",
        parse_mode='Markdown'
    )
    return REGISTER_ID

async def receive_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not re.match(r'^\d{6}$', text):
        await update.message.reply_text("❌ Xato! Iltimos, aynan **6 ta raqamdan** iborat ID kiriting:")
        return REGISTER_ID
    
    context.user_data['temp_student_id'] = text
    faculties = [f for f in db.get_all_faculties() if f['is_active']]
    
    keyboard = [[InlineKeyboardButton(f['name'], callback_data=f"reg_fac_{f['id']}")] for f in faculties]
    keyboard.append([InlineKeyboardButton("👤 Adminstrator (Umumiy)", callback_data="reg_fac_none")])
    
    await update.message.reply_text(
        f"✅ ID qabul qilindi: {text}\n\nEndi, fakultetingizni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return REGISTER_FACULTY

async def receive_faculty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.replace("reg_fac_", "")
    
    user_id = query.from_user.id
    student_id = context.user_data.get('temp_student_id')
    
    fid = None if data == "none" else int(data)
    db.register_student(user_id, student_id, fid)
    
    context.user_data['student_id'] = student_id
    context.user_data['faculty_id'] = fid
    
    if fid:
        faculty = db.get_faculty(fid)
        context.user_data['faculty_name'] = faculty['name'] if faculty else "Umumiy"
        msg = f"🎉 Tabriklaymiz! Siz {context.user_data['faculty_name']} talabasi sifatida ro'yxatdan o'tdingiz."
    else:
        context.user_data['faculty_name'] = "Umumiy"
        msg = "🎉 Tabriklaymiz! Siz umumiy foydalanuvchi sifatida ro'yxatdan o'tdingiz."

    await query.message.edit_text(f"{msg}\n\nEndi savolingizni yozishingiz mumkin! 🎓")
    return ConversationHandler.END

async def change_faculty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    student = db.get_student(user_id)
    if not student:
        await update.message.reply_text("Avval /start orqali ro'yxatdan o'ting.")
        return
        
    faculties = [f for f in db.get_all_faculties() if f['is_active']]
    keyboard = [[InlineKeyboardButton(f['name'], callback_data=f"fac_{f['id']}")] for f in faculties]
    keyboard.append([InlineKeyboardButton("👤 Adminstrator (Umumiy)", callback_data="fac_none")])
    
    await update.message.reply_text("Fakultetni o'zgartiring:", reply_markup=InlineKeyboardMarkup(keyboard))

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sid = context.user_data.get('student_id', 'aniqlanmagan')
    fname = context.user_data.get('faculty_name', 'tanlanmagan')
    await update.message.reply_text(
        f"💡 Yordam:\n\n• Savolingizni yozing\n• /faculty — fakultet o'zgartirish\n• /start — qayta ro'yxatdan o'tish\n\n🆔 ID: {sid}\n🏫 Fakultet: {fname}"
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    import state

    if data.startswith("reg_fac_"):
        # Fallback handler: fires when bot restarted mid-registration and
        # the ConversationHandler lost its REGISTER_FACULTY state.
        raw_fid = data.replace("reg_fac_", "")
        fid = None if raw_fid == "none" else int(raw_fid)
        user_id = query.from_user.id
        student_id = context.user_data.get('temp_student_id') or context.user_data.get('student_id')
        # Try to load from DB if context is empty
        if not student_id:
            s_db = db.get_student(user_id)
            if s_db:
                student_id = s_db['student_id']
        if student_id:
            db.register_student(user_id, student_id, fid)
            context.user_data['student_id'] = student_id
            context.user_data['faculty_id'] = fid
            faculty_name = "Umumiy"
            if fid:
                faculty = db.get_faculty(fid)
                faculty_name = faculty['name'] if faculty else "Umumiy"
            context.user_data['faculty_name'] = faculty_name
            await query.message.edit_text(
                f"🎉 Tabriklaymiz! Siz {faculty_name} talabasi sifatida ro'yxatdan o'tdingiz.\n\n"
                "Endi savolingizni yozishingiz mumkin! 🎓"
            )
        else:
            await query.message.reply_text("❌ Xatolik: avval /start orqali ID kiriting.")

    elif data.startswith("fac_"):
        raw_fid = data.replace("fac_", "")
        fid = None if raw_fid == "none" else int(raw_fid)
        
        user_id = query.from_user.id
        student_id = context.user_data.get('student_id')
        
        if not student_id:
            student = db.get_student(user_id)
            if student: student_id = student['student_id']
            
        if student_id:
            db.register_student(user_id, student_id, fid)
            context.user_data['faculty_id'] = fid
            faculty_name = "Umumiy"
            if fid:
                faculty = db.get_faculty(fid)
                faculty_name = faculty['name'] if faculty else "Umumiy"
            context.user_data['faculty_name'] = faculty_name
            await query.message.reply_text(f"✅ Fakultet o'zgartirildi: {faculty_name}")

    elif data.startswith("opt_") or data == "ask_admin":
        user = query.from_user
        username = user.username or user.first_name or "Talaba"
        fid = context.user_data.get('faculty_id')
        sid = context.user_data.get('student_id')
        
        if not sid:
            s_db = db.get_student(user.id)
            if s_db: sid = s_db['student_id']

        if data == "ask_admin":
            original_q = context.user_data.get('last_question', 'Noma\'lum savol')
            qid = db.save_question(str(user.id), sid, username, user.full_name or username, fid, original_q, "Admin javobini kuting...", "uz", "MANUAL")
            await query.message.reply_text("📩 Savolingiz adminstratorga yuborildi. Tez orada javob olasiz!")
            
            # Non-blocking forward and link
            asyncio.create_task(forward_and_link(qid, user.full_name or username, original_q, None, sid, fid, is_manual=True))
            return

        if data.startswith("opt_idx_"):
            idx = int(data.replace("opt_idx_", ""))
            temp_options = context.user_data.get('temp_options', [])
            if idx < len(temp_options):
                selected = temp_options[idx]
            else:
                selected = "Noma'lum savol"
        else:
            selected = data.replace("opt_", "")
            
        # Display the full selected question clearly
        clean_q = ai_responder.clean_label(selected)
        await query.message.reply_text(f"🔍 Tanlandi: {clean_q}")
        
        answer, options, lang, category = ai_responder.get_answer(selected, state.knowledge_base, state.clients, faculty_id=fid)
        db.save_question(str(user.id), sid, username, user.full_name or username, fid, selected, answer, lang, category)
        logger.log_message(str(user.id), username, selected, answer, lang, category)
        
        # Check if we should show Admin button (not found or refers to staff)
        referral_kws = ["topilmadi", "not found", "murojaat qiling", "mas'ul xodimi", "adminstrator", "ofisiga"]
        show_admin_btn = (category == "UNANSWERED") or any(kw in answer.lower() for kw in referral_kws)
        
        kb = []
        if options:
            context.user_data['temp_options'] = options
            kb = [[InlineKeyboardButton(o[:57] + "..." if len(o) > 60 else o, callback_data=f"opt_idx_{i}")] for i, o in enumerate(options)]
        if show_admin_btn:
            kb.append([InlineKeyboardButton("👤 Adminstratorga yuborish", callback_data="ask_admin")])
            context.user_data['last_question'] = selected
            
        await query.message.reply_text(f"🤖 AI Yordamchi:\n\n{answer}", reply_markup=InlineKeyboardMarkup(kb) if kb else None)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_working, offline_msg = db.is_within_working_hours()
    if not is_working:
        await update.message.reply_text(offline_msg)
        return

    import state
    max_req = int(db.get_setting("rate_limit_requests", "2"))
    win_sec = int(db.get_setting("rate_limit_window", "120"))
    
    is_allowed, wait_time = state.check_rate_limit(str(update.effective_user.id), max_requests=max_req, window_seconds=win_sec)
    if not is_allowed:
        minutes = wait_time // 60
        seconds = wait_time % 60
        await update.message.reply_text(f"⏳ Siz qisqa vaqt ichida ko'p savol berdingiz. Iltimos {minutes} daqiqa va {seconds} soniya kuting.")
        return

    import tempfile
    
    # 1. Yuklab olish
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)
    
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tf:
        await file.download_to_drive(custom_path=tf.name)
        file_path = tf.name

    await update.message.chat.send_action("typing")
    
    # 2. Matnga o'girish
    import state
    try:
        text = ai_responder.transcribe_audio(file_path, state.clients['groq'])
    except Exception as e:
        logging.error(f"Voice Transcription Error: {e}")
        await update.message.reply_text("Ovozli xabarni o'qishda xatolik yuz berdi. Iltimos, yozib yuboring.")
        return
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)

    if not text or len(text.strip()) < 2:
        await update.message.reply_text("Ovozli xabarda nima deyilganini tushunib bo'lmadi.")
        return

    # 3. Foydalanuvchiga matnni ko'rsatish
    await update.message.reply_text(f"🎤 Siz: <i>{text}</i>", parse_mode='HTML')
    
    # 4. Oddiy matn kabi davom ettirish
    update.message.text = text
    await handle_message(update, context)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        is_working, offline_msg = db.is_within_working_hours()
        if not is_working:
            await update.message.reply_text(offline_msg)
            return

        import state
        max_req = int(db.get_setting("rate_limit_requests", "2"))
        win_sec = int(db.get_setting("rate_limit_window", "120"))
        
        is_allowed, wait_time = state.check_rate_limit(str(update.effective_user.id), max_requests=max_req, window_seconds=win_sec)
        if not is_allowed:
            minutes = wait_time // 60
            seconds = wait_time % 60
            await update.message.reply_text(f"⏳ Siz qisqa vaqt ichida ko'p savol berdingiz. Iltimos {minutes} daqiqa va {seconds} soniya kuting.")
            return

        question = update.message.text
        user = update.message.from_user
        
        # Auto-register/load student
        student = db.get_student(user.id)
        if not student:
            # Maybe they didn't finish the flow? Check if they have an ID in context
            sid = context.user_data.get('student_id') or context.user_data.get('temp_student_id')
            if not sid:
                # NEW: Auto-register as Guest to ensure the question is saved
                sid = f"GUEST_{user.id}"
                db.register_student(user.id, sid, None)
                student = {"student_id": sid, "faculty_id": None}
                # Also notify them they can register for a better experience later
                # but don't block the AI answer now
            else:
                # They have a temp ID but weren't in DB yet
                db.register_student(user.id, sid, None)
                student = {"student_id": sid, "faculty_id": None}

        sid = student.get('student_id')
        fid = context.user_data.get('faculty_id') or student.get('faculty_id')
        username = user.username or user.first_name or "Talaba"

        import state
        
        # Verify AI state
        if not state.clients:
            logging.error("❌ AI clients not initialized in handle_message")
            await update.message.reply_text("⚠️ Kechirasiz, AI xizmat hozirda ishlamayapti. Tez orada tuzatiladi.")
            return
        if not state.knowledge_base:
            logging.warning("⚠️ Knowledge base is empty — answering with AI only (no documents)")
            # Don't block — let it answer from FAQ DB items even without file KB

        await update.message.chat.send_action("typing")
        
        # 1. Get Answer
        answer, options, lang, category = ai_responder.get_answer(question, state.knowledge_base, state.clients, faculty_id=fid)

        # 2. Save Question
        qid = db.save_question(str(user.id), sid, username, user.full_name or username, fid, question, answer, lang, category)
        logger.log_message(str(user.id), username, question, answer, lang, category)

        # 3. Respond to Student FIRST
        referral_kws = ["topilmadi", "not found", "murojaat qiling", "mas'ul xodimi", "adminstrator", "ofisiga"]
        show_admin_btn = (category == "UNANSWERED") or any(kw in answer.lower() for kw in referral_kws)
        
        kb = []
        if options:
            context.user_data['temp_options'] = options
            kb = [[InlineKeyboardButton(o[:57] + "..." if len(o) > 60 else o, callback_data=f"opt_idx_{i}")] for i, o in enumerate(options)]
        if show_admin_btn:
            kb.append([InlineKeyboardButton("👤 Adminstratorga yuborish", callback_data="ask_admin")])
            context.user_data['last_question'] = question
            
        await update.message.reply_text(f"🤖 AI Yordamchi:\n\n{answer}", reply_markup=InlineKeyboardMarkup(kb) if kb else None)

        # 4. Forward to Admin (As background task) - Disabled: now only forwards when 'Ask Admin' is clicked
        # asyncio.create_task(forward_and_link(qid, user.full_name or username, question, answer, sid, fid))

    except Exception as e:
        err_msg = str(e)
        st = traceback.format_exc()
        logging.error(f"❌ Handle Message Error: {err_msg}\n{st}")
        
        # User-friendly error
        await update.message.reply_text("Uzr, savolingizni tushunishda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring! 🧐")


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Noma'lum buyruq. Savolingizni yozishingiz mumkin! 😊")

async def forward_and_link(qid, name, q, a, sid, fid, is_manual=False):
    try:
        if is_manual:
            chat_id, mid = await notifier.notify_admin_manual(name, q, sid, fid)
        else:
            chat_id, mid = await notifier.forward_to_admin(name, q, a, sid, fid)
        
        if qid and chat_id and mid:
            db.link_admin_message(qid, chat_id, mid)
    except Exception as e:
        logging.error(f"❌ Error in forward_and_link: {str(e)}")

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Only process text replies in groups
    if not update.message or not update.message.reply_to_message or not update.message.text:
        return
    
    chat_id = update.effective_chat.id
    reply_to_mid = update.message.reply_to_message.message_id
    
    # 1. Find linked question
    question_data = db.get_question_by_admin_message(chat_id, reply_to_mid)
    if not question_data:
        return # Not a reply to a bot question
    
    # 2. Extract answer and admin info
    answer = update.message.text
    admin_user = update.effective_user
    
    # 3. Relay to student
    student_tg_id = question_data['student_telegram_id']
    admin_name = admin_user.full_name or "Adminstrator"
    relay_msg = f"✨ **Sizning savolingizga javob keldi:**\n\n❓ {question_data['question']}\n\n✅ 👤 **{admin_name} javobi:**\n{answer}"
    
    try:
        await context.bot.send_message(chat_id=student_tg_id, text=relay_msg, parse_mode='Markdown')
        # 4. Update DB
        db.update_question_answer_tg(question_data['id'], answer, admin_user.id, admin_user.full_name)
        await update.message.reply_text("✅ Javobingiz talabaga yuborildi.")
    except Exception as e:
        logging.error(f"❌ Error relaying admin reply: {str(e)}")
        await update.message.reply_text("⚠️ Xatolik: Javobni talabaga yuborib bo'lmadi. (Balki talaba botni bloklagandur)")
