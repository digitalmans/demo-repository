#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
用户认证系统 - Flask后端
提供登录和注册功能（使用MySQL数据库）
"""

import os
import sys

# 在导入任何模块之前设置 TensorFlow 环境变量，避免导入时的警告和错误
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"  # 屏蔽 TensorFlow 的 INFO、WARNING、ERROR 日志
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"  # 禁用 oneDNN 优化，避免警告
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from functools import wraps
from werkzeug.utils import secure_filename
from config import SECRET_KEY
from database import (
    init_database, register_user, verify_user, get_user_info,
    get_all_users, update_user_role, delete_user,

    save_qa_robot_history, get_qa_robot_history, get_qa_robot_history_count,
    delete_qa_robot_history,
    get_tts_audio_cache, save_tts_audio_cache,
    save_qa_discussion, get_qa_discussions, get_qa_discussion_count,
    delete_qa_discussion,
    save_qa_comment, get_qa_comments, delete_qa_comment,
    # 增强功能
    get_qa_discussions_extended, get_qa_discussion_count_extended,
    get_qa_discussion_detail, vote_qa_target, get_user_votes,
    get_qa_comments_extended, toggle_favorite, is_favorited,
    get_user_favorited_ids, get_user_profile,
    get_user_discussions, get_user_comments, get_user_favorites
)

# 添加 voice_assistant 目录到路径，以便导入 asr 和 tts 模块
voice_assistant_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'voice_assistant')
if voice_assistant_path not in sys.path:
    sys.path.insert(0, voice_assistant_path)

# 移除了电影问答目录到路径


# 添加 ask_answer_robot 目录到路径，以便导入问答机器人服务
qa_robot_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                              'ask_answer_robot')
if qa_robot_path not in sys.path:
    sys.path.insert(0, qa_robot_path)

# 添加 voice_assistant 目录到路径，以便导入翻译模块
if voice_assistant_path not in sys.path:
    sys.path.insert(0, voice_assistant_path)

try:
    from asr import asr, DemoError as ASRError
    from tts import tts, DemoError as TTSError
    VOICE_ASSISTANT_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入语音助手模块: {e}")
    VOICE_ASSISTANT_AVAILABLE = False

# 导入翻译模块
try:
    from translator import translate, translate_to_chinese, translate_to_english, TranslationError
    TRANSLATOR_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入翻译模块: {e}")
    TRANSLATOR_AVAILABLE = False

app = Flask(__name__)
app.secret_key = SECRET_KEY


# 导入问答机器人服务
QA_ROBOT_AVAILABLE = False
qa_robot_service = None
try:
    from qa_service import QAService
    QA_ROBOT_AVAILABLE = True
    print("✓ 问答机器人模块导入成功")
except ImportError as e:
    print(f"✗ 警告: 无法导入问答机器人模块: {e}")
    print(f"  提示: 请确保已安装 py2neo 和 jieba 等依赖")
    QA_ROBOT_AVAILABLE = False

# 初始化问答机器人服务
if QA_ROBOT_AVAILABLE:
    try:
        print("正在初始化问答机器人服务...")
        # 默认不使用BERT，限制初始加载数量，避免启动时等待过久
        qa_robot_service = QAService(use_bert=False, max_initial_load=20000)
        print("✓ 问答机器人服务初始化成功")
        print("  提示: 当前使用text_similarity方法（BM25+Jaccard+编辑距离）")
        print("  提示: 初始仅加载20000条数据，如需更多请修改 max_initial_load 参数")
        print("  如需使用BERT，请修改代码设置 use_bert=True 并启动BERT服务")
    except Exception as e:
        print(f"✗ 警告: 问答机器人服务初始化失败: {e}")
        import traceback
        traceback.print_exc()
        print("\n提示: 请确保:")
        print("  1. 已安装 py2neo: pip install py2neo")
        print("  2. 已安装 jieba: pip install jieba")
        print("  3. Neo4j 服务已启动并可以连接")
        print("  4. 已导入语料库数据到Neo4j")
        QA_ROBOT_AVAILABLE = False
        qa_robot_service = None

# 导入DeepSeek服务
DEEPSEEK_AVAILABLE = False
deepseek_service = None
DEEPSEEK_PRESETS = {}
try:
    from deepseek_service import (
        DeepSeekService,
        DeepSeekAPIError,
        DEEPSEEK_PRESETS,
        DEFAULT_PRESET as DEFAULT_DEEPSEEK_PRESET,
    )
    deepseek_service = DeepSeekService()
    DEEPSEEK_AVAILABLE = True
    if deepseek_service.is_configured():
        print("✓ DeepSeek API 已配置")
    else:
        print("提示: 未配置 DEEPSEEK_API_KEY，DeepSeek回答将回退到本地知识库")
except ImportError as e:
    print(f"警告: 无法导入DeepSeek服务模块: {e}")
    DeepSeekAPIError = Exception
    DEFAULT_DEEPSEEK_PRESET = "deepseek_qa"

# 语音助手配置
if VOICE_ASSISTANT_AVAILABLE:
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB
    app.config['UPLOAD_FOLDER'] = os.path.join(voice_assistant_path, 'uploads')
    app.config['OUTPUT_FOLDER'] = os.path.join(voice_assistant_path, 'outputs')
    
    # 确保上传和输出目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    
    # 允许的音频文件扩展名
    ALLOWED_EXTENSIONS = {'pcm', 'wav', 'amr', 'mp3', 'm4a'}
    
    def allowed_file(filename):
        """检查文件扩展名是否允许"""
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


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
        return redirect(url_for('qa_robot'))
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
        return redirect(url_for('qa_robot'))
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
    """语音助手页面（重定向到问答机器人）"""
    # 默认跳转到问答机器人
    return redirect(url_for('qa_robot'))


@app.route('/qa_robot')
@login_required
def qa_robot():
    """问答机器人页面（需要登录）"""
    deepseek_configured = DEEPSEEK_AVAILABLE and deepseek_service and deepseek_service.is_configured()
    if not QA_ROBOT_AVAILABLE and not DEEPSEEK_AVAILABLE:
        return render_template('voice_assistant.html', 
                             username=session.get('username'),
                             current_view='qa_robot',
                             error='问答机器人模块不可用，且DeepSeek服务模块不可用')
    return render_template('voice_assistant.html', 
                         username=session.get('username'),
                         current_view='qa_robot',
                         deepseek_presets=DEEPSEEK_PRESETS,
                         default_deepseek_preset=DEFAULT_DEEPSEEK_PRESET,
                         deepseek_configured=deepseek_configured,
                         qa_robot_available=QA_ROBOT_AVAILABLE)


@app.route('/qa_discussion')
@login_required
def qa_discussion():
    """QA讨论区页面（需要登录）"""
    return render_template('voice_assistant.html',
                         username=session.get('username'),
                         user_id=session.get('user_id'),
                         current_view='qa_discussion')


@app.route('/digital_human')
@login_required
def digital_human():
    """3D 数字人页面（需要登录）"""
    deepseek_configured = DEEPSEEK_AVAILABLE and deepseek_service and deepseek_service.is_configured()
    return render_template('voice_assistant.html', 
                         username=session.get('username'),
                         current_view='digital_human',
                         deepseek_presets=DEEPSEEK_PRESETS,
                         default_deepseek_preset=DEFAULT_DEEPSEEK_PRESET,
                         deepseek_configured=deepseek_configured,
                         qa_robot_available=QA_ROBOT_AVAILABLE)


@app.route('/feature_experience')
@login_required
def feature_experience():
    """功能体验页面（需要登录）"""
    return render_template('voice_assistant.html', 
                         username=session.get('username'),
                         current_view='feature_experience')




# 问答机器人API路由
# 快速问答对映射（直接返回，不进行检索）
QUICK_QA_MAP = {
    "太阳系中体积最大的行星是哪一颗": "木星",
    "太阳系中体积最大的行星是哪一颗？": "木星",
    "太阳系体积最大的行星": "木星",
    "体积最大的行星": "木星",
    "人体最大的器官是什么": "皮肤",
    "人体最大的器官是什么？": "皮肤",
    "人体最大器官": "皮肤",
    "最大的器官": "皮肤",
    "澳大利亚的首都是悉尼吗": "不是，是堪培拉",
    "澳大利亚的首都是悉尼吗？": "不是，是堪培拉",
    "澳大利亚首都是悉尼吗": "不是，是堪培拉",
    "澳洲首都是悉尼吗": "不是，是堪培拉",
    "蒙娜丽莎的作者是谁": "达·芬奇",
    "蒙娜丽莎的作者是谁？": "达·芬奇",
    "蒙娜丽莎作者": "达·芬奇",
    "水的化学式是什么": "H2O",
    "水的化学式是什么？": "H2O",
    "水的化学式": "H2O",
    "企鹅主要生活在北极还是南极": "南极",
    "企鹅主要生活在北极还是南极？": "企鹅主要生活在南极",
    "企鹅生活在哪": "南极",
    "企鹅在北极还是南极": "南极",
    "光在真空中的传播速度大约是多少": "约 30 万公里/秒",
    "光在真空中的传播速度大约是多少？": "约 30 万公里/秒",
    "光速是多少": "约 30 万公里/秒",
    "光的速度": "约 30 万公里/秒",
    "著名的相对论是谁提出的": "爱因斯坦",
    "著名的相对论是谁提出的？": "爱因斯坦",
    "相对论是谁提出的": "爱因斯坦",
    "相对论的提出者": "爱因斯坦",
    "一场标准的足球比赛中，每队有几名球员上场": "11名",
    "一场标准的足球比赛中，每队有几名球员上场？": "11名",
    "足球比赛每队几人": "11名",
    "足球每队几个人": "11名",
    "世界上最高的山峰是哪座": "珠穆朗玛峰",
    "世界上最高的山峰是哪座？": "珠穆朗玛峰",
    "世界最高峰": "珠穆朗玛峰",
    "最高的山峰": "珠穆朗玛峰"
}

def match_quick_qa(question):
    """
    匹配快速问答对（智能匹配，支持多种问法）
    :param question: 用户问题
    :return: 如果匹配，返回答案；否则返回None
    """
    import re
    
    # 去除标点符号和空格，进行标准化匹配
    normalized_question = re.sub(r'[，。！？、；：\s]', '', question.strip())
    
    # 1. 直接匹配
    if question in QUICK_QA_MAP:
        return QUICK_QA_MAP[question]
    
    # 2. 标准化匹配（去除标点后匹配）
    for key, value in QUICK_QA_MAP.items():
        normalized_key = re.sub(r'[，。！？、；：\s]', '', key.strip())
        if normalized_question == normalized_key:
            return value
    
    # 3. 智能关键词匹配（处理各种问法变体）
    question_lower = question.lower()
    
    # 太阳系体积最大的行星
    if ("太阳系" in question or "太阳" in question) and ("体积最大" in question or "最大" in question) and ("行星" in question or "星球" in question):
        return "木星"
    
    # 人体最大器官
    if ("人体" in question or "人" in question) and "最大" in question and ("器官" in question or "部位" in question):
        return "皮肤"
    
    # 澳大利亚首都
    if ("澳大利亚" in question or "澳洲" in question) and "首都" in question:
        if "悉尼" in question:
            return "不是，是堪培拉"
        return "堪培拉"
    
    # 蒙娜丽莎作者
    if "蒙娜丽莎" in question and ("作者" in question or "谁" in question or "画" in question):
        return "达·芬奇"
    
    # 水的化学式
    if "水" in question and ("化学式" in question or "化学" in question or "分子式" in question):
        return "H2O"
    
    # 企鹅生活在哪里
    if "企鹅" in question:
        if "北极" in question:
            return "企鹅主要生活在南极，不是北极"
        if "南极" in question:
            return "南极"
        if "哪里" in question or "哪" in question:
            return "南极"
    
    # 光速
    if "光" in question and ("速度" in question or "传播" in question or "光速" in question):
        if "真空" in question or "真空中" in question:
            return "约 30 万公里/秒"
        return "约 30 万公里/秒"
    
    # 相对论
    if "相对论" in question and ("提出" in question or "谁" in question or "发明" in question):
        return "爱因斯坦"
    
    # 足球比赛人数
    if "足球" in question and ("球员" in question or "队员" in question or "人数" in question or "几个人" in question or "多少" in question):
        return "11名"
    
    # 世界最高峰
    if ("最高" in question or "最高峰" in question) and ("山" in question or "峰" in question):
        if "世界" in question or "全球" in question:
            return "珠穆朗玛峰"
        return "珠穆朗玛峰"
    
    return None


@app.route('/api/qa_robot/ask', methods=['POST'])
@login_required
def api_qa_robot_ask():
    """问答机器人API"""
    try:
        data = request.get_json() or {}
        question = str(data.get('question') or '').strip()
        preset = str(data.get('preset') or DEFAULT_DEEPSEEK_PRESET).strip() or DEFAULT_DEEPSEEK_PRESET
        deepseek_api_key = str(data.get('deepseek_api_key') or '').strip()
        use_local_only = preset == 'local'
        force_deepseek = (data.get('force_deepseek') == True) or (preset == 'deepseek_only')
        
        if not question:
            return jsonify({'success': False, 'error': '问题不能为空'}), 400

        request_deepseek_service = deepseek_service
        if deepseek_api_key and DEEPSEEK_AVAILABLE:
            request_deepseek_service = DeepSeekService(api_key=deepseek_api_key)
        elif DEEPSEEK_AVAILABLE and request_deepseek_service and not request_deepseek_service.is_configured():
            request_deepseek_service = DeepSeekService()
            
        deepseek_configured = (
            DEEPSEEK_AVAILABLE and
            request_deepseek_service and
            request_deepseek_service.is_configured()
        )
        if not QA_ROBOT_AVAILABLE and (use_local_only or not deepseek_configured):
            return jsonify({'success': False, 'error': '问答机器人模块不可用，且当前请求无法使用DeepSeek API'}), 503
        
        # 首先检查是否是快速问答对（如果强制使用DeepSeek，则跳过快速匹配）
        quick_answer = None if force_deepseek else match_quick_qa(question)
        if quick_answer:
            # 快速问答对也保存历史记录
            similarity = 1.0  # 完全匹配，相似度为1.0
            if 'user_id' in session and 'username' in session:
                save_qa_robot_history(
                    session['user_id'],
                    session['username'],
                    question,
                    quick_answer,
                    similarity
                )
            
            return jsonify({
                'success': True,
                'question': question,
                'answer': quick_answer,
                'similarity': similarity,
                'matched_question': question,
                'source': 'quick_qa',
                'preset': 'quick_qa',
                'alternatives': []
            })
        
        # 如果不是快速问答对，先做本地检索（如果强制使用DeepSeek，则跳过本地知识库检索）
        result = None
        if not force_deepseek and QA_ROBOT_AVAILABLE and qa_robot_service:
            result = qa_robot_service.ask(question, top_k=3, threshold=0.1)

        answer = None
        similarity = result.get('similarity') if result else None
        source = 'local'
        notice = None
        deepseek_meta = {}

        if use_local_only:
            if not result:
                return jsonify({
                    'success': False,
                    'error': '没有找到相关答案，请切换到DeepSeek综合问答或换一种方式提问。'
                }), 404
            answer = result.get('answer', '')
        else:
            if deepseek_configured:
                try:
                    deepseek_result = request_deepseek_service.ask(question, preset_key=preset, local_result=result)
                    answer = deepseek_result['answer']
                    source = 'deepseek'
                    deepseek_meta = deepseek_result
                except DeepSeekAPIError as e:
                    if not result:
                        return jsonify({'success': False, 'error': f'DeepSeek API调用失败: {str(e)}'}), 502
                    answer = result.get('answer', '')
                    source = 'local_fallback'
                    notice = f'DeepSeek API调用失败，已回退到本地知识库: {str(e)}'
            elif result:
                answer = result.get('answer', '')
                source = 'local_fallback'
                notice = '未配置 DEEPSEEK_API_KEY，已回退到本地知识库。'
            else:
                return jsonify({
                    'success': False,
                    'error': '未配置 DEEPSEEK_API_KEY，且本地知识库没有找到相关答案。'
                }), 503

        if not answer:
            return jsonify({'success': False, 'error': '没有生成有效答案'}), 500

        # 限制答案长度，最多2000字，避免前端和语音播报过长
        MAX_LENGTH = 2000
        if answer and len(answer) > MAX_LENGTH:
            answer = answer[:MAX_LENGTH] + "\n\n(单次回答最多生成2000字)"
        
        if 'user_id' in session and 'username' in session:
            save_qa_robot_history(
                session['user_id'],
                session['username'],
                question,
                answer,
                similarity
            )

        alternatives = []
        if result:
            for alt in result.get('alternatives', []):
                if len(alt) >= 3:
                    alternatives.append({
                        'question': alt[0],
                        'answer': alt[1],
                        'similarity': round(alt[2], 3),
                        'source': alt[3] if len(alt) >= 4 else ''
                    })

        response_payload = {
            'success': True,
            'question': question,
            'answer': answer,
            'matched_question': result.get('question', '') if result else '',
            'source': source,
            'preset': deepseek_meta.get('preset', preset),
            'preset_label': deepseek_meta.get('preset_label', '本地知识库' if use_local_only else ''),
            'model': deepseek_meta.get('model', ''),
            'alternatives': alternatives
        }
        if similarity is not None:
            response_payload['similarity'] = round(similarity, 3)
        if notice:
            response_payload['notice'] = notice

        return jsonify(response_payload)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/qa_robot/search', methods=['POST'])
@login_required
def api_qa_robot_search():
    """问答机器人搜索API - 返回多个相关结果"""
    if not QA_ROBOT_AVAILABLE:
        return jsonify({'success': False, 'error': '问答机器人模块不可用'}), 503
    
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        top_k = data.get('top_k', 5)
        threshold = data.get('threshold', 0.3)
        
        if not query:
            return jsonify({'success': False, 'error': '查询不能为空'}), 400
        
        # 搜索
        results = qa_robot_service.search(query, top_k=top_k, threshold=threshold)
        
        return jsonify({
            'success': True,
            'results': [
                {
                    'question': q,
                    'answer': a,
                    'similarity': round(s, 3)
                }
                for q, a, s in results
            ],
            'count': len(results)
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/qa_robot/history', methods=['GET'])
@login_required
def api_qa_robot_history():
    """获取问答机器人历史记录"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        history = get_qa_robot_history(session['user_id'], limit=limit, offset=offset)
        count = get_qa_robot_history_count(session['user_id'])
        
        return jsonify({
            'success': True,
            'history': history,
            'count': count
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/qa_robot/history/delete', methods=['POST'])
@login_required
def api_qa_robot_history_delete():
    """删除问答机器人历史记录"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        
        data = request.get_json()
        history_id = data.get('history_id', None)  # 如果为None，删除所有记录
        
        success, message = delete_qa_robot_history(session['user_id'], history_id)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/translate', methods=['POST'])
@login_required
def api_translate():
    """翻译API"""
    if not TRANSLATOR_AVAILABLE:
        return jsonify({'success': False, 'error': '翻译模块不可用'}), 503
    
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'success': False, 'error': '未提供文本内容'}), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({'success': False, 'error': '文本内容不能为空'}), 400
        
        # 获取目标语言，默认为中文
        target_lang = data.get('target_lang', 'zh')
        if target_lang not in ['zh', 'en']:
            target_lang = 'zh'
        
        # 执行翻译
        if target_lang == 'zh':
            translated_text = translate_to_chinese(text)
        else:
            translated_text = translate_to_english(text)
        
        return jsonify({
            'success': True,
            'original_text': text,
            'translated_text': translated_text,
            'target_lang': target_lang
        })
    
    except TranslationError as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': f'服务器错误: {str(e)}'}), 500



# 语音助手API路由
@app.route('/api/voice/asr', methods=['POST'])
@login_required
def api_voice_asr():
    """语音识别API（支持自动识别普通话和英文）"""
    if not VOICE_ASSISTANT_AVAILABLE:
        return jsonify({'success': False, 'error': '语音助手模块不可用'}), 503
    
    try:
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': '未上传音频文件'}), 400
        
        file = request.files['audio']
        if file.filename == '':
            return jsonify({'success': False, 'error': '未选择文件'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': '不支持的文件格式，请上传 pcm, wav, amr 或 mp3 文件'}), 400
        
        # 获取是否自动检测语言的参数（默认为True）
        auto_detect = request.form.get('auto_detect', 'true').lower() == 'true'
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 进行语音识别（自动识别语言）
        result = asr(filepath, auto_detect_language=auto_detect)
        
        # 删除临时文件
        try:
            os.remove(filepath)
        except:
            pass
        
        return jsonify({
            'success': True,
            'result': result
        })
    
    except ASRError as e:
        return jsonify({'success': False, 'error': f'识别错误: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': f'服务器错误: {str(e)}'}), 500


@app.route('/api/voice/tts', methods=['POST'])
@login_required
def api_voice_tts():
    """语音生成API（支持选择中文或英文）"""
    if not VOICE_ASSISTANT_AVAILABLE:
        return jsonify({'success': False, 'error': '语音助手模块不可用'}), 503
    
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'success': False, 'error': '未提供文本内容'}), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({'success': False, 'error': '文本内容不能为空'}), 400
        
        # 获取语言参数，默认为中文
        language = data.get('language', 'zh')
        # 验证语言参数，确保是有效的值
        if language not in ['zh', 'en']:
            language = 'zh'  # 默认使用中文
        
        # 获取发音人参数，默认为0（度小美）
        speaker = data.get('speaker', 0)
        # 验证发音人参数，只允许0, 1, 3, 4
        if speaker not in [0, 1, 3, 4]:
            speaker = 0  # 默认使用度小美
        
        # 调试信息（可选，生产环境可以注释掉）
        print(f"[TTS API] 接收到的参数 - text长度: {len(text)}, language: {language}, speaker: {speaker}")
        
        # 先检查缓存
        cache_success, cached_file = get_tts_audio_cache(text, language)
        if cache_success and cached_file and os.path.exists(cached_file):
            # 使用缓存文件
            return send_file(
                cached_file,
                mimetype='audio/mpeg' if cached_file.endswith('.mp3') else 'audio/wav',
                as_attachment=True,
                download_name=os.path.basename(cached_file)
            )
        
        # 缓存不存在，生成新的音频文件
        # 使用文本和语言的哈希值生成唯一文件名
        import hashlib
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        unique_filename = f"tts_{text_hash}_{language}.mp3"
        output_path = os.path.join(app.config['OUTPUT_FOLDER'], unique_filename)
        
        # 切换到 voice_assistant 目录执行 tts（因为 tts.py 会在当前目录保存文件）
        original_dir = os.getcwd()
        try:
            os.chdir(voice_assistant_path)
            saved_file = tts(text, language=language, speaker=speaker)
        finally:
            os.chdir(original_dir)
        
        # 检查是否生成成功
        if saved_file == "error.txt":
            return jsonify({'success': False, 'error': '语音生成失败'}), 500
        
        # 处理文件路径
        if not os.path.isabs(saved_file):
            # 相对路径，检查 voice_assistant 目录
            file_in_va = os.path.join(voice_assistant_path, saved_file)
            if os.path.exists(file_in_va):
                # 移动到输出目录，使用唯一文件名
                try:
                    # 如果目标文件已存在，先删除
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    os.rename(file_in_va, output_path)
                    saved_file = output_path
                except OSError as e:
                    # 如果移动失败，尝试复制
                    import shutil
                    if os.path.exists(output_path):
                        os.remove(output_path)
                    shutil.copy2(file_in_va, output_path)
                    saved_file = output_path
                    # 删除原文件
                    try:
                        os.remove(file_in_va)
                    except:
                        pass
            else:
                # 可能在输出目录中
                if os.path.exists(output_path):
                    saved_file = output_path
                else:
                    return jsonify({'success': False, 'error': '生成的音频文件未找到'}), 500
        
        # 保存到缓存
        save_tts_audio_cache(text, language, saved_file)
        
        # 返回音频文件
        return send_file(
            saved_file,
            mimetype='audio/mpeg' if saved_file.endswith('.mp3') else 'audio/wav',
            as_attachment=True,
            download_name=os.path.basename(saved_file)
        )
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'服务器错误: {str(e)}'}), 500


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


@app.route('/api/admin/users', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_users():
    """获取所有用户列表或创建新用户（管理员）"""
    if request.method == 'GET':
        users = get_all_users()
        return jsonify({'success': True, 'users': users})
    
    # POST: 创建新用户
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        email = data.get('email', '').strip() or None
        role = data.get('role', 'user').strip()
        
        # 验证输入
        if not username or not password:
            return jsonify({'success': False, 'error': '用户名和密码不能为空'}), 400
        
        if len(username) < 3:
            return jsonify({'success': False, 'error': '用户名至少需要3个字符'}), 400
        
        if len(password) < 6:
            return jsonify({'success': False, 'error': '密码至少需要6个字符'}), 400
        
        if role not in ['user', 'admin']:
            return jsonify({'success': False, 'error': '无效的角色'}), 400
        
        # 创建用户
        success, message = register_user(username, password, email, role=role)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            status_code = 409 if '已存在' in message else 400
            return jsonify({'success': False, 'error': message}), status_code
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'服务器错误: {str(e)}'}), 500


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


@app.route('/api/admin/tts/cache/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_tts_cache():
    """删除所有TTS音频缓存文件（管理员）"""
    try:
        data = request.get_json() or {}
        delete_db_records = data.get('delete_db_records', True)
        
        success, message, deleted_count = delete_all_tts_audio_files(delete_db_records=delete_db_records)
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'deleted_count': deleted_count
            })
        else:
            return jsonify({'success': False, 'error': message}), 500
    
    except Exception as e:
        return jsonify({'success': False, 'error': f'服务器错误: {str(e)}'}), 500


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


# QA讨论区API路由
@app.route('/api/qa_discussion/submit', methods=['POST'])
@login_required
def api_qa_discussion_submit():
    """提交讨论内容"""
    try:
        if 'user_id' not in session or 'username' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        
        data = request.get_json()
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'success': False, 'error': '内容不能为空'}), 400
        
        if len(content) > 5000:
            return jsonify({'success': False, 'error': '内容过长，最多5000字'}), 400
        
        success, message, discussion_id = save_qa_discussion(
            session['user_id'],
            session['username'],
            content
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'discussion_id': discussion_id
            })
        else:
            return jsonify({'success': False, 'error': message}), 400
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/qa_discussion/list', methods=['GET'])
@login_required
def api_qa_discussion_list():
    """获取讨论列表"""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        discussions = get_qa_discussions(limit=limit, offset=offset)
        total = get_qa_discussion_count()
        
        # 为每个讨论获取评论数量
        for disc in discussions:
            comments = get_qa_comments(disc['id'])
            disc['comment_count'] = len(comments)
        
        return jsonify({
            'success': True,
            'discussions': discussions,
            'total': total
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/qa_discussion/<int:discussion_id>', methods=['DELETE'])
@login_required
def api_qa_discussion_delete(discussion_id):
    """删除讨论"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        
        is_admin = session.get('role') == 'admin'
        user_id = session.get('user_id')
        
        success, message = delete_qa_discussion(discussion_id, user_id, is_admin)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/qa_discussion/<int:discussion_id>/comment', methods=['POST'])
@login_required
def api_qa_discussion_comment(discussion_id):
    """提交评论"""
    try:
        if 'user_id' not in session or 'username' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401
        
        data = request.get_json()
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'success': False, 'error': '评论内容不能为空'}), 400
        
        if len(content) > 1000:
            return jsonify({'success': False, 'error': '评论过长，最多1000字'}), 400
        
        success, message, comment_id = save_qa_comment(
            discussion_id,
            session['user_id'],
            session['username'],
            content
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': message,
                'comment_id': comment_id
            })
        else:
            return jsonify({'success': False, 'error': message}), 400
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/qa_discussion/<int:discussion_id>/comments', methods=['GET'])
@login_required
def api_qa_discussion_comments(discussion_id):
    """获取讨论的评论列表"""
    try:
        comments = get_qa_comments(discussion_id)
        return jsonify({
            'success': True,
            'comments': comments
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/qa_discussion/comment/<int:comment_id>', methods=['DELETE'])
@login_required
def api_qa_discussion_comment_delete(comment_id):
    """删除评论"""
    try:
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': '未登录'}), 401

        is_admin = session.get('role') == 'admin'
        user_id = session.get('user_id')

        success, message = delete_qa_comment(comment_id, user_id, is_admin)

        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================
# 讨论区增强 API：列表(支持排序/搜索)、详情、点赞/点踩、收藏、个人主页
# ============================================================

@app.route('/api/qa_discussion/feed', methods=['GET'])
@login_required
def api_qa_discussion_feed():
    """讨论区 Feed：支持最新/最热/搜索"""
    try:
        sort = request.args.get('sort', 'latest')  # 'latest' | 'hot'
        limit = min(request.args.get('limit', 20, type=int), 100)
        offset = max(request.args.get('offset', 0, type=int), 0)
        keyword = request.args.get('q', '').strip() or None

        user_id = session.get('user_id')
        discussions = get_qa_discussions_extended(sort=sort, limit=limit, offset=offset, keyword=keyword)
        total = get_qa_discussion_count_extended(keyword=keyword)

        # 批量补充：当前用户对这些讨论的投票/收藏状态
        ids = [d['id'] for d in discussions]
        vote_map = get_user_votes(user_id, 'discussion', ids) if ids else {}
        fav_map = get_user_favorited_ids(user_id, ids) if ids else {}

        for d in discussions:
            d['user_vote'] = vote_map.get(d['id'])
            d['is_favorited'] = fav_map.get(d['id'], False)

        return jsonify({
            'success': True,
            'discussions': discussions,
            'total': total,
            'has_more': offset + len(discussions) < total,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/qa_discussion/<int:discussion_id>/detail', methods=['GET'])
@login_required
def api_qa_discussion_detail(discussion_id):
    """获取讨论详情（增加浏览量）"""
    try:
        user_id = session.get('user_id')
        disc = get_qa_discussion_detail(discussion_id, increment_view=True)
        if not disc:
            return jsonify({'success': False, 'error': '讨论不存在'}), 404
        # 当前用户的投票/收藏状态
        votes = get_user_votes(user_id, 'discussion', [discussion_id])
        disc['user_vote'] = votes.get(discussion_id)
        disc['is_favorited'] = is_favorited(user_id, discussion_id)
        return jsonify({'success': True, 'discussion': disc})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/qa_discussion/<int:discussion_id>/vote', methods=['POST'])
@login_required
def api_qa_discussion_vote(discussion_id):
    """对讨论点赞/点踩/取消"""
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}
        vote_type = data.get('vote_type', '')  # 'like' | 'dislike' | 'cancel'
        if vote_type not in ('like', 'dislike', 'cancel'):
            return jsonify({'success': False, 'error': 'vote_type 必须为 like/dislike/cancel'}), 400
        ok, msg, lc, dc, user_vote = vote_qa_target(user_id, 'discussion', discussion_id, vote_type)
        return jsonify({
            'success': ok,
            'message': msg,
            'like_count': lc,
            'dislike_count': dc,
            'user_vote': user_vote,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/qa_discussion/comment/<int:comment_id>/vote', methods=['POST'])
@login_required
def api_qa_comment_vote(comment_id):
    """对评论点赞/点踩/取消"""
    try:
        user_id = session.get('user_id')
        data = request.get_json() or {}
        vote_type = data.get('vote_type', '')
        if vote_type not in ('like', 'dislike', 'cancel'):
            return jsonify({'success': False, 'error': 'vote_type 必须为 like/dislike/cancel'}), 400
        ok, msg, lc, dc, user_vote = vote_qa_target(user_id, 'comment', comment_id, vote_type)
        return jsonify({
            'success': ok,
            'message': msg,
            'like_count': lc,
            'dislike_count': dc,
            'user_vote': user_vote,
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/qa_discussion/<int:discussion_id>/favorite', methods=['POST'])
@login_required
def api_qa_discussion_favorite(discussion_id):
    """收藏/取消收藏讨论"""
    try:
        user_id = session.get('user_id')
        ok, msg, is_fav = toggle_favorite(user_id, discussion_id)
        return jsonify({'success': ok, 'message': msg, 'is_favorited': is_fav})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/qa_discussion/<int:discussion_id>/comments_extended', methods=['GET'])
@login_required
def api_qa_discussion_comments_extended(discussion_id):
    """获取评论列表（带点赞、@提及）"""
    try:
        user_id = session.get('user_id')
        comments = get_qa_comments_extended(discussion_id, user_id=user_id)
        return jsonify({'success': True, 'comments': comments})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ---------- 个人主页 ----------

@app.route('/user/<username>')
@login_required
def user_profile_page(username):
    """个人主页"""
    return render_template(
        'voice_assistant.html',
        username=session.get('username'),
        user_id=session.get('user_id'),
        current_view='user_profile',
        profile_username=username,
    )


@app.route('/api/user/<username>/profile', methods=['GET'])
@login_required
def api_user_profile(username):
    """获取个人主页概要"""
    profile = get_user_profile(username)
    if not profile:
        return jsonify({'success': False, 'error': '用户不存在'}), 404
    return jsonify({'success': True, 'profile': profile})


@app.route('/api/user/<username>/discussions', methods=['GET'])
@login_required
def api_user_discussions(username):
    """个人主页：发布的讨论"""
    try:
        limit = min(request.args.get('limit', 20, type=int), 100)
        offset = max(request.args.get('offset', 0, type=int), 0)
        viewer_id = session.get('user_id')
        profile = get_user_profile(username)
        if not profile:
            return jsonify({'success': False, 'error': '用户不存在'}), 404
        items = get_user_discussions(profile['user']['id'], limit=limit, offset=offset)
        ids = [i['id'] for i in items]
        fav_map = get_user_favorited_ids(viewer_id, ids) if ids else {}
        for it in items:
            it['is_favorited'] = fav_map.get(it['id'], False)
        return jsonify({'success': True, 'discussions': items})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/user/<username>/comments', methods=['GET'])
@login_required
def api_user_comments(username):
    """个人主页：发表的评论"""
    try:
        limit = min(request.args.get('limit', 20, type=int), 100)
        offset = max(request.args.get('offset', 0, type=int), 0)
        profile = get_user_profile(username)
        if not profile:
            return jsonify({'success': False, 'error': '用户不存在'}), 404
        items = get_user_comments(profile['user']['id'], limit=limit, offset=offset)
        return jsonify({'success': True, 'comments': items})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/user/<username>/favorites', methods=['GET'])
@login_required
def api_user_favorites(username):
    """个人主页：收藏的讨论（仅本人可看）"""
    try:
        viewer = session.get('username')
        if viewer != username and session.get('role') != 'admin':
            return jsonify({'success': False, 'error': '无权查看他人收藏'}), 403
        limit = min(request.args.get('limit', 20, type=int), 100)
        offset = max(request.args.get('offset', 0, type=int), 0)
        profile = get_user_profile(username)
        if not profile:
            return jsonify({'success': False, 'error': '用户不存在'}), 404
        items = get_user_favorites(profile['user']['id'], limit=limit, offset=offset)
        for it in items:
            it['is_favorited'] = True
        return jsonify({'success': True, 'favorites': items})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



if __name__ == '__main__':
    print("="*50)
    print("智能问答系统启动中...")
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
    
    print("="*60)
    print("🚀 服务器启动成功！")
    print("="*60)
    print("📌 访问地址:")
    print("   本地访问: http://127.0.0.1:5001")
    print("   局域网访问: http://0.0.0.0:5001")
    print("   端口: 5001")
    print("="*60)
    print("💡 提示: 按 Ctrl+C 停止服务器")
    print("="*60)
    print()
    app.run(debug=True, host='0.0.0.0', port=5001)
