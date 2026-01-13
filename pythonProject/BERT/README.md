# 基于BERT模型的智能客服系统

本系统实现了基于文本相似度的智能客服功能，支持通过编辑距离和BERT语义相似度匹配用户问题。

## 功能模块

### 1. 数据预处理 (`data_preprocessing.py`)
- **功能**: 从源数据中提取最佳答案的问答数据
- **函数**:
  - `read_data()`: 读取保险数据，筛选最佳答案
  - `save_data()`: 保存处理后的问答数据为CSV格式

### 2. BERT向量转换 (`bert_vector.py`)
- **功能**: 将问题转换为BERT向量表示
- **函数**:
  - `get_insurance_question()`: 获取问答数据中的问题
  - `bertconvert()`: 通过bert-as-service将问题转换为向量

### 3. 问题搜索 (`question_search.py`)
- **功能**: 在问答库中查找相同或相似的问题
- **函数**:
  - `find_similar_question()`: 使用编辑距离查找相似问题
  - `similarity_score()`: 计算字符串相似度得分

### 4. 智能客服系统 (`customer_service.py`)
- **功能**: 智能客服主程序
- **类**: `CustomerService`
- **方法**:
  - `answer()`: 回答用户问题
  - `batch_answer()`: 批量回答问题

### 5. 文本工具 (`text_utils.py`)
- **功能**: 文本清理工具函数
- **函数**:
  - `replace_punctuation()`: 去除文本中的标点符号（代码4.4）
  - `clean_text()`: 清理问题文本，只保留中文字符
  - `clean_ans()`: 清理答案信息中的不合法字符（代码4.8）

### 6. 编辑距离搜索 (`edit_distance_search.py`)
- **功能**: 根据编辑距离查找相同问题（代码4.3）
- **函数**:
  - `getSameQuestionByEditDistance()`: 根据编辑距离计算是否存在相同问题
  - `getSimilaryQuestionByIndex()`: 根据问题索引查找问题及相应答案（代码4.7）

### 7. 余弦相似度 (`cosine_similarity.py`)
- **功能**: 计算向量余弦相似度（代码4.6）
- **函数**:
  - `cosine_similarity()`: 计算两个向量的余弦相似度
  - `cosine_similarity_batch()`: 批量计算余弦相似度

### 8. 智能服务 (`intelligent_service.py`)
- **功能**: 智能客服核心服务（代码4.5）
- **函数**:
  - `getBestAnswer()`: 根据用户输入问题，系统给予相应回答
  - 支持编辑距离匹配和BERT语义匹配

### 9. API服务器 (`api_server.py`)
- **功能**: 封装API并部署在服务器上（代码4.9）
- **框架**: 使用aiohttp部署Web服务
- **端口**: 9010
- **访问方式**: GET请求，参数为`question`

## 安装依赖

```bash
pip install -r requirements.txt
```

### 可选依赖

如果需要使用BERT语义匹配功能，需要：
1. 安装bert-serving-client: `pip install bert-serving-client`
2. 启动bert-as-service服务（需要单独安装和启动）

如果只使用编辑距离匹配，可以只安装：
```bash
pip install numpy python-Levenshtein
```

## 使用步骤

### 1. 数据预处理

```python
from BERT import read_data, save_data

# 读取并处理数据
insurance_ques, insurance_ans = read_data()
save_data(insurance_ques, insurance_ans)
```

### 2. 生成问题向量（可选，用于BERT语义匹配）

```python
from BERT import get_insurance_question, bertconvert

# 获取问题列表
questions = get_insurance_question()

# 转换为BERT向量
bertconvert(questions)
```

### 3. 使用智能客服系统

```python
from BERT import CustomerService

# 创建客服系统实例
cs = CustomerService()

# 回答问题
answer, method, similarity = cs.answer("最近在安*长青树中看到什么豁免,这个是什么意思?")
print(f"答案: {answer}")
print(f"匹配方法: {method}")
print(f"相似度: {similarity:.4f}")
```

## 数据格式

### 输入数据格式 (`baoxianzhidao_filter.csv`)
CSV文件，包含4列：
- `title`: 问题标题
- `question`: 问题内容（可为空）
- `reply`: 回复内容
- `is_best`: 是否为最佳答案（1表示是，0表示否）

### 输出数据格式 (`insurance_data.csv`)
CSV文件，包含2列：
- `insurance_ques`: 保险问题描述
- `insurance_ans`: 对应答案

## 匹配策略

系统采用三种情况处理用户问题：

1. **完全相同或高度相似** (编辑距离相似度 >= 0.8)
   - 直接返回匹配问题的答案

2. **语义相似** (BERT相似度 >= 0.7)
   - 返回最相似问题的答案

3. **无法匹配**
   - 返回提示信息，建议用户换一种方式提问

## 文件结构

```
BERT/
├── __init__.py              # 包初始化文件
├── data_preprocessing.py    # 数据预处理（代码4.1）
├── bert_vector.py           # BERT向量转换（代码4.2）
├── question_search.py       # 问题搜索（简化版）
├── customer_service.py      # 智能客服主程序
├── text_utils.py           # 文本工具（代码4.4, 4.8）
├── edit_distance_search.py # 编辑距离搜索（代码4.3, 4.7）
├── cosine_similarity.py    # 余弦相似度（代码4.6）
├── intelligent_service.py  # 智能服务（代码4.5）
├── api_server.py           # API服务器（代码4.9）
├── requirements.txt        # 依赖包列表
└── README.md               # 说明文档
```

## 注意事项

1. **数据文件**: 需要准备源数据文件 `baoxianzhidao_filter.csv`
2. **BERT服务**: 使用BERT功能需要启动bert-as-service服务
3. **模拟模式**: 如果未安装bert-serving-client，系统会使用模拟模式生成随机向量
4. **性能优化**: 大量数据建议使用BERT向量进行快速语义匹配
5. **API部署**: API服务默认运行在9010端口，可通过浏览器或HTTP客户端访问
6. **文本清理**: 系统会自动清理标点符号和非法字符，提高匹配准确度
7. **相似度阈值**: 
   - 编辑距离阈值：0.98（完全相同）
   - BERT语义相似度阈值：0.9（高度相似）

## 示例数据

系统处理后的问答数据示例：
- 问题: "最近在安*长青树中看到什么豁免,这个是什么意思?"
- 答案: "您好,这个是重疾险中给予投保者的一项权利..."
