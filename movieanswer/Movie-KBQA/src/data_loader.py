#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
数据加载模块
从CSV文件中加载电影、演员、类型等数据，构建知识库
"""

import os
import csv
import json
from collections import defaultdict


class DataLoader:
    """数据加载器"""
    
    def __init__(self, data_dir=None):
        """
        初始化数据加载器
        :param data_dir: 数据目录路径，默认为当前目录的data/import
        """
        if data_dir is None:
            # 获取当前文件所在目录的父目录，然后找到data/import
            current_dir = os.path.dirname(os.path.abspath(__file__))
            data_dir = os.path.join(os.path.dirname(current_dir), 'data', 'import')
        
        self.data_dir = data_dir
        self.movies = {}  # {mid: {title, introduction, rating, releasedate}}
        self.persons = {}  # {pid: {name, birth, death, biography, birthplace}}
        self.genres = {}  # {gid: gname}
        self.movie_to_genres = defaultdict(list)  # {mid: [gid1, gid2, ...]}
        self.person_to_movies = defaultdict(list)  # {pid: [mid1, mid2, ...]}
        self.movie_to_persons = defaultdict(list)  # {mid: [pid1, pid2, ...]}
        
        # 加载所有数据
        self.load_all_data()
    
    def _safe_get(self, row, key, default=''):
        """
        安全地获取CSV行中的值，处理None情况
        :param row: CSV行字典
        :param key: 键名
        :param default: 默认值
        :return: 处理后的字符串值
        """
        # 尝试多种可能的键名（处理BOM和引号问题）
        possible_keys = [key, f'"{key}"', f'\ufeff"{key}"', f'\ufeff{key}']
        value = None
        for k in possible_keys:
            if k in row:
                value = row[k]
                break
        
        if value is None:
            return default
        if isinstance(value, str):
            # 去除引号和BOM
            value = value.strip('"').strip('\ufeff').strip()
            if value == '\\N' or value == '':
                return default
            return value
        return str(value).strip('"').strip('\ufeff').strip()
    
    def load_all_data(self):
        """加载所有CSV数据"""
        print("正在加载数据...")
        self.load_movies()
        self.load_persons()
        self.load_genres()
        self.load_movie_to_genres()
        self.load_person_to_movies()
        print(f"数据加载完成: {len(self.movies)} 部电影, {len(self.persons)} 位演员, {len(self.genres)} 种类型")
    
    def load_movies(self):
        """加载电影数据"""
        movie_file = os.path.join(self.data_dir, 'movie.csv')
        if not os.path.exists(movie_file):
            print(f"警告: 找不到文件 {movie_file}")
            return
        
        try:
            # 使用utf-8-sig编码自动处理BOM
            with open(movie_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    # 清理键名（去除引号和BOM）
                    cleaned_row = {}
                    for k, v in row.items():
                        if k is not None:
                            clean_key = k.strip('"').strip('\ufeff').strip()
                            cleaned_row[clean_key] = v
                    
                    mid = self._safe_get(cleaned_row, 'mid')
                    if not mid:  # 跳过mid为空的行
                        continue
                    self.movies[mid] = {
                        'title': self._safe_get(cleaned_row, 'title'),
                        'introduction': self._safe_get(cleaned_row, 'introduction'),
                        'rating': self._safe_get(cleaned_row, 'rating'),
                        'releasedate': self._safe_get(cleaned_row, 'releasedate')
                    }
                    count += 1
                print(f"成功加载 {count} 部电影")
        except Exception as e:
            print(f"加载电影数据时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def load_persons(self):
        """加载演员数据"""
        person_file = os.path.join(self.data_dir, 'person.csv')
        if not os.path.exists(person_file):
            print(f"警告: 找不到文件 {person_file}")
            return
        
        try:
            # 使用utf-8-sig编码自动处理BOM
            with open(person_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                count = 0
                for row in reader:
                    # 清理键名（去除引号和BOM）
                    cleaned_row = {}
                    for k, v in row.items():
                        if k is not None:
                            clean_key = k.strip('"').strip('\ufeff').strip()
                            cleaned_row[clean_key] = v
                    
                    pid = self._safe_get(cleaned_row, 'pid')
                    if not pid:  # 跳过pid为空的行
                        continue
                    
                    birth = self._safe_get(cleaned_row, 'birth')
                    death = self._safe_get(cleaned_row, 'death')
                    
                    self.persons[pid] = {
                        'name': self._safe_get(cleaned_row, 'name'),
                        'birth': None if birth == '\\N' or not birth else birth,
                        'death': None if death == '\\N' or not death else death,
                        'biography': self._safe_get(cleaned_row, 'biography'),
                        'birthplace': self._safe_get(cleaned_row, 'birthplace')
                    }
                    count += 1
                print(f"成功加载 {count} 位演员")
        except Exception as e:
            print(f"加载演员数据时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def load_genres(self):
        """加载类型数据"""
        genre_file = os.path.join(self.data_dir, 'genre.csv')
        if not os.path.exists(genre_file):
            print(f"警告: 找不到文件 {genre_file}")
            return
        
        try:
            with open(genre_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 清理键名
                    cleaned_row = {}
                    for k, v in row.items():
                        if k is not None:
                            clean_key = k.strip('"').strip('\ufeff').strip()
                            cleaned_row[clean_key] = v
                    
                    gid = self._safe_get(cleaned_row, 'gid')
                    gname = self._safe_get(cleaned_row, 'gname')
                    if gid and gname:  # 只添加有效的类型
                        self.genres[gid] = gname
        except Exception as e:
            print(f"加载类型数据时出错: {e}")
    
    def load_movie_to_genres(self):
        """加载电影-类型关系"""
        mtg_file = os.path.join(self.data_dir, 'movie_to_genre.csv')
        if not os.path.exists(mtg_file):
            print(f"警告: 找不到文件 {mtg_file}")
            return
        
        try:
            with open(mtg_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 清理键名
                    cleaned_row = {}
                    for k, v in row.items():
                        if k is not None:
                            clean_key = k.strip('"').strip('\ufeff').strip()
                            cleaned_row[clean_key] = v
                    
                    mid = self._safe_get(cleaned_row, 'mid')
                    gid = self._safe_get(cleaned_row, 'gid')
                    if mid and gid:
                        self.movie_to_genres[mid].append(gid)
        except Exception as e:
            print(f"加载电影-类型关系时出错: {e}")
    
    def load_person_to_movies(self):
        """加载演员-电影关系，同时构建电影-演员关系"""
        ptm_file = os.path.join(self.data_dir, 'person_to_movie.csv')
        if not os.path.exists(ptm_file):
            print(f"警告: 找不到文件 {ptm_file}")
            return
        
        try:
            with open(ptm_file, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # 清理键名
                    cleaned_row = {}
                    for k, v in row.items():
                        if k is not None:
                            clean_key = k.strip('"').strip('\ufeff').strip()
                            cleaned_row[clean_key] = v
                    
                    pid = self._safe_get(cleaned_row, 'pid')
                    mid = self._safe_get(cleaned_row, 'mid')
                    if pid and mid:
                        self.person_to_movies[pid].append(mid)
                        self.movie_to_persons[mid].append(pid)
        except Exception as e:
            print(f"加载演员-电影关系时出错: {e}")
    
    def get_movie_by_title(self, title):
        """根据电影标题查找电影"""
        for mid, movie in self.movies.items():
            if title in movie['title'] or movie['title'] in title:
                return mid, movie
        return None, None
    
    def get_person_by_name(self, name):
        """根据演员姓名查找演员"""
        for pid, person in self.persons.items():
            if name in person['name'] or person['name'] in name:
                return pid, person
        return None, None
    
    def get_movie_genres(self, mid):
        """获取电影的类型"""
        genre_ids = self.movie_to_genres.get(mid, [])
        return [self.genres.get(gid, '') for gid in genre_ids if gid in self.genres]
    
    def get_movie_actors(self, mid):
        """获取电影的演员列表"""
        actor_ids = self.movie_to_persons.get(mid, [])
        return [self.persons.get(pid, {}).get('name', '') for pid in actor_ids if pid in self.persons]
    
    def get_actor_movies(self, pid):
        """获取演员演过的电影列表"""
        movie_ids = self.person_to_movies.get(pid, [])
        return [(mid, self.movies.get(mid, {}).get('title', '')) for mid in movie_ids if mid in self.movies]
    
    def save_knowledge_base(self, output_file):
        """将知识库保存为JSON文件"""
        knowledge_base = {
            'movies': self.movies,
            'persons': self.persons,
            'genres': self.genres,
            'movie_to_genres': dict(self.movie_to_genres),
            'person_to_movies': dict(self.person_to_movies),
            'movie_to_persons': dict(self.movie_to_persons)
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(knowledge_base, f, ensure_ascii=False, indent=2)
        
        print(f"知识库已保存到: {output_file}")
    
    def load_knowledge_base(self, input_file):
        """从JSON文件加载知识库"""
        with open(input_file, 'r', encoding='utf-8') as f:
            knowledge_base = json.load(f)
        
        self.movies = knowledge_base.get('movies', {})
        self.persons = knowledge_base.get('persons', {})
        self.genres = knowledge_base.get('genres', {})
        self.movie_to_genres = defaultdict(list, knowledge_base.get('movie_to_genres', {}))
        self.person_to_movies = defaultdict(list, knowledge_base.get('person_to_movies', {}))
        self.movie_to_persons = defaultdict(list, knowledge_base.get('movie_to_persons', {}))
        
        print(f"知识库已从 {input_file} 加载")


if __name__ == '__main__':
    # 测试数据加载
    loader = DataLoader()
    print(f"\n示例电影: {list(loader.movies.items())[0]}")
    print(f"\n示例演员: {list(loader.persons.items())[0]}")
