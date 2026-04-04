# -*- coding: utf-8 -*-
import ast
import os

errors = []
for root, dirs, files in os.walk('.'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    ast.parse(file.read())
            except Exception as e:
                errors.append(f'{path}: {e}')

for e in errors:
    print(e)

if not errors:
    print('All Python files OK - UTF-8 encoding verified')