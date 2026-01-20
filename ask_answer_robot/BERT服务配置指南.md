# BERT服务配置指南

## 什么是BERT服务

BERT（Bidirectional Encoder Representations from Transformers）是一种预训练的语言模型，可以用于文本的语义向量化。通过BERT服务，可以将文本转换为高维向量，用于计算语义相似度，提高问答检索的准确性。

## 安装步骤

### 1. 安装bert-as-service

```bash
pip install bert-serving-server bert-serving-client
```

### 2. 下载中文BERT模型

需要下载中文BERT预训练模型。推荐使用：

**选项1：使用Google官方中文BERT模型**
- 模型名称：`chinese_L-12_H-768_A-12`
- 下载地址：https://storage.googleapis.com/bert_models/2018_11_03/chinese_L-12_H-768_A-12.zip
- 解压后得到模型目录

**选项2：使用Hugging Face的中文BERT模型**
- 模型名称：`bert-base-chinese`
- 使用transformers库加载

**选项3：使用其他中文BERT模型**
- 如：`chinese-bert-wwm-ext`、`chinese-roberta-wwm-ext` 等

### 3. 启动BERT服务

#### 方式1：使用bert-serving-start（推荐）

```bash
# 基本启动命令
bert-serving-start \
    -model_dir /path/to/chinese_L-12_H-768_A-12 \
    -num_worker=1 \
    -max_seq_len=128 \
    -port=5555 \
    -port_out=5556

# Windows PowerShell 示例（如果模型在D盘）
bert-serving-start -model_dir D:\models\chinese_L-12_H-768_A-12 -num_worker=1 -max_seq_len=128 -port=5555 -port_out=5556

# 如果使用GPU（需要安装tensorflow-gpu）
bert-serving-start \
    -model_dir /path/to/chinese_L-12_H-768_A-12 \
    -num_worker=1 \
    -max_seq_len=128 \
    -port=5555 \
    -port_out=5556 \
    -device_map=0  # 使用GPU 0
```

#### 方式2：使用Python脚本启动

创建 `start_bert_server.py`：

```python
#!/usr/bin/env python
# -*- coding:utf-8 -*-

import subprocess
import sys

# BERT模型路径
MODEL_DIR = r"D:\models\chinese_L-12_H-768_A-12"  # 修改为你的模型路径

# 启动参数
args = [
    sys.executable, "-m", "bert_serving.server",
    "-model_dir", MODEL_DIR,
    "-num_worker", "1",
    "-max_seq_len", "128",
    "-port", "5555",
    "-port_out", "5556"
]

print("正在启动BERT服务...")
print(f"模型路径: {MODEL_DIR}")
print(f"端口: 5555 (输入), 5556 (输出)")

try:
    subprocess.run(args, check=True)
except KeyboardInterrupt:
    print("\nBERT服务已停止")
except Exception as e:
    print(f"启动失败: {e}")
```

运行：
```bash
python start_bert_server.py
```

## 参数说明

- `-model_dir`: BERT模型目录路径（必需）
- `-num_worker`: 工作进程数（建议1-2，根据CPU核心数）
- `-max_seq_len`: 最大序列长度（默认128，可根据需要调整）
- `-port`: 输入端口（默认5555）
- `-port_out`: 输出端口（默认5556）
- `-device_map`: GPU设备映射（如 `0` 表示使用GPU 0，`-1` 表示使用CPU）

## 验证BERT服务

### 方法1：使用Python测试

```python
from bert_serving.client import BertClient

# 连接BERT服务
bc = BertClient(ip='localhost', port=5555)

# 测试编码
texts = ['你好', '世界']
vectors = bc.encode(texts)
print(f"向量维度: {vectors.shape}")
print("✓ BERT服务连接成功！")
```

### 方法2：在问答机器人中启用

修改 `start/app.py`：

```python
# 修改这一行
qa_robot_service = QAService(use_bert=True, max_initial_load=20000)
```

然后重启服务器，应该会看到：
```
✓ BERT服务连接成功 (host=localhost, port=5555)
```

## 常见问题

### 1. 端口被占用

**错误**: `Address already in use`

**解决**:
- 检查端口5555是否被占用：`netstat -ano | findstr 5555` (Windows)
- 修改端口号：`-port=5557 -port_out=5558`
- 或者关闭占用端口的程序

