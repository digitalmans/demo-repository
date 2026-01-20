#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
Web应用入口
提供基于Flask的Web界面
"""

from flask import Flask, render_template, request, jsonify
from qa_service import QAService
import os


app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False  # 支持中文JSON

# 初始化问答服务
qa_service = None

def init_service():
    """初始化问答服务"""
    global qa_service
    try:
        qa_service = QAService()
        print("✓ 问答服务初始化成功")
        return True
    except Exception as e:
        print(f"✗ 问答服务初始化失败: {e}")
        return False


@app.route('/')
def index():
    """首页"""
    return render_template('qa_chat.html')


@app.route('/api/ask', methods=['POST'])
def ask():
    """问答API接口"""
    global qa_service
    
    if not qa_service:
        return jsonify({
            'success': False,
            'error': '问答服务未初始化'
        }), 500
    
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({
                'success': False,
                'error': '问题不能为空'
            }), 400
        
        # 获取答案
        result = qa_service.ask(question, top_k=3, threshold=0.3)
        
        if result:
            return jsonify({
                'success': True,
                'answer': result['answer'],
                'question': result['question'],
                'similarity': round(result['similarity'], 3),
                'alternatives': [
                    {
                        'question': q,
                        'answer': a,
                        'similarity': round(s, 3)
                    }
                    for q, a, s in result.get('alternatives', [])
                ]
            })
        else:
            return jsonify({
                'success': False,
                'error': '没有找到相关答案',
                'answer': '抱歉，我没有找到相关答案。请尝试换一种方式提问。'
            })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/search', methods=['POST'])
def search():
    """搜索API接口"""
    global qa_service
    
    if not qa_service:
        return jsonify({
            'success': False,
            'error': '问答服务未初始化'
        }), 500
    
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        top_k = data.get('top_k', 5)
        threshold = data.get('threshold', 0.3)
        
        if not query:
            return jsonify({
                'success': False,
                'error': '查询不能为空'
            }), 400
        
        # 搜索
        results = qa_service.search(query, top_k=top_k, threshold=threshold)
        
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
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/health', methods=['GET'])
def health():
    """健康检查接口"""
    global qa_service
    return jsonify({
        'status': 'ok' if qa_service else 'error',
        'service_initialized': qa_service is not None
    })


if __name__ == '__main__':
    print("=" * 60)
    print("问答机器人 Web 服务")
    print("=" * 60)
    
    # 初始化服务
    if not init_service():
        print("无法启动服务，请检查Neo4j连接")
        exit(1)
    
    print("\n服务启动中...")
    print("访问地址: http://127.0.0.1:5003")
    print("按 Ctrl+C 停止服务\n")
    
    app.run(host='0.0.0.0', port=5003, debug=True)
