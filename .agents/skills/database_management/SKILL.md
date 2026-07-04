---
name: "Database Management and Schema Guide"
description: "Instructions, table/graph schemas, operations, and troubleshooting for MySQL and Neo4j databases in the Intelligent QA System."
---

# 智能问答系统数据库管理与 Schema 指南

本 Skill 旨在协助开发者管理、查询、重置及排查本智能问答系统中使用的 **MySQL** 和 **Neo4j** 数据库。

---

## 1. 数据库基本配置

数据库配置文件位于 `start/config.py`，你可以在该文件中找到和修改连接信息：

* **MySQL 配置** (`MYSQL_CONFIG`):
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
* **Neo4j 配置**:
  * 默认连接地址: `http://localhost:7474` (HTTP) 或 `bolt://localhost:7687` (Bolt)
  * 默认用户名: `neo4j`
  * 默认密码: 在 `ask_answer_robot/retrieval_engine.py` (检索引擎) 和 `ask_answer_robot/data_importer.py` (数据导入器) 中配置。

---

## 2. MySQL 数据库 Schema

MySQL 数据库的初始化入口为 `start/database.py` 中的 `init_database()`。首次运行程序时会自动创建以下表结构：

### 2.1 用户表 (`users`)
存储系统用户和管理员的认证信息与角色。
* **DDL 结构**:
  ```sql
  CREATE TABLE users (
      id INT AUTO_INCREMENT PRIMARY KEY,
      username VARCHAR(50) NOT NULL UNIQUE,
      password VARCHAR(255) NOT NULL,
      email VARCHAR(100),
      role VARCHAR(20) DEFAULT 'user' COMMENT '用户角色: user(普通用户), admin(管理员)',
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      last_login TIMESTAMP NULL,
      INDEX idx_username (username),
      INDEX idx_role (role)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
  ```
* **默认账号**:
  * 超级管理员: `daministrator` / `123456`
  * 备用管理员: `admin` / `admin123`

### 2.2 问答机器人历史记录表 (`qa_robot_history`)
记录用户向通用问答机器人提问的历史以及相似度匹配得分。
* **DDL 结构**:
  ```sql
  CREATE TABLE qa_robot_history (
      id INT AUTO_INCREMENT PRIMARY KEY,
      user_id INT NOT NULL,
      username VARCHAR(50) NOT NULL,
      question TEXT NOT NULL,
      answer TEXT NOT NULL,
      similarity FLOAT COMMENT '相似度分数',
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      INDEX idx_user_id (user_id),
      INDEX idx_username (username),
      INDEX idx_created_at (created_at),
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
  ```

### 2.3 TTS 音频文件缓存表 (`tts_audio_cache`)
为避免重复向百度 API 请求相同的文本转语音服务，系统会对音频文件进行本地 MD5 哈希缓存。
* **DDL 结构**:
  ```sql
  CREATE TABLE tts_audio_cache (
      id INT AUTO_INCREMENT PRIMARY KEY,
      text_hash VARCHAR(64) NOT NULL COMMENT '文本内容的MD5哈希值',
      language VARCHAR(10) NOT NULL DEFAULT 'zh' COMMENT '语言: zh(中文), en(英文)',
      file_path VARCHAR(500) NOT NULL COMMENT '音频文件路径',
      file_size BIGINT COMMENT '文件大小（字节）',
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
      last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后访问时间',
      access_count INT DEFAULT 0 COMMENT '访问次数',
      UNIQUE KEY uk_text_lang (text_hash, language),
      INDEX idx_text_hash (text_hash),
      INDEX idx_language (language),
      INDEX idx_last_accessed (last_accessed)
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
  ```

### 2.4 QA 讨论区主表 (`qa_discussion`)
存储用户在讨论区发布的问题与帖子。
* **DDL 结构**:
  ```sql
  CREATE TABLE qa_discussion (
      id INT AUTO_INCREMENT PRIMARY KEY,
      user_id INT NOT NULL,
      username VARCHAR(50) NOT NULL,
      content TEXT NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
      INDEX idx_user_id (user_id),
      INDEX idx_username (username),
      INDEX idx_created_at (created_at),
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
  ```

