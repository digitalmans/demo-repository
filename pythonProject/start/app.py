#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
用户认证系统 - Flask后端
提供登录和注册功能（使用MySQL数据库）
"""

import os
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps
from config import SECRET_KEY
from database import (
    init_database, register_user, verify_user, get_user_info,
    get_all_users, update_user_role, delete_user
)

app = Flask(__name__)
app.secret_key = SECRET_KEY


def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """管理员权限验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            return jsonify({'success': False, 'error': '需要管理员权限'}), 403
        return f(*args, **kwargs)
    return decorated_function


@app.route('/')
def index():
    """首页，重定向到登录页"""
    if 'username' in session:
        return redirect(url_for('voice_assistant'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'success': False, 'error': '用户名和密码不能为空'}), 400
        
        # 验证用户
        success, message, user_data = verify_user(username, password)
        
        if not success:
            return jsonify({'success': False, 'error': message}), 401
        
        # 登录成功，设置session
        session['username'] = username
        session['user_id'] = user_data['id']
        session['role'] = user_data.get('role', 'user')
        
        # 根据角色跳转
        if user_data.get('role') == 'admin':
            return jsonify({
                'success': True, 
                'message': '管理员登录成功', 
                'user': user_data,
                'redirect': '/admin'
            })
        else:
            return jsonify({
                'success': True, 
                'message': '登录成功', 
                'user': user_data,
                'redirect': '/voice_assistant'
            })
    
    # GET请求，返回登录页面
    if 'username' in session:
        return redirect(url_for('voice_assistant'))
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        confirm_password = data.get('confirm_password', '').strip()
        email = data.get('email', '').strip() or None
        
        # 验证输入
        if not username or not password:
            return jsonify({'success': False, 'error': '用户名和密码不能为空'}), 400
        
        if len(username) < 3:
            return jsonify({'success': False, 'error': '用户名至少需要3个字符'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'error': '密码至少需要6个字符'}), 400
        
        if password != confirm_password:
            return jsonify({'success': False, 'error': '两次输入的密码不一致'}), 400
        
        # 注册新用户
        success, message = register_user(username, password, email)
        
        if not success:
            status_code = 409 if '已存在' in message else 400
            return jsonify({'success': False, 'error': message}), status_code
        
        return jsonify({'success': True, 'message': '注册成功，请登录'})
    
    # GET请求，返回注册页面
    return render_template('register.html')


@app.route('/logout')
def logout():
    """登出"""
    session.pop('username', None)
    session.pop('user_id', None)
    session.pop('role', None)
    return redirect(url_for('login'))


@app.route('/voice_assistant')
@login_required
def voice_assistant():
    """语音助手页面（需要登录）"""
    # 重定向到主应用的语音助手
    # 这里可以返回一个包含语音助手功能的页面，或者重定向到主应用
    return render_template('voice_assistant.html', username=session.get('username'))


@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    """管理员后台页面"""
    return render_template('admin.html', username=session.get('username'))


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """管理员登录页面"""
    if request.method == 'POST':
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return jsonify({'success': False, 'error': '用户名和密码不能为空'}), 400
        
        # 验证用户
        success, message, user_data = verify_user(username, password)
        
        if not success:
            return jsonify({'success': False, 'error': message}), 401
        
        # 检查是否为管理员
        if user_data.get('role') != 'admin':
            return jsonify({'success': False, 'error': '该账号不是管理员'}), 403
        
        # 登录成功，设置session
        session['username'] = username
        session['user_id'] = user_data['id']
        session['role'] = 'admin'
        
        return jsonify({
            'success': True, 
            'message': '管理员登录成功', 
            'user': user_data
        })
    
    # GET请求，返回管理员登录页面
    if 'username' in session and session.get('role') == 'admin':
        return redirect(url_for('admin_panel'))
    return render_template('admin_login.html')


@app.route('/api/user_info')
@login_required
def user_info():
    """获取当前用户信息"""
    username = session.get('username')
    user_data = get_user_info(username)
    
    if user_data:
        return jsonify({'success': True, 'user': user_data})
    return jsonify({'success': False, 'error': '用户不存在'}), 404


@app.route('/api/admin/users')
@login_required
@admin_required
def admin_get_users():
    """获取所有用户列表（管理员）"""
    users = get_all_users()
    return jsonify({'success': True, 'users': users})


@app.route('/api/admin/user/<int:user_id>/role', methods=['PUT'])
@login_required
@admin_required
def admin_update_role(user_id):
    """更新用户角色（管理员）"""
    data = request.get_json()
    new_role = data.get('role', '').strip()
    
    if new_role not in ['user', 'admin']:
        return jsonify({'success': False, 'error': '无效的角色'}), 400
    
    success, message = update_user_role(user_id, new_role)
    
    if success:
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'error': message}), 400


@app.route('/api/admin/user/<int:user_id>', methods=['DELETE'])
@login_required
@admin_required
def admin_delete_user(user_id):
    """删除用户（管理员）"""
    current_user_id = session.get('user_id')
    success, message = delete_user(user_id, current_user_id)
    
    if success:
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'error': message}), 400


if __name__ == '__main__':
    print("="*50)
    print("用户认证系统启动中...")
    print("="*50)
    
    # 初始化数据库
    try:
        print("正在初始化数据库...")
        init_database()
        print("数据库初始化成功")
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        print("请检查MySQL服务是否运行，以及config.py中的配置是否正确")
        exit(1)
    
    print("="*50)
    print("访问地址: http://127.0.0.1:5001")
    print("按 Ctrl+C 停止服务器")
    print("="*50)
    app.run(debug=True, host='0.0.0.0', port=5001)
