class LoginSystem {
    constructor() {
        this.initializeElements();
        this.bindEvents();
        this.loadRememberedCredentials();
        this.currentTab = 'password';
        this.smsCountdown = 60;
        this.smsTimer = null;
    }

    initializeElements() {
        // 标签切换
        this.tabBtns = document.querySelectorAll('.tab-btn');
        this.passwordLoginForm = document.getElementById('passwordLoginForm');
        this.smsLoginForm = document.getElementById('smsLoginForm');
        
        // 密码登录
        this.usernameInput = document.getElementById('username');
        this.passwordInput = document.getElementById('password');
        this.rememberMeCheckbox = document.getElementById('rememberMe');
        this.togglePasswordBtn = document.getElementById('togglePassword');
        this.passwordLoginBtn = this.passwordLoginForm.querySelector('.login-btn');
        
        // 手机验证码登录
        this.phoneInput = document.getElementById('phone');
        this.smsCodeInput = document.getElementById('smsCode');
        this.sendSmsBtn = document.getElementById('sendSmsBtn');
        this.smsLoginBtn = this.smsLoginForm.querySelector('.login-btn');
        
        // 消息和错误提示
        this.systemMessage = document.getElementById('systemMessage');
        this.usernameError = document.getElementById('usernameError');
        this.passwordError = document.getElementById('passwordError');
        this.phoneError = document.getElementById('phoneError');
        this.smsCodeError = document.getElementById('smsCodeError');
    }

    bindEvents() {
        // 标签切换事件
        this.tabBtns.forEach(btn => {
            btn.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });
        
        // 密码登录表单事件
        this.passwordLoginForm.addEventListener('submit', (e) => this.handlePasswordSubmit(e));
        this.togglePasswordBtn.addEventListener('click', () => this.togglePassword());
        this.usernameInput.addEventListener('input', () => this.validateUsername());
        this.passwordInput.addEventListener('input', () => this.validatePassword());
        
        // 手机验证码登录表单事件
        this.smsLoginForm.addEventListener('submit', (e) => this.handleSmsSubmit(e));
        this.sendSmsBtn.addEventListener('click', () => this.sendSmsCode());
        this.phoneInput.addEventListener('input', () => this.validatePhone());
        this.smsCodeInput.addEventListener('input', () => this.validateSmsCode());
    }

    // 标签切换功能
    switchTab(tabName) {
        if (this.currentTab === tabName) return;
        
        // 更新标签按钮状态
        this.tabBtns.forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
        
        // 切换表单显示
        this.passwordLoginForm.classList.remove('active');
        this.smsLoginForm.classList.remove('active');
        document.getElementById(`${tabName}LoginForm`).classList.add('active');
        
        // 更新当前标签
        this.currentTab = tabName;
        
        // 清空错误消息
        this.clearAllErrors();
        this.hideSystemMessage();
    }

    // 密码登录提交
    handlePasswordSubmit(e) {
        e.preventDefault();
        
        if (this.validatePasswordForm()) {
            this.showSystemMessage('正在登录...', 'info');
            this.passwordLoginBtn.disabled = true;
            
            // 模拟登录请求
            setTimeout(() => {
                this.performPasswordLogin();
            }, 1500);
        }
    }

    // 验证码登录提交
    handleSmsSubmit(e) {
        e.preventDefault();
        
        if (this.validateSmsForm()) {
            this.showSystemMessage('正在登录...', 'info');
            this.smsLoginBtn.disabled = true;
            
            // 模拟登录请求
            setTimeout(() => {
                this.performSmsLogin();
            }, 1500);
        }
    }

    // 密码表单验证
    validatePasswordForm() {
        let isValid = true;
        
        if (!this.validateUsername()) {
            isValid = false;
        }
        
        if (!this.validatePassword()) {
            isValid = false;
        }
        
        return isValid;
    }

    // 验证码表单验证
    validateSmsForm() {
        let isValid = true;
        
        if (!this.validatePhone()) {
            isValid = false;
        }
        
        if (!this.validateSmsCode()) {
            isValid = false;
        }
        
        return isValid;
    }

    // 用户名验证
    validateUsername() {
        const username = this.usernameInput.value.trim();
        
        if (username === '') {
            this.showError(this.usernameError, '用户名不能为空');
            this.usernameInput.classList.add('error');
            return false;
        } else if (username.length < 3) {
            this.showError(this.usernameError, '用户名至少需要3个字符');
            this.usernameInput.classList.add('error');
            return false;
        } else if (username.length > 20) {
            this.showError(this.usernameError, '用户名不能超过20个字符');
            this.usernameInput.classList.add('error');
            return false;
        } else {
            this.clearError(this.usernameError);
            this.usernameInput.classList.remove('error');
            return true;
        }
    }

