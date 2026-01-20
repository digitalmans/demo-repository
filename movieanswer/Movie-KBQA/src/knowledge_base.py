#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
知识库构建模块
从数据中生成问答对，构建检索式问答知识库
"""

import os
import sys
from data_loader import DataLoader


class KnowledgeBase:
    """问答知识库"""
    
    def __init__(self, data_loader=None):
        """
        初始化知识库
        :param data_loader: DataLoader实例，如果为None则自动创建
        """
        if data_loader is None:
            self.data_loader = DataLoader()
        else:
            self.data_loader = data_loader
        
        # 问答对列表: [(question, answer, category), ...]
        self.qa_pairs = []
        
        # 构建知识库
        self.build_knowledge_base()
    
    def build_knowledge_base(self):
        """构建问答知识库"""
        print("正在构建问答知识库...")
        
        # 1. 电影评分相关问答
        self._build_movie_rating_qa()
        
        # 2. 电影上映时间相关问答
        self._build_movie_release_qa()
        
        # 3. 电影类型相关问答
        self._build_movie_genre_qa()
        
        # 4. 电影简介相关问答
        self._build_movie_intro_qa()
        
        # 5. 电影演员相关问答
        self._build_movie_actors_qa()
        
        # 6. 演员简介相关问答
        self._build_actor_info_qa()
        
        # 7. 演员电影作品相关问答
        self._build_actor_movies_qa()
        
        # 8. 演员出生日期相关问答
        self._build_actor_birth_qa()
        
        # 9. 演员电影数量相关问答
        self._build_actor_movie_count_qa()
        
        # 10. 演员类型电影相关问答
        self._build_actor_genre_movies_qa()
        
        print(f"知识库构建完成，共生成 {len(self.qa_pairs)} 个问答对")
    
    def _build_movie_rating_qa(self):
        """构建电影评分问答对"""
        for mid, movie in self.data_loader.movies.items():
            title = movie['title']
            rating = movie['rating']
            if title and rating:
                questions = [
                    f"{title}的评分是多少",
                    f"{title}得了多少分",
                    f"{title}的评分有多少",
                    f"{title}的评分",
                    f"{title}的分数是多少",
                    f"{title}电影分数是多少",
                    f"{title}评分",
                    f"{title}这部电影的评分是多少"
                ]
                answer = f"{title}的评分是{rating}分"
                for q in questions:
                    self.qa_pairs.append((q, answer, 'movie_rating'))
    
    def _build_movie_release_qa(self):
        """构建电影上映时间问答对"""
        for mid, movie in self.data_loader.movies.items():
            title = movie['title']
            release_date = movie['releasedate']
            if title and release_date:
                questions = [
                    f"{title}什么时候上映的",
                    f"{title}的上映时间",
                    f"{title}上映日期",
                    f"{title}什么时候上映",
                    f"{title}的上映日期是什么时候"
                ]
                answer = f"{title}的上映时间是{release_date}"
                for q in questions:
                    self.qa_pairs.append((q, answer, 'movie_release'))
    
    def _build_movie_genre_qa(self):
        """构建电影类型问答对"""
        for mid, movie in self.data_loader.movies.items():
            title = movie['title']
            genres = self.data_loader.get_movie_genres(mid)
            if title and genres:
                genre_str = '、'.join(genres)
                questions = [
                    f"{title}是什么类型的电影",
                    f"{title}的类型",
                    f"{title}属于什么类型",
                    f"{title}的电影类型是什么"
                ]
                answer = f"{title}的类型是{genre_str}"
                for q in questions:
                    self.qa_pairs.append((q, answer, 'movie_genre'))
    
    def _build_movie_intro_qa(self):
        """构建电影简介问答对"""
        MAX_LENGTH = 2000
        for mid, movie in self.data_loader.movies.items():
            title = movie['title']
            intro = movie['introduction']
            if title and intro and len(intro) > 10:
                questions = [
                    f"{title}的简介",
                    f"{title}的剧情介绍",
                    f"{title}讲的是什么",
                    f"{title}的内容是什么",
                    f"{title}的剧情"
                ]
                # 截取前2000字作为答案，超过则添加备注
                if len(intro) > MAX_LENGTH:
                    answer = f"{title}的简介：{intro[:MAX_LENGTH]}\n\n(单次回答最多生成2000字)"
                else:
                    answer = f"{title}的简介：{intro}"
                for q in questions:
                    self.qa_pairs.append((q, answer, 'movie_intro'))
    
    def _build_movie_actors_qa(self):
        """构建电影演员问答对"""
        for mid, movie in self.data_loader.movies.items():
            title = movie['title']
            actors = self.data_loader.get_movie_actors(mid)
            if title and actors:
                actor_str = '、'.join(actors[:10])  # 最多显示10个演员
                if len(actors) > 10:
                    actor_str += f"等{len(actors)}位演员"
                questions = [
                    f"{title}有哪些演员出演",
                    f"{title}的演员",
                    f"{title}的主演是谁",
                    f"{title}有哪些演员",
                    f"{title}的演员有哪些"
                ]
                answer = f"{title}的演员有：{actor_str}"
                for q in questions:
                    self.qa_pairs.append((q, answer, 'movie_actors'))
    
    def _build_actor_info_qa(self):
        """构建演员简介问答对"""
        for pid, person in self.data_loader.persons.items():
            name = person['name']
            biography = person['biography']
            if name and biography and len(biography) > 10:
                questions = [
                    f"{name}的简介",
                    f"{name}的介绍",
                    f"{name}是谁",
                    f"{name}的个人资料"
                ]
                # 截取前2000字作为答案，超过则添加备注
                MAX_LENGTH = 2000
                if len(biography) > MAX_LENGTH:
                    answer = f"{name}的简介：{biography[:MAX_LENGTH]}\n\n(单次回答最多生成2000字)"
                else:
                    answer = f"{name}的简介：{biography}"
                for q in questions:
                    self.qa_pairs.append((q, answer, 'actor_info'))
    
    def _build_actor_movies_qa(self):
        """构建演员电影作品问答对"""
        for pid, person in self.data_loader.persons.items():
            name = person['name']
            movies = self.data_loader.get_actor_movies(pid)
            if name and movies:
                movie_titles = [m[1] for m in movies[:10]]  # 最多显示10部电影
                movie_str = '、'.join(movie_titles)
                if len(movies) > 10:
                    movie_str += f"等{len(movies)}部电影"
                questions = [
                    f"{name}演了什么电影",
                    f"{name}出演了什么电影",
                    f"{name}演过什么电影",
                    f"{name}演过哪些电影",
                    f"{name}演过的电影有什么",
                    f"{name}有哪些电影"
                ]
                answer = f"{name}演过的电影有：{movie_str}"
                for q in questions:
                    self.qa_pairs.append((q, answer, 'actor_movies'))
    
    def _build_actor_birth_qa(self):
        """构建演员出生日期问答对"""
        for pid, person in self.data_loader.persons.items():
            name = person['name']
            birth = person['birth']
            if name and birth:
                questions = [
                    f"{name}的出生日期",
                    f"{name}什么时候出生的",
                    f"{name}的生日",
                    f"{name}出生日期是什么时候"
                ]
                answer = f"{name}的出生日期是{birth}"
                for q in questions:
                    self.qa_pairs.append((q, answer, 'actor_birth'))
    
    def _build_actor_movie_count_qa(self):
        """构建演员电影数量问答对"""
        for pid, person in self.data_loader.persons.items():
            name = person['name']
            movies = self.data_loader.get_actor_movies(pid)
            if name and movies:
                count = len(movies)
                questions = [
                    f"{name}一共演过多少电影",
                    f"{name}演了多少部电影",
                    f"{name}的电影数量",
                    f"{name}演过几部电影"
                ]
                answer = f"{name}一共演过{count}部电影"
                for q in questions:
                    self.qa_pairs.append((q, answer, 'actor_movie_count'))
    
    def _build_actor_genre_movies_qa(self):
        """构建演员类型电影问答对"""
        for pid, person in self.data_loader.persons.items():
            name = person['name']
            movies = self.data_loader.get_actor_movies(pid)
            if name and movies:
                # 按类型分组
                genre_movies = {}
                for mid, movie_title in movies:
                    genres = self.data_loader.get_movie_genres(mid)
                    for genre in genres:
                        if genre not in genre_movies:
                            genre_movies[genre] = []
                        genre_movies[genre].append(movie_title)
                
                # 为每种类型生成问答对
                for genre, movie_list in genre_movies.items():
                    if movie_list:
                        movie_str = '、'.join(movie_list[:5])  # 最多显示5部
                        if len(movie_list) > 5:
                            movie_str += f"等{len(movie_list)}部"
                        questions = [
                            f"{name}出演过哪些{genre}电影",
                            f"{name}演过什么{genre}电影",
                            f"{name}的{genre}电影有哪些"
                        ]
                        answer = f"{name}出演过的{genre}电影有：{movie_str}"
                        for q in questions:
                            self.qa_pairs.append((q, answer, 'actor_genre_movies'))
    
    def add_qa_pair(self, question, answer, category='custom'):
        """添加自定义问答对"""
        self.qa_pairs.append((question, answer, category))
        print(f"已添加问答对: {question} -> {answer}")
    
    def remove_qa_pair(self, question=None, answer=None):
        """删除问答对"""
        removed = []
        if question:
            self.qa_pairs = [(q, a, c) for q, a, c in self.qa_pairs if q != question]
            removed.append(f"问题: {question}")
        elif answer:
            self.qa_pairs = [(q, a, c) for q, a, c in self.qa_pairs if a != answer]
            removed.append(f"答案: {answer}")
        
        if removed:
            print(f"已删除问答对: {', '.join(removed)}")
        return len(removed) > 0
    
    def get_all_qa_pairs(self):
        """获取所有问答对"""
        return self.qa_pairs
    
    def get_qa_by_category(self, category):
        """根据类别获取问答对"""
        return [(q, a, c) for q, a, c in self.qa_pairs if c == category]
    
    def save_to_file(self, filepath):
        """保存知识库到文件"""
        import json
        data = {
            'qa_pairs': self.qa_pairs,
            'total_count': len(self.qa_pairs)
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"知识库已保存到: {filepath}")
    
    def load_from_file(self, filepath):
        """从文件加载知识库"""
        import json
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.qa_pairs = data.get('qa_pairs', [])
        print(f"知识库已从 {filepath} 加载，共 {len(self.qa_pairs)} 个问答对")


if __name__ == '__main__':
    # 测试知识库构建
    kb = KnowledgeBase()
    print(f"\n总问答对数: {len(kb.qa_pairs)}")
    print(f"\n示例问答对:")
    for i, (q, a, c) in enumerate(kb.qa_pairs[:5]):
        print(f"{i+1}. [{c}] Q: {q}")
        print(f"   A: {a}")
