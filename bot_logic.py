import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)
import database as db
import ai_responder
import logger

def setup_bot_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("faculty", change_faculty))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    faculties = [f for f in db.get_all_faculties() if f['is_active']]
    if not faculties:
        await update.message.reply_text(
            "Assalomu alaykum! OʻzMPU botiga xush kelibsiz! 🎓\n\nSavolingizni yozing:"
        )
        return
    keyboard = [[InlineKeyboardButton(f['name'], callback_data=f"fac_{f['id']}")] for f in faculties]
    await update.message.reply_text(
        "Assalomu alaykum! OʻzMPU botiga xush kelibsiz! 🎓\n\n"
        "Qaysi fakultet bo'yicha savol berasiz?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    fname = context.user_data.get('faculty_name', 'tanlanmagan')
    await update.message.reply_text(
        f"💡 Yordam:\n\n• Savolingizni yozing\n• /faculty — fakultet o'zgartirish\n• /start — qayta boshlash\n\n🏫 Fakultet: {fname}"
    )

async def change_faculty(update: Update, context: ContextTypes.DEFAULT_TYPE):
    faculties = [f for f in db.get_all_faculties() if f['is_active']]
    keyboard = [[InlineKeyboardButton(f['name'], callback_data=f"fac_{f['id']}")] for f in faculties]
    await update.message.reply_text("Fakultetni tanlang:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    import state

    if data.startswith("fac_"):
        fid = int(data.replace("fac_", ""))
        faculty = db.get_faculty(fid)
        if faculty:
            context.user_data['faculty_id'] = fid
            context.user_data['faculty_name'] = faculty['name']
            await query.message.reply_text(
                f"✅ {faculty['name']} tanlandi!\n\nSavolingizni yozing 📚"
            )

    elif data.startswith("opt_"):
        # Improved handling: if truncated, we might need a better way to map back
        # For now, we still use the text, but truncated callback data is a T-Bot limit (64 chars)
        selected = data.replace("opt_", "")
        user = query.from_user
        username = user.username or user.first_name or "Talaba"
        fid = context.user_data.get('faculty_id')
        await query.message.reply_text(f"🔍 {selected}")
        
        answer, options, lang, category = ai_responder.get_answer(selected, state.knowledge_base, state.clients)
        db.save_question(str(user.id), username, user.full_name or username, fid, selected, answer, lang, category)
        logger.log_message(str(user.id), username, selected, answer, lang, category)
        
        if options:
            kb = [[InlineKeyboardButton(o[:40], callback_data=f"opt_{o[:40]}")] for o in options]
            await query.message.reply_text(answer, reply_markup=InlineKeyboardMarkup(kb))
        else:
            await query.message.reply_text(answer)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    user = update.message.from_user
    username = user.username or user.first_name or "Talaba"
    fid = context.user_data.get('faculty_id')

    import state

    await update.message.chat.send_action("typing")
    answer, options, lang, category = ai_responder.get_answer(question, state.knowledge_base, state.clients)

    db.save_question(str(user.id), username, user.full_name or username, fid, question, answer, lang, category)
    logger.log_message(str(user.id), username, question, answer, lang, category)

    # Forward to faculty Telegram group
    if fid:
        faculty = db.get_faculty(fid)
        if faculty and faculty.get('telegram_group_id'):
            try:
                msg = (f"📨 Yangi savol!\n👤 {user.full_name or username}\n"
                       f"🏫 {faculty['name']}\n❓ {question}\n🤖 {answer[:300]}")
                await update.message.get_bot().send_message(chat_id=faculty['telegram_group_id'], text=msg)
            except Exception as e:
                logging.error(f"⚠️ Group send error: {e}")

    if options:
        kb = [[InlineKeyboardButton(o[:40], callback_data=f"opt_{o[:40]}")] for o in options]
        await update.message.reply_text(answer, reply_markup=InlineKeyboardMarkup(kb))
    else:
        await update.message.reply_text(answer)

async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Savolingizni yozing! 😊")