### 2.5 QA 讨论区评论表 (`qa_comments`)
存储针对具体帖子的用户评论和回复。
* **DDL 结构**:
  ```sql
  CREATE TABLE qa_comments (
      id INT AUTO_INCREMENT PRIMARY KEY,
      discussion_id INT NOT NULL,
      user_id INT NOT NULL,
      username VARCHAR(50) NOT NULL,
      content TEXT NOT NULL,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      INDEX idx_discussion_id (discussion_id),
      INDEX idx_user_id (user_id),
      INDEX idx_created_at (created_at),
      FOREIGN KEY (discussion_id) REFERENCES qa_discussion(id) ON DELETE CASCADE,
      FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
  ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
  ```

---

## 3. Neo4j 图数据库 Schema

通用问答机器人利用 Neo4j 存储大量的预设问答知识。

### 3.1 节点定义 (`QA`)
所有知识以 `QA` 标签的节点进行存储：
* **节点属性**:
  * `id`: 问答对的唯一标识号 (ID)
  * `question`: 原始问题文本
  * `answer`: 对应匹配的答案
  * `source`: 语料来源 (例如 CSV 导入的文件名等)

### 3.2 数据导入与重置

如果需要清空或重新导入通用知识图谱：

1. **导入/更新通用问答语料 (CSV)**:
   将你的 CSV 格式语料库文件放入 `ask_answer_robot/语料库/` 中，然后运行数据导入工具：
   ```bash
   cd ask_answer_robot
   python import_data.py
   ```
2. **导入快速问答对 (Quick QA)**:
   ```bash
   python import_quick_qa.py
   ```

---

## 4. 常用操作与查询命令

### 4.1 MySQL 操作命令 (CLI)
* **进入 MySQL 控制台**:
  ```bash
  mysql -u root -p
  ```
* **手动创建数据库**:
  ```sql
  CREATE DATABASE IF NOT EXISTS voice_assistant_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
  ```
* **重置指定用户为管理员**:
  ```sql
  UPDATE voice_assistant_db.users SET role='admin' WHERE username='你的用户名';
  ```

### 4.2 Neo4j 常用 Cypher 查询
在 Neo4j Browser (`http://localhost:7474`) 中运行：
* **统计知识库总问答对数**:
  ```cypher
  MATCH (q:QA) RETURN count(q) AS total_qa;
  ```
* **查询前 5 条问答内容**:
  ```cypher
  MATCH (q:QA) RETURN q.id, q.question, q.answer LIMIT 5;
  ```
* **按关键词模糊搜索问题**:
  ```cypher
  MATCH (q:QA) WHERE q.question CONTAINS 'Python' RETURN q.question, q.answer LIMIT 10;
  ```
* **安全清空所有 QA 数据**:
  ```cypher
  MATCH (q:QA) DETACH DELETE q;
  ```

---

## 5. 常见问题排查与解决

1. **MySQL 连接失败 (`pymysql.err.OperationalError`)**:
   * **症状**: 启动项目时提示 `Can't connect to MySQL server on 'localhost'`。
   * **解决**: 请检查 Windows 服务的 MySQL 是否启动。在管理员身份的 PowerShell 中运行：
     ```powershell
     Start-Service -Name mysql
     # 或者如果是特定的版本服务名 (如 mysql80):
     Start-Service -Name mysql80
     ```
2. **Neo4j 连接失败**:
   * **症状**: 机器人模块后台报错，无法成功载入快速问答。
   * **解决**: 
     1. 检查 `ask_answer_robot/retrieval_engine.py` 和 `data_importer.py` 中的 `neo4j_password` 是否与你实际安装的 Neo4j 密码一致。
     2. 检查 Neo4j 服务是否启动。
