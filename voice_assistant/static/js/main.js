// 标签页切换
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tab = btn.dataset.tab;
        
        // 更新按钮状态
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // 更新内容面板
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(`${tab}-tab`).classList.add('active');
        
        // 重置状态
        resetForms();
    });
});

// 重置表单
function resetForms() {
    // 重置ASR
    document.getElementById('asr-file-name').textContent = '';
    document.getElementById('asr-submit').disabled = true;
    document.getElementById('asr-result').style.display = 'none';
    document.getElementById('asr-loading').style.display = 'none';
    selectedFile = null;
    audioFileInput.value = ''; // 清空文件输入
    
    // 重置TTS
    document.getElementById('tts-text').value = '';
    if (document.getElementById('tts-language')) {
        document.getElementById('tts-language').value = 'zh';
    }
    document.getElementById('tts-result').style.display = 'none';
    document.getElementById('tts-loading').style.display = 'none';
}

// 语音识别 - 文件上传
const asrUploadArea = document.getElementById('asr-upload-area');
const audioFileInput = document.getElementById('audio-file');
const asrFileName = document.getElementById('asr-file-name');
const asrSubmit = document.getElementById('asr-submit');

// 保存当前选择的文件
let selectedFile = null;

asrUploadArea.addEventListener('click', () => {
    audioFileInput.click();
});

asrUploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    asrUploadArea.style.background = '#f0f2ff';
});

asrUploadArea.addEventListener('dragleave', () => {
    asrUploadArea.style.background = '#f8f9ff';
});

asrUploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    asrUploadArea.style.background = '#f8f9ff';
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
});

audioFileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

function handleFileSelect(file) {
    // 检查文件大小
    if (file.size > 16 * 1024 * 1024) {
        alert('文件大小不能超过16MB');
        selectedFile = null;
        asrFileName.textContent = '';
        asrSubmit.disabled = true;
        return;
    }
    
    // 检查文件格式（允许的格式：pcm, wav, amr, mp3, m4a）
    const allowedExtensions = ['pcm', 'wav', 'amr', 'mp3', 'm4a'];
    const fileExtension = file.name.split('.').pop().toLowerCase();
    
    if (!allowedExtensions.includes(fileExtension)) {
        alert(`不支持的文件格式: ${fileExtension}\n支持的格式: ${allowedExtensions.join(', ')}`);
        selectedFile = null;
        asrFileName.textContent = '';
        asrSubmit.disabled = true;
        return;
    }
    
    // 保存文件引用
    selectedFile = file;
    asrFileName.textContent = `已选择: ${file.name}`;
    asrSubmit.disabled = false;
}

// 语音识别 - 提交
asrSubmit.addEventListener('click', async () => {
    // 优先使用保存的文件引用，如果没有则从input获取
    const file = selectedFile || audioFileInput.files[0];
    if (!file) {
        alert('请先选择音频文件');
        return;
    }
    
    const formData = new FormData();
    formData.append('audio', file);
    
    // 显示加载状态
    document.getElementById('asr-loading').style.display = 'block';
    document.getElementById('asr-result').style.display = 'none';
    asrSubmit.disabled = true;
    
    try {
        const response = await fetch('/api/asr', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        document.getElementById('asr-loading').style.display = 'none';
        
        if (data.success) {
            document.getElementById('asr-result-text').textContent = data.result;
            document.getElementById('asr-result').style.display = 'block';
        } else {
            showError('asr-result', data.error || '识别失败');
        }
    } catch (error) {
        document.getElementById('asr-loading').style.display = 'none';
        showError('asr-result', '网络错误: ' + error.message);
    } finally {
        asrSubmit.disabled = false;
    }
});

// 语音生成 - 提交
const ttsSubmit = document.getElementById('tts-submit');
const ttsText = document.getElementById('tts-text');
const ttsLanguage = document.getElementById('tts-language');

ttsSubmit.addEventListener('click', async () => {
    const text = ttsText.value.trim();
    
    if (!text) {
        alert('请输入要转换的文本');
        return;
    }
    
    // 获取选择的语言
    const language = ttsLanguage.value || 'zh';
    
    // 显示加载状态
    document.getElementById('tts-loading').style.display = 'block';
    document.getElementById('tts-result').style.display = 'none';
    ttsSubmit.disabled = true;
    
    try {
        // 调用TTS API，自动翻译并生成语音
        const response = await fetch('/api/tts', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                text: text,
                language: language,
                translate: true  // 启用自动翻译
            })
        });
        
        if (response.ok) {
            // 获取音频blob
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            
            // 创建音频播放器
            const audioPlayer = document.getElementById('tts-audio-player');
            audioPlayer.innerHTML = `<audio controls src="${url}"></audio>`;
            
            // 设置下载链接
            const downloadBtn = document.getElementById('tts-download');
            downloadBtn.href = url;
            downloadBtn.download = 'speech.mp3';
            
            document.getElementById('tts-result').style.display = 'block';
        } else {
            const data = await response.json();
            showError('tts-result', data.error || '生成失败');
        }
    } catch (error) {
        showError('tts-result', '网络错误: ' + error.message);
    } finally {
        document.getElementById('tts-loading').style.display = 'none';
        ttsSubmit.disabled = false;
    }
});

// 显示错误信息
function showError(containerId, message) {
    const container = document.getElementById(containerId);
    container.innerHTML = `<div class="error">${message}</div>`;
    container.style.display = 'block';
}
