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
            autocommit=True,
            ssl_disabled=True
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
            charset=MYSQL_CONFIG['charset'],
            ssl_disabled=True
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
                phone VARCHAR(20) DEFAULT NULL,
                birthday DATE DEFAULT NULL,
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

            # 检查是否需要添加phone字段（兼容旧表）
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'users' 
                AND COLUMN_NAME = 'phone'
            """, (MYSQL_CONFIG['database'],))
            if cursor.fetchone()['count'] == 0:
                cursor.execute("ALTER TABLE users ADD COLUMN phone VARCHAR(20) DEFAULT NULL")
                print("已添加phone字段")

            # 检查是否需要添加birthday字段（兼容旧表）
            cursor.execute("""
                SELECT COUNT(*) as count 
                FROM INFORMATION_SCHEMA.COLUMNS 
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = 'users' 
                AND COLUMN_NAME = 'birthday'
            """, (MYSQL_CONFIG['database'],))
            if cursor.fetchone()['count'] == 0:
                cursor.execute("ALTER TABLE users ADD COLUMN birthday DATE DEFAULT NULL")
                print("已添加birthday字段")
            
            # 创建默认管理员账号（如果不存在）
            cursor.execute("SELECT id FROM users WHERE username = 'admin'")
            if not cursor.fetchone():
                admin_password = hash_password('admin123')  # 默认管理员密码
                cursor.execute(
                    "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                    ('admin', admin_password, 'admin')
                )
                print("已创建默认管理员账号: admin / admin123")
            
            # 创建指定管理员账号 daministrator（如果不存在）
            cursor.execute("SELECT id FROM users WHERE username = 'daministrator'")
            if not cursor.fetchone():
                admin_password = hash_password('123456')  # 管理员密码
                cursor.execute(
                    "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                    ('daministrator', admin_password, 'admin')
                )
                print("已创建管理员账号: daministrator / 123456")
            

            # 创建TTS音频文件缓存表
            create_tts_cache_table_sql = """
            CREATE TABLE IF NOT EXISTS tts_audio_cache (
                id INT AUTO_INCREMENT PRIMARY KEY,
                text_hash VARCHAR(64) NOT NULL COMMENT '文本内容的MD5哈希值',
                language VARCHAR(10) NOT NULL DEFAULT 'zh' COMMENT '语言: zh(中文), en(英文)',
                file_path VARCHAR(500) NOT NULL COMMENT '音频文件路径',
                file_size BIGINT COMMENT '文件大小（字节）',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后访问时间',
                access_count INT DEFAULT 0 COMMENT '访问次数',
                UNIQUE KEY uk_text_lang (text_hash, language),
                INDEX idx_text_hash (text_hash),
                INDEX idx_language (language),
                INDEX idx_last_accessed (last_accessed)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cursor.execute(create_tts_cache_table_sql)
            print("TTS音频文件缓存表已创建或已存在")
            
            # 创建问答机器人历史记录表
            create_qa_robot_history_table_sql = """
            CREATE TABLE IF NOT EXISTS qa_robot_history (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                username VARCHAR(50) NOT NULL,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                similarity FLOAT COMMENT '相似度分数',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_user_id (user_id),
                INDEX idx_username (username),
                INDEX idx_created_at (created_at),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cursor.execute(create_qa_robot_history_table_sql)
            print("问答机器人历史记录表已创建或已存在")
            
            # 创建QA讨论区表
            create_qa_discussion_table_sql = """
            CREATE TABLE IF NOT EXISTS qa_discussion (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                username VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                INDEX idx_user_id (user_id),
                INDEX idx_username (username),
                INDEX idx_created_at (created_at),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cursor.execute(create_qa_discussion_table_sql)
            print("QA讨论区表已创建或已存在")
            
            # 创建QA评论表
            create_qa_comments_table_sql = """
            CREATE TABLE IF NOT EXISTS qa_comments (
                id INT AUTO_INCREMENT PRIMARY KEY,
                discussion_id INT NOT NULL,
                user_id INT NOT NULL,
                username VARCHAR(50) NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_discussion_id (discussion_id),
                INDEX idx_user_id (user_id),
                INDEX idx_created_at (created_at),
                FOREIGN KEY (discussion_id) REFERENCES qa_discussion(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cursor.execute(create_qa_comments_table_sql)
            print("QA评论表已创建或已存在")

            # ========== 讨论区增强：给已存在的表补字段 ==========
            # MySQL 8 不支持 `ADD COLUMN IF NOT EXISTS`，改用 information_schema 探测
            cursor.execute("""
                SELECT TABLE_NAME, COLUMN_NAME FROM information_schema.COLUMNS
                WHERE TABLE_SCHEMA = %s
            """, (MYSQL_CONFIG.get('database', 'voice_assistant_db'),))
            existing_cols = {}
            for row in cursor.fetchall():
                existing_cols.setdefault(row['TABLE_NAME'], set()).add(row['COLUMN_NAME'])

            disc_cols = existing_cols.get('qa_discussion', set())
            cmnt_cols = existing_cols.get('qa_comments', set())

            schema_upgrades = [
                ('qa_discussion', 'view_count', 'INT NOT NULL DEFAULT 0'),
                ('qa_discussion', 'like_count', 'INT NOT NULL DEFAULT 0'),
                ('qa_discussion', 'dislike_count', 'INT NOT NULL DEFAULT 0'),
                ('qa_comments',   'like_count', 'INT NOT NULL DEFAULT 0'),
                ('qa_comments',   'dislike_count', 'INT NOT NULL DEFAULT 0'),
            ]
            for tbl, col, col_def in schema_upgrades:
                if col in (disc_cols if tbl == 'qa_discussion' else cmnt_cols):
                    continue  # 已存在
                try:
                    cursor.execute(f"ALTER TABLE {tbl} ADD COLUMN {col} {col_def}")
                    print(f"[schema] {tbl}.{col} 已添加")
                except Exception as e:
                    print(f"[schema] 添加 {tbl}.{col} 失败: {e}")

            # 点赞/点踩记录表（用户对讨论或评论的投票）
            create_qa_likes_table_sql = """
            CREATE TABLE IF NOT EXISTS qa_likes (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                target_type ENUM('discussion', 'comment') NOT NULL,
                target_id INT NOT NULL,
                vote_type ENUM('like', 'dislike') NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uk_user_target (user_id, target_type, target_id),
                INDEX idx_target (target_type, target_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cursor.execute(create_qa_likes_table_sql)
            print("QA点赞/点踩表已创建或已存在")

            # 收藏夹表
            create_qa_favorites_table_sql = """
            CREATE TABLE IF NOT EXISTS qa_favorites (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                discussion_id INT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE KEY uk_user_disc (user_id, discussion_id),
                INDEX idx_user_id (user_id),
                INDEX idx_discussion_id (discussion_id),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (discussion_id) REFERENCES qa_discussion(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cursor.execute(create_qa_favorites_table_sql)
            print("QA收藏表已创建或已存在")

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
                "SELECT id, username, password, email, phone, birthday, role, created_at FROM users WHERE username = %s",
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
                'phone': user.get('phone'),
                'birthday': user['birthday'].strftime('%Y-%m-%d') if user.get('birthday') else None,
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
                "SELECT id, username, email, phone, birthday, role, created_at, last_login FROM users WHERE username = %s",
                (username,)
            )
            user = cursor.fetchone()
            
            if user:
                user_data = {
                    'id': user['id'],
                    'username': user['username'],
                    'email': user['email'],
                    'phone': user.get('phone'),
                    'birthday': user['birthday'].strftime('%Y-%m-%d') if user.get('birthday') else None,
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


def update_user_profile(user_id, new_username, new_email=None, new_phone=None, new_birthday=None):
    """
    更新用户个人资料
    :param user_id: 用户ID
    :param new_username: 新用户名
    :param new_email: 新邮箱
    :param new_phone: 新手机号
    :param new_birthday: 新生日 (YYYY-MM-DD)
    :return: (success, message)
    """
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # 检查用户名是否被其他人占用
            cursor.execute("SELECT id FROM users WHERE username = %s AND id != %s", (new_username, user_id))
            if cursor.fetchone():
                connection.close()
                return False, "该用户名已被其他账号占用"
            
            # 如果是空字符串转为None
            email = new_email.strip() if new_email and new_email.strip() else None
            phone = new_phone.strip() if new_phone and new_phone.strip() else None
            birthday = new_birthday.strip() if new_birthday and new_birthday.strip() else None
            
            sql = """
                UPDATE users 
                SET username = %s, email = %s, phone = %s, birthday = %s 
                WHERE id = %s
            """
            cursor.execute(sql, (new_username, email, phone, birthday, user_id))
            connection.commit()
        connection.close()
        return True, "更新个人资料成功"
    except Exception as e:
        print(f"更新个人资料错误: {e}")
        return False, f"更新失败: {str(e)}"


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



        
    except Exception as e:
        print(f"获取历史记录总数错误: {e}")
        return 0


def get_tts_audio_cache(text, language='zh'):
    """
    获取TTS音频缓存
    :param text: 文本内容
    :param language: 语言（'zh' 或 'en'）
    :return: (success, file_path) 如果找到缓存返回文件路径，否则返回None
    """
    try:
        connection = get_db_connection()
        
        # 计算文本的MD5哈希值
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        
        with connection.cursor() as cursor:
            # 查询缓存
            cursor.execute(
                "SELECT file_path FROM tts_audio_cache WHERE text_hash = %s AND language = %s",
                (text_hash, language)
            )
            result = cursor.fetchone()
            
            if result:
                file_path = result['file_path']
                # 检查文件是否存在
                import os
                if os.path.exists(file_path):
                    # 更新访问次数和最后访问时间
                    cursor.execute(
                        "UPDATE tts_audio_cache SET access_count = access_count + 1, last_accessed = CURRENT_TIMESTAMP WHERE text_hash = %s AND language = %s",
                        (text_hash, language)
                    )
                    connection.close()
                    return True, file_path
                else:
                    # 文件不存在，删除缓存记录
                    cursor.execute(
                        "DELETE FROM tts_audio_cache WHERE text_hash = %s AND language = %s",
                        (text_hash, language)
                    )
        
        connection.close()
        return False, None
        
    except Exception as e:
        print(f"获取TTS缓存错误: {e}")
        return False, None


def save_tts_audio_cache(text, language, file_path):
    """
    保存TTS音频缓存
    :param text: 文本内容
    :param language: 语言（'zh' 或 'en'）
    :param file_path: 音频文件路径
    :return: (success, message)
    """
    try:
        connection = get_db_connection()
        
        # 计算文本的MD5哈希值
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        
        # 获取文件大小
        import os
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else None
        
        with connection.cursor() as cursor:
            # 使用 INSERT ... ON DUPLICATE KEY UPDATE 来处理重复
            cursor.execute(
                """INSERT INTO tts_audio_cache (text_hash, language, file_path, file_size, access_count)
                   VALUES (%s, %s, %s, %s, 1)
                   ON DUPLICATE KEY UPDATE 
                   file_path = VALUES(file_path),
                   file_size = VALUES(file_size),
                   access_count = access_count + 1,
                   last_accessed = CURRENT_TIMESTAMP""",
                (text_hash, language, file_path, file_size)
            )
        
        connection.close()
        return True, "缓存保存成功"
        
    except Exception as e:
        print(f"保存TTS缓存错误: {e}")
        return False, f"保存失败: {str(e)}"


def delete_all_tts_audio_files(delete_db_records=True):
    """
    删除所有TTS音频缓存文件
    :param delete_db_records: 是否同时删除数据库记录，默认为True
    :return: (success, message, deleted_count)
    """
    try:
        import os
        connection = get_db_connection()
        
        deleted_count = 0
        failed_count = 0
        not_found_count = 0
        
        with connection.cursor() as cursor:
            # 获取所有缓存记录
            cursor.execute("SELECT id, file_path FROM tts_audio_cache")
            records = cursor.fetchall()
            
            for record in records:
                file_path = record['file_path']
                record_id = record['id']
                
                # 删除物理文件
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                        print(f"已删除文件: {file_path}")
                    except Exception as e:
                        failed_count += 1
                        print(f"删除文件失败 {file_path}: {e}")
                else:
                    not_found_count += 1
                    print(f"文件不存在: {file_path}")
                
                # 如果选择删除数据库记录
                if delete_db_records:
                    cursor.execute("DELETE FROM tts_audio_cache WHERE id = %s", (record_id,))
        
        connection.close()
        
        message = f"删除完成: 成功删除 {deleted_count} 个文件"
        if not_found_count > 0:
            message += f", {not_found_count} 个文件不存在"
        if failed_count > 0:
            message += f", {failed_count} 个文件删除失败"
        if delete_db_records:
            message += ", 数据库记录已清除"
        
        return True, message, deleted_count
        
    except Exception as e:
        print(f"删除TTS音频文件错误: {e}")
        return False, f"删除失败: {str(e)}", 0





def save_qa_robot_history(user_id, username, question, answer, similarity=None):
    """
    保存问答机器人历史记录
    :param user_id: 用户ID
    :param username: 用户名
    :param question: 问题
    :param answer: 答案
    :param similarity: 相似度分数（可选）
    :return: (success, message, history_id)
    """
    try:
        connection = get_db_connection()
        
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO qa_robot_history (user_id, username, question, answer, similarity) VALUES (%s, %s, %s, %s, %s)",
                (user_id, username, question, answer, similarity)
            )
            history_id = cursor.lastrowid
        
        connection.close()
        return True, "历史记录保存成功", history_id
        
    except Exception as e:
        print(f"保存历史记录错误: {e}")
        return False, f"保存失败: {str(e)}", None


def get_qa_robot_history(user_id, limit=100, offset=0):
    """
    获取用户的问答机器人历史记录
    :param user_id: 用户ID
    :param limit: 返回记录数限制
    :param offset: 偏移量
    :return: 历史记录列表
    """
    try:
        connection = get_db_connection()
        
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, question, answer, similarity, created_at 
                FROM qa_robot_history 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s OFFSET %s
                """,
                (user_id, limit, offset)
            )
            records = cursor.fetchall()
            
            history_list = []
            for record in records:
                history_list.append({
                    'id': record['id'],
                    'question': record['question'],
                    'answer': record['answer'],
                    'similarity': float(record['similarity']) if record['similarity'] else None,
                    'created_at': record['created_at'].isoformat() if record['created_at'] else None
                })
        
        connection.close()
        return history_list
        
    except Exception as e:
        print(f"获取历史记录错误: {e}")
        return []


def get_qa_robot_history_count(user_id):
    """
    获取用户的问答机器人历史记录总数
    :param user_id: 用户ID
    :return: 记录总数
    """
    try:
        connection = get_db_connection()
        
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT COUNT(*) as count FROM qa_robot_history WHERE user_id = %s",
                (user_id,)
            )
            result = cursor.fetchone()
            count = result['count'] if result else 0
        
        connection.close()
        return count
        
    except Exception as e:
        print(f"获取历史记录总数错误: {e}")
        return 0


def delete_qa_robot_history(user_id, history_id=None):
    """
    删除问答机器人历史记录
    :param user_id: 用户ID
    :param history_id: 历史记录ID，如果为None则删除该用户的所有记录
    :return: (success, message)
    """
    try:
        connection = get_db_connection()
        
        with connection.cursor() as cursor:
            if history_id:
                # 删除指定记录（只能删除自己的）
                cursor.execute(
                    "DELETE FROM qa_robot_history WHERE id = %s AND user_id = %s",
                    (history_id, user_id)
                )
            else:
                # 删除该用户的所有记录
                cursor.execute(
                    "DELETE FROM qa_robot_history WHERE user_id = %s",
                    (user_id,)
                )
        
        connection.close()
        return True, "删除成功"
        
    except Exception as e:
        print(f"删除历史记录错误: {e}")
        return False, f"删除失败: {str(e)}"


# QA讨论区相关函数
def save_qa_discussion(user_id, username, content):
    """保存QA讨论内容"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "INSERT INTO qa_discussion (user_id, username, content) VALUES (%s, %s, %s)",
                (user_id, username, content)
            )
            discussion_id = cursor.lastrowid
        connection.close()
        return True, "发布成功", discussion_id
    except Exception as e:
        print(f"保存讨论内容错误: {e}")
        return False, f"发布失败: {str(e)}", None


def get_qa_discussions(limit=50, offset=0):
    """获取QA讨论列表"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, user_id, username, content, created_at, updated_at FROM qa_discussion ORDER BY created_at DESC LIMIT %s OFFSET %s",
                (limit, offset)
            )
            discussions = cursor.fetchall()
            discussion_list = []
            for disc in discussions:
                discussion_list.append({
                    'id': disc['id'],
                    'user_id': disc['user_id'],
                    'username': disc['username'],
                    'content': disc['content'],
                    'created_at': disc['created_at'].isoformat() if disc['created_at'] else None,
                    'updated_at': disc['updated_at'].isoformat() if disc['updated_at'] else None
                })
        connection.close()
        return discussion_list
    except Exception as e:
        print(f"获取讨论列表错误: {e}")
        return []


def get_qa_discussion_count():
    """获取讨论总数"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) as count FROM qa_discussion")
            result = cursor.fetchone()
            count = result['count'] if result else 0
        connection.close()
        return count
    except Exception as e:
        print(f"获取讨论总数错误: {e}")
        return 0


def delete_qa_discussion(discussion_id, user_id=None, is_admin=False):
    """删除讨论"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            if not is_admin and user_id:
                cursor.execute("DELETE FROM qa_discussion WHERE id = %s AND user_id = %s", (discussion_id, user_id))
            else:
                cursor.execute("DELETE FROM qa_discussion WHERE id = %s", (discussion_id,))
            if cursor.rowcount > 0:
                connection.close()
                return True, "删除成功"
            else:
                connection.close()
                return False, "删除失败：讨论不存在或无权删除"
    except Exception as e:
        print(f"删除讨论错误: {e}")
        return False, f"删除失败: {str(e)}"


def save_qa_comment(discussion_id, user_id, username, content):
    """保存QA评论"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM qa_discussion WHERE id = %s", (discussion_id,))
            if not cursor.fetchone():
                return False, "讨论不存在", None
            cursor.execute(
                "INSERT INTO qa_comments (discussion_id, user_id, username, content) VALUES (%s, %s, %s, %s)",
                (discussion_id, user_id, username, content)
            )
            comment_id = cursor.lastrowid
        connection.close()
        return True, "评论成功", comment_id
    except Exception as e:
        print(f"保存评论错误: {e}")
        return False, f"评论失败: {str(e)}", None


def get_qa_comments(discussion_id):
    """获取某个讨论的所有评论"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, discussion_id, user_id, username, content, created_at FROM qa_comments WHERE discussion_id = %s ORDER BY created_at ASC",
                (discussion_id,)
            )
            comments = cursor.fetchall()
            comment_list = []
            for comment in comments:
                comment_list.append({
                    'id': comment['id'],
                    'discussion_id': comment['discussion_id'],
                    'user_id': comment['user_id'],
                    'username': comment['username'],
                    'content': comment['content'],
                    'created_at': comment['created_at'].isoformat() if comment['created_at'] else None
                })
        connection.close()
        return comment_list
    except Exception as e:
        print(f"获取评论列表错误: {e}")
        return []


