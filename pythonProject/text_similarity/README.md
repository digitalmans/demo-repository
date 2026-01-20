# 文本相似度计算工具包

本工具包提供了多种文本相似度计算方法和自然语言处理功能。

## 功能模块

### 1. 编辑距离 (Edit Distance)
- **文件**: `edit_distance.py`
- **功能**: 计算两个字符串之间的Levenshtein距离（编辑距离）
- **方法**: 使用动态规划算法

### 2. 汉明距离 (Hamming Distance)
- **文件**: `hamming_distance.py`
- **功能**: 计算两个等长字符串之间的汉明距离
- **适用**: 等长字符串的字符差异计算

### 3. TF-IDF
- **文件**: `tfidf.py`
- **功能**: 计算词频-逆文档频率（Term Frequency-Inverse Document Frequency）
- **类**: `TFIDF`
- **用途**: 评估词在文档中的重要性

### 4. BM25
- **文件**: `bm25.py`
- **功能**: BM25算法，用于搜索引擎中的文档相关性评分
- **类**: `BM25`
- **用途**: 计算查询与文档之间的相似度

### 5. N-gram 语言模型
- **文件**: `ngram.py`
- **功能**: N-gram统计语言模型
- **类**: `NGramModel`
- **用途**: 计算文本的概率，支持bigram、trigram等

### 6. N-gram 距离
- **文件**: `ngram_distance.py`
- **功能**: 计算两个字符串之间的N-gram距离
- **类**: `NGram`
- **用途**: 基于N-gram的字符串相似度计算

### 7. Jaccard 距离/相似度
- **文件**: `jaccard.py`
- **功能**: 计算两个集合或文本的Jaccard相似系数和距离
- **函数**: `jaccard_similarity`, `jaccard_distance`, `jaccard_similarity_text`, `jaccard_distance_text`
- **用途**: 基于集合交并比的相似度计算

### 8. 最长公共子序列 (LCS)
- **文件**: `lcs.py`
- **功能**: 计算两个字符串的最长公共子序列
- **函数**: `lcs_length`, `lcs_sequence`, `lcs_similarity`
- **用途**: 基于公共子序列的相似度计算

### 9. Point-wise 模型
- **文件**: `pointwise.py`
- **功能**: 基于表示方法的语义文本相似度计算模型
- **类**: `PointWiseModel`
- **用途**: 将文本相似度转换为二分类任务，支持BOW/CNN/RNN表示和余弦相似度/MLP匹配

### 10. Pair-wise 模型
- **文件**: `pairwise.py`
- **功能**: Pair-wise语义匹配模型，通过构建偏序关系训练
- **类**: `PairwiseModel`
- **用途**: 使语义相似的句子对得分显著高于不相似的句子对

### 11. 损失函数
- **文件**: `loss_functions.py`
- **功能**: 各种损失函数实现
- **类**: 
  - `BinaryCrossEntropyLoss`: 二分类交叉熵损失（Point-wise）
  - `PairwiseHingeLoss`: Hinge损失（Pair-wise）
  - `PairwiseLogLoss`: Log损失（Pair-wise）
  - `SoftmaxWithLoss`: Softmax交叉熵损失

### 12. 训练脚本
- **文件**: `train_pairwise.py`
- **功能**: Pair-wise模型训练框架
- **函数**: `load_config`, `train`, `predict`

## 安装依赖

```bash
pip install numpy
```

## 使用示例

### 编辑距离
```python
from text_similarity import edit_distance

distance = edit_distance('hello', 'world')
print(distance)  # 输出: 4.0
```

### 汉明距离
```python
from text_similarity import hamming_distance

distance = hamming_distance('abc', 'abd')
print(distance)  # 输出: 1
```

### TF-IDF
```python
from text_similarity import TFIDF

corpus = [
    ['this', 'is', 'a', 'test'],
    ['this', 'is', 'another', 'test']
]
tfidf = TFIDF(corpus)
result = tfidf.get_tf_idf()
print(result)
```

