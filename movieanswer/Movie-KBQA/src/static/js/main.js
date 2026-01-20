// 电影问答机器人 - 前端JavaScript

let messageCount = 0;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    // 加载统计信息
    loadStats();
    
    // 绑定回车键发送
    const questionInput = document.getElementById('question-input');
    questionInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            sendQuestion();
        }
    });
    
    // 自动聚焦输入框
    questionInput.focus();
});

// 发送问题
async function sendQuestion() {
    const questionInput = document.getElementById('question-input');
    const question = questionInput.value.trim();
    
    if (!question) {
        return;
    }
    
    // 禁用按钮
    const sendBtn = document.getElementById('send-btn');
    const btnText = sendBtn.querySelector('.btn-text');
    const btnLoading = sendBtn.querySelector('.btn-loading');
    
    sendBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoading.style.display = 'inline';
    
    // 添加用户消息
    addMessage(question, 'user');
    
    // 清空输入框
    questionInput.value = '';
    
    // 添加加载消息
    const loadingId = addLoadingMessage();
    
    try {
        const response = await fetch('/api/ask', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ question: question })
        });
        
        const data = await response.json();
        
        // 移除加载消息
        removeMessage(loadingId);
        
        if (data.success) {
            addMessage(data.answer, 'bot');
        } else {
            addMessage('抱歉，发生了错误: ' + (data.error || '未知错误'), 'bot', true);
        }
    } catch (error) {
        removeMessage(loadingId);
        addMessage('网络错误: ' + error.message, 'bot', true);
    } finally {
        // 恢复按钮
        sendBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
        
        // 重新聚焦输入框
        questionInput.focus();
    }
}

// 添加消息
function addMessage(text, type, isError = false) {
    const chatMessages = document.getElementById('chat-messages');
    
    // 如果是第一条消息，移除欢迎消息
    if (messageCount === 0) {
        const welcomeMessage = chatMessages.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.id = 'msg-' + Date.now();
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    if (isError) {
        contentDiv.style.background = '#fee';
        contentDiv.style.color = '#c33';
        contentDiv.style.borderLeftColor = '#c33';
    }
    
    contentDiv.textContent = text;
    
    const timeDiv = document.createElement('div');
    timeDiv.className = 'message-time';
    timeDiv.textContent = getCurrentTime();
    
    messageDiv.appendChild(contentDiv);
    messageDiv.appendChild(timeDiv);
    chatMessages.appendChild(messageDiv);
    
    // 滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // 更新消息计数
    messageCount++;
    updateMessageCount();
    
    return messageDiv.id;
}

// 添加加载消息
function addLoadingMessage() {
    const chatMessages = document.getElementById('chat-messages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message bot';
    messageDiv.id = 'loading-' + Date.now();
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    contentDiv.style.textAlign = 'center';
    contentDiv.innerHTML = '<div class="spinner"></div><p style="margin-top: 10px; color: #666;">正在思考中...</p>';
    
    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);
    
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv.id;
}

// 移除消息
function removeMessage(messageId) {
    const message = document.getElementById(messageId);
    if (message) {
        message.remove();
    }
}

// 清空对话
function clearChat() {
    if (confirm('确定要清空所有对话记录吗？')) {
        const chatMessages = document.getElementById('chat-messages');
        chatMessages.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">👋</div>
                <h3>欢迎使用电影问答机器人！</h3>
                <p>我是您的电影知识助手，可以回答关于电影、演员等相关问题。</p>
                <p>请在左侧输入您的问题，我会尽力为您解答。</p>
            </div>
        `;
        messageCount = 0;
        updateMessageCount();
    }
}

// 更新消息计数
function updateMessageCount() {
    const countElement = document.getElementById('message-count');
    countElement.textContent = `${messageCount} 条消息`;
}

// 获取当前时间
function getCurrentTime() {
    const now = new Date();
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    return `${hours}:${minutes}`;
}

// 加载统计信息
async function loadStats() {
    const statsContent = document.getElementById('stats-content');
    statsContent.innerHTML = '<div class="loading">加载中...</div>';
    
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        if (data.success) {
            const stats = data.stats;
            statsContent.innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">问答对数</span>
                    <span class="stat-value">${stats.total_qa_pairs}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">电影数量</span>
                    <span class="stat-value">${stats.total_movies}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">演员数量</span>
                    <span class="stat-value">${stats.total_persons}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">类型数量</span>
                    <span class="stat-value">${stats.total_genres}</span>
                </div>
            `;
        } else {
            statsContent.innerHTML = '<p style="color: #c33;">加载失败</p>';
        }
    } catch (error) {
        statsContent.innerHTML = '<p style="color: #c33;">网络错误</p>';
    }
}
