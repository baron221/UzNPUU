import os
import logging
import asyncio
import database as db
import state

def esc(text):
    """Simple HTML escaping for safety."""
    if not text: return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

async def forward_to_admin(user_full_name, question, answer, sid, fid=None):
    """
    Forwards a student question to the relevant admin Telegram group.
    """
    try:
        if not state.bot_app:
            logging.error("❌ Cannot forward to admin: state.bot_app is not initialized")
            return

        faculty_name = "Umumiy"
        group_id = os.environ.get("ADMIN_GROUP_ID") 
        
        if fid:
            faculty = db.get_faculty(fid)
            if faculty:
                faculty_name = faculty['name']
                group_id = faculty.get('telegram_group_id') or group_id

        if group_id:
            group_id = str(group_id).strip()
            msg = (f"📨 <b>Yangi savol!</b>\n"
                   f"🆔 ID: <code>{esc(sid)}</code>\n"
                   f"👤 <b>{esc(user_full_name)}</b>\n"
                   f"🏫 {esc(faculty_name)}\n"
                   f"❓ {esc(question)}\n"
                   f"🤖 AI Javobi: {esc(answer[:200])}...")
            
            sent_msg = await state.bot_app.bot.send_message(chat_id=group_id, text=msg, parse_mode='HTML')
            logging.info(f"✅ Forwarded question from {sid} to group {group_id}")
            return group_id, sent_msg.message_id
        else:
            logging.warning(f"⚠️ Cannot forward question: No group_id found for faculty {fid} and ADMIN_GROUP_ID is empty.")
        return None, None
            
    except Exception as e:
        logging.error(f"⚠️ Forward error: {str(e)}")
        return None, None

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
            group_id = str(group_id).strip()
            msg = (f"🚨 <b>ADMIN KERAK! (Manual)</b>\n"
                   f"🆔 ID: <code>{esc(sid)}</code>\n"
                   f"👤 <b>{esc(user_full_name)}</b>\n"
                   f"🏫 {esc(faculty_name)}\n"
                   f"❓ {esc(question)}\n"
                   f"⚠️ Talaba admin javobini kutmoqda.")
            sent_msg = await state.bot_app.bot.send_message(chat_id=group_id, text=msg, parse_mode='HTML')
            logging.info(f"✅ Manual alert sent to group {group_id}")
            return group_id, sent_msg.message_id
        else:
            logging.warning(f"⚠️ Cannot send manual alert: No group_id found for faculty {fid} and ADMIN_GROUP_ID is empty.")
        return None, None
    except Exception as e:
        logging.error(f"⚠️ Manual notify error: {str(e)}")
        return None, None
