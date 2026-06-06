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
import state

# Conversation States
REGISTER_ID, REGISTER_FACULTY = range(2)

# Max voice message duration (seconds)
MAX_VOICE_DURATION = 120

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
        fallbacks=[
            CommandHandler("start", start),
            CommandHandler("cancel", cancel_cmd),
            CommandHandler("faculty", change_faculty)
        ],
        name="registration_conv",
        persistent=False
    )
    
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("faculty", change_faculty))
    app.add_handler(CommandHandler("cancel", cancel_cmd))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.TEXT & ~filters.COMMAND, handle_message))
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
            keyboard.append([InlineKeyboardButton("📚 Umumiy (Fakultetsiz)", callback_data="reg_fac_none")])
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
            f"Assalomu alaykum! NPUU botiga qayta xush kelibsiz! 🎓\n\n"
            f"Sizning ID: {student['student_id']}\n"
            f"Fakultet: {context.user_data.get('faculty_name', 'Umumiy')}\n\n"
            "Savolingizni yozishingiz mumkin ✍️",
            reply_markup=InlineKeyboardMarkup(kb)
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Assalomu alaykum! NPUU botiga xush kelibsiz! 🎓\n\n"
        "Botdan foydalanish uchun ro'yxatdan o'tishingiz kerak.\n"
        "Iltimos, **talaba ID raqamingizni** kiriting:\n\n"
        "❌ Bekor qilish uchun /cancel yozing.",
        parse_mode='Markdown'
    )
    return REGISTER_ID

async def cancel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Bekor qilindi. Savolingizni yozing yoki /start orqali qayta ro'yxatdan o'ting."
    )
    return ConversationHandler.END

async def start_reset_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    try:
        conn = db.get_conn()
        conn.execute("DELETE FROM students WHERE telegram_id=?", (str(user_id),))
        conn.commit()
    except Exception as e:
        logging.error(f"Error deleting student in reset: {e}")
    finally:
        conn.close()
    
    context.user_data.clear()
    
    await query.message.reply_text(
        "Eski ma'lumotlaringiz tizimdan o'chirildi.\n\n"
        "Iltimos, yangi **talaba ID raqamingizni** kiriting:\n\n"
        "❌ Bekor qilish uchun /cancel yozing.",
        parse_mode='Markdown'
    )
    return REGISTER_ID

async def receive_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    # Must be digits only
    if not re.match(r'^\d+$', text):
        await update.message.reply_text("❌ Xato! Iltimos, faqat raqamlardan iborat ID kiriting:")
        return REGISTER_ID

    allowed_student = db.is_student_allowed(text)
    
    if not allowed_student:
        await update.message.reply_text(
            "❌ Kechirasiz, sizning ID raqamingiz tizimda topilmadi.\n"
            "Ruxsat etilgan talabalar ro'yxatida yo'qsiz. Iltimos, ma'muriyatga murojaat qiling."
        )
        return REGISTER_ID
    
    full_name = allowed_student.get('full_name') or ''
    welcome_text = f"✅ ID qabul qilindi: {text}"
    if full_name:
        welcome_text += f"\nSizning ismingiz: {full_name}"
    welcome_text += "\n\nEndi, fakultetingizni tanlang:"
    
    context.user_data['temp_student_id'] = text
    faculties = [f for f in db.get_all_faculties() if f['is_active']]
    
    keyboard = [[InlineKeyboardButton(f['name'], callback_data=f"reg_fac_{f['id']}")] for f in faculties]
    keyboard.append([InlineKeyboardButton("📚 Umumiy (Fakultetsiz)", callback_data="reg_fac_none")])
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return REGISTER_FACULTY

