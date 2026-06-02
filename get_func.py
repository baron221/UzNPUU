import ast
import base64
with open('/home/opc/npuu-bot/database.py', 'r', encoding='utf-8') as f:
    code = f.read()

module = ast.parse(code)
for node in module.body:
    if isinstance(node, ast.FunctionDef) and node.name == 'delete_faculty':
        func_code = ast.get_source_segment(code, node)
        print(base64.b64encode(func_code.encode()).decode())
        break