def delete_qa_comment(comment_id, user_id=None, is_admin=False):
    """删除评论"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            if not is_admin and user_id:
                cursor.execute("DELETE FROM qa_comments WHERE id = %s AND user_id = %s", (comment_id, user_id))
            else:
                cursor.execute("DELETE FROM qa_comments WHERE id = %s", (comment_id,))
            if cursor.rowcount > 0:
                connection.close()
                return True, "删除成功"
            else:
                connection.close()
                return False, "删除失败：评论不存在或无权删除"
    except Exception as e:
        print(f"删除评论错误: {e}")
        return False, f"删除失败: {str(e)}"


# ============================================================
# 讨论区增强功能：点赞/点踩、收藏、浏览量、热度排序、@提及解析
# ============================================================

def get_qa_discussions_extended(sort='latest', limit=20, offset=0, keyword=None):
    """
    获取讨论列表（支持最新/最热/搜索）
    :param sort: 'latest' 最新 / 'hot' 最热
    :param limit: 每页数量
    :param offset: 偏移量
    :param keyword: 搜索关键词（匹配内容/用户名）
    """
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            where_clauses = []
            params = []

            if keyword:
                where_clauses.append("(d.content LIKE %s OR d.username LIKE %s)")
                kw = f"%{keyword}%"
                params.extend([kw, kw])

            where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

            if sort == 'hot':
                # 热度公式：点赞*2 - 点踩 + 评论数*1.5
                order_sql = "ORDER BY (d.like_count * 2 - d.dislike_count) DESC, d.created_at DESC"
            else:
                order_sql = "ORDER BY d.created_at DESC"

            sql = f"""
                SELECT d.id, d.user_id, d.username, d.content,
                       d.created_at, d.updated_at,
                       d.view_count, d.like_count, d.dislike_count
                FROM qa_discussion d
                {where_sql}
                {order_sql}
                LIMIT %s OFFSET %s
            """
            cursor.execute(sql, params + [limit, offset])
            discussions = cursor.fetchall()

            discussion_list = []
            for disc in discussions:
                cursor.execute("SELECT COUNT(*) AS c FROM qa_comments WHERE discussion_id = %s", (disc['id'],))
                ccnt = cursor.fetchone()['c'] or 0
                lc = disc.get('like_count', 0) or 0
                dc = disc.get('dislike_count', 0) or 0
                discussion_list.append({
                    'id': disc['id'],
                    'user_id': disc['user_id'],
                    'username': disc['username'],
                    'content': disc['content'],
                    'created_at': disc['created_at'].isoformat() if disc['created_at'] else None,
                    'updated_at': disc['updated_at'].isoformat() if disc['updated_at'] else None,
                    'view_count': disc.get('view_count', 0) or 0,
                    'like_count': lc,
                    'dislike_count': dc,
                    'comment_count': ccnt,
                    'hot_score': lc * 2 - dc + ccnt * 1.5,
                })
        connection.close()
        return discussion_list
    except Exception as e:
        print(f"获取讨论列表(扩展)错误: {e}")
        return []


def get_qa_discussion_count_extended(keyword=None):
    """获取讨论总数（支持搜索）"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            if keyword:
                kw = f"%{keyword}%"
                cursor.execute(
                    "SELECT COUNT(*) AS c FROM qa_discussion WHERE content LIKE %s OR username LIKE %s",
                    (kw, kw)
                )
            else:
                cursor.execute("SELECT COUNT(*) AS c FROM qa_discussion")
            result = cursor.fetchone()
            count = result['c'] if result else 0
        connection.close()
        return count
    except Exception as e:
        print(f"获取讨论总数(扩展)错误: {e}")
        return 0


