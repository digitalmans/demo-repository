#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
数据库配置
"""

# MySQL数据库配置
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',  # 请根据实际情况修改
    'password': 'xh050316',
    'database': 'voice_assistant_db',  # 数据库名称
    'charset': 'utf8mb4'
}

# 应用配置
SECRET_KEY = 'your-secret-key-change-this-in-production'
