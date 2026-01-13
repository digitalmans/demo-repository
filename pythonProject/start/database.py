#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
数据库操作模块
"""

import pymysql
from pymysql.err import OperationalError, IntegrityError
from config import MYSQL_CONFIG
import hashlib


def get_db_connection():
    """
    获取数据库连接
    :return: 数据库连接对象
    """
    try:
        connection = pymysql.connect(
            host=MYSQL_CONFIG['host'],
            port=MYSQL_CONFIG['port'],
            user=MYSQL_CONFIG['user'],
            password=MYSQL_CONFIG['password'],
            database=MYSQL_CONFIG['database'],
            charset=MYSQL_CONFIG['charset'],
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True
        )
        return connection
    except OperationalError as e:
        print(f"数据库连接错误: {e}")
        raise


def init_database():
    """
    初始化数据库和表结构
    """
    try:
        # 先连接到MySQL服务器（不指定数据库）
        connection = pymysql.connect(
            host=MYSQL_CONFIG['host'],
            port=MYSQL_CONFIG['port'],
            user=MYSQL_CONFIG['user'],
            password=MYSQL_CONFIG['password'],
            charset=MYSQL_CONFIG['charset']
        )
        
        with connection.cursor() as cursor:
            # 创建数据库（如果不存在）
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_CONFIG['database']} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"数据库 {MYSQL_CONFIG['database']} 已创建或已存在")
        
        connection.close()
        
        # 连接到指定数据库
        connection = get_db_connection()
        
        with connection.cursor() as cursor:
            # 创建用户表
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS users (
                id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                email VARCHAR(100),
                role VARCHAR(20) DEFAULT 'user' COMMENT '用户角色: user(普通用户), admin(管理员)',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP NULL,
                INDEX idx_username (username),
                INDEX idx_role (role)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cursor.execute(create_table_sql)
            print("用户表已创建或已存在")
            
            # 检查是否需要添加role字段（兼容旧表）
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'users' 
                AND COLUMN_NAME = 'role'
            """, (MYSQL_CONFIG['database'],))
            result = cursor.fetchone()
            if result['count'] == 0:
                cursor.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user' COMMENT '用户角色: user(普通用户), admin(管理员)'")
                cursor.execute("ALTER TABLE users ADD INDEX idx_role (role)")
                print("已添加role字段")
            
            # 创建默认管理员账号（如果不存在）
            cursor.execute("SELECT id FROM users WHERE username = 'admin'")
            if not cursor.fetchone():
                admin_password = hash_password('admin123')  # 默认管理员密码
                cursor.execute(
                    "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                    ('admin', admin_password, 'admin')
                )
                print("已创建默认管理员账号: admin / admin123")
        
        connection.close()
        print("数据库初始化完成")
        
    except Exception as e:
        print(f"数据库初始化错误: {e}")
        raise


def hash_password(password):
    """
    密码哈希
    :param password: 明文密码
    :return: 哈希后的密码
    """
    return hashlib.sha256(password.encode()).hexdigest()


def register_user(username, password, email=None, role='user'):
    """
    注册新用户
    :param username: 用户名
    :param password: 密码
    :param email: 邮箱（可选）
    :param role: 用户角色，默认为'user'，只有管理员可以创建管理员账号
    :return: (success, message)
    """
    try:
        connection = get_db_connection()
        
        with connection.cursor() as cursor:
            # 检查用户名是否已存在
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return False, "用户名已存在"
            
            # 插入新用户
            hashed_password = hash_password(password)
            cursor.execute(
                "INSERT INTO users (username, password, email, role) VALUES (%s, %s, %s, %s)",
                (username, hashed_password, email, role)
            )
            
        connection.close()
        return True, "注册成功"
        
    except IntegrityError:
        return False, "用户名已存在"
    except Exception as e:
        print(f"注册错误: {e}")
        return False, f"注册失败: {str(e)}"


def verify_user(username, password):
    """
    验证用户登录
    :param username: 用户名
    :param password: 密码
    :return: (success, message, user_data)
    """
    try:
        connection = get_db_connection()
        
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, username, password, email, role, created_at FROM users WHERE username = %s",
                (username,)
            )
            user = cursor.fetchone()
            
            if not user:
                return False, "用户名不存在", None
            
            hashed_password = hash_password(password)
            if user['password'] != hashed_password:
                return False, "密码错误", None
            
            # 更新最后登录时间
            cursor.execute(
                "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = %s",
                (user['id'],)
            )
            
            # 返回用户信息（不包含密码）
            user_data = {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user.get('role', 'user'),
                'created_at': user['created_at'].isoformat() if user['created_at'] else None
            }
            
        connection.close()
        return True, "登录成功", user_data
        
    except Exception as e:
        print(f"登录验证错误: {e}")
        return False, f"登录失败: {str(e)}", None


def get_user_info(username):
    """
    获取用户信息
    :param username: 用户名
    :return: 用户信息字典或None
    """
    try:
        connection = get_db_connection()
        
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, username, email, role, created_at, last_login FROM users WHERE username = %s",
                (username,)
            )
            user = cursor.fetchone()
            
            if user:
                user_data = {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'role': user.get('role', 'user'),
                    'created_at': user['created_at'].isoformat() if user['created_at'] else None,
                    'last_login': user['last_login'].isoformat() if user['last_login'] else None
                }
                connection.close()
                return user_data
        
        connection.close()
        return None
        
    except Exception as e:
        print(f"获取用户信息错误: {e}")
        return None


def get_all_users():
    """
    获取所有用户列表（仅管理员）
    :return: 用户列表
    """
    try:
        connection = get_db_connection()
        
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, username, email, role, created_at, last_login FROM users ORDER BY created_at DESC"
            )
            users = cursor.fetchall()
            
            user_list = []
            for user in users:
                user_list.append({
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'role': user.get('role', 'user'),
                    'created_at': user['created_at'].isoformat() if user['created_at'] else None,
                    'last_login': user['last_login'].isoformat() if user['last_login'] else None
                })
            
            connection.close()
            return user_list
        
    except Exception as e:
        print(f"获取用户列表错误: {e}")
        return []


def update_user_role(user_id, new_role):
    """
    更新用户角色（仅管理员）
    :param user_id: 用户ID
    :param new_role: 新角色 ('user' 或 'admin')
    :return: (success, message)
    """
    try:
        connection = get_db_connection()
        
        with connection.cursor() as cursor:
            # 检查用户是否存在
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                return False, "用户不存在"
            
            # 更新角色
            cursor.execute(
                "UPDATE users SET role = %s WHERE id = %s",
                (new_role, user_id)
            )
            
        connection.close()
        return True, "角色更新成功"
        
    except Exception as e:
        print(f"更新用户角色错误: {e}")
        return False, f"更新失败: {str(e)}"


def delete_user(user_id, current_user_id):
    """
    删除用户（仅管理员，不能删除自己）
    :param user_id: 要删除的用户ID
    :param current_user_id: 当前登录用户ID
    :return: (success, message)
    """
    try:
        if user_id == current_user_id:
            return False, "不能删除自己的账号"
        
        connection = get_db_connection()
        
        with connection.cursor() as cursor:
            # 检查用户是否存在
            cursor.execute("SELECT id FROM users WHERE id = %s", (user_id,))
            if not cursor.fetchone():
                return False, "用户不存在"
            
            # 删除用户
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            
        connection.close()
        return True, "用户删除成功"
        
    except Exception as e:
        print(f"删除用户错误: {e}")
        return False, f"删除失败: {str(e)}"
