import os
import logging
import asyncio
import database as db
import state

def esc(text):
    """Simple HTML escaping for safety."""
    if not text: return ""
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def default_group_id():
    """Fallback group used when a faculty has no group of its own."""
    return db.get_setting("admin_group_id", "").strip() or os.environ.get("ADMIN_GROUP_ID")

async def default_admin_bot():
    """
    Bot used for the default/fallback admin group (Settings > admin_bot_token).
    Falls back to the main student-facing bot if no separate one is configured.
    """
    admin_token = db.get_setting("admin_bot_token", "").strip()
    if admin_token:
        from telegram import Bot
        return Bot(token=admin_token)
    return state.bot_app.bot if state.bot_app else None

async def resolve_group_and_bot(fid):
    """
    Decides where a notification goes and which bot sends it:
    - a faculty with its own telegram_group_id keeps using the main
      student-facing bot (unchanged, existing behavior) so the dedicated
      notification bot never touches groups it wasn't added to.
    - everything else falls back to the default admin group, sent by the
      dedicated notification bot configured in Settings (if any).
    """
    faculty_name = "Umumiy"
    faculty_group_id = None
    if fid:
        faculty = db.get_faculty(fid)
        if faculty:
            faculty_name = faculty['name']
            faculty_group_id = (faculty.get('telegram_group_id') or '').strip() or None

    if faculty_group_id:
        bot = state.bot_app.bot if state.bot_app else None
        return faculty_group_id, faculty_name, bot

    return default_group_id(), faculty_name, await default_admin_bot()

async def forward_to_admin(user_full_name, question, answer, sid, fid=None, student_tg_id=None):
    """
    Forwards a student question to the relevant admin Telegram group.
    """
    try:
        group_id, faculty_name, bot = await resolve_group_and_bot(fid)
        if not bot:
            logging.error("❌ Cannot forward to admin: no bot available (set admin_bot_token or start the main bot)")
            return

        if group_id:
            group_id = str(group_id).strip()
            msg = (f"📨 <b>Yangi savol!</b>\n"
                   f"🆔 ID: <code>{esc(sid)}</code>\n"
                   f"👤 <b>{esc(user_full_name)}</b>\n"
                   f"🏫 {esc(faculty_name)}\n"
                   f"❓ {esc(question)}\n"
                   f"🤖 AI Javobi: {esc(answer[:200])}...")
            
            reply_markup = None
            if student_tg_id and str(student_tg_id) != "WEB":
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                admin_panel_url = os.environ.get("ADMIN_PANEL_URL", "https://uz-npuu.vercel.app")
                chat_url = f"{admin_panel_url}/admin/questions?tg_id={student_tg_id}"
                reply_markup = InlineKeyboardMarkup([[
                    InlineKeyboardButton("💬 Panelda suhbatni ochish", url=chat_url)
                ]])

            sent_msg = await bot.send_message(
                chat_id=group_id,
                text=msg,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            logging.info(f"✅ Forwarded question from {sid} to group {group_id}")
            return group_id, sent_msg.message_id
        else:
            logging.warning(f"⚠️ Cannot forward question: No group_id found for faculty {fid} and no default admin group is set in Settings.")
        return None, None

    except Exception as e:
        logging.error(f"⚠️ Forward error: {str(e)}")
        return None, None

async def notify_admin_manual(user_full_name, question, sid, fid=None, student_tg_id=None):
    """
    Specifically for 'Ask Admin' escalations.
    """
    try:
        group_id, faculty_name, bot = await resolve_group_and_bot(fid)
        if not bot:
            logging.error("❌ Cannot send manual alert: no bot available (set admin_bot_token or start the main bot)")
            return

        if group_id:
            group_id = str(group_id).strip()
            msg = (f"🚨 <b>ADMIN KERAK! (Manual)</b>\n"
                   f"🆔 ID: <code>{esc(sid)}</code>\n"
                   f"👤 <b>{esc(user_full_name)}</b>\n"
                   f"🏫 {esc(faculty_name)}\n"
                   f"❓ {esc(question)}\n"
                   f"⚠️ Talaba admin javobini kutmoqda.")

            reply_markup = None
            if student_tg_id and str(student_tg_id) != "WEB":
                from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                admin_panel_url = os.environ.get("ADMIN_PANEL_URL", "https://uz-npuu.vercel.app")
                chat_url = f"{admin_panel_url}/admin/questions?tg_id={student_tg_id}"
                reply_markup = InlineKeyboardMarkup([[
                    InlineKeyboardButton("💬 Panelda suhbatni ochish", url=chat_url)
                ]])

            sent_msg = await bot.send_message(
                chat_id=group_id,
                text=msg,
                parse_mode='HTML',
                reply_markup=reply_markup
            )
            logging.info(f"✅ Manual alert sent to group {group_id}")
            return group_id, sent_msg.message_id
        else:
            logging.warning(f"⚠️ Cannot send manual alert: No group_id found for faculty {fid} and no default admin group is set in Settings.")
        return None, None
    except Exception as e:
        logging.error(f"⚠️ Manual notify error: {str(e)}")
        return None, None

async def notify_group_admin_reply(admin_name, question_text, answer_text, sid, fid=None):
    """
    Sends admin's web panel reply to the faculty Telegram group so the group can see it.
    """
    try:
        group_id, faculty_name, bot = await resolve_group_and_bot(fid)
        if not bot:
            return

        if not group_id:
            logging.warning(f"⚠️ notify_group_admin_reply: No group_id for faculty {fid}")
            return

        group_id = str(group_id).strip()

        # Don't show internal follow-up messages in the group
        if question_text in ["__ADMIN_FOLLOW_UP__", "Adminstruatordan xabari"]:
            q_display = "(Admin xabari)"
        else:
            q_display = esc(question_text[:200])

        msg = (
            f"✅ <b>Admin javobi berildi</b>\n"
            f"🆔 Talaba ID: <code>{esc(sid)}</code>\n"
            f"🏫 {esc(faculty_name)}\n"
            f"❓ <b>Savol:</b> {q_display}\n"
            f"💬 <b>{esc(admin_name)} javobi:</b>\n{esc(answer_text)}"
        )
        await bot.send_message(chat_id=group_id, text=msg, parse_mode='HTML')
        logging.info(f"✅ Admin reply forwarded to group {group_id}")
    except Exception as e:
        logging.error(f"⚠️ notify_group_admin_reply error: {str(e)}")