### BM25
```python
from text_similarity import BM25

docs = [
    ['自然语言', '处理', '是', '计算机', '科学'],
    ['人工智能', '是', '重要', '方向']
]
bm = BM25(docs)
score = bm.score_all(['自然语言', '计算机'])
print(score)
```

### N-gram语言模型
```python
from text_similarity import NGramModel

corpus = ['自然语言处理', '人工智能']
model = NGramModel(n=2)
model.train(corpus)
prob = model.sentence_probability('自然语言')
print(prob)
```

### N-gram距离
```python
from text_similarity import NGram

twogram = NGram(2)
distance = twogram.distance('ABCD', 'ABTUIO')
print(distance)
```

### Jaccard相似度
```python
from text_similarity import jaccard_similarity, jaccard_similarity_text

# 集合相似度
set1 = {'a', 'b', 'c'}
set2 = {'b', 'c', 'd'}
similarity = jaccard_similarity(set1, set2)
print(similarity)

# 文本相似度（需要jieba）
text1 = "香农在信息论中提出的信息熵定义为自信息的期望"
text2 = "信息熵作为自信息的期望"
similarity = jaccard_similarity_text(text1, text2, use_jieba=True)
print(similarity)
```

### 最长公共子序列
```python
from text_similarity import lcs_length, lcs_sequence, lcs_similarity

str1 = "ABCDGH"
str2 = "AEDFHR"
lcs_len = lcs_length(str1, str2)
lcs_seq = lcs_sequence(str1, str2)
similarity = lcs_similarity(str1, str2)
print(f"LCS长度: {lcs_len}, LCS序列: {lcs_seq}, 相似度: {similarity}")
```

### Point-wise模型
```python
from text_similarity import PointWiseModel

model = PointWiseModel(representation_method='bow', matching_method='cosine')
score = model.predict("宝马启动空调就开了", "宝马启动空调")
print(f"相似度得分: {score}")
```

### Pair-wise模型
```python
from text_similarity import PairwiseModel

model = PairwiseModel(representation_method='bow', matching_method='cosine', margin=1.0)
query = "用电视机当笔记本电脑显示器好吗"
pos_sentence = "电视机可以当笔记本电脑的显示器吗"
neg_sentence = "笔记本电脑屏幕可以当电视机"

score_pos = model.predict(query, pos_sentence)
score_neg = model.predict(query, neg_sentence)
print(f"正样本得分: {score_pos:.4f}")
print(f"负样本得分: {score_neg:.4f}")

# 计算损失
from text_similarity import PairwiseHingeLoss
loss_layer = PairwiseHingeLoss({"margin": 1.0})
loss = loss_layer.ops(score_pos, score_neg)
print(f"Hinge损失: {loss:.4f}")
```

## 文件结构

```
text_similarity/
├── __init__.py          # 包初始化文件
├── edit_distance.py     # 编辑距离计算
├── hamming_distance.py  # 汉明距离计算
├── tfidf.py             # TF-IDF计算
├── bm25.py              # BM25算法
├── ngram.py             # N-gram语言模型
├── ngram_distance.py    # N-gram距离计算
├── jaccard.py           # Jaccard距离/相似度
├── lcs.py               # 最长公共子序列
├── pointwise.py         # Point-wise语义匹配模型
├── pairwise.py          # Pair-wise语义匹配模型
├── loss_functions.py    # 损失函数实现
├── train_pairwise.py    # 训练脚本
└── README.md            # 说明文档
```

## 注意事项

1. BM25和N-gram模型在实际使用时，建议配合中文分词工具（如jieba）使用
2. TF-IDF支持字符串和词列表两种输入格式
3. 编辑距离和汉明距离适用于不同场景，注意选择合适的算法
4. Jaccard相似度计算中文文本时，需要安装jieba: `pip install jieba`
5. Point-wise模型使用随机初始化的词向量，实际应用中应使用预训练的词向量（如Word2Vec、GloVe等）
6. N-gram距离和N-gram语言模型是不同的概念，分别用于距离计算和概率建模
7. Pair-wise模型需要三元组训练数据：(查询句子, 正样本, 负样本)
8. 损失函数支持Hinge Loss和Log Loss两种，可根据任务选择