def get_qa_discussion_detail(discussion_id, increment_view=False):
    """
    获取单条讨论详情（包含完整统计字段）
    :param increment_view: 是否+1 浏览量
    """
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            if increment_view:
                cursor.execute(
                    "UPDATE qa_discussion SET view_count = view_count + 1 WHERE id = %s",
                    (discussion_id,)
                )
            cursor.execute(
                """SELECT id, user_id, username, content, created_at, updated_at,
                          view_count, like_count, dislike_count
                   FROM qa_discussion WHERE id = %s""",
                (discussion_id,)
            )
            disc = cursor.fetchone()
            if not disc:
                connection.close()
                return None
            cursor.execute("SELECT COUNT(*) AS c FROM qa_comments WHERE discussion_id = %s", (disc['id'],))
            ccnt = cursor.fetchone()['c'] or 0
            lc = disc.get('like_count', 0) or 0
            dc = disc.get('dislike_count', 0) or 0
            result = {
                'id': disc['id'],
                'user_id': disc['user_id'],
                'username': disc['username'],
                'content': disc['content'],
                'created_at': disc['created_at'].isoformat() if disc['created_at'] else None,
                'updated_at': disc['updated_at'].isoformat() if disc['updated_at'] else None,
                'view_count': disc.get('view_count', 0) or 0,
                'like_count': lc,
                'dislike_count': dc,
                'comment_count': ccnt,
                'hot_score': lc * 2 - dc + ccnt * 1.5,
            }
        connection.close()
        return result
    except Exception as e:
        print(f"获取讨论详情错误: {e}")
        return None


