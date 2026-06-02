filepath = '/home/opc/npuu-bot/database.py'
with open(filepath, 'r', encoding='utf-8') as f:
    code = f.read()

old_func = """def delete_faculty(faculty_id):
    conn = get_conn()
    conn.execute("UPDATE faculties SET is_active=0 WHERE id=?", (faculty_id,))
    conn.commit()
    conn.close()"""

new_func = """def delete_faculty(faculty_id):
    conn = get_conn()
    conn.execute("DELETE FROM faculties WHERE id=?", (faculty_id,))
    conn.commit()
    conn.close()"""

code = code.replace(old_func, new_func)

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(code)
print("database.py patched.")