    // 密码验证
    validatePassword() {
        const password = this.passwordInput.value;
        
        if (password === '') {
            this.showError(this.passwordError, '密码不能为空');
            this.passwordInput.classList.add('error');
            return false;
        } else if (password.length < 6) {
            this.showError(this.passwordError, '密码至少需要6个字符');
            this.passwordInput.classList.add('error');
            return false;
        } else {
            this.clearError(this.passwordError);
            this.passwordInput.classList.remove('error');
            return true;
        }
    }

    // 手机号验证
    validatePhone() {
        const phone = this.phoneInput.value.trim();
        const phoneRegex = /^1[3-9]\d{9}$/;
        
        if (phone === '') {
            this.showError(this.phoneError, '手机号不能为空');
            this.phoneInput.classList.add('error');
            return false;
        } else if (!phoneRegex.test(phone)) {
            this.showError(this.phoneError, '请输入正确的手机号格式');
            this.phoneInput.classList.add('error');
            return false;
        } else {
            this.clearError(this.phoneError);
            this.phoneInput.classList.remove('error');
            return true;
        }
    }

    // 验证码验证
    validateSmsCode() {
        const smsCode = this.smsCodeInput.value.trim();
        
        if (smsCode === '') {
            this.showError(this.smsCodeError, '验证码不能为空');
            this.smsCodeInput.classList.add('error');
            return false;
        } else if (smsCode.length !== 6) {
            this.showError(this.smsCodeError, '验证码必须是6位数字');
            this.smsCodeInput.classList.add('error');
            return false;
        } else if (!/^\d{6}$/.test(smsCode)) {
            this.showError(this.smsCodeError, '验证码只能包含数字');
            this.smsCodeInput.classList.add('error');
            return false;
        } else {
            this.clearError(this.smsCodeError);
            this.smsCodeInput.classList.remove('error');
            return true;
        }
    }

