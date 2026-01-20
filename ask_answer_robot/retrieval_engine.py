#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
检索式问答引擎
基于BERT语义相似度和text_similarity模块从Neo4j中检索最相关的答案
"""

import jieba
import re
import os
import sys
import numpy as np
import threading
import time
from py2neo import Graph
from collections import Counter

# 添加text_similarity到路径
text_similarity_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'text_similarity')
if text_similarity_path not in sys.path:
    sys.path.insert(0, text_similarity_path)

try:
    from bm25 import BM25
    from jaccard import jaccard_similarity_text
    from edit_distance import edit_distance
    TEXT_SIMILARITY_AVAILABLE = True
except ImportError as e:
    print(f"警告: 无法导入text_similarity模块: {e}")
    TEXT_SIMILARITY_AVAILABLE = False

# 尝试导入BERT
try:
    from bert_serving.client import BertClient
    BERT_AVAILABLE = True
except ImportError:
    print("警告: bert_serving未安装，将使用text_similarity方法")
    BERT_AVAILABLE = False


class RetrievalEngine:
    """检索式问答引擎 - 基于BERT和text_similarity"""
    
    def __init__(self, neo4j_uri="http://localhost:7474",
                 neo4j_username="neo4j",
                 neo4j_password="xh050316",
                 use_bert=False,
                 bert_host="localhost",
                 bert_port=5555,
                 max_initial_load=20000):
        """
        初始化检索引擎
        :param neo4j_uri: Neo4j数据库URI
        :param neo4j_username: 用户名
        :param neo4j_password: 密码
        :param use_bert: 是否使用BERT（需要bert-as-service运行）
        :param bert_host: BERT服务主机
        :param bert_port: BERT服务端口
        :param max_initial_load: 初始加载的最大数据量（默认20000，避免启动过慢）
        """
        self.neo4j_uri = neo4j_uri
        self.neo4j_username = neo4j_username
        self.neo4j_password = neo4j_password
        self.graph = None
        
        # BERT配置（已禁用，强制使用text_similarity方法）
        self.use_bert = False  # 强制禁用BERT，使用text_similarity方法
        self.bert_client = None
        self.bert_host = bert_host
        self.bert_port = bert_port
        
        # 初始化jieba
        jieba.initialize()
        
        # 停用词
        self.stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', 
                          '不', '人', '都', '一', '一个', '上', '也', '很',
                          '到', '说', '要', '去', '你', '会', '着', '没有',
                          '看', '好', '自己', '这', '那', '什么', '怎么',
                          '吗', '呢', '啊', '吧', '呀', '哦', '嗯'}
        
        # 连接数据库
        self.connect_neo4j()
        
        # 初始化BERT客户端（已禁用）
        # if self.use_bert:
        #     self._init_bert_client()
        
        # 缓存：存储所有问答对和向量
        self.qa_pairs = []  # [(question, answer, qa_id), ...]
        self.question_vectors = None  # BERT向量矩阵
        self.bm25_model = None  # BM25模型
        
        # 后台加载相关
        self.total_qa_count = 0  # 总数据量
        self.loading_complete = False  # 是否加载完成
        self.loading_thread = None  # 后台加载线程
        self._qa_pairs_lock = threading.Lock()  # 线程锁，保护qa_pairs
        
        # 加载初始数据
        self.max_initial_load = max_initial_load
        self._load_initial_data(max_initial_load=max_initial_load)
        
        # 启动后台加载线程
        self._start_background_loading()
    
    def connect_neo4j(self):
        """连接Neo4j数据库"""
        connection_methods = [
            ("使用auth参数连接", lambda: Graph(self.neo4j_uri, auth=(self.neo4j_username, self.neo4j_password))),
            ("使用username/password参数连接", lambda: Graph(self.neo4j_uri, username=self.neo4j_username, password=self.neo4j_password)),
            ("使用Bolt协议连接", lambda: Graph("bolt://localhost:7687", auth=(self.neo4j_username, self.neo4j_password))),
        ]
        
        for method_name, method in connection_methods:
            try:
                self.graph = method()
                self.graph.run("RETURN 1")
                print(f"✓ 成功连接到Neo4j数据库")
                return
            except Exception as e:
                continue
        
        raise Exception("无法连接到Neo4j数据库，请确保服务已启动")
    
    def _init_bert_client(self):
        """初始化BERT客户端"""
        try:
            print(f"正在连接BERT服务 (host={self.bert_host}, port={self.bert_port})...")
            # 设置较短的超时时间，避免长时间等待
            self.bert_client = BertClient(ip=self.bert_host, port=self.bert_port, timeout=5000)
            # 测试连接（设置超时）
            test_vec = self.bert_client.encode(['测试'])
            print(f"✓ BERT服务连接成功 (host={self.bert_host}, port={self.bert_port})")
        except Exception as e:
            print(f"✗ BERT服务连接失败: {e}")
            print("  将使用text_similarity方法进行检索（不依赖BERT服务）")
            self.use_bert = False
            self.bert_client = None
    
    def _load_initial_data(self, max_initial_load=20000):
        """
        加载初始数据（快速启动）
        :param max_initial_load: 初始加载的最大数量
        """
        print("正在加载初始数据（快速启动模式）...")
        
        # 先检查数据总量
        try:
            print("  检查Neo4j中的数据量...")
            count_result = self.graph.run("MATCH (qa:QA) RETURN count(qa) as count").data()
            self.total_qa_count = count_result[0]['count'] if count_result else 0
            
            if self.total_qa_count == 0:
                print("警告: Neo4j中没有找到问答数据")
                self.loading_complete = True
                return
            
            print(f"  数据库中共有 {self.total_qa_count} 个问答对")
            
            # 如果数据量小于初始加载量，直接全部加载
            if self.total_qa_count <= max_initial_load:
                print("  数据量较小，直接加载全部数据...")
                query = "MATCH (qa:QA) RETURN qa.id as id, qa.question as question, qa.answer as answer, qa.source as source"
                load_all = True
            else:
                print(f"  初始加载前 {max_initial_load} 条，剩余数据将在后台继续加载...")
                query = f"MATCH (qa:QA) RETURN qa.id as id, qa.question as question, qa.answer as answer, qa.source as source ORDER BY qa.id LIMIT {max_initial_load}"
                load_all = False
            
            print("  从Neo4j读取初始数据...")
            result = self.graph.run(query).data()
            
            if not result:
                print("警告: 未读取到问答数据")
                self.loading_complete = True
                return
            
            # 存储问答对（包含source信息）
            print(f"  处理 {len(result)} 条记录...")
            with self._qa_pairs_lock:
                self.qa_pairs = [
                    (item['question'], item['answer'], item.get('source', 'unknown'), item['id'])
                    for item in result
                    if item.get('question') and item.get('answer')
                ]
            
            print(f"✓ 初始加载完成: {len(self.qa_pairs)} 个问答对")
            
            if load_all:
                self.loading_complete = True
                print("  所有数据已加载完成")
            else:
                print(f"  剩余 {self.total_qa_count - len(self.qa_pairs)} 条数据将在后台继续加载...")
            
            # 如果数据量较大，跳过BM25索引构建（使用实时计算）
            if len(self.qa_pairs) > 10000:
                print("  数据量较大，BM25索引将在首次使用时构建（避免启动时间过长）")
                self.bm25_model = None  # 延迟构建
            else:
                # 构建BM25索引（数据量小时快速构建）
                if TEXT_SIMILARITY_AVAILABLE:
                    print("  正在构建BM25索引...")
                    self._build_bm25_index()
            
            # BERT已禁用，使用text_similarity方法
            print("  提示: 已禁用BERT，使用text_similarity方法（BM25+Jaccard+编辑距离）")
            
        except Exception as e:
            print(f"加载数据时出错: {e}")
            import traceback
            traceback.print_exc()
            self.loading_complete = True
    
    def _start_background_loading(self):
        """启动后台加载线程"""
        if self.loading_complete:
            return
        
        # 线程安全地检查
        with self._qa_pairs_lock:
            current_count = len(self.qa_pairs)
        
        if self.total_qa_count <= current_count:
            self.loading_complete = True
            return
        
        print("  启动后台数据加载线程...")
        self.loading_thread = threading.Thread(target=self._background_load_remaining_data, daemon=True)
        self.loading_thread.start()
        print("  ✓ 后台加载线程已启动（服务器可正常使用）")
    
    def _background_load_remaining_data(self):
        """后台加载剩余数据"""
        try:
            # 线程安全地获取当前数量
            with self._qa_pairs_lock:
                loaded_count = len(self.qa_pairs)
            remaining_count = self.total_qa_count - loaded_count
            
            if remaining_count <= 0:
                self.loading_complete = True
                return
            
            print(f"\n[后台加载] 开始加载剩余 {remaining_count} 条数据...")
            
            # 分批加载，避免一次性加载太多
            batch_size = 10000
            offset = loaded_count
            
            while offset < self.total_qa_count:
                try:
                    # 查询下一批数据
                    query = f"""
                    MATCH (qa:QA) 
                    RETURN qa.id as id, qa.question as question, qa.answer as answer, qa.source as source
                    ORDER BY qa.id 
                    SKIP {offset} LIMIT {batch_size}
                    """
                    
                    result = self.graph.run(query).data()
                    
                    if not result:
                        break
                    
                    # 处理并添加数据（包含source信息）
                    new_pairs = [
                        (item['question'], item['answer'], item.get('source', 'unknown'), item['id'])
                        for item in result
                        if item.get('question') and item.get('answer')
                    ]
                    
                    # 线程安全地添加数据
                    with self._qa_pairs_lock:
                        self.qa_pairs.extend(new_pairs)
                    
                    offset += len(result)
                    # 线程安全地获取当前数量
                    with self._qa_pairs_lock:
                        current_count = len(self.qa_pairs)
                    progress = 100 * current_count // self.total_qa_count
                    
                    print(f"[后台加载] 已加载: {current_count}/{self.total_qa_count} ({progress}%)")
                    
                    # 如果这批数据较少，说明已经加载完
                    if len(result) < batch_size:
                        break
                    
                    # 短暂休眠，避免占用过多资源
                    time.sleep(0.1)
                    
                except Exception as e:
                    print(f"[后台加载] 加载数据时出错: {e}")
                    break
            
            self.loading_complete = True
            # 线程安全地获取最终数量
            with self._qa_pairs_lock:
                final_count = len(self.qa_pairs)
            print(f"[后台加载] ✓ 所有数据加载完成！共 {final_count} 条")
            
            # 数据加载完成后，如果数据量合适，可以构建BM25索引
            if final_count <= 50000 and TEXT_SIMILARITY_AVAILABLE and self.bm25_model is None:
                print("[后台加载] 数据加载完成，开始构建BM25索引...")
                self._build_bm25_index()
            
        except Exception as e:
            print(f"[后台加载] 后台加载过程出错: {e}")
            import traceback
            traceback.print_exc()
            self.loading_complete = True
    
    def _build_bm25_index(self):
        """构建BM25索引"""
        try:
            # 对问题进行分词
            print(f"    对 {len(self.qa_pairs)} 个问题进行分词...")
            questions_segmented = []
            total = len(self.qa_pairs)
            for idx, (question, _, _, _) in enumerate(self.qa_pairs):
                words = self._segment(question)
                questions_segmented.append(words)
                # 每处理1000条显示一次进度
                if (idx + 1) % 1000 == 0 or (idx + 1) == total:
                    print(f"    已处理: {idx + 1}/{total} ({100*(idx+1)//total}%)")
            
            # 创建BM25模型
            print("    创建BM25模型...")
            self.bm25_model = BM25(questions_segmented)
            print(f"✓ BM25索引构建完成")
        except Exception as e:
            print(f"构建BM25索引时出错: {e}")
            self.bm25_model = None
    
    def _build_bert_index(self):
        """构建BERT向量索引"""
        try:
            # 线程安全地获取数据
            with self._qa_pairs_lock:
                current_pairs = self.qa_pairs.copy()
            
            questions = [qa[0] for qa in current_pairs]
            total = len(questions)
            
            # 批量编码（BERT可以批量处理）
            batch_size = 32
            vectors_list = []
            
            print(f"    正在计算 {total} 个问题的BERT向量...")
            for i in range(0, len(questions), batch_size):
                batch = questions[i:i+batch_size]
                # 去除空格（BERT处理）
                batch_cleaned = ["".join(q.split()) for q in batch]
                batch_vectors = self.bert_client.encode(batch_cleaned)
                vectors_list.append(batch_vectors)
                
                # 显示进度
                processed = min(i + batch_size, total)
                if processed % 320 == 0 or processed == total:
                    print(f"    已处理: {processed}/{total} ({100*processed//total}%)")
            
            # 合并所有向量
            print("    合并向量...")
            self.question_vectors = np.vstack(vectors_list)
            print(f"✓ BERT向量索引构建完成 (shape: {self.question_vectors.shape})")
        except Exception as e:
            print(f"构建BERT索引时出错: {e}")
            import traceback
            traceback.print_exc()
            self.question_vectors = None
            self.use_bert = False  # 禁用BERT，使用其他方法
    
    def _segment(self, text):
        """
        对文本进行分词
        :param text: 输入文本
        :return: 分词后的词列表
        """
        # 去除标点符号
        text = re.sub(r'[^\w\s]', '', text)
        # 分词
        words = list(jieba.cut(text))
        # 过滤停用词和单字符
        words = [w.strip() for w in words 
                if len(w.strip()) > 1 and w.strip() not in self.stop_words]
        return words
    
    def _ensure_bert_index(self):
        """确保BERT索引已构建（延迟加载）"""
        if not self.use_bert or self.bert_client is None:
            return False
        
        if self.question_vectors is None:
            print("首次使用BERT检索，正在构建向量索引（这可能需要一些时间）...")
            self._build_bert_index()
        
        return self.question_vectors is not None
    
    def _calculate_bert_similarity(self, query, top_k=10):
        """
        使用BERT计算语义相似度
        :param query: 查询文本
        :param top_k: 返回前k个结果
        :return: [(index, similarity_score), ...] 列表
        """
        # 延迟加载BERT索引
        if not self._ensure_bert_index():
            return []
        
        try:
            # 线程安全地获取当前数据量
            with self._qa_pairs_lock:
                current_count = len(self.qa_pairs)
            
            # 如果向量数量与当前数据量不匹配，需要重新构建
            if self.question_vectors is not None and self.question_vectors.shape[0] < current_count:
                # 数据已更新，需要重新构建向量
                print("  检测到新数据，重新构建BERT向量索引...")
                self._build_bert_index()
            
            # 将查询转换为向量
            query_cleaned = "".join(query.split())
            query_vec = self.bert_client.encode([query_cleaned])[0]
            
            # 计算余弦相似度
            # 归一化向量
            query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-8)
            vectors_norm = self.question_vectors / (np.linalg.norm(self.question_vectors, axis=1, keepdims=True) + 1e-8)
            
            # 计算点积（余弦相似度）
            similarities = np.dot(vectors_norm, query_norm)
            
            # 获取top_k
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            # 返回索引和相似度
            results = [(int(idx), float(similarities[idx])) for idx in top_indices]
            return results
            
        except Exception as e:
            print(f"BERT相似度计算错误: {e}")
            return []
    
    def _ensure_bm25_index(self):
        """确保BM25索引已构建（延迟加载）"""
        if self.bm25_model is not None:
            return True
        
        if not TEXT_SIMILARITY_AVAILABLE:
            return False
        
        # 线程安全地检查
        with self._qa_pairs_lock:
            current_count = len(self.qa_pairs)
        
        if current_count == 0:
            return False
        
        print("首次使用BM25检索，正在构建索引（这可能需要一些时间）...")
        self._build_bm25_index()
        return self.bm25_model is not None
    
    def _calculate_bm25_similarity(self, query, top_k=10):
        """
        使用BM25计算相似度
        :param query: 查询文本
        :param top_k: 返回前k个结果
        :return: [(index, similarity_score), ...] 列表
        """
        # 延迟构建BM25索引
        if not self._ensure_bm25_index():
            return []
        
        try:
            # 线程安全地获取当前数据量
            with self._qa_pairs_lock:
                current_count = len(self.qa_pairs)
            
            # 如果BM25模型的数据量与当前数据量不匹配，需要重新构建
            if self.bm25_model is not None:
                # 检查模型是否与当前数据匹配（简单检查：通过doc_num）
                if hasattr(self.bm25_model, 'doc_num') and self.bm25_model.doc_num < current_count:
                    print("  检测到新数据，重新构建BM25索引...")
                    self._build_bm25_index()
            
            # 分词
            query_words = self._segment(query)
            
            if not query_words:
                return []
            
            # 计算BM25分数
            scores = self.bm25_model.score_all(query_words)
            
            # 归一化到0-1范围（BM25分数可能为负）
            if len(scores) > 0:
                min_score = np.min(scores)
                max_score = np.max(scores)
                if max_score > min_score:
                    scores = (scores - min_score) / (max_score - min_score)
                else:
                    scores = np.ones_like(scores)
            
            # 获取top_k
            top_indices = np.argsort(scores)[::-1][:top_k]
            
            # 返回索引和相似度
            results = [(int(idx), float(scores[idx])) for idx in top_indices]
            return results
            
        except Exception as e:
            print(f"BM25相似度计算错误: {e}")
            return []
    
    def _calculate_jaccard_similarity(self, query, question):
        """
        计算Jaccard相似度
        :param query: 查询文本
        :param question: 问题文本
        :return: 相似度分数
        """
        if not TEXT_SIMILARITY_AVAILABLE:
            return 0.0
        
        try:
            similarity = jaccard_similarity_text(query, question, use_jieba=True)
            return similarity
        except Exception as e:
            return 0.0
    
    def _calculate_edit_distance_similarity(self, query, question):
        """
        计算编辑距离相似度
        :param query: 查询文本
        :param question: 问题文本
        :return: 相似度分数（0-1）
        """
        if not TEXT_SIMILARITY_AVAILABLE:
            return 0.0
        
        try:
            distance = edit_distance(query, question)
            max_len = max(len(query), len(question))
            similarity = 1 - (distance / max_len) if max_len > 0 else 0.0
            return similarity
        except Exception as e:
            return 0.0
    
    def _combine_scores(self, bert_results, bm25_results, query, questions, top_k=5):
        """
        综合多种方法的相似度分数
        :param bert_results: BERT结果 [(index, score), ...]
        :param bm25_results: BM25结果 [(index, score), ...]
        :param query: 查询文本
        :param questions: 问题列表
        :param top_k: 返回前k个结果
        :return: [(index, final_score, question, answer), ...] 列表
        """
        # 创建索引到分数的映射
        score_dict = {}
        
        # BERT分数（权重0.6）
        for idx, score in bert_results:
            if idx not in score_dict:
                score_dict[idx] = {'bert': 0.0, 'bm25': 0.0, 'jaccard': 0.0, 'edit': 0.0}
            score_dict[idx]['bert'] = score
        
        # BM25分数（权重0.2）
        for idx, score in bm25_results:
            if idx not in score_dict:
                score_dict[idx] = {'bert': 0.0, 'bm25': 0.0, 'jaccard': 0.0, 'edit': 0.0}
            score_dict[idx]['bm25'] = score
        
        # 对于top候选，计算额外的相似度
        top_candidates = set()
        for idx, _ in bert_results[:top_k*2]:
            top_candidates.add(idx)
        for idx, _ in bm25_results[:top_k*2]:
            top_candidates.add(idx)
        
        # 计算Jaccard和编辑距离（仅对top候选）
        for idx in top_candidates:
            if idx < len(questions):
                question = questions[idx]
                score_dict[idx]['jaccard'] = self._calculate_jaccard_similarity(query, question)
                score_dict[idx]['edit'] = self._calculate_edit_distance_similarity(query, question)
        
        # 线程安全地获取当前数据
        with self._qa_pairs_lock:
            current_pairs = self.qa_pairs.copy()
            current_count = len(current_pairs)
        
        # 综合评分
        final_results = []
        for idx, scores in score_dict.items():
            if idx >= current_count:
                continue
            
            # 加权综合（不使用BERT，仅使用text_similarity方法）
            final_score = (
                0.0 * scores['bert'] +      # BERT已禁用
                0.4 * scores['bm25'] +      # BM25关键词匹配（主要）
                0.3 * scores['jaccard'] +   # Jaccard集合相似度
                0.3 * scores['edit']        # 编辑距离相似度
            )
            
            question, answer, source, qa_id = current_pairs[idx]
            final_results.append((idx, final_score, question, answer, source))
        
        # 按分数排序
        final_results.sort(key=lambda x: x[1], reverse=True)
        
        return final_results[:top_k]
    
    def search(self, query, top_k=5, threshold=0.1):
        """
        检索最相关的问答对
        :param query: 用户查询
        :param top_k: 返回前k个结果
        :param threshold: 相似度阈值（默认0.1，较低以确保能返回结果）
        :return: [(question, answer, similarity_score), ...] 列表
        """
        # 线程安全地获取当前数据
        with self._qa_pairs_lock:
            current_pairs = self.qa_pairs.copy()
            current_count = len(current_pairs)
        
        if current_count == 0:
            return []
        
        # 如果数据量很大且索引未构建，使用优化的快速检索方法
        if current_count > 10000 and self.bm25_model is None:
            # 使用优化的快速检索（使用关键词快速筛选）
            results = self._fast_search(query, current_pairs, top_k=top_k, threshold=threshold)
            # 如果结果不够，降低阈值重试
            if len(results) < top_k:
                results = self._fast_search(query, current_pairs, top_k=top_k*2, threshold=0.0)
            return results[:top_k]
        
        # 使用BERT计算相似度（已禁用，强制使用text_similarity方法）
        bert_results = []  # 强制禁用BERT，使用text_similarity方法
        
        # 使用BM25计算相似度（会自动延迟构建索引）
        bm25_results = self._calculate_bm25_similarity(query, top_k=top_k*3) if TEXT_SIMILARITY_AVAILABLE else []
        
        # 如果都没有结果，使用优化的快速检索方法
        if not bert_results and not bm25_results:
            # 使用优化的快速检索（使用关键词快速筛选）
            results = self._fast_search(query, current_pairs, top_k=top_k, threshold=threshold)
            # 如果结果不够，降低阈值重试
            if len(results) < top_k:
                results = self._fast_search(query, current_pairs, top_k=top_k*2, threshold=0.0)
            return results[:top_k]
        
        # 综合多种方法
        questions = [qa[0] for qa in current_pairs]
        combined_results = self._combine_scores(bert_results, bm25_results, query, questions, top_k=top_k*2)
        
        # 过滤阈值，但如果结果为空，返回最相似的结果（即使低于阈值）
        filtered_results = [
            (q, a, s, src) for _, s, q, a, src in combined_results if s >= threshold
        ]
        
        # 如果过滤后没有结果，返回最相似的结果（即使低于阈值）
        if not filtered_results and combined_results:
            filtered_results = [
                (q, a, s, src) for _, s, q, a, src in combined_results[:top_k]
            ]
        
        return filtered_results[:top_k]
    
    def _fast_search(self, query, qa_pairs, top_k=5, threshold=0.0, max_check=3000):
        """
        快速检索方法（优化版：使用关键词快速筛选）
        :param query: 查询文本
        :param qa_pairs: 要搜索的问答对列表
        :param top_k: 返回前k个结果
        :param threshold: 相似度阈值（默认0.0，确保能返回结果）
        :param max_check: 最多检查的数据量（优化为3000以提高速度）
        :return: [(question, answer, similarity_score), ...] 列表
        """
        results = []
        
        # 对查询进行分词
        query_words = set(self._segment(query))
        query_lower = query.lower()
        
        # 如果数据量很大，先使用关键词快速筛选候选
        if len(qa_pairs) > max_check:
            # 第一步：快速筛选包含关键词的候选（只检查前max_check条）
            candidates = []
            check_pairs = qa_pairs[:max_check]
            
            for idx, (question, answer, source, _) in enumerate(check_pairs):
                question_lower = question.lower()
                question_words = set(self._segment(question))
                
                # 快速匹配：检查是否包含查询关键词
                match_score = 0
                if query_lower in question_lower:
                    match_score += 2.0  # 完全匹配
                else:
                    # 检查关键词重叠
                    common_words = query_words & question_words
                    if common_words:
                        match_score += len(common_words) * 0.5
                
                if match_score > 0:
                    candidates.append((idx, match_score, question, answer, source))
            
            # 按匹配分数排序，只对top候选计算详细相似度
            candidates.sort(key=lambda x: x[1], reverse=True)
            candidates = candidates[:min(200, len(candidates))]  # 只对前200个候选计算详细相似度
            
            # 对候选计算详细相似度
            for idx, match_score, question, answer, source in candidates:
                # 使用Jaccard相似度（快速）
                similarity = self._calculate_jaccard_similarity(query, question)
                
                # 如果查询很短，提升包含关键词的相似度
                if len(query) <= 10 and match_score > 0:
                    similarity = max(similarity, 0.3)
                
                # 如果相似度较高，再计算编辑距离
                if similarity >= threshold * 0.3 or threshold == 0.0:
                    edit_sim = self._calculate_edit_distance_similarity(query, question)
                    # 综合两种相似度
                    final_sim = 0.6 * similarity + 0.4 * edit_sim
                    
                    if final_sim >= threshold or threshold == 0.0:
                        results.append((question, answer, final_sim, source))
        else:
            # 数据量较小，直接计算
            for idx, (question, answer, source, _) in enumerate(qa_pairs):
                similarity = self._calculate_jaccard_similarity(query, question)
                
                if len(query) <= 10:
                    question_lower = question.lower()
                    if query_lower in question_lower or any(word in question_lower for word in query_words if len(word) > 1):
                        similarity = max(similarity, 0.3)
                
                if similarity >= threshold * 0.3 or threshold == 0.0:
                    edit_sim = self._calculate_edit_distance_similarity(query, question)
                    final_sim = 0.6 * similarity + 0.4 * edit_sim
                    
                    if final_sim >= threshold or threshold == 0.0:
                        results.append((question, answer, final_sim, source))
        
        # 按相似度排序
        results.sort(key=lambda x: x[2], reverse=True)
        return results[:top_k]
    
    def answer(self, query, top_k=3, threshold=0.1):
        """
        回答问题
        :param query: 用户查询
        :param top_k: 返回前k个结果
        :param threshold: 相似度阈值（默认0.1，较低以确保能返回结果）
        :return: 最佳答案，如果没有找到则返回None
        """
        # 先尝试使用默认阈值
        results = self.search(query, top_k=top_k, threshold=threshold)
        
        # 如果没找到结果，降低阈值重试
        if not results:
            results = self.search(query, top_k=top_k, threshold=0.0)
        
        if results:
            # 返回相似度最高的答案
            best_question, best_answer, best_score, best_source = results[0]
            
            # 如果相似度太低，添加提示
            if best_score < 0.3:
                best_answer = f"{best_answer}\n\n[提示: 相似度较低({best_score:.2f})，答案可能不完全匹配您的问题]"
            
            return {
                'answer': best_answer,
                'question': best_question,
                'similarity': best_score,
                'source': best_source,
                'alternatives': [(q, a, s, src) for q, a, s, src in results[1:]]
            }
        else:
            return None


def main():
    """测试函数"""
    print("初始化检索引擎...")
    
    # 尝试使用BERT
    try:
        engine = RetrievalEngine(use_bert=True)
    except Exception as e:
        print(f"使用BERT初始化失败: {e}")
        print("尝试不使用BERT...")
        engine = RetrievalEngine(use_bert=False)
    
    print("\n检索式问答机器人已就绪！")
    print("输入 'quit' 或 'exit' 退出\n")
    
    while True:
        query = input("您的问题: ").strip()
        
        if not query:
            continue
        
        if query.lower() in ['quit', 'exit', '退出']:
            print("再见！")
            break
        
        result = engine.answer(query)
        
        if result:
            print(f"\n最佳答案 (相似度: {result['similarity']:.3f}):")
            print(f"问题: {result['question']}")
            print(f"答案: {result['answer']}")
            
            if result['alternatives']:
                print(f"\n其他候选答案:")
                for i, (q, a, s) in enumerate(result['alternatives'][:2], 1):
                    print(f"  {i}. [{s:.3f}] {a[:50]}...")
        else:
            print("\n抱歉，没有找到相关答案。")
        
        print()


if __name__ == '__main__':
    main()
