注意： 由于仓库存储有限，我把可运行完整代码放这里了，包括用来训练的语料库：
我用夸克网盘给你分享了「pythonProject」，点击链接或复制整段内容，打开「夸克APP」即可获取。
/~4d803A7vfi~:/
链接：https://pan.quark.cn/s/3a4d5abf311a?pwd=zXHN
提取码：zXHN


# 智能问答系统

基于 Flask 的多功能智能问答平台，集成电影问答、通用问答机器人、语音助手和讨论区等功能。

## 功能特性

- 🎬 **电影问答**: 基于知识库的检索式电影问答系统
- 🤖 **问答机器人**: 基于 Neo4j 知识图谱的通用问答系统
- 💬 **讨论区**: 用户问答讨论和评论功能
- 🔊 **语音功能**: 支持文本转语音（TTS），多发音人选择
- 👥 **用户管理**: 完整的用户认证、权限管理和历史记录
- 🔐 **管理员后台**: 用户管理、内容审核等功能

## 环境要求

- Python 3.7+
- MySQL 5.7+ 或 MySQL 8.0+
- Neo4j 4.0+（可选，用于通用问答机器人）
- 百度 TTS API（用于语音功能）

## 安装步骤

### 1. 克隆项目

```bash
git clone <repository-url>
cd pythonProject
```

### 2. 创建虚拟环境（推荐）

你可以选择以下两种方式之一来创建并激活虚拟环境：

#### 方式一：使用 Conda 创建（可指定 Python 3.13.5 版本）
```bash
# 创建虚拟环境
conda create --prefix "C:\Users\Asus\Desktop\智能问答系统\pythonProject\.venv" python=3.13.5

# Windows 激活虚拟环境
conda activate "C:\Users\Asus\Desktop\智能问答系统\pythonProject\.venv"
```

#### 方式二：使用 Python 自带的 venv（极速创建）
```bash
# 创建虚拟环境
python -m venv .venv

# Windows 激活虚拟环境 (PowerShell)
.\.venv\Scripts\Activate.ps1

# Windows 激活虚拟环境 (CMD)
.\.venv\Scripts\activate
```

### 3. 安装依赖

```bash
pip install Flask==3.0.0
pip install pymysql
pip install py2neo==2021.2.3
pip install pandas==2.0.3
pip install jieba==0.42.1
pip install numpy>=1.20.0
pip install scikit-learn
```
数据库下载地址：https://neo4j.com/
下载方法参考： https://blog.csdn.net/weixin_66401877/article/details/153195602
<<<<<<< HEAD

=======
数据库下载需要科学上网。
>>>>>>> dc1a204e374ffceb0824039fe1af2ef7530360d6
运行前要配置百度语音api,配置方法参考： https://blog.csdn.net/Exaggeration08/article/details/105610925
在 ./voice_assistant/tts.py 中配置相应的API_KEY和SECRET_KEY 
然后再./voice_assistant/translator.py 中配置APP_ID ,SECRET_KEY ,TRANSLATE_URL 
不过翻译功能暂时还不能用。自己看着修改。

### 4. 配置数据库

#### MySQL 配置

编辑 `start/config.py`，修改数据库连接信息：

```python
MYSQL_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'your_password',
    'database': 'voice_assistant_db',
    'charset': 'utf8mb4'
}
```

创建数据库：

```sql
CREATE DATABASE voice_assistant_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

#### Neo4j 配置（可选）

如果使用通用问答机器人，需要配置 Neo4j：

1. 安装并启动 Neo4j 服务
2. 默认连接：`http://localhost:7474`
3. 用户名：`neo4j`
4. 密码：在 `ask_answer_robot/retrieval_engine.py` 中配置

### 5. 初始化数据库

首次运行会自动创建数据库表。默认管理员账号：
- 用户名：`daministrator`
- 密码：`123456`

## 启动方法

### 方式一：使用主启动文件（推荐）

```bash
python main.py
```

### 方式二：直接启动

```bash
cd start
python app.py
```

启动成功后访问：
- 主页面：http://localhost:5001
- 管理员后台：http://localhost:5001/admin

## 项目架构

### 目录结构

```
pythonProject/
├── main.py                 # 主启动文件
├── start/                  # 主应用目录
│   ├── app.py             # Flask 主应用
│   ├── database.py        # 数据库操作模块
│   ├── config.py          # 配置文件
│   ├── templates/         # HTML 模板
│   └── static/           # 静态资源（CSS、JS）
├── movieanswer/           # 电影问答模块
│   └── Movie-KBQA/       # 电影知识库问答
│       └── src/          # 检索服务源码
├── ask_answer_robot/     # 通用问答机器人模块
│   ├── retrieval_engine.py  # 检索引擎
│   ├── qa_service.py     # 问答服务
│   └── data_importer.py  # 数据导入工具
├── voice_assistant/      # 语音助手模块
│   ├── tts.py           # 文本转语音
│   ├── asr.py           # 语音识别
│   └── translator.py    # 翻译服务
└── text_similarity/     # 文本相似度算法模块
    ├── bm25.py
    ├── jaccard.py
    └── edit_distance.py
```