    // 发送验证码
    async sendSmsCode() {
        if (!this.validatePhone()) {
            return;
        }
        
        const phone = this.phoneInput.value.trim();
        
        this.showSystemMessage('正在发送验证码...', 'info');
        this.sendSmsBtn.disabled = true;
        
        try {
            // 调用发送验证码API
            const response = await fetch('http://localhost:8000/api/send_sms', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ phone })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.startSmsCountdown();
                this.showSystemMessage(`验证码已发送至 ${phone}，请注意查收`, 'success');
            } else {
                this.showSystemMessage(result.message, 'error');
                this.sendSmsBtn.disabled = false;
            }
        } catch (error) {
            this.showSystemMessage('网络错误，请稍后重试', 'error');
            this.sendSmsBtn.disabled = false;
        }
    }

    // 验证码倒计时
    startSmsCountdown() {
        this.smsCountdown = 60;
        this.sendSmsBtn.textContent = `${this.smsCountdown}秒后重发`;
        this.sendSmsBtn.classList.add('counting');
        
        this.smsTimer = setInterval(() => {
            this.smsCountdown--;
            this.sendSmsBtn.textContent = `${this.smsCountdown}秒后重发`;
            
            if (this.smsCountdown <= 0) {
                this.stopSmsCountdown();
            }
        }, 1000);
    }

    // 停止倒计时
    stopSmsCountdown() {
        if (this.smsTimer) {
            clearInterval(this.smsTimer);
            this.smsTimer = null;
        }
        
        this.sendSmsBtn.textContent = '获取验证码';
        this.sendSmsBtn.disabled = false;
        this.sendSmsBtn.classList.remove('counting');
    }

    // 密码登录验证
    async performPasswordLogin() {
        const username = this.usernameInput.value.trim();
        const password = this.passwordInput.value;
        
        try {
            // 调用密码登录API
            const response = await fetch('http://localhost:8000/api/login/password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ username, password })
            });
            
            const result = await response.json();
            
            if (result.success) {
                // 保存记住密码
                if (this.rememberMeCheckbox.checked) {
                    this.saveCredentials(username, password);
                } else {
                    this.clearCredentials();
                }
                
                this.showSystemMessage('登录成功！正在跳转...', 'success');
                
                // 模拟跳转
                setTimeout(() => {
                    this.redirectToDashboard();
                }, 1500);
            } else {
                this.showSystemMessage(result.message, 'error');
                this.passwordLoginBtn.disabled = false;
                // 清空密码
                this.passwordInput.value = '';
                this.passwordInput.focus();
            }
        } catch (error) {
            this.showSystemMessage('网络错误，请稍后重试', 'error');
            this.passwordLoginBtn.disabled = false;
        }
    }

    // 手机验证码登录验证
    async performSmsLogin() {
        const phone = this.phoneInput.value.trim();
        const smsCode = this.smsCodeInput.value.trim();
        
        try {
            // 调用短信验证码登录API
            const response = await fetch('http://localhost:8000/api/login/sms', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ phone, smsCode })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showSystemMessage('登录成功！正在跳转...', 'success');
                
                // 模拟跳转
                setTimeout(() => {
                    this.redirectToDashboard();
                }, 1500);
            } else {
                this.showSystemMessage(result.message, 'error');
                this.smsLoginBtn.disabled = false;
                // 清空验证码
                this.smsCodeInput.value = '';
                this.smsCodeInput.focus();
            }
        } catch (error) {
            this.showSystemMessage('网络错误，请稍后重试', 'error');
            this.smsLoginBtn.disabled = false;
        }
    }

    // 密码验证逻辑
    isValidPasswordCredentials(username, password) {
        // 这里应该是实际的后端验证
        // 模拟验证：admin/admin 或 user/user
        return (username === 'admin' && password === 'admin') || 
               (username === 'user' && password === 'user');
    }

    // 验证码验证逻辑
    isValidSmsCredentials(phone, smsCode) {
        // 这里应该是实际的后端验证
        // 模拟验证：任意手机号 + 123456
        return smsCode === '123456';
    }

    togglePassword() {
        const type = this.passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
        this.passwordInput.setAttribute('type', type);
        this.togglePasswordBtn.classList.toggle('show');
    }

    saveCredentials(username, password) {
        try {
            // 使用localStorage保存凭证
            localStorage.setItem('rememberedUsername', username);
            // 简单加密密码（实际项目中应该使用更安全的方式）
            const encryptedPassword = btoa(password);
            localStorage.setItem('rememberedPassword', encryptedPassword);
        } catch (error) {
            console.error('保存凭证失败:', error);
        }
    }

    clearCredentials() {
        try {
            localStorage.removeItem('rememberedUsername');
            localStorage.removeItem('rememberedPassword');
        } catch (error) {
            console.error('清除凭证失败:', error);
        }
    }

    loadRememberedCredentials() {
        try {
            const username = localStorage.getItem('rememberedUsername');
            const encryptedPassword = localStorage.getItem('rememberedPassword');
            
            if (username && encryptedPassword) {
                this.usernameInput.value = username;
                // 解密密码
                const password = atob(encryptedPassword);
                this.passwordInput.value = password;
                this.rememberMeCheckbox.checked = true;
            }
        } catch (error) {
            console.error('加载凭证失败:', error);
            this.clearCredentials();
        }
    }

    showError(element, message) {
        element.textContent = message;
        element.style.display = 'block';
    }

    clearError(element) {
        element.textContent = '';
        element.style.display = 'none';
    }

    showSystemMessage(message, type) {
        this.systemMessage.textContent = message;
        this.systemMessage.className = `system-message ${type}`;
        this.systemMessage.style.display = 'block';
        
        // 自动隐藏消息
        if (type !== 'info') {
            setTimeout(() => {
                this.hideSystemMessage();
            }, 3000);
        }
    }

    hideSystemMessage() {
        this.systemMessage.style.display = 'none';
    }

    redirectToDashboard() {
        // 这里应该是实际的跳转逻辑
        alert('登录成功！将跳转到控制台页面');
        // window.location.href = 'dashboard.html';
    }
}

// 页面加载完成后初始化登录系统
document.addEventListener('DOMContentLoaded', () => {
    new LoginSystem();
});

// 添加键盘事件增强用户体验
document.addEventListener('keydown', (e) => {
    // 如果是密码框并且按下Enter，触发表单提交
    if (e.target.type === 'password' && e.key === 'Enter') {
        const activeForm = document.querySelector('.login-form.active');
        if (activeForm) {
            activeForm.dispatchEvent(new Event('submit'));
        }
    }
});

// 添加输入框焦点效果
document.querySelectorAll('input').forEach(input => {
    input.addEventListener('focus', function() {
        this.parentElement.classList.add('focused');
    });
    
    input.addEventListener('blur', function() {
        this.parentElement.classList.remove('focused');
    });
});