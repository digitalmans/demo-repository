#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
检索式问答系统 - Web界面
提供Flask Web应用，支持问答和语料库管理
"""

import os
from flask import Flask, render_template, request, jsonify
from retrieval_service import RetrievalService

app = Flask(__name__)

# 初始化服务
current_dir = os.path.dirname(os.path.abspath(__file__))
kb_file = os.path.join(os.path.dirname(current_dir), 'data', 'knowledge_base.json')

# 创建服务实例
service = RetrievalService(kb_file=kb_file)


@app.route('/')
def index():
    """主页"""
    return render_template('retrieval_chat.html')


@app.route('/api/ask', methods=['POST'])
def api_ask():
    """问答API"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({'success': False, 'error': '问题不能为空'}), 400
        
        # 获取答案
        answer = service.ask(question, top_k=1, threshold=0.1)
        
        return jsonify({
            'success': True,
            'question': question,
            'answer': answer
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/search', methods=['POST'])
def api_search():
    """搜索API - 返回多个相关结果"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        top_k = data.get('top_k', 3)
        threshold = data.get('threshold', 0.1)
        
        if not question:
            return jsonify({'success': False, 'error': '问题不能为空'}), 400
        
        # 搜索相关结果
        results = service.search(question, top_k=top_k, threshold=threshold)
        
        formatted_results = []
        for q, a, score, cat in results:
            formatted_results.append({
                'question': q,
                'answer': a,
                'score': round(score, 3),
                'category': cat
            })
        
        return jsonify({
            'success': True,
            'question': question,
            'results': formatted_results,
            'count': len(formatted_results)
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/qa/add', methods=['POST'])
def api_add_qa():
    """添加问答对API"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        answer = data.get('answer', '').strip()
        category = data.get('category', 'custom').strip()
        
        if not question or not answer:
            return jsonify({'success': False, 'error': '问题和答案不能为空'}), 400
        
        success, message = service.add_qa(question, answer, category)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/qa/remove', methods=['POST'])
def api_remove_qa():
    """删除问答对API"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip() or None
        answer = data.get('answer', '').strip() or None
        
        if not question and not answer:
            return jsonify({'success': False, 'error': '请指定要删除的问题或答案'}), 400
        
        success, message = service.remove_qa(question=question, answer=answer)
        
        if success:
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'error': message}), 400
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/qa/list', methods=['GET'])
def api_list_qa():
    """列出问答对API"""
    try:
        category = request.args.get('category', None)
        limit = int(request.args.get('limit', 20))
        
        qa_pairs = service.list_qa(category=category, limit=limit)
        
        formatted_pairs = []
        for q, a, c in qa_pairs:
            formatted_pairs.append({
                'question': q,
                'answer': a,
                'category': c
            })
        
        return jsonify({
            'success': True,
            'qa_pairs': formatted_pairs,
            'count': len(formatted_pairs)
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def api_stats():
    """统计信息API"""
    try:
        stats = service.get_statistics()
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    print("="*60)
    print("电影问答机器人 - Web服务")
    print("="*60)
    print(f"访问地址: http://127.0.0.1:5002")
    print("按 Ctrl+C 停止服务器")
    print("="*60)
    app.run(debug=True, host='0.0.0.0', port=5002)
