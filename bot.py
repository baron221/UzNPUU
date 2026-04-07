import os
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes,
)
from file_loader import load_knowledge_base
from ai_responder import setup_ai, get_answer, parse_qa_pairs
import ai_responder
from logger import log_message

load_dotenv()
logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

print("🚀 Starting University Bot...")
knowledge_base = load_knowledge_base("knowledge/")
clients = setup_ai()
ai_responder._cached_pairs = parse_qa_pairs(knowledge_base)
print("✅ Bot is ready!\n")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Assalomu alaykum! Nizomiy nomidagi UzNPUU rasmiy botidasiz. Qanday yordam bera olaman? 🎓"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💡 Savol yozing, masalan:\n\n"
        "• Imtihon jadvali qachon?\n"
        "• HEMIS parolni tiklash\n"
        "• GPA qanday hisoblanadi?\n\n"
        "Rus va ingliz tilida ham so'rashingiz mumkin! 🌍"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text
    user = update.message.from_user
    username = user.username or user.first_name or "Talaba"

    await update.message.chat.send_action("typing")
    answer, options, lang, category = get_answer(question, knowledge_base, clients)

    # Log the interaction
    log_message(
        user_id=str(user.id),
        username=username,
        question=question,
        answer=answer,
        lang=lang,
        category=category
    )

    if options:
        keyboard = [[InlineKeyboardButton(opt, callback_data=opt)] for opt in options]
        await update.message.reply_text(answer, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text(answer)

async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    selected = query.data
    user = query.from_user
    username = user.username or user.first_name or "Talaba"

    await query.message.reply_text(f"🔍 Qidirilmoqda: {selected}")
    answer, options, lang, category = get_answer(selected, knowledge_base, clients)

    log_message(str(user.id), username, selected, answer, lang, category)

    if options:
        keyboard = [[InlineKeyboardButton(opt, callback_data=opt)] for opt in options]
        await query.message.reply_text(answer, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await query.message.reply_text(answer)

async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Buyruq tanilmadi. Savolingizni to'g'ridan-to'g'ri yozing! 😊")

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN not found in .env file!")
    app = (ApplicationBuilder().token(token)
           .connect_timeout(30).read_timeout(30).write_timeout(30).build())
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(handle_button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    print("✅ Bot is live!\n")
    app.run_polling()

if __name__ == "__main__":
    main()