def vote_qa_target(user_id, target_type, target_id, vote_type):
    """
    对讨论/评论点赞或点踩
    :return: (success, message, current_like_count, current_dislike_count, user_vote)
    - user_vote: 'like' / 'dislike' / None
    """
    if target_type not in ('discussion', 'comment'):
        return False, "目标类型错误", 0, 0, None
    if vote_type not in ('like', 'dislike', 'cancel'):
        return False, "投票类型错误", 0, 0, None
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # 确认目标存在
            if target_type == 'discussion':
                cursor.execute("SELECT id, like_count, dislike_count FROM qa_discussion WHERE id = %s", (target_id,))
            else:
                cursor.execute("SELECT id, like_count, dislike_count FROM qa_comments WHERE id = %s", (target_id,))
            target = cursor.fetchone()
            if not target:
                connection.close()
                return False, "目标不存在", 0, 0, None

            # 查已有投票
            cursor.execute(
                "SELECT id, vote_type FROM qa_likes WHERE user_id=%s AND target_type=%s AND target_id=%s",
                (user_id, target_type, target_id)
            )
            existing = cursor.fetchone()
            old_vote = existing['vote_type'] if existing else None

            # 同票幂等保护：如果新票与旧票完全相同，等同于取消
            if old_vote and vote_type == old_vote:
                new_vote = None
            elif vote_type == 'cancel':
                new_vote = None
            else:
                new_vote = vote_type

            # 取消原票
            if old_vote:
                cursor.execute("DELETE FROM qa_likes WHERE id=%s", (existing['id'],))
                col = 'like_count' if old_vote == 'like' else 'dislike_count'
                if target_type == 'discussion':
                    cursor.execute(f"UPDATE qa_discussion SET {col} = GREATEST({col} - 1, 0) WHERE id=%s", (target_id,))
                else:
                    cursor.execute(f"UPDATE qa_comments SET {col} = GREATEST({col} - 1, 0) WHERE id=%s", (target_id,))

            # 添加新票
            if new_vote and new_vote != old_vote:
                cursor.execute(
                    "INSERT INTO qa_likes (user_id, target_type, target_id, vote_type) VALUES (%s,%s,%s,%s)",
                    (user_id, target_type, target_id, new_vote)
                )
                col = 'like_count' if new_vote == 'like' else 'dislike_count'
                if target_type == 'discussion':
                    cursor.execute(f"UPDATE qa_discussion SET {col} = {col} + 1 WHERE id=%s", (target_id,))
                else:
                    cursor.execute(f"UPDATE qa_comments SET {col} = {col} + 1 WHERE id=%s", (target_id,))

            # 拿最新计数
            if target_type == 'discussion':
                cursor.execute("SELECT like_count, dislike_count FROM qa_discussion WHERE id=%s", (target_id,))
            else:
                cursor.execute("SELECT like_count, dislike_count FROM qa_comments WHERE id=%s", (target_id,))
            row = cursor.fetchone()
        connection.close()
        return True, "投票成功", row['like_count'], row['dislike_count'], new_vote
    except Exception as e:
        print(f"投票错误: {e}")
        return False, f"投票失败: {str(e)}", 0, 0, None