async def receive_faculty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.replace("reg_fac_", "")
    
    user_id = query.from_user.id
    student_id = context.user_data.get('temp_student_id')
    
    try:
        fid = None if data == "none" else int(data)
    except ValueError:
        await query.message.reply_text("❌ Xatolik yuz berdi. Qaytadan /start bosing.")
        return ConversationHandler.END

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
    keyboard.append([InlineKeyboardButton("📚 Umumiy (Fakultetsiz)", callback_data="fac_none")])
    
    await update.message.reply_text("Fakultetni o'zgartiring:", reply_markup=InlineKeyboardMarkup(keyboard))

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # Always load fresh from DB to avoid stale context after restart
    student = db.get_student(user_id)
    if student:
        sid = student.get('student_id', 'aniqlanmagan')
        fac = db.get_faculty(student['faculty_id']) if student.get('faculty_id') else None
        fname = fac['name'] if fac else 'Tanlanmagan'
    else:
        sid = context.user_data.get('student_id', 'aniqlanmagan')
        fname = context.user_data.get('faculty_name', 'tanlanmagan')
    await update.message.reply_text(
        f"💡 Yordam:\n\n• Savolingizni yozing\n• /faculty — fakultet o'zgartirish\n• /cancel — bekor qilish\n• /start — qayta ro'yxatdan o'tish\n\n🆔 ID: {sid}\n🏫 Fakultet: {fname}"
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("reg_fac_"):
        raw_fid = data.replace("reg_fac_", "")
        try:
            fid = None if raw_fid == "none" else int(raw_fid)
        except ValueError:
            await query.message.reply_text("❌ Xatolik. /start bosing.")
            return
        user_id = query.from_user.id
        student_id = context.user_data.get('temp_student_id') or context.user_data.get('student_id')
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

    elif data.startswith("fb_"):
        parts = data.split('_')
        if len(parts) >= 3:
            try:
                val = int(parts[1])
                qid = int(parts[2])
            except ValueError:
                return
            feedback_val = 1 if val == 1 else -1
            db.update_question_feedback(qid, feedback_val)
            try:
                await query.message.edit_reply_markup(reply_markup=None)
                if val == 1:
                    await query.message.reply_text("Rahmat, bahoingiz qabul qilindi! ✅", disable_notification=True)
                else:
                    kb = [[InlineKeyboardButton("👤 Administratorga yuborish", callback_data="ask_admin")]]
                    await query.message.reply_text(
                        "Rahmat! Javob sifatini yaxshilashga yordam berganingiz uchun tashakkur. 🔄\n\n"
                        "Savolingizni administratorga yuborishni xohlaysizmi?",
                        reply_markup=InlineKeyboardMarkup(kb),
                        disable_notification=True
                    )
            except Exception as e:
                logging.error(f"Feedback callback error: {e}")

    elif data.startswith("fac_"):
        raw_fid = data.replace("fac_", "")
        try:
            fid = None if raw_fid == "none" else int(raw_fid)
        except ValueError:
            return
        
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
        
        if not sid or not fid:
            s_db = db.get_student(user.id)
            if s_db:
                if not sid:
                    sid = s_db.get('student_id')
                    context.user_data['student_id'] = sid
                if not fid:
                    fid = s_db.get('faculty_id')
                    context.user_data['faculty_id'] = fid

        if data == "ask_admin":
            original_q = context.user_data.get('last_question', "Noma'lum savol")
            qid = db.save_question(str(user.id), sid, username, user.full_name or username, fid, original_q, "Admin javobini kuting...", "uz", "MANUAL")
            await query.message.reply_text("📩 Savolingiz administratorga yuborildi. Tez orada javob olasiz!")
            asyncio.create_task(forward_and_link(qid, user.full_name or username, original_q, None, sid, fid, is_manual=True, student_tg_id=str(user.id)))
            return

        if data.startswith("opt_idx_"):
            try:
                idx = int(data.replace("opt_idx_", ""))
            except ValueError:
                return
            temp_options = context.user_data.get('temp_options', [])
            selected = temp_options[idx] if idx < len(temp_options) else "Noma'lum savol"
        else:
            selected = data.replace("opt_", "")
            
        await query.message.edit_text("Hujjatlarimizdan qidirilmoqda... 🔍")
        answer, options, lang, category, topic = ai_responder.get_answer(selected, state.knowledge_base, state.clients, faculty_id=fid)
        
        # Truncate if too long for Telegram
        if len(answer) > 4000:
            answer = answer[:4000] + "..."
        
        qid = db.save_question(str(user.id), sid, username, user.full_name or username, fid, selected, answer, lang, category)
        if topic and topic != "Boshqa":
            db.update_question_topic(qid, topic)
        logger.log_message(str(user.id), username, selected, answer, lang, category)
        
        kb = []
        if options:
            context.user_data['temp_options'] = options
            kb = [[InlineKeyboardButton(o[:57] + "..." if len(o) > 60 else o, callback_data=f"opt_idx_{i}")] for i, o in enumerate(options)]
        
        referral_kws = [
            "topilmadi", "not found", "murojaat", "mas'ul xodimi", 
            "administrator", "admin", "operator", "ofisiga",
            "bog'lan", "boglan", "aloqa", "muloqot", "chat", "yuborish tugmasini"
        ]
        show_admin_btn_opt = (category in ["UNANSWERED", "ERROR", "GENERAL"]) or any(kw in answer.lower() for kw in referral_kws)
        
        if show_admin_btn_opt:
            kb.append([InlineKeyboardButton("👤 Administratorga yuborish", callback_data="ask_admin")])
            context.user_data['last_question'] = selected
        elif category not in ["VAGUE", "GENERAL", "ERROR", "GREETING", "THANKS", "BYE"]:
            kb.append([
                InlineKeyboardButton("👍 Yordam berdi", callback_data=f"fb_1_{qid}"),
                InlineKeyboardButton("👎 Yordam bermadi", callback_data=f"fb_0_{qid}")
            ])
            context.user_data['last_question'] = selected
            
        import re
        has_media = re.search(r'\[(?:IMAGE|FILE):\s*(https?://[^\s\]]+)\]', answer, re.IGNORECASE)
        
        if has_media:
            try:
                await query.message.delete()
            except Exception as delete_err:
                logging.warning(f"Could not delete message in callback: {delete_err}")
            await send_response_to_student(context.bot, query.message.chat_id, f"🤖 AI Yordamchi:\n\n{answer}", reply_markup=InlineKeyboardMarkup(kb) if kb else None)
        else:
            try:
                await query.message.edit_text(f"🤖 AI Yordamchi:\n\n{answer}", reply_markup=InlineKeyboardMarkup(kb) if kb else None)
            except Exception as edit_err:
                await send_response_to_student(context.bot, query.message.chat_id, f"🤖 AI Yordamchi:\n\n{answer}", reply_markup=InlineKeyboardMarkup(kb) if kb else None)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_working, offline_msg = db.is_within_working_hours()
    if not is_working:
        await update.message.reply_text(offline_msg)
        return

    max_req = int(db.get_setting("rate_limit_requests", "5"))
    win_sec = int(db.get_setting("rate_limit_window", "300"))
    
    is_allowed, wait_time = state.check_rate_limit(str(update.effective_user.id), max_requests=max_req, window_seconds=win_sec)
    if not is_allowed:
        minutes = wait_time // 60
        seconds = wait_time % 60
        if minutes > 0:
            await update.message.reply_text(f"⏳ Siz qisqa vaqt ichida ko'p savol berdingiz. Iltimos {minutes} daqiqa kuting.")
        else:
            await update.message.reply_text(f"⏳ Siz qisqa vaqt ichida ko'p savol berdingiz. Iltimos {seconds} soniya kuting.")
        return

    # Check voice duration
    voice = update.message.voice
    if voice.duration > MAX_VOICE_DURATION:
        await update.message.reply_text(f"⚠️ Ovozli xabar {MAX_VOICE_DURATION} soniyadan qisqa bo'lishi kerak.")
        return

    import tempfile
    file_path = None
    
    try:
        file = await context.bot.get_file(voice.file_id)
        with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tf:
            await file.download_to_drive(custom_path=tf.name)
            file_path = tf.name

        await update.message.chat.send_action("typing")
        
        # Detect language for better transcription
        text = ai_responder.transcribe_audio(file_path, state.clients['groq'])
    except Exception as e:
        logging.error(f"Voice Transcription Error: {e}")
        await update.message.reply_text("Ovozli xabarni o'qishda xatolik yuz berdi. Iltimos, yozib yuboring.")
        return
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

    if not text or len(text.strip()) < 2:
        await update.message.reply_text("Ovozli xabarda nima deyilganini tushunib bo'lmadi.")
        return

    # Show transcribed text
    await update.message.reply_text(f"🎤 Siz: <i>{text}</i>", parse_mode='HTML')
    
    # Process as regular text message (create a fake update with text)
    # Instead of mutating the frozen message, call handle_message logic directly
    await _process_question(update, context, text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    await _process_question(update, context, question)


async def _process_question(update: Update, context: ContextTypes.DEFAULT_TYPE, question: str):
    """Core question processing logic — used by both text and voice handlers."""
    try:
        is_working, offline_msg = db.is_within_working_hours()
        if not is_working:
            await update.message.reply_text(offline_msg)
            return

        max_req = int(db.get_setting("rate_limit_requests", "5"))
        win_sec = int(db.get_setting("rate_limit_window", "300"))
        
        is_allowed, wait_time = state.check_rate_limit(str(update.effective_user.id), max_requests=max_req, window_seconds=win_sec)
        if not is_allowed:
            minutes = wait_time // 60
            seconds = wait_time % 60
            if minutes > 0:
                await update.message.reply_text(f"⏳ Siz qisqa vaqt ichida ko'p savol berdingiz. Iltimos {minutes} daqiqa kuting.")
            else:
                await update.message.reply_text(f"⏳ Siz qisqa vaqt ichida ko'p savol berdingiz. Iltimos {seconds} soniya kuting.")
            return

        user = update.effective_user
        
        # Ensure student is fully registered
        student = db.get_student(user.id)
        sid = student.get('student_id') if student else None
        fid = (context.user_data.get('faculty_id') or student.get('faculty_id')) if student else None
        
        if student:
            context.user_data['student_id'] = sid
            context.user_data['faculty_id'] = fid
        
        if not student or not fid or str(sid).startswith('GUEST_'):
            await update.message.reply_text(
                "Iltimos, botdan foydalanish uchun avval ro'yxatdan o'ting va fakultetingizni tanlang:\n👉 /start"
            )
            return
        username = user.username or user.first_name or "Talaba"

        if not state.clients:
            logging.error("❌ AI clients not initialized in handle_message")
            await update.message.reply_text("⚠️ Kechirasiz, AI xizmat hozirda ishlamayapti. Tez orada tuzatiladi.")
            return

        await update.message.chat.send_action("typing")
        
        # 1. Get Answer
        answer, options, lang, category, topic = ai_responder.get_answer(question, state.knowledge_base, state.clients, faculty_id=fid)

        # 2. Truncate if too long for Telegram (4096 char limit)
        if len(answer) > 4000:
            answer = answer[:4000] + "..."

        # 3. Save Question
        qid = db.save_question(str(user.id), sid, username, user.full_name or username, fid, question, answer, lang, category)
        if topic and topic != "Boshqa":
            db.update_question_topic(qid, topic)
        logger.log_message(str(user.id), username, question, answer, lang, category)

        # 4. Build keyboard
        question_lower = question.lower()
        admin_req_kws = ["admin", "operator", "bog'la", "boglan", "aloqa"]
        is_req_admin = any(kw in question_lower for kw in admin_req_kws)

        referral_kws = [
            "topilmadi", "not found", "murojaat", "mas'ul xodimi", 
            "administrator", "admin", "operator", "ofisiga",
            "bog'lan", "boglan", "aloqa", "muloqot", "chat", "yuborish tugmasini"
        ]
        show_admin_btn = (category in ["UNANSWERED", "VAGUE", "ERROR", "GENERAL"]) or is_req_admin or any(kw in answer.lower() for kw in referral_kws)
        
        kb = []
        if options:
            context.user_data['temp_options'] = options
            kb = [[InlineKeyboardButton(o[:57] + "..." if len(o) > 60 else o, callback_data=f"opt_idx_{i}")] for i, o in enumerate(options)]
        
        if show_admin_btn:
            kb.append([InlineKeyboardButton("👤 Administratorga yuborish", callback_data="ask_admin")])
            context.user_data['last_question'] = question
        elif category not in ["VAGUE", "GENERAL", "ERROR", "GREETING", "THANKS", "BYE"]:
            kb.append([
                InlineKeyboardButton("👍 Yordam berdi", callback_data=f"fb_1_{qid}"),
                InlineKeyboardButton("👎 Yordam bermadi", callback_data=f"fb_0_{qid}")
            ])
            context.user_data['last_question'] = question
            
        await send_response_to_student(context.bot, update.effective_chat.id, f"🤖 AI Yordamchi:\n\n{answer}", reply_markup=InlineKeyboardMarkup(kb) if kb else None)

    except Exception as e:
        err_msg = str(e)
        st = traceback.format_exc()
        logging.error(f"❌ Handle Message Error: {err_msg}\n{st}")
        await update.message.reply_text("Uzr, savolingizni tushunishda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring! 🧐")


async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Noma'lum buyruq. Savolingizni yozishingiz mumkin! 😊")

async def forward_and_link(qid, name, q, a, sid, fid, is_manual=False, student_tg_id=None):
    try:
        result = None
        if is_manual:
            result = await notifier.notify_admin_manual(name, q, sid, fid, student_tg_id=student_tg_id)
        else:
            result = await notifier.forward_to_admin(name, q, a, sid, fid, student_tg_id=student_tg_id)
        
        if result and len(result) == 2:
            chat_id, mid = result
            if qid and chat_id and mid:
                db.link_admin_message(qid, chat_id, mid)
    except Exception as e:
        logging.error(f"❌ Error in forward_and_link: {str(e)}")

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.reply_to_message or not update.message.text:
        return
    
    chat_id = update.effective_chat.id
    reply_to_mid = update.message.reply_to_message.message_id
    
    question_data = db.get_question_by_admin_message(chat_id, reply_to_mid)
    if not question_data:
        return
    
    answer = update.message.text
    admin_user = update.effective_user
    
    import html
    student_tg_id = question_data['student_telegram_id']
    admin_name = admin_user.full_name or "Administrator"
    relay_msg = (
        f"✨ <b>Sizning savolingizga javob keldi:</b>\n\n"
        f"❓ {html.escape(question_data['question'])}\n\n"
        f"✅ <b>Javob:</b>\n{html.escape(answer)}"
    )
    
    try:
        await send_response_to_student(context.bot, student_tg_id, relay_msg)
        db.update_question_answer_tg(question_data['id'], answer, admin_user.id, admin_user.full_name)
    except Exception as e:
        logging.error(f"❌ Error relaying admin reply: {str(e)}")
        await update.message.reply_text("⚠️ Xatolik: Javobni talabaga yuborib bo'lmadi. (Balki talaba botni bloklagandur)")

async def send_response_to_student(bot, chat_id, text, reply_markup=None):
    """
    Sends a response text to the student. Supports [IMAGE: URL] and [FILE: URL] tags.
    """
    import re
    import logging
    
    # Parse image tag
    image_match = re.search(r'\[IMAGE:\s*(https?://[^\s\]]+)\]', text, re.IGNORECASE)
    file_match = re.search(r'\[FILE:\s*(https?://[^\s\]]+)\]', text, re.IGNORECASE)
    
    # Clean tags from the text
    clean_text = text
    if image_match:
        clean_text = clean_text.replace(image_match.group(0), '')
    if file_match:
        clean_text = clean_text.replace(file_match.group(0), '')
        
    clean_text = clean_text.strip()
    
    try:
        if image_match:
            image_url = image_match.group(1)
            # If text is too long for caption (max 1024 chars), send photo first, then text
            if len(clean_text) > 1000:
                await bot.send_photo(chat_id=chat_id, photo=image_url)
                return await bot.send_message(chat_id=chat_id, text=clean_text, reply_markup=reply_markup, parse_mode='HTML')
            else:
                return await bot.send_photo(chat_id=chat_id, photo=image_url, caption=clean_text, reply_markup=reply_markup, parse_mode='HTML')
        elif file_match:
            file_url = file_match.group(1)
            if len(clean_text) > 1000:
                await bot.send_document(chat_id=chat_id, document=file_url)
                return await bot.send_message(chat_id=chat_id, text=clean_text, reply_markup=reply_markup, parse_mode='HTML')
            else:
                return await bot.send_document(chat_id=chat_id, document=file_url, caption=clean_text, reply_markup=reply_markup, parse_mode='HTML')
        else:
            try:
                return await bot.send_message(chat_id=chat_id, text=clean_text, reply_markup=reply_markup, parse_mode='HTML')
            except Exception as html_err:
                logging.warning(f"HTML send failed: {html_err}. Retrying as plain text...")
                return await bot.send_message(chat_id=chat_id, text=clean_text, reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"Error sending rich response: {e}")
        try:
            return await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode='HTML')
        except:
            return await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup)
