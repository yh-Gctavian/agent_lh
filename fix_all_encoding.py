# -*- coding: utf-8 -*-
"""修复所有Python文件的UTF-8编码"""

import os
import re
from pathlib import Path

def fix_file_encoding(filepath):
    """修复单个文件的编码"""
    try:
        # 尝试用不同编码读取
        encodings = ['utf-8', 'gbk', 'gb2312', 'gb18030', 'latin-1']
        content = None
        
        for enc in encodings:
            try:
                with open(filepath, 'r', encoding=enc) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            print(f"无法读取: {filepath}")
            return False
        
        # 确保有UTF-8头部声明
        if not content.startswith('# -*- coding: utf-8 -*-'):
            if content.startswith('#!'):
                # 保留shebang
                lines = content.split('\n')
                lines.insert(1, '# -*- coding: utf-8 -*-')
                content = '\n'.join(lines)
            else:
                content = '# -*- coding: utf-8 -*-\n' + content
        
        # 修复常见乱码
        replacements = {
            '娴': '修复',
            '妯″潡': '模块',
            '缁╂晥': '绩效',
            '鎸囨爣': '指标',
            '鑳滅巼': '胜率',
            '鍒嗘瀽': '分析',
            '鏁忔劅': '敏感',
            '鎬у垎': '性分',
            '绮楀害': '粒度',
            '鍙傛暟': '参数',
            '浼樺寲': '优化',
            '缃戞牸': '网格',
            '鎼滅储': '搜索',
            '楠岃瘉': '验证',
            '鎶ュ憡': '报告',
            '鐢熸垚': '生成',
            '鏍煎紡': '格式',
            '澶氬洜瀛愬垎灞傚垎鏋': '多因子分层分析',
            '璇': '误',
            '璇锋眰': '请求',
            '閲嶈瘯': '重试',
            '寮傚父': '异常',
            '缂栫爜': '编码',
            '淇': '修',
            '澶': '头',
            '娉ㄩ噴': '注释',
            '涔辩爜': '乱码',
            '瀵煎叆': '导入',
            '璺寰': '路径',
            '澶勭悊': '处理',
            '闂棰': '问题',
            '娣诲姞': '添加',
            '瑙ｅ喅': '解决',
            '鏀': '支',
            '鎸': '持',
            'pip install': 'pip install',
        }
        
        for wrong, right in replacements.items():
            content = content.replace(wrong, right)
        
        # 以UTF-8写入
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"已修复: {filepath}")
        return True
        
    except Exception as e:
        print(f"修复失败 {filepath}: {e}")
        return False

def main():
    """主函数"""
    base_dir = Path('wave_bottom_strategy')
    
    fixed = 0
    failed = 0
    
    for py_file in base_dir.rglob('*.py'):
        if fix_file_encoding(py_file):
            fixed += 1
        else:
            failed += 1
    
    print(f"\n修复完成: {fixed}个文件, 失败: {failed}个文件")

if __name__ == '__main__':
    main()