### 核心模块

1. **主应用层** (`start/app.py`)
   - Flask Web 应用
   - 路由管理
   - 用户认证与授权
   - API 接口

2. **数据层** (`start/database.py`)
   - MySQL 数据库操作
   - 用户管理
   - 历史记录存储
   - 讨论区数据管理

3. **问答模块**
   - **电影问答** (`movieanswer/`): 基于知识库的检索式问答
   - **通用问答** (`ask_answer_robot/`): 基于 Neo4j 的问答机器人

4. **算法模块** (`text_similarity/`)
   - BM25 检索
   - Jaccard 相似度
   - 编辑距离
   - TF-IDF

5. **服务模块** (`voice_assistant/`)
   - 语音合成（TTS）
   - 语音识别（ASR）
   - 文本翻译

### 技术栈

<<<<<<< HEAD
- **后端**: Python, Flask
- **数据库**: MySQL, Neo4j
- **前端**: HTML, CSS, JavaScript
- **算法**: 文本相似度算法, 检索式问答
=======
#### 后端技术

- **Web框架**: Flask 3.0.0
- **编程语言**: Python 3.7+
- **数据库驱动**:
  - PyMySQL - MySQL数据库连接
  - Py2neo 2021.2.3 - Neo4j图数据库连接
- **数据处理**:
  - Pandas 2.0.3 - 数据分析和处理
  - NumPy >=1.20.0 - 数值计算
- **中文处理**:
  - Jieba 0.42.1 - 中文分词
- **其他库**:
  - Werkzeug - Flask依赖，文件上传处理
  - Hashlib - 密码加密（MD5/SHA）
  - Threading - 多线程异步数据加载
  - JSON - 数据序列化

#### 前端技术

- **HTML5**: 页面结构
- **CSS3**: 
  - 内联样式和样式表
  - Flexbox布局
  - 渐变背景、动画效果
  - 响应式设计
- **JavaScript (ES6+)**:
  - 原生JavaScript（无框架依赖）
  - Fetch API - 异步HTTP请求
  - DOM操作
  - 事件处理
  - 音频播放控制（HTML5 Audio API）
  - 动态内容渲染

#### 数据库

- **MySQL 5.7+/8.0+**:
  - 用户认证和权限管理
  - 问答历史记录存储
  - 讨论区数据存储
  - 评论数据存储
  - TTS音频缓存
- **Neo4j 4.0+**:
  - 知识图谱存储
  - 问答对关系存储
  - 图数据库查询（Cypher查询语言）

#### 核心算法与技术点

- **文本相似度算法**:
  - **BM25**: 信息检索排序算法，用于计算查询与文档的相关性
  - **Jaccard相似度**: 基于集合交并比的相似度计算
  - **编辑距离 (Edit Distance)**: 字符串相似度计算（Levenshtein距离）
  - **TF-IDF**: 词频-逆文档频率，用于关键词提取和文本相似度
  - **最长公共子序列 (LCS)**: 文本相似度计算
  - **N-gram模型**: 文本特征提取

- **检索优化技术**:
  - **倒排索引 (Inverted Index)**: 快速候选问题检索
  - **候选过滤**: 基于关键词的预筛选，减少计算量
  - **多算法融合**: BM25、Jaccard、编辑距离加权组合
  - **相似度阈值过滤**: 低于阈值的结果不返回

- **中文处理技术**:
  - **中文分词**: 使用Jieba进行中文文本分词
  - **关键词提取**: 从问题中提取关键信息
  - **文本归一化**: 去除标点、空格等

- **性能优化**:
  - **异步数据加载**: 使用多线程后台加载大量数据
  - **数据缓存**: TTS音频缓存，避免重复生成
  - **索引优化**: 数据库索引优化查询速度
  - **分批加载**: 初始加载部分数据，剩余数据异步加载

#### 第三方服务集成

- **百度TTS API**:
  - 文本转语音服务
  - 支持4种中文发音人（度小美、度小字、度逍遥、度丫丫）
  - 音频格式：MP3
  - 语音缓存机制

- **百度翻译API** (已集成但未启用):
  - 中英文翻译功能
  - 需要配置APP_ID、SECRET_KEY、TRANSLATE_URL

#### 系统架构特点