def get_user_votes(user_id, target_type, target_ids):
    """
    批量获取某用户对一组 target_id 的投票状态
    :return: {target_id: 'like'/'dislike'/None}
    """
    if not target_ids:
        return {}
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            placeholders = ','.join(['%s'] * len(target_ids))
            cursor.execute(
                f"""SELECT target_id, vote_type FROM qa_likes
                    WHERE user_id=%s AND target_type=%s AND target_id IN ({placeholders})""",
                [user_id, target_type] + list(target_ids)
            )
            rows = cursor.fetchall()
        connection.close()
        result = {tid: None for tid in target_ids}
        for r in rows:
            result[r['target_id']] = r['vote_type']
        return result
    except Exception as e:
        print(f"获取投票状态错误: {e}")
        return {tid: None for tid in target_ids}


def get_qa_comments_extended(discussion_id, user_id=None):
    """获取评论列表（带点赞统计、@提及解析）"""
    import re
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT id, discussion_id, user_id, username, content,
                          created_at, like_count, dislike_count
                   FROM qa_comments WHERE discussion_id = %s ORDER BY created_at ASC""",
                (discussion_id,)
            )
            comments = cursor.fetchall()
            comment_list = []
            ids = [c['id'] for c in comments]
            votes_map = get_user_votes(user_id, 'comment', ids) if user_id and ids else {i: None for i in ids}
            for c in comments:
                mentioned = re.findall(r'@([\w一-龥]{1,30})', c['content'] or '')
                comment_list.append({
                    'id': c['id'],
                    'discussion_id': c['discussion_id'],
                    'user_id': c['user_id'],
                    'username': c['username'],
                    'content': c['content'],
                    'created_at': c['created_at'].isoformat() if c['created_at'] else None,
                    'like_count': c.get('like_count', 0) or 0,
                    'dislike_count': c.get('dislike_count', 0) or 0,
                    'user_vote': votes_map.get(c['id']),
                    'mentioned_users': mentioned,
                })
        connection.close()
        return comment_list
    except Exception as e:
        print(f"获取评论(扩展)错误: {e}")
        return []


def toggle_favorite(user_id, discussion_id):
    """收藏/取消收藏讨论。返回 (success, message, is_favorited)"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM qa_discussion WHERE id=%s", (discussion_id,))
            if not cursor.fetchone():
                connection.close()
                return False, "讨论不存在", False
            cursor.execute(
                "SELECT id FROM qa_favorites WHERE user_id=%s AND discussion_id=%s",
                (user_id, discussion_id)
            )
            existing = cursor.fetchone()
            if existing:
                cursor.execute("DELETE FROM qa_favorites WHERE id=%s", (existing['id'],))
                connection.close()
                return True, "已取消收藏", False
            else:
                cursor.execute(
                    "INSERT INTO qa_favorites (user_id, discussion_id) VALUES (%s, %s)",
                    (user_id, discussion_id)
                )
                connection.close()
                return True, "收藏成功", True
    except Exception as e:
        print(f"收藏切换错误: {e}")
        return False, f"操作失败: {str(e)}", False


