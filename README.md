# 数字人程序登录界面

一个功能完整的登录界面，支持密码登录和手机验证码登录两种方式，包含前端界面和后端API。

## 技术栈

### 前端
- HTML5：页面结构
- CSS3：样式设计（包含渐变、玻璃态效果、响应式布局）
- JavaScript (ES6+)：交互逻辑

### 后端
- Python Flask：Web框架
- SQLite：数据库存储
- SHA-256：密码加密

## 功能特点

### 登录功能
- 密码登录：支持用户名和密码登录
- 手机验证码登录：支持手机号和验证码登录
- 标签页切换：平滑切换两种登录方式

### 用户体验
- 实时表单验证
- 密码显示/隐藏功能
- 记住密码功能
- 验证码倒计时功能
- 系统消息提示
- 键盘事件增强

### 安全特性
- 密码SHA-256加密存储
- 输入数据验证
- API接口安全

### 后端API
- 用户注册
- 密码登录
- 手机验证码登录
- 发送短信验证码

## 文件结构

```
├── index.html          # 登录界面主页面
├── styles.css          # 样式文件
├── script.js           # 前端逻辑
├── app.py              # Flask后端API
├── database.py         # 数据库操作
└── README.md           # 项目说明文档
```

## 环境配置

### 安装依赖
```bash
pip install flask
```

## 运行方法

### 1. 启动后端服务器
```bash
python app.py
```

服务器将在 `http://localhost:8000` 启动

### 2. 打开前端页面
使用浏览器打开 `index.html` 文件

## API接口说明

### 1. 用户注册
- URL: `/api/register`
- Method: POST
- Request Body:
  ```json
  {
    "username": "用户名",
    "password": "密码",
    "phone": "手机号"
  }
  ```

### 2. 密码登录
- URL: `/api/login/password`
- Method: POST
- Request Body:
  ```json
  {
    "username": "用户名",
    "password": "密码"
  }
  ```

### 3. 手机验证码登录
- URL: `/api/login/sms`
- Method: POST
- Request Body:
  ```json
  {
    "phone": "手机号",
    "smsCode": "验证码"
  }
  ```

### 4. 发送短信验证码
- URL: `/api/send_sms`
- Method: POST
- Request Body:
  ```json
  {
    "phone": "手机号"
  }
  ```

### 5. 获取用户列表（测试用）
- URL: `/api/users`
- Method: GET

## 使用示例

### 密码登录
1. 在登录界面选择"密码登录"
2. 输入用户名：`admin`
3. 输入密码：`admin123`
4. 点击"登录"按钮

### 手机验证码登录
1. 在登录界面选择"手机验证码登录"
2. 输入手机号：`13800138000`
3. 点击"获取验证码"按钮（验证码默认为 `123456`）
4. 输入验证码：`123456`
5. 点击"登录"按钮

## 注意事项

1. 数据库默认使用SQLite，数据存储在 `users.db` 文件中
2. 短信验证码功能目前是模拟实现，实际使用需要集成短信服务商API
3. 生产环境建议使用更安全的密码加密算法和HTTPS协议
4. 示例用户信息：
   - 用户名：admin，密码：admin123，手机号：13800138000
   - 用户名：user，密码：user123，手机号：13900139000

## 浏览器兼容性

- Chrome (推荐)
- Firefox
- Safari
- Edge

## 开发说明

本项目使用了现代化的前端技术和后端框架，适合作为数字人程序的登录模块使用。可以根据实际需求进行扩展和定制。