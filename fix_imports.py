# -*- coding: utf-8 -*-
import os
import glob

# 找到所有需要修复的文件
files = glob.glob('wave_bottom_strategy/**/*.py', recursive=True)

for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
        
        if 'from utils.logger import get_logger' in content:
            new_content = content.replace('from utils.logger import get_logger', 'from wave_bottom_strategy.utils.logger import get_logger')
            with open(f, 'w', encoding='utf-8') as file:
                file.write(new_content)
            print(f'Fixed: {f}')
        else:
            print(f'No change needed: {f}')
    except Exception as e:
        print(f'Error with {f}: {e}')

print('Done!')