import re

filepath = "api.py"
with open(filepath, "r", encoding="utf-8") as f:
    code = f.read()

# Replace get_admin_questions
old_q = """async def get_admin_questions(faculty_id: Optional[int] = None, status: Optional[str] = None, limit: int = 50, current_user: dict = Depends(get_current_admin)):
    questions = db.get_questions(faculty_id=faculty_id, status=status, limit=limit)
    return {"questions": questions}"""

new_q = """async def get_admin_questions(faculty_id: Optional[int] = None, status: Optional[str] = None, limit: int = 50, current_user: dict = Depends(get_current_admin)):
    if current_user.get('role') == 'superadmin':
        faculty_id = None
    elif current_user.get('faculty_id'):
        faculty_id = current_user.get('faculty_id')
    questions = db.get_questions(faculty_id=faculty_id, status=status, limit=limit)
    return {"questions": questions}"""

code = code.replace(old_q, new_q)

# Replace get_admin_faq
old_faq = """async def get_admin_faq(faculty_id: Optional[int] = None, current_user: dict = Depends(get_current_admin)):
    return {"items": db.get_faq_items(faculty_id=faculty_id)}"""

new_faq = """async def get_admin_faq(faculty_id: Optional[int] = None, current_user: dict = Depends(get_current_admin)):
    if current_user.get('role') == 'superadmin':
        faculty_id = None
    elif current_user.get('faculty_id'):
        faculty_id = current_user.get('faculty_id')
    return {"items": db.get_faq_items(faculty_id=faculty_id)}"""

code = code.replace(old_faq, new_faq)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(code)

print("Patch applied to api.py successfully.")
