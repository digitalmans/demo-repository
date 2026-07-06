#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
智能问答系统 - 主启动文件
用于启动 start/app.py 中的 Flask 应用
"""

import os
import sys

# Configure standard output encoding to utf-8 to prevent encoding errors on Windows
if sys.platform.startswith('win'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

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
    from database import init_database

    # 启动 Flask 应用
    # 默认配置：host=0.0.0.0, port=5001, debug=True
    print("=" * 60)
    print("智能问答系统启动中...")
    print("=" * 60)

    # 初始化数据库（容错：失败不退出，让 Flask 仍能启动供调试）
    db_ok = False
    try:
        print("正在初始化数据库...")
        init_database()
        print("✓ 数据库初始化成功")
        db_ok = True
    except Exception as e:
        print(f"[警告] 数据库初始化失败: {e}")
        print("        数据库相关功能（注册/登录/讨论区）将不可用，但服务仍可启动")
    print(f"数据库状态: {'✓ 可用' if db_ok else '✗ 不可用（需要修）'}")
    print("=" * 60)
    print(f"访问地址: http://localhost:5001")
    print(f"管理员后台: http://localhost:5001/admin")
    print("=" * 60)

    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)
