# 语音助手Web应用

基于Flask的语音识别(ASR)和语音生成(TTS)Web应用系统。

## 功能特性

- 🎤 **语音识别 (ASR)**: 将音频文件转换为文本
- 🔊 **语音生成 (TTS)**: 将文本转换为语音文件
- 🌐 **Web界面**: 现代化的响应式Web界面
- 📱 **移动端支持**: 适配手机和平板设备

## 安装步骤

### 1. 安装Python依赖

```bash
pip install -r requirements.txt
```

### 2. 配置API密钥

确保 `asr.py` 和 `tts.py` 中的 `API_KEY` 和 `SECRET_KEY` 已正确配置。

### 3. 运行应用

```bash
python app.py
```

### 4. 访问应用

打开浏览器访问: `http://127.0.0.1:5000`

## 项目结构

```
pythonProject/
├── app.py                 # Flask后端应用
├── asr.py                 # 语音识别模块
├── tts.py                 # 语音生成模块
├── main.py                # 命令行入口程序
├── requirements.txt       # Python依赖
├── templates/
│   └── index.html        # 前端页面
├── static/
│   ├── css/
│   │   └── style.css     # 样式文件
│   └── js/
│       └── main.js        # JavaScript逻辑
├── uploads/              # 上传文件临时目录（自动创建）
└── outputs/              # 生成的音频文件目录（自动创建）
```

## API接口

### 语音识别 API

- **URL**: `/api/asr`
- **方法**: `POST`
- **参数**: `audio` (文件)
- **返回**: JSON格式的识别结果

### 语音生成 API

- **URL**: `/api/tts`
- **方法**: `POST`
- **参数**: JSON格式 `{"text": "要转换的文本"}`
- **返回**: MP3音频文件

## 使用说明

### 语音识别

1. 点击"语音识别"标签
2. 选择或拖拽音频文件（支持 PCM, WAV, AMR, MP3 格式）
3. 点击"开始识别"按钮
4. 查看识别结果

### 语音生成

1. 点击"语音生成"标签
2. 在文本框中输入要转换的文本
3. 点击"生成语音"按钮
4. 播放或下载生成的音频文件

## 注意事项

- 上传文件大小限制: 16MB
- 支持的音频格式: PCM, WAV, AMR, MP3
- 确保网络连接正常，需要访问百度语音API

## 技术栈

- **后端**: Flask (Python)
- **前端**: HTML5, CSS3, JavaScript (原生)
- **API**: 百度语音识别与合成API

## 许可证

MIT License
