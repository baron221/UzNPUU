import ast
import base64

with open('/home/opc/npuu-bot/bot_logic.py', 'r', encoding='utf-8') as f:
    code = f.read()

module = ast.parse(code)
for node in module.body:
    if isinstance(node, ast.AsyncFunctionDef) and node.name == 'handle_message':
        func_code = ast.get_source_segment(code, node)
        print(base64.b64encode(func_code.encode()).decode())
        break
