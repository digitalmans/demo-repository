#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
数据导入模块
将ask_answer_robot语料库中的问答对导入到Neo4j数据库
"""

import os
import csv
import pandas as pd
from py2neo import Graph
import sys


class DataImporter:
    """数据导入器"""
    
    def __init__(self, neo4j_uri="http://localhost:7474", 
                 neo4j_username="neo4j", 
                 neo4j_password="xh050316"):
        """
        初始化数据导入器
        :param neo4j_uri: Neo4j数据库URI
        :param neo4j_username: 用户名
        :param neo4j_password: 密码
        """
        self.neo4j_uri = neo4j_uri
        self.neo4j_username = neo4j_username
        self.neo4j_password = neo4j_password
        self.graph = None
        self.corpus_dir = os.path.join(os.path.dirname(__file__), "语料库")
    
    def connect_neo4j(self):
        """连接Neo4j数据库"""
        connection_methods = [
            ("使用Bolt协议连接", lambda: Graph("bolt://localhost:7687", auth=(self.neo4j_username, self.neo4j_password))),
            ("使用HTTP协议连接", lambda: Graph(self.neo4j_uri, auth=(self.neo4j_username, self.neo4j_password))),
        ]
        
        for method_name, method in connection_methods:
            try:
                print(f"尝试{method_name}...")
                graph = method()
                graph.run("RETURN 1")
                print(f"成功连接到Neo4j数据库")
                self.graph = graph
                return graph
            except Exception as e:
                error_msg = str(e)[:100]
                try:
                    print(f"  {method_name}失败: {error_msg}")
                except:
                    print(f"  {method_name}失败")
                continue
        
        print("\n所有连接方式都失败了！")
        print("请确保Neo4j服务已启动")
        print("默认连接信息:")
        print("  - Bolt: bolt://localhost:7687")
        print("  - HTTP: http://localhost:7474")
        print("  - 用户名: neo4j")
        print("  - 密码: xh050316")
        sys.exit(1)
    
    def clear_database(self):
        """清空数据库中的问答数据（可选）"""
        if not self.graph:
            self.connect_neo4j()
        
        print("正在清空问答数据...")
        try:
            # 先统计要删除的数据量
            count_result = self.graph.run("MATCH (q:QA) RETURN count(q) as count").data()
            count = count_result[0]['count'] if count_result else 0
            
            if count == 0:
                print("数据库中没有QA数据，无需清空")
                return
            
            print(f"找到 {count} 个QA节点，开始删除...")
            
            # 只删除QA节点和关系，保留其他数据
            self.graph.run("MATCH (q:QA) DETACH DELETE q")
            
            # 验证删除结果
            verify_result = self.graph.run("MATCH (q:QA) RETURN count(q) as count").data()
            remaining = verify_result[0]['count'] if verify_result else 0
            
            if remaining == 0:
                print(f"✓ 成功清空 {count} 个QA节点")
            else:
                print(f"警告: 仍有 {remaining} 个QA节点未删除")
        except Exception as e:
            print(f"清空数据库时出错: {e}")
            import traceback
            traceback.print_exc()
    
    def read_csv_file(self, file_path):
        """
        读取CSV文件，返回问答对列表
        :param file_path: CSV文件路径
        :return: [(question, answer), ...] 列表
        """
        qa_pairs = []
        
        try:
            # 尝试使用pandas读取（更快，但可能遇到编码问题）
            try:
                df = pd.read_csv(
                    file_path,
                    sep='\t',
                    encoding='utf-8',
                    header=None,
                    names=['question', 'answer'],
                    quoting=csv.QUOTE_MINIMAL,
                    on_bad_lines='skip',
                    engine='python'
                )
                
                for _, row in df.iterrows():
                    question = str(row['question']).strip() if pd.notna(row['question']) else ''
                    answer = str(row['answer']).strip() if pd.notna(row['answer']) else ''
                    
                    if question and answer and len(question) > 0 and len(answer) > 0:
                        qa_pairs.append((question, answer))
            
            except Exception as e:
                print(f"  使用pandas读取失败，改用csv模块: {e}")
                # 如果pandas失败，使用csv模块
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    reader = csv.reader(f, delimiter='\t')
                    for row in reader:
                        if len(row) >= 2:
                            question = row[0].strip()
                            answer = row[1].strip()
                            if question and answer:
                                qa_pairs.append((question, answer))
        
        except Exception as e:
            print(f"  读取文件 {file_path} 时出错: {e}")
        
        return qa_pairs
    
    def import_qa_pairs(self, qa_pairs, source_file):
        """
        将问答对导入Neo4j
        :param qa_pairs: 问答对列表 [(question, answer), ...]
        :param source_file: 来源文件名
        :return: 成功导入的数量
        """
        if not self.graph:
            self.connect_neo4j()
        
        count = 0
        batch_size = 100  # 批量处理
        
        for i in range(0, len(qa_pairs), batch_size):
            batch = qa_pairs[i:i+batch_size]
            
            for question, answer in batch:
                try:
                    # 创建QA节点，使用MERGE避免重复
                    # 使用问题的hash作为唯一标识
                    import hashlib
                    qa_id = hashlib.md5(f"{question}{answer}".encode('utf-8')).hexdigest()
                    
                    # 创建或更新QA节点
                    self.graph.run(
                        """
                        MERGE (qa:QA {id: $qa_id})
                        SET qa.question = $question,
                            qa.answer = $answer,
                            qa.source = $source
                        """,
                        qa_id=qa_id,
                        question=question,
                        answer=answer,
                        source=source_file
                    )
                    count += 1
                    
                except Exception as e:
                    print(f"  导入问答对时出错: {e}")
                    continue
        
        return count
    
    def import_all_corpus(self, clear_existing=False):
        """
        导入所有语料库文件
        :param clear_existing: 是否清空现有数据
        """
        if not self.graph:
            self.connect_neo4j()
        
        if clear_existing:
            self.clear_database()
        
        if not os.path.exists(self.corpus_dir):
            print(f"错误: 语料库目录不存在: {self.corpus_dir}")
            return
        
        # 获取所有CSV文件
        csv_files = [f for f in os.listdir(self.corpus_dir) if f.endswith('.csv')]
        
        if not csv_files:
            print(f"错误: 在 {self.corpus_dir} 中未找到CSV文件")
            return
        
        print(f"\n找到 {len(csv_files)} 个语料库文件")
        print("=" * 60)
        
        total_imported = 0
        
        for csv_file in csv_files:
            file_path = os.path.join(self.corpus_dir, csv_file)
            print(f"\n正在处理: {csv_file}")
            
            # 读取问答对
            qa_pairs = self.read_csv_file(file_path)
            print(f"  读取到 {len(qa_pairs)} 个问答对")
            
            if qa_pairs:
                # 导入到Neo4j
                imported_count = self.import_qa_pairs(qa_pairs, csv_file)
                print(f"  成功导入 {imported_count} 个问答对")
                total_imported += imported_count
            else:
                print(f"  未读取到有效问答对")
        
        print("\n" + "=" * 60)
        print(f"导入完成！共导入 {total_imported} 个问答对")
        print("=" * 60)
        
        # 统计信息
        try:
            qa_count = self.graph.run("MATCH (q:QA) RETURN count(q) as count").data()[0]['count']
            print(f"\n数据库中现有问答对总数: {qa_count}")
        except Exception as e:
            print(f"获取统计信息时出错: {e}")


def main():
    """主函数"""
    print("=" * 60)
    print("问答机器人语料库导入工具")
    print("=" * 60)
    
    importer = DataImporter()
    
    # 询问是否清空现有数据
    clear_choice = input("\n是否清空现有问答数据？(y/n，默认n): ").strip().lower()
    clear_existing = (clear_choice == 'y' or clear_choice == 'yes')
    
    # 导入所有语料库
    importer.import_all_corpus(clear_existing=clear_existing)
    
    print("\n导入完成！")


if __name__ == '__main__':
    main()
