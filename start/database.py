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
