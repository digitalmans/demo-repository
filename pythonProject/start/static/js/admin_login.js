// 管理员登录表单处理
document.getElementById('admin-login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const password = document.getElementById('password').value.trim();
    const loginBtn = document.getElementById('admin-login-btn');
    const errorMsg = document.getElementById('error-message');
    const successMsg = document.getElementById('success-message');
    
    // 隐藏之前的消息
    errorMsg.style.display = 'none';
    successMsg.style.display = 'none';
    
    // 验证输入
    if (!username || !password) {
        showError('请输入用户名和密码');
        return;
    }
    
    // 禁用按钮，显示加载状态
    loginBtn.disabled = true;
    loginBtn.innerHTML = '<span class="loading"></span>登录中...';
    
    try {
        const response = await fetch('/admin/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                password: password
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess('管理员登录成功，正在跳转...');
            // 延迟跳转
            setTimeout(() => {
                window.location.href = '/admin';
            }, 1000);
        } else {
            showError(data.error || '登录失败，请检查用户名和密码');
            loginBtn.disabled = false;
            loginBtn.innerHTML = '管理员登录';
        }
    } catch (error) {
        showError('网络错误: ' + error.message);
        loginBtn.disabled = false;
        loginBtn.innerHTML = '管理员登录';
    }
});

function showError(message) {
    const errorMsg = document.getElementById('error-message');
    errorMsg.textContent = message;
    errorMsg.style.display = 'block';
}

function showSuccess(message) {
    const successMsg = document.getElementById('success-message');
    successMsg.textContent = message;
    successMsg.style.display = 'block';
}
