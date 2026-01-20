// 注册表单处理
document.getElementById('register-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const email = document.getElementById('email').value.trim();
    const password = document.getElementById('password').value.trim();
    const confirmPassword = document.getElementById('confirm_password').value.trim();
    const registerBtn = document.getElementById('register-btn');
    const errorMsg = document.getElementById('error-message');
    const successMsg = document.getElementById('success-message');
    
    // 隐藏之前的消息
    errorMsg.style.display = 'none';
    successMsg.style.display = 'none';
    
    // 验证输入
    if (!username || !password) {
        showError('用户名和密码不能为空');
        return;
    }
    
    if (username.length < 3) {
        showError('用户名至少需要3个字符');
        return;
    }
    
    if (password.length < 6) {
        showError('密码至少需要6个字符');
        return;
    }
    
    if (password !== confirmPassword) {
        showError('两次输入的密码不一致');
        return;
    }
    
    // 禁用按钮，显示加载状态
    registerBtn.disabled = true;
    registerBtn.innerHTML = '<span class="loading"></span>注册中...';
    
    try {
        const response = await fetch('/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                email: email,
                password: password,
                confirm_password: confirmPassword
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showSuccess('注册成功！正在跳转到登录页面...');
            // 延迟跳转
            setTimeout(() => {
                window.location.href = '/login';
            }, 1500);
        } else {
            showError(data.error || '注册失败，请重试');
            registerBtn.disabled = false;
            registerBtn.innerHTML = '注册';
        }
    } catch (error) {
        showError('网络错误: ' + error.message);
        registerBtn.disabled = false;
        registerBtn.innerHTML = '注册';
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