def is_favorited(user_id, discussion_id):
    """是否已收藏"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id FROM qa_favorites WHERE user_id=%s AND discussion_id=%s",
                (user_id, discussion_id)
            )
            row = cursor.fetchone()
        connection.close()
        return row is not None
    except Exception as e:
        print(f"查询收藏状态错误: {e}")
        return False


def get_user_favorited_ids(user_id, discussion_ids):
    """批量查询某用户对一组讨论的收藏状态"""
    if not discussion_ids:
        return {}
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            placeholders = ','.join(['%s'] * len(discussion_ids))
            cursor.execute(
                f"""SELECT discussion_id FROM qa_favorites
                    WHERE user_id=%s AND discussion_id IN ({placeholders})""",
                [user_id] + list(discussion_ids)
            )
            rows = cursor.fetchall()
        connection.close()
        result = {tid: False for tid in discussion_ids}
        for r in rows:
            result[r['discussion_id']] = True
        return result
    except Exception as e:
        print(f"批量查询收藏状态错误: {e}")
        return {tid: False for tid in discussion_ids}


def get_user_profile(username):
    """
    获取个人主页数据：用户信息、发布数、评论数、收藏数、获赞总数
    """
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, username, email, phone, birthday, role, created_at FROM users WHERE username=%s", (username,))
            user = cursor.fetchone()
            if not user:
                connection.close()
                return None
            uid = user['id']

            cursor.execute("SELECT COUNT(*) AS c FROM qa_discussion WHERE user_id=%s", (uid,))
            discussion_count = cursor.fetchone()['c'] or 0

            cursor.execute("SELECT COUNT(*) AS c FROM qa_comments WHERE user_id=%s", (uid,))
            comment_count = cursor.fetchone()['c'] or 0

            cursor.execute("SELECT COUNT(*) AS c FROM qa_favorites WHERE user_id=%s", (uid,))
            favorite_count = cursor.fetchone()['c'] or 0

            # 累计获得点赞
            cursor.execute(
                "SELECT IFNULL(SUM(like_count),0) AS total_likes FROM qa_discussion WHERE user_id=%s",
                (uid,)
            )
            disc_likes = cursor.fetchone()['total_likes'] or 0
            cursor.execute(
                "SELECT IFNULL(SUM(like_count),0) AS total_likes FROM qa_comments WHERE user_id=%s",
                (uid,)
            )
            cmt_likes = cursor.fetchone()['total_likes'] or 0
            total_likes = disc_likes + cmt_likes

            cursor.execute(
                "SELECT IFNULL(SUM(view_count),0) AS total_views FROM qa_discussion WHERE user_id=%s",
                (uid,)
            )
            total_views = cursor.fetchone()['total_views'] or 0

        connection.close()
        # 把 Decimal 转成 int，避免前端类型不一致
        return {
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user.get('email'),
                'phone': user.get('phone'),
                'birthday': user['birthday'].strftime('%Y-%m-%d') if user.get('birthday') else None,
                'role': user.get('role', 'user'),
                'created_at': user['created_at'].isoformat() if user.get('created_at') else None,
            },
            'stats': {
                'discussion_count': int(discussion_count),
                'comment_count': int(comment_count),
                'favorite_count': int(favorite_count),
                'total_likes': int(total_likes),
                'total_views': int(total_views),
            }
        }
    except Exception as e:
        print(f"获取个人主页数据错误: {e}")
        return None


def get_user_discussions(user_id, limit=20, offset=0):
    """获取某用户发布的讨论列表"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT id, user_id, username, content, created_at, updated_at,
                          view_count, like_count, dislike_count
                   FROM qa_discussion WHERE user_id=%s
                   ORDER BY created_at DESC LIMIT %s OFFSET %s""",
                (user_id, limit, offset)
            )
            rows = cursor.fetchall()
            result = []
            for d in rows:
                cursor.execute("SELECT COUNT(*) AS c FROM qa_comments WHERE discussion_id=%s", (d['id'],))
                ccnt = cursor.fetchone()['c'] or 0
                result.append({
                    'id': d['id'],
                    'user_id': d['user_id'],
                    'username': d['username'],
                    'content': d['content'],
                    'created_at': d['created_at'].isoformat() if d['created_at'] else None,
                    'view_count': d.get('view_count', 0) or 0,
                    'like_count': d.get('like_count', 0) or 0,
                    'dislike_count': d.get('dislike_count', 0) or 0,
                    'comment_count': ccnt,
                })
        connection.close()
        return result
    except Exception as e:
        print(f"获取用户讨论列表错误: {e}")
        return []


def get_user_comments(user_id, limit=20, offset=0):
    """获取某用户发表的评论列表（含所属讨论预览）"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT c.id, c.discussion_id, c.user_id, c.username, c.content,
                          c.created_at, c.like_count, c.dislike_count,
                          LEFT(d.content, 80) AS discussion_preview
                   FROM qa_comments c
                   JOIN qa_discussion d ON c.discussion_id = d.id
                   WHERE c.user_id=%s
                   ORDER BY c.created_at DESC LIMIT %s OFFSET %s""",
                (user_id, limit, offset)
            )
            rows = cursor.fetchall()
            result = []
            for c in rows:
                result.append({
                    'id': c['id'],
                    'discussion_id': c['discussion_id'],
                    'user_id': c['user_id'],
                    'username': c['username'],
                    'content': c['content'],
                    'created_at': c['created_at'].isoformat() if c['created_at'] else None,
                    'like_count': c.get('like_count', 0) or 0,
                    'dislike_count': c.get('dislike_count', 0) or 0,
                    'discussion_preview': c.get('discussion_preview', ''),
                })
        connection.close()
        return result
    except Exception as e:
        print(f"获取用户评论列表错误: {e}")
        return []


def get_user_favorites(user_id, limit=20, offset=0):
    """获取某用户收藏的讨论列表"""
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT d.id, d.user_id, d.username, d.content, d.created_at,
                          d.view_count, d.like_count, d.dislike_count,
                          f.created_at AS favorited_at
                   FROM qa_favorites f
                   JOIN qa_discussion d ON f.discussion_id = d.id
                   WHERE f.user_id=%s
                   ORDER BY f.created_at DESC LIMIT %s OFFSET %s""",
                (user_id, limit, offset)
            )
            rows = cursor.fetchall()
            result = []
            for d in rows:
                cursor.execute("SELECT COUNT(*) AS c FROM qa_comments WHERE discussion_id=%s", (d['id'],))
                ccnt = cursor.fetchone()['c'] or 0
                result.append({
                    'id': d['id'],
                    'user_id': d['user_id'],
                    'username': d['username'],
                    'content': d['content'],
                    'created_at': d['created_at'].isoformat() if d['created_at'] else None,
                    'view_count': d.get('view_count', 0) or 0,
                    'like_count': d.get('like_count', 0) or 0,
                    'dislike_count': d.get('dislike_count', 0) or 0,
                    'comment_count': ccnt,
                    'favorited_at': d['favorited_at'].isoformat() if d['favorited_at'] else None,
                })
        connection.close()
        return result
    except Exception as e:
        print(f"获取用户收藏列表错误: {e}")
        return []

