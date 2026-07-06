#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
数据库配置
"""

import os

# MySQL数据库配置
# 注意：原项目默认 3306，但本机已有 MySQL 9.7.0 占着 3306，
# 新装的 MySQL 8.0 跑在 3307；密码设置为 123456
MYSQL_CONFIG = {
    'host': '127.0.0.1',
    'port': 3307,
    'user': 'root',
    'password': '123456',
    'database': 'voice_assistant_db',
    'charset': 'utf8mb4'
}

# 应用配置
SECRET_KEY = 'your-secret-key-change-this-in-production'

# 上传/输出目录（macOS 沙盒下用户配置目录也可能被拦截，优先用 /tmp 兜底）
def _safe_mkdir(path):
    try:
        os.makedirs(path, exist_ok=True)
        return path
    except (PermissionError, OSError):
        alt = os.path.join('/tmp', 'demo-qa', os.path.basename(path))
        os.makedirs(alt, exist_ok=True)
        return alt

UPLOAD_FOLDER = _safe_mkdir(os.path.expanduser('~/Library/Application Support/demo-qa/uploads'))
OUTPUT_FOLDER = _safe_mkdir(os.path.expanduser('~/Library/Application Support/demo-qa/outputs'))