### 2. 模型路径错误

**错误**: `No such file or directory`

**解决**:
- 确认模型目录路径正确
- 确认模型目录包含以下文件：
  - `bert_config.json`
  - `vocab.txt`
  - `bert_model.ckpt.*` (三个文件)

### 3. 内存不足

**错误**: `Out of memory`

**解决**:
- 减少 `num_worker` 数量
- 减少 `max_seq_len` 长度
- 使用更小的BERT模型
- 增加系统内存

### 4. TensorFlow版本问题

**错误**: 各种TensorFlow相关错误

**解决**:
```bash
# 安装兼容的TensorFlow版本
pip install tensorflow==1.15.0  # 或 tensorflow-gpu==1.15.0

# 或者使用新版本（需要兼容的bert-serving-server）
pip install tensorflow==2.x
```

### 5. 连接超时

**错误**: `no response from the server`

**解决**:
- 确认BERT服务已启动
- 检查防火墙设置
- 增加超时时间（在代码中修改timeout参数）

## 性能优化建议

1. **使用GPU加速**（如果有NVIDIA GPU）:
   ```bash
   pip install tensorflow-gpu
   bert-serving-start -model_dir ... -device_map=0
   ```

2. **调整worker数量**:
   - CPU: 1-2个worker
   - GPU: 1个worker（GPU可以并行处理）

3. **调整序列长度**:
   - 短文本：64或128
   - 长文本：256或512（会增加内存使用）

4. **批量处理**:
   - 代码中已实现批量编码（batch_size=32）
   - 可以根据内存情况调整

## 启动脚本示例

### Windows批处理文件 (`start_bert.bat`)

```batch
@echo off
echo 正在启动BERT服务...
echo.

set MODEL_DIR=D:\models\chinese_L-12_H-768_A-12
set PORT=5555
set PORT_OUT=5556

bert-serving-start ^
    -model_dir %MODEL_DIR% ^
    -num_worker=1 ^
    -max_seq_len=128 ^
    -port=%PORT% ^
    -port_out=%PORT_OUT%

pause
```

### Linux/Mac Shell脚本 (`start_bert.sh`)

```bash
#!/bin/bash

MODEL_DIR="/path/to/chinese_L-12_H-768_A-12"
PORT=5555
PORT_OUT=5556

echo "正在启动BERT服务..."
echo "模型路径: $MODEL_DIR"
echo "端口: $PORT (输入), $PORT_OUT (输出)"

bert-serving-start \
    -model_dir "$MODEL_DIR" \
    -num_worker=1 \
    -max_seq_len=128 \
    -port=$PORT \
    -port_out=$PORT_OUT
```

## 在问答机器人中使用

### 启用BERT

1. **启动BERT服务**（在另一个终端）:
   ```bash
   bert-serving-start -model_dir /path/to/model -port=5555
   ```

2. **修改配置**（`start/app.py`）:
   ```python
   qa_robot_service = QAService(use_bert=True, max_initial_load=20000)
   ```

3. **重启服务器**:
   ```bash
   python start/app.py
   ```

### 禁用BERT（默认）

如果不想使用BERT，保持默认配置即可：
```python
qa_robot_service = QAService(use_bert=False, max_initial_load=20000)
```

## 注意事项

1. **BERT服务需要持续运行**：启动后不要关闭终端，服务需要一直运行
2. **首次启动较慢**：第一次启动需要加载模型，可能需要1-2分钟
3. **内存占用**：BERT服务会占用较多内存（通常2-4GB）
4. **CPU vs GPU**：GPU可以显著加速，但需要NVIDIA GPU和CUDA支持

## 快速测试

运行以下Python脚本测试BERT服务：

```python
from bert_serving.client import BertClient

try:
    bc = BertClient(ip='localhost', port=5555, timeout=10000)
    result = bc.encode(['测试文本'])
    print(f"✓ BERT服务连接成功！")
    print(f"向量维度: {result.shape}")
except Exception as e:
    print(f"✗ 连接失败: {e}")
    print("请确认BERT服务已启动")
```

## 更多资源

- bert-as-service官方文档: https://github.com/hanxiao/bert-as-service
- 中文BERT模型下载: https://github.com/google-research/bert
- Hugging Face模型库: https://huggingface.co/models
