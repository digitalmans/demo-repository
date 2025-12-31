from flask import Flask, request, jsonify
import sqlite3
import hashlib
import time
import re

app = Flask(__name__)

# 数据库配置
DB_NAME = 'users.db'

# 工具函数
def hash_password(password):
    """使用SHA-256加密密码"""
    return hashlib.sha256(password.encode()).hexdigest()


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """初始化数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            last_login TEXT
        );
    ''')
    
    # 创建测试用户
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        # 添加管理员用户
        admin_password = hash_password('admin123')
        created_at = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        cursor.execute(
            'INSERT INTO users (username, password, phone, created_at) VALUES (?, ?, ?, ?)',
            ('admin', admin_password, '13800138000', created_at)
        )
        
        # 添加普通用户
        user_password = hash_password('user123')
        cursor.execute(
            'INSERT INTO users (username, password, phone, created_at) VALUES (?, ?, ?, ?)',
            ('user', user_password, '13900139000', created_at)
        )
    
    conn.commit()
    conn.close()


@app.route('/api/register', methods=['POST'])
def register():
    """用户注册API"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        phone = data.get('phone')
        
        # 参数验证
        if not all([username, password, phone]):
            return jsonify({'success': False, 'message': '请填写完整的注册信息'}), 400
        
        if len(username) < 3 or len(username) > 20:
            return jsonify({'success': False, 'message': '用户名长度必须在3-20个字符之间'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'message': '密码长度不能少于6个字符'}), 400
        
        if not re.match(r'^1[3-9]\d{9}$', phone):
            return jsonify({'success': False, 'message': '请输入正确的手机号格式'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查用户名是否已存在
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': '用户名已存在'}), 400
        
        # 检查手机号是否已存在
        cursor.execute('SELECT id FROM users WHERE phone = ?', (phone,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': '手机号已被注册'}), 400
        
        # 添加新用户
        hashed_password = hash_password(password)
        created_at = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        
        cursor.execute(
            'INSERT INTO users (username, password, phone, created_at) VALUES (?, ?, ?, ?)',
            (username, hashed_password, phone, created_at)
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': '用户注册成功'}), 201
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'注册失败: {str(e)}'}), 500


@app.route('/api/login/password', methods=['POST'])
def password_login():
    """密码登录API"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # 参数验证
        if not all([username, password]):
            return jsonify({'success': False, 'message': '请填写用户名和密码'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 验证用户名和密码
        hashed_password = hash_password(password)
        cursor.execute(
            'SELECT id, username, phone FROM users WHERE username = ? AND password = ?',
            (username, hashed_password)
        )
        
        user = cursor.fetchone()
        if not user:
            conn.close()
            return jsonify({'success': False, 'message': '用户名或密码错误'}), 401
        
        # 更新最后登录时间
        last_login = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        cursor.execute(
            'UPDATE users SET last_login = ? WHERE id = ?',
            (last_login, user['id'])
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'phone': user['phone']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'登录失败: {str(e)}'}), 500


@app.route('/api/login/sms', methods=['POST'])
def sms_login():
    """手机验证码登录API（模拟）"""
    try:
        data = request.get_json()
        phone = data.get('phone')
        sms_code = data.get('smsCode')
        
        # 参数验证
        if not all([phone, sms_code]):
            return jsonify({'success': False, 'message': '请填写手机号和验证码'}), 400
        
        if not re.match(r'^1[3-9]\d{9}$', phone):
            return jsonify({'success': False, 'message': '请输入正确的手机号格式'}), 400
        
        # 模拟验证码验证（实际项目中应该与发送的验证码进行比对）
        if sms_code != '123456':
            return jsonify({'success': False, 'message': '验证码错误'}), 401
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查手机号是否已注册
        cursor.execute(
            'SELECT id, username, phone FROM users WHERE phone = ?',
            (phone,)
        )
        
        user = cursor.fetchone()
        if not user:
            conn.close()
            return jsonify({'success': False, 'message': '该手机号尚未注册'}), 401
        
        # 更新最后登录时间
        last_login = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        cursor.execute(
            'UPDATE users SET last_login = ? WHERE id = ?',
            (last_login, user['id'])
        )
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': '登录成功',
            'user': {
                'id': user['id'],
                'username': user['username'],
                'phone': user['phone']
            }
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'登录失败: {str(e)}'}), 500


@app.route('/api/send_sms', methods=['POST'])
def send_sms():
    """发送短信验证码API（模拟）"""
    try:
        data = request.get_json()
        phone = data.get('phone')
        
        # 参数验证
        if not phone:
            return jsonify({'success': False, 'message': '请输入手机号'}), 400
        
        if not re.match(r'^1[3-9]\d{9}$', phone):
            return jsonify({'success': False, 'message': '请输入正确的手机号格式'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查手机号是否已注册
        cursor.execute('SELECT id FROM users WHERE phone = ?', (phone,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': '该手机号尚未注册'}), 400
        
        conn.close()
        
        # 模拟发送验证码（实际项目中应该调用短信服务商API）
        print(f"向手机号 {phone} 发送验证码 123456")
        
        return jsonify({
            'success': True,
            'message': '验证码已发送，请注意查收',
            'countdown': 60  # 倒计时秒数
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'发送验证码失败: {str(e)}'}), 500


@app.route('/api/users', methods=['GET'])
def get_users():
    """获取所有用户信息API（仅用于测试）"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, username, phone, created_at, last_login FROM users')
        users = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'success': True,
            'users': [dict(user) for user in users]
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取用户列表失败: {str(e)}'}), 500


# 跨域配置
@app.after_request
def add_cors_headers(response):
    """添加CORS响应头"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response


if __name__ == '__main__':
    # 初始化数据库
    init_db()
    
    # 启动服务器
    print("服务器启动在 http://localhost:5000")
    print("API接口:")
    print("  POST /api/register - 用户注册")
    print("  POST /api/login/password - 密码登录")
    print("  POST /api/login/sms - 手机验证码登录")
    print("  POST /api/send_sms - 发送短信验证码")
    print("  GET /api/users - 获取所有用户信息")
    print("\n测试账号:")
    print("  用户名: admin, 密码: admin123, 手机号: 13800138000")
    print("  用户名: user, 密码: user123, 手机号: 13900139000")
    print("  验证码登录: 任意已注册手机号 + 验证码 123456")
    
    app.run(host='0.0.0.0', port=8000, debug=True)