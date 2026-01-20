#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
语音助手Web应用 - Flask后端
提供语音识别(ASR)和语音生成(TTS)的Web API
"""

import os
import json
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from asr import asr, DemoError as ASRError
from tts import tts, DemoError as TTSError

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 限制上传文件大小为16MB
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['OUTPUT_FOLDER'] = 'outputs'

# 确保上传和输出目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)

# 允许的音频文件扩展名
ALLOWED_EXTENSIONS = {'pcm', 'wav', 'amr', 'mp3', 'm4a'}


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')


@app.route('/api/asr', methods=['POST'])
def api_asr():
    """语音识别API"""
    try:
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': '未上传音频文件'}), 400
        
        file = request.files['audio']
        if file.filename == '':
            return jsonify({'success': False, 'error': '未选择文件'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': '不支持的文件格式，请上传 pcm, wav, amr 或 mp3 文件'}), 400
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 进行语音识别
        result = asr(filepath)
        
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


@app.route('/api/tts', methods=['POST'])
def api_tts():
    """语音生成API"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'success': False, 'error': '未提供文本内容'}), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({'success': False, 'error': '文本内容不能为空'}), 400
        
        # 生成语音
        saved_file = tts(text)
        
        # 检查是否生成成功
        if saved_file == "error.txt":
            return jsonify({'success': False, 'error': '语音生成失败'}), 500
        
        # 处理文件路径
        if not os.path.isabs(saved_file):
            # 相对路径，检查当前目录
            if os.path.exists(saved_file):
                # 移动到输出目录
                filename = os.path.basename(saved_file)
                output_path = os.path.join(app.config['OUTPUT_FOLDER'], filename)
                os.rename(saved_file, output_path)
                saved_file = output_path
            else:
                # 可能在输出目录中
                output_path = os.path.join(app.config['OUTPUT_FOLDER'], saved_file)
                if os.path.exists(output_path):
                    saved_file = output_path
                else:
                    return jsonify({'success': False, 'error': '生成的音频文件未找到'}), 500
        
        # 返回音频文件
        return send_file(
            saved_file,
            mimetype='audio/mpeg' if saved_file.endswith('.mp3') else 'audio/wav',
            as_attachment=True,
            download_name=saved_file.split(os.sep)[-1]
        )
    
    except TTSError as e:
        return jsonify({'success': False, 'error': f'生成错误: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': f'服务器错误: {str(e)}'}), 500


@app.route('/api/tts/download', methods=['POST'])
def api_tts_download():
    """语音生成API - 返回下载链接"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'success': False, 'error': '未提供文本内容'}), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({'success': False, 'error': '文本内容不能为空'}), 400
        
        # 生成语音
        saved_file = tts(text)
        
        # 检查是否生成成功
        if saved_file == "error.txt":
            return jsonify({'success': False, 'error': '语音生成失败'}), 500
        
        # 移动文件到输出目录
        output_filename = saved_file
        if os.path.exists(saved_file):
            output_path = os.path.join(app.config['OUTPUT_FOLDER'], saved_file)
            os.rename(saved_file, output_path)
            output_filename = saved_file
        
        return jsonify({
            'success': True,
            'filename': output_filename,
            'download_url': f'/api/download/{output_filename}'
        })
    
    except TTSError as e:
        return jsonify({'success': False, 'error': f'生成错误: {str(e)}'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': f'服务器错误: {str(e)}'}), 500


@app.route('/api/download/<filename>')
def download_file(filename):
    """下载生成的文件"""
    filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_file(
            filepath,
            mimetype='audio/mpeg' if filename.endswith('.mp3') else 'audio/wav',
            as_attachment=True
        )
    return jsonify({'error': '文件不存在'}), 404


if __name__ == '__main__':
    print("="*50)
    print("语音助手Web应用启动中...")
    print("="*50)
    print("访问地址: http://127.0.0.1:5000")
    print("按 Ctrl+C 停止服务器")
    print("="*50)
    app.run(debug=True, host='0.0.0.0', port=5000)
