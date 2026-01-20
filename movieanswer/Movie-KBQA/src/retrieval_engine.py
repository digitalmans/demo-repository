#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
检索式问答引擎
使用文本相似度算法匹配问题，返回最相关的答案
改进版：使用text_similarity模块，支持动态答案生成
"""

import os
import sys
import jieba
import re
from collections import Counter

# 导入text_similarity模块
text_similarity_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'text_similarity')
if text_similarity_path not in sys.path:
    sys.path.insert(0, text_similarity_path)

try:
    from jaccard import jaccard_similarity_text
    from edit_distance import edit_distance
    from tfidf import TFIDF
    USE_TEXT_SIMILARITY = True
except ImportError as e:
    USE_TEXT_SIMILARITY = False
    print(f"警告: 无法导入text_similarity模块: {e}，将使用内置相似度算法")


class RetrievalEngine:
    """检索式问答引擎"""
    
    def __init__(self, knowledge_base):
        """
        初始化检索引擎
        :param knowledge_base: KnowledgeBase实例
        """
        self.kb = knowledge_base
        self.qa_pairs = knowledge_base.get_all_qa_pairs()
        self.data_loader = knowledge_base.data_loader
        
        # 初始化jieba
        jieba.initialize()
        
        # 构建问题索引（分词后的关键词）
        self.question_index = {}
        self._build_index()
        
        # TF-IDF模型暂不使用（需要更复杂的实现）
        
        print(f"检索引擎初始化完成，索引了 {len(self.qa_pairs)} 个问答对")
    
    def _build_index(self):
        """构建问题索引"""
        for idx, (question, answer, category) in enumerate(self.qa_pairs):
            # 对问题进行分词
            words = list(jieba.cut(question))
            # 去除停用词和标点
            words = [w.strip() for w in words if len(w.strip()) > 1 and w.strip() not in '，。！？、；：']
            # 建立倒排索引
            for word in words:
                if word not in self.question_index:
                    self.question_index[word] = []
                self.question_index[word].append(idx)
    
    def _extract_entities(self, query):
        """从查询中提取实体（电影名、演员名等）"""
        entities = {
            'movies': [],
            'actors': []
        }
        
        # 提取电影名（按长度排序，优先匹配长名称）
        movie_matches = []
        for mid, movie in self.data_loader.movies.items():
            title = movie.get('title', '')
            if title:
                # 检查是否包含电影名
                if title in query:
                    movie_matches.append((len(title), mid, title))
                # 也检查是否包含部分匹配（至少3个字符）
                elif len(title) >= 3 and any(title[i:i+3] in query for i in range(len(title)-2)):
                    movie_matches.append((len(title), mid, title))
        
        # 按长度降序排序，优先匹配完整名称
        movie_matches.sort(reverse=True)
        entities['movies'] = [(mid, title) for _, mid, title in movie_matches[:5]]  # 最多5个
        
        # 提取演员名（按长度排序，优先匹配长名称）
        actor_matches = []
        for pid, person in self.data_loader.persons.items():
            name = person.get('name', '')
            if name:
                # 检查是否包含演员名
                if name in query:
                    actor_matches.append((len(name), pid, name))
                # 也检查是否包含部分匹配（至少2个字符）
                elif len(name) >= 2 and any(name[i:i+2] in query for i in range(len(name)-1)):
                    actor_matches.append((len(name), pid, name))
        
        # 按长度降序排序
        actor_matches.sort(reverse=True)
        entities['actors'] = [(pid, name) for _, pid, name in actor_matches[:5]]  # 最多5个
        
        return entities
    
    def _calculate_similarity(self, query, question):
        """
        计算查询和问题的相似度（使用多种算法）
        :param query: 用户查询
        :param question: 知识库中的问题
        :return: 相似度分数 (0-1)
        """
        scores = []
        
        # 方法1: Jaccard相似度
        if USE_TEXT_SIMILARITY:
            try:
                jaccard_score = jaccard_similarity_text(query, question, use_jieba=True)
                scores.append(('jaccard', jaccard_score))
            except:
                pass
        
        # 方法2: 编辑距离相似度
        if USE_TEXT_SIMILARITY:
            try:
                max_len = max(len(query), len(question))
                if max_len > 0:
                    ed = edit_distance(query, question)
                    edit_score = 1.0 - (ed / max_len)
                    scores.append(('edit', edit_score))
            except:
                pass
        
        # 方法3: 词频相似度（简化版TF-IDF）
        query_words = list(jieba.cut(query))
        question_words = list(jieba.cut(question))
        query_tf = Counter(query_words)
        question_tf = Counter(question_words)
        common_words = set(query_words) & set(question_words)
        if common_words:
            score = 0.0
            for word in common_words:
                score += query_tf[word] * question_tf[word]
            max_score = max(len(query_words), len(question_words))
            if max_score > 0:
                tf_score = score / max_score
                scores.append(('tfidf', tf_score))
        
        # 方法4: 简单的词重叠度
        query_words = set(jieba.cut(query))
        question_words = set(jieba.cut(question))
        query_words = {w for w in query_words if len(w.strip()) > 1}
        question_words = {w for w in question_words if len(w.strip()) > 1}
        
        if query_words and question_words:
            intersection = query_words & question_words
            union = query_words | question_words
            if union:
                word_overlap = len(intersection) / len(union)
                scores.append(('word_overlap', word_overlap))
        
        # 方法5: 完全匹配奖励
        if query in question or question in query:
            scores.append(('exact_match', 1.0))
        elif query.replace(' ', '') in question.replace(' ', '') or question.replace(' ', '') in query.replace(' ', ''):
            scores.append(('exact_match', 0.8))
        
        # 综合所有相似度分数（加权平均）
        if not scores:
            return 0.0
        
        # 权重配置
        weights = {
            'jaccard': 0.3,
            'edit': 0.2,
            'tfidf': 0.3,
            'word_overlap': 0.15,
            'exact_match': 0.05
        }
        
        total_score = 0.0
        total_weight = 0.0
        for method, score in scores:
            weight = weights.get(method, 0.1)
            total_score += score * weight
            total_weight += weight
        
        final_score = total_score / total_weight if total_weight > 0 else 0.0
        return min(1.0, final_score)
    
    def _generate_dynamic_answer(self, query):
        """动态生成答案（直接从数据中提取）"""
        entities = self._extract_entities(query)
        
        # 提取关键词
        query_words = list(jieba.cut(query))
        query_text = ''.join(query_words)
        
        # 1. 电影评分查询
        if any(word in query for word in ['评分', '分数', '得分', '多少分', '分']):
            for mid, title in entities['movies']:
                movie = self.data_loader.movies.get(mid)
                if movie and movie.get('rating'):
                    rating = movie['rating']
                    if rating and rating != '\\N':
                        return f"{title}的评分是{rating}分"
        
        # 2. 电影上映时间查询
        if any(word in query for word in ['上映', '什么时候', '日期', '时间', '上映时间']):
            for mid, title in entities['movies']:
                movie = self.data_loader.movies.get(mid)
                if movie and movie.get('releasedate'):
                    release_date = movie['releasedate']
                    if release_date and release_date != '\\N':
                        return f"{title}的上映时间是{release_date}"
        
        # 3. 电影类型查询
        if any(word in query for word in ['类型', '风格', '什么类型', '属于', '类型是']):
            for mid, title in entities['movies']:
                genres = self.data_loader.get_movie_genres(mid)
                if genres:
                    genre_str = '、'.join(genres)
                    return f"{title}的类型是{genre_str}"
        
        # 4. 电影简介查询
        if any(word in query for word in ['简介', '介绍', '剧情', '内容', '讲什么', '是什么']):
            for mid, title in entities['movies']:
                movie = self.data_loader.movies.get(mid)
                if movie and movie.get('introduction'):
                    intro = movie['introduction']
                    if intro and len(intro) > 10:
                        # 限制简介长度，最多2000字
                        MAX_INTRO_LENGTH = 2000
                        if len(intro) > MAX_INTRO_LENGTH:
                            intro = intro[:MAX_INTRO_LENGTH] + "\n\n(单次回答最多生成2000字)"
                        return f"{title}的简介：{intro}"
        
        # 5. 电影演员查询
        if any(word in query for word in ['演员', '主演', '出演', '谁演', '有哪些演员']):
            for mid, title in entities['movies']:
                actors = self.data_loader.get_movie_actors(mid)
                if actors:
                    actor_str = '、'.join(actors[:10])
                    if len(actors) > 10:
                        actor_str += f"等{len(actors)}位演员"
                    return f"{title}的演员有：{actor_str}"
        
        # 6. 演员简介查询（需要区分是电影简介还是演员简介）
        if any(word in query for word in ['简介', '介绍', '是谁', '资料']) and entities['actors']:
            for pid, name in entities['actors']:
                person = self.data_loader.persons.get(pid)
                if person and person.get('biography'):
                    bio = person['biography']
                    if bio and len(bio) > 10:
                        # 限制简介长度，最多2000字
                        MAX_BIO_LENGTH = 2000
                        if len(bio) > MAX_BIO_LENGTH:
                            bio = bio[:MAX_BIO_LENGTH] + "\n\n(单次回答最多生成2000字)"
                        return f"{name}的简介：{bio}"
        
        # 7. 演员电影作品查询
        if any(word in query for word in ['演过', '演了', '出演', '作品', '电影', '演什么']):
            for pid, name in entities['actors']:
                movies = self.data_loader.get_actor_movies(pid)
                if movies:
                    movie_titles = [m[1] for m in movies[:10] if m[1]]
                    if movie_titles:
                        movie_str = '、'.join(movie_titles)
                        if len(movies) > 10:
                            movie_str += f"等{len(movies)}部电影"
                        return f"{name}演过的电影有：{movie_str}"
        
        # 8. 演员出生日期查询
        if any(word in query for word in ['出生', '生日', '什么时候出生', '出生日期']):
            for pid, name in entities['actors']:
                person = self.data_loader.persons.get(pid)
                if person and person.get('birth'):
                    birth = person['birth']
                    if birth and birth != '\\N':
                        return f"{name}的出生日期是{birth}"
        
        # 9. 演员电影数量查询
        if any(word in query for word in ['多少', '几部', '数量', '一共']):
            for pid, name in entities['actors']:
                movies = self.data_loader.get_actor_movies(pid)
                if movies:
                    return f"{name}一共演过{len(movies)}部电影"
        
        return None
    
    def search(self, query, top_k=3, threshold=0.05):
        """
        检索最相关的答案（优化版：使用倒排索引快速筛选）
        :param query: 用户查询
        :param top_k: 返回前k个最相关的答案
        :param threshold: 相似度阈值，低于此值的结果将被过滤（降低到0.05）
        :return: [(question, answer, score, category), ...]
        """
        if not query or not query.strip():
            return []
        
        query = query.strip()
        
        # 首先尝试动态生成答案
        dynamic_answer = self._generate_dynamic_answer(query)
        if dynamic_answer:
            return [('动态生成', dynamic_answer, 0.95, 'dynamic')]
        
        # 使用倒排索引快速筛选候选（优化性能）
        candidate_indices = self._get_candidates_from_index(query)
        
        # 如果候选集太大，限制数量以提高速度
        max_candidates = 1000
        if len(candidate_indices) > max_candidates:
            # 只取前max_candidates个候选
            candidate_indices = candidate_indices[:max_candidates]
        
        # 只对候选集计算相似度（大幅提升速度）
        scores = []
        for idx in candidate_indices:
            if idx < len(self.qa_pairs):
                question, answer, category = self.qa_pairs[idx]
                # 使用改进的相似度计算方法
                final_score = self._calculate_similarity(query, question)
                
                if final_score >= threshold:
                    scores.append((question, answer, final_score, category))
        
        # 如果候选集结果太少，补充一些结果（使用快速方法）
        if len(scores) < top_k and len(candidate_indices) < len(self.qa_pairs):
            # 对前5000条进行快速检索
            quick_scores = []
            quick_check = min(5000, len(self.qa_pairs))
            for idx in range(quick_check):
                if idx in candidate_indices:
                    continue  # 已经计算过了
                question, answer, category = self.qa_pairs[idx]
                # 快速相似度计算（仅Jaccard）
                try:
                    if USE_TEXT_SIMILARITY:
                        score = jaccard_similarity_text(query, question, use_jieba=True)
                    else:
                        query_words = set(jieba.cut(query))
                        question_words = set(jieba.cut(question))
                        intersection = query_words & question_words
                        union = query_words | question_words
                        score = len(intersection) / len(union) if union else 0.0
                    
                    if score >= threshold * 0.7:  # 降低阈值以获取更多候选
                        quick_scores.append((question, answer, score, category))
                except:
                    pass
            
            # 合并结果
            scores.extend(quick_scores)
        
        # 按相似度排序
        scores.sort(key=lambda x: x[2], reverse=True)
        
        # 返回top_k个结果
        return scores[:top_k]
    
    def _get_candidates_from_index(self, query):
        """
        使用倒排索引快速获取候选问答对索引
        :param query: 用户查询
        :return: 候选索引列表
        """
        # 对查询进行分词
        query_words = list(jieba.cut(query))
        query_words = [w.strip() for w in query_words if len(w.strip()) > 1 and w.strip() not in '，。！？、；：']
        
        if not query_words:
            # 如果没有关键词，返回前1000个索引
            return list(range(min(1000, len(self.qa_pairs))))
        
        # 使用倒排索引查找包含这些关键词的问答对
        candidate_indices = set()
        
        # 找到包含至少一个关键词的问答对
        for word in query_words:
            if word in self.question_index:
                candidate_indices.update(self.question_index[word])
        
        # 如果找到的候选太少，扩大搜索范围
        if len(candidate_indices) < 50:
            # 对每个关键词，添加更多相关索引
            for word in query_words:
                if word in self.question_index:
                    indices = self.question_index[word]
                    # 添加前100个
                    candidate_indices.update(indices[:100])
        
        # 如果还是没有足够的候选，返回前1000个
        if len(candidate_indices) < 10:
            return list(range(min(1000, len(self.qa_pairs))))
        
        # 按出现频率排序（包含更多关键词的优先）
        candidate_scores = {}
        for idx in candidate_indices:
            score = 0
            question, _, _ = self.qa_pairs[idx]
            question_words = set(jieba.cut(question))
            for word in query_words:
                if word in question_words:
                    score += 1
            candidate_scores[idx] = score
        
        # 按分数排序，返回索引列表
        sorted_candidates = sorted(candidate_scores.items(), key=lambda x: x[1], reverse=True)
        return [idx for idx, _ in sorted_candidates]
    
    def answer(self, query, top_k=1, threshold=0.05):
        """
        回答问题
        :param query: 用户查询
        :param top_k: 返回前k个答案
        :param threshold: 相似度阈值（降低到0.05）
        :return: 答案字符串，如果没有找到则返回None
        """
        results = self.search(query, top_k=top_k, threshold=threshold)
        
        if not results:
            return None
        
        # 限制答案长度的函数
        MAX_LENGTH = 2000
        def limit_length(text):
            if len(text) > MAX_LENGTH:
                return text[:MAX_LENGTH] + "\n\n(单次回答最多生成2000字)"
            return text
        
        # 返回最相关的答案
        if top_k == 1:
            answer = results[0][1]  # 返回答案
            return limit_length(answer)
        else:
            # 返回多个答案
            answers = []
            for question, answer, score, category in results:
                answers.append(f"[相似度: {score:.2f}] {limit_length(answer)}")
            combined_answer = '\n'.join(answers)
            return limit_length(combined_answer)
    
    def update_knowledge_base(self):
        """更新知识库后重新构建索引"""
        self.qa_pairs = self.kb.get_all_qa_pairs()
        self.question_index = {}
        self._build_index()
        
        # TF-IDF模型暂不使用
        
        print(f"索引已更新，当前有 {len(self.qa_pairs)} 个问答对")


if __name__ == '__main__':
    # 测试检索引擎
    from knowledge_base import KnowledgeBase
    
    print("正在初始化知识库...")
    kb = KnowledgeBase()
    
    print("\n正在初始化检索引擎...")
    engine = RetrievalEngine(kb)
    
    # 测试查询
    test_queries = [
        "李连杰演过什么电影",
        "英雄的评分是多少",
        "巩俐的简介",
        "梁朝伟的出生日期"
    ]
    
    print("\n开始测试检索...")
    for query in test_queries:
        print(f"\n查询: {query}")
        results = engine.search(query, top_k=3, threshold=0.05)
        if results:
            for i, (q, a, score, cat) in enumerate(results, 1):
                print(f"  [{i}] [{cat}] 相似度: {score:.3f}")
                print(f"      问题: {q}")
                print(f"      答案: {a[:100]}...")
        else:
            print("  未找到相关答案")