- **模块化设计**: 各功能模块独立，便于维护和扩展
- **RESTful API**: 前后端分离，API接口标准化
- **Session管理**: Flask Session实现用户状态管理
- **权限控制**: 基于角色的访问控制（RBAC）
- **错误处理**: 完善的异常捕获和错误提示
- **快速问答匹配**: 预设问答对直接匹配，无需检索
>>>>>>> dc1a204e374ffceb0824039fe1af2ef7530360d6

## 主要功能模块

### 1. 电影问答

- 基于知识库的检索式问答
- 支持电影评分、演员信息、上映时间等查询
- 快速问答对直接匹配（9个预设问题）

### 2. 通用问答机器人

- 基于 Neo4j 知识图谱
- 支持多种文本相似度算法（BM25、Jaccard、编辑距离）
- 快速问答对直接匹配（10个预设问题）
- 异步数据加载，支持大数据集

### 3. 讨论区

- 用户发布问题和讨论
- 支持评论和回复
- 管理员审核和管理

### 4. 语音功能

- 文本转语音（TTS）
- 支持4种中文发音人选择
- 语音缓存机制

### 5. 用户管理

- 用户注册和登录
- 角色管理（普通用户、管理员）
- 历史记录查询和删除
- 管理员后台管理

## API 接口

### 用户认证

- `POST /api/register` - 用户注册
- `POST /api/login` - 用户登录
- `GET /api/logout` - 退出登录
- `GET /api/user_info` - 获取用户信息

### 电影问答

- `POST /api/movie/ask` - 提交问题
- `POST /api/movie/search` - 搜索相关问题
- `GET /api/movie/history` - 获取历史记录
- `POST /api/movie/history/delete` - 删除历史记录
- `GET /api/movie/stats` - 获取统计信息

### 问答机器人

- `POST /api/qa_robot/ask` - 提交问题
- `POST /api/qa_robot/search` - 搜索相关问题
- `GET /api/qa_robot/history` - 获取历史记录
- `POST /api/qa_robot/history/delete` - 删除历史记录
- `GET /api/qa_robot/stats` - 获取统计信息

### 讨论区

- `POST /api/qa_discussion/submit` - 提交讨论
- `GET /api/qa_discussion/list` - 获取讨论列表
- `GET /api/qa_discussion/<id>` - 获取讨论详情
- `POST /api/qa_discussion/<id>/comment` - 添加评论
- `DELETE /api/qa_discussion/<id>` - 删除讨论（管理员）

### 语音服务

- `POST /api/voice/tts` - 文本转语音

### 管理员接口

- `GET /api/admin/users` - 获取用户列表
- `POST /api/admin/users` - 创建用户
- `PUT /api/admin/user/<id>/role` - 更新用户角色
- `DELETE /api/admin/user/<id>` - 删除用户

## 数据导入

### 电影问答数据

电影问答数据位于 `movieanswer/Movie-KBQA/data/import/`，系统启动时自动加载。

### 通用问答机器人数据

1. 准备 CSV 语料库文件，放置在 `ask_answer_robot/语料库/` 目录
2. 运行数据导入脚本：

```bash
cd ask_answer_robot
python import_data.py
```

3. 导入快速问答对：

```bash
python import_quick_qa.py
```

## 配置说明

### 数据库配置

编辑 `start/config.py` 修改数据库连接信息。

### 应用密钥

修改 `start/config.py` 中的 `SECRET_KEY`，生产环境请使用强随机密钥。

### Neo4j 配置

编辑 `ask_answer_robot/retrieval_engine.py` 修改 Neo4j 连接信息。

### 语音服务配置

编辑 `voice_assistant/tts.py` 配置百度 TTS API 密钥。

## 注意事项

1. **数据库初始化**: 首次运行会自动创建数据库表，确保 MySQL 服务已启动
2. **Neo4j 服务**: 通用问答机器人需要 Neo4j 服务，如不使用可忽略相关错误
3. **数据加载**: 通用问答机器人首次启动会加载 20000 条数据，剩余数据在后台异步加载
4. **管理员账号**: 默认管理员账号为 `daministrator`，密码 `123456`，首次登录后建议修改
5. **端口占用**: 默认使用 5001 端口，如被占用请修改 `main.py` 或 `start/app.py` 中的端口配置

## 项目结构说明

- `main.py`: 主启动入口
- `start/`: 主应用代码
- `movieanswer/`: 电影问答模块
- `ask_answer_robot/`: 通用问答机器人模块
- `voice_assistant/`: 语音助手模块
- `text_similarity/`: 文本相似度算法库

## 开发说明

### 添加新的问答模块

1. 在对应目录创建服务类
2. 在 `start/app.py` 中导入并初始化
3. 添加路由和 API 接口
4. 创建前端模板

### 扩展快速问答对

编辑 `start/app.py` 中的 `QUICK_QA_MAP` 或 `MOVIE_QUICK_QA_MAP` 字典。

## 许可证

本项目仅供学习和研究使用。
