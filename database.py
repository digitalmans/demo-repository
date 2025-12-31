import sqlite3
import hashlib
import time

class Database:
    def __init__(self, db_name='users.db'):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_table()

    def connect(self):
        """连接到SQLite数据库"""
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            print(f"已连接到数据库: {self.db_name}")
        except sqlite3.Error as e:
            print(f"数据库连接错误: {e}")

    def create_table(self):
        """创建用户表"""
        try:
            sql = '''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                last_login TEXT
            );
            '''
            self.cursor.execute(sql)
            self.conn.commit()
            print("用户表创建成功或已存在")
        except sqlite3.Error as e:
            print(f"创建表错误: {e}")

    def hash_password(self, password):
        """使用SHA-256加密密码"""
        return hashlib.sha256(password.encode()).hexdigest()

    def add_user(self, username, password, phone):
        """添加新用户"""
        try:
            hashed_password = self.hash_password(password)
            created_at = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            sql = "INSERT INTO users (username, password, phone, created_at) VALUES (?, ?, ?, ?)"
            self.cursor.execute(sql, (username, hashed_password, phone, created_at))
            self.conn.commit()
            return True, "用户注册成功"
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed: users.username" in str(e):
                return False, "用户名已存在"
            elif "UNIQUE constraint failed: users.phone" in str(e):
                return False, "手机号已被注册"
            else:
                return False, f"注册失败: {e}"
        except sqlite3.Error as e:
            return False, f"注册失败: {e}"

    def verify_password(self, username, password):
        """验证用户名和密码"""
        try:
            hashed_password = self.hash_password(password)
            sql = "SELECT id, username, phone FROM users WHERE username = ? AND password = ?"
            self.cursor.execute(sql, (username, hashed_password))
            user = self.cursor.fetchone()
            if user:
                # 更新最后登录时间
                self.update_last_login(user[0])
                return True, "登录成功", {
                    'id': user[0],
                    'username': user[1],
                    'phone': user[2]
                }
            else:
                return False, "用户名或密码错误", None
        except sqlite3.Error as e:
            return False, f"登录失败: {e}", None

    def verify_phone(self, phone):
        """验证手机号是否存在"""
        try:
            sql = "SELECT id, username FROM users WHERE phone = ?"
            self.cursor.execute(sql, (phone,))
            user = self.cursor.fetchone()
            if user:
                return True, {"id": user[0], "username": user[1]}
            else:
                return False, None
        except sqlite3.Error as e:
            print(f"验证手机号错误: {e}")
            return False, None

    def update_last_login(self, user_id):
        """更新用户最后登录时间"""
        try:
            last_login = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
            sql = "UPDATE users SET last_login = ? WHERE id = ?"
            self.cursor.execute(sql, (last_login, user_id))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"更新最后登录时间错误: {e}")

    def get_user_by_id(self, user_id):
        """根据用户ID获取用户信息"""
        try:
            sql = "SELECT id, username, phone, created_at, last_login FROM users WHERE id = ?"
            self.cursor.execute(sql, (user_id,))
            return self.cursor.fetchone()
        except sqlite3.Error as e:
            print(f"获取用户信息错误: {e}")
            return None

    def get_all_users(self):
        """获取所有用户信息"""
        try:
            sql = "SELECT id, username, phone, created_at, last_login FROM users"
            self.cursor.execute(sql)
            return self.cursor.fetchall()
        except sqlite3.Error as e:
            print(f"获取所有用户错误: {e}")
            return []

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            print("数据库连接已关闭")

# 测试数据库功能
if __name__ == "__main__":
    db = Database()
    
    # 添加测试用户
    print("添加测试用户...")
    result, message = db.add_user("admin", "admin123", "13800138000")
    print(f"管理员用户: {message}")
    
    result, message = db.add_user("user", "user123", "13900139000")
    print(f"普通用户: {message}")
    
    # 验证密码登录
    print("\n验证密码登录...")
    result, message, user = db.verify_password("admin", "admin123")
    print(f"管理员登录: {message}, 用户信息: {user}")
    
    # 验证手机号
    print("\n验证手机号...")
    result, user = db.verify_phone("13900139000")
    print(f"手机号验证: {result}, 用户信息: {user}")
    
    # 获取所有用户
    print("\n所有用户信息:")
    users = db.get_all_users()
    for user in users:
        print(f"ID: {user[0]}, 用户名: {user[1]}, 手机号: {user[2]}, 创建时间: {user[3]}, 最后登录: {user[4]}")
    
    db.close()