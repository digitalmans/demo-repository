#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
智能问答系统 - 主启动文件
用于启动 start/app.py 中的 Flask 应用
"""

import os
import sys

# 添加 start 目录到 Python 路径
current_dir = os.path.dirname(os.path.abspath(__file__))
start_dir = os.path.join(current_dir, 'start')
if start_dir not in sys.path:
    sys.path.insert(0, start_dir)

# 切换到 start 目录（如果需要）
os.chdir(start_dir)

# 导入并运行 Flask 应用
if __name__ == '__main__':
    from app import app
    
    # 启动 Flask 应用
    # 默认配置：host=0.0.0.0, port=5001, debug=True
    print("=" * 60)
    print("智能问答系统启动中...")
    print("=" * 60)
    print(f"访问地址: http://localhost:5001")
    print(f"管理员后台: http://localhost:5001/admin")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5001, debug=True)
