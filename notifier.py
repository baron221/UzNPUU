import os
import logging
import asyncio
import database as db
import state

async def forward_to_admin(user_full_name, question, answer, sid, fid=None):
    """
    Forwards a student question to the relevant admin Telegram group.
    Can be called from both the Telegram Bot and the Web API.
    """
    try:
        if not state.bot_app:
            logging.error("❌ Cannot forward to admin: state.bot_app is not initialized")
            return

        faculty_name = "Umumiy"
        group_id = os.environ.get("ADMIN_GROUP_ID") # Fallback general group
        
        if fid:
            faculty = db.get_faculty(fid)
            if faculty:
                faculty_name = faculty['name']
                group_id = faculty.get('telegram_group_id') or group_id

        if group_id:
            msg = (f"📨 **Yangi savol!**\n"
                   f"🆔 ID: `{sid}`\n"
                   f"👤 {user_full_name}\n"
                   f"🏫 {faculty_name}\n"
                   f"❓ {question}\n"
                   f"🤖 AI Javobi: {answer[:200]}...")
            
            # Use the bot instance from state.bot_app
            await state.bot_app.bot.send_message(chat_id=group_id, text=msg, parse_mode='Markdown')
            logging.info(f"✅ Forwarded question from {sid} to group {group_id}")
            
    except Exception as e:
        logging.error(f"⚠️ Forward error: {e}")

async def notify_admin_manual(user_full_name, question, sid, fid=None):
    """
    Specifically for 'Ask Admin' escalations.
    """
    try:
        if not state.bot_app: return

        faculty_name = "Umumiy"
        group_id = os.environ.get("ADMIN_GROUP_ID")
        
        if fid:
            faculty = db.get_faculty(fid)
            if faculty:
                faculty_name = faculty['name']
                group_id = faculty.get('telegram_group_id') or group_id

        if group_id:
            msg = (f"🚨 **ADMIN KERAK! (Manual)**\n"
                   f"🆔 ID: `{sid}`\n"
                   f"👤 {user_full_name}\n"
                   f"🏫 {faculty_name}\n"
                   f"❓ {question}\n"
                   f"⚠️ Talaba admin javobini kutmoqda.")
            await state.bot_app.bot.send_message(chat_id=group_id, text=msg, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"⚠️ Manual notify error: {e}")
