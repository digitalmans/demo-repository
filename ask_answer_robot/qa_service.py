#!/usr/bin/env python
# -*- coding:utf-8 -*-

"""
问答服务主模块
提供统一的问答接口
"""

from retrieval_engine import RetrievalEngine


class QAService:
    """问答服务"""
    
    def __init__(self, neo4j_uri="http://localhost:7474",
                 neo4j_username="neo4j",
                 neo4j_password="xh050316",
                 use_bert=False,
                 max_initial_load=20000):
        """
        初始化问答服务
        :param neo4j_uri: Neo4j数据库URI
        :param neo4j_username: 用户名
        :param neo4j_password: 密码
        :param use_bert: 是否使用BERT（默认False，避免启动时等待BERT服务）
        :param max_initial_load: 初始加载的最大数据量（默认20000，避免启动过慢）
        """
        self.engine = RetrievalEngine(neo4j_uri, neo4j_username, neo4j_password, 
                                      use_bert=use_bert, max_initial_load=max_initial_load)
    
    def ask(self, question, top_k=3, threshold=0.3):
        """
        回答问题
        :param question: 用户问题
        :param top_k: 返回前k个候选答案
        :param threshold: 相似度阈值
        :return: 答案字典或None
        """
        return self.engine.answer(question, top_k=top_k, threshold=threshold)
    
    def search(self, query, top_k=5, threshold=0.3):
        """
        搜索相关问题
        :param query: 查询文本
        :param top_k: 返回前k个结果
        :param threshold: 相似度阈值
        :return: 结果列表
        """
        return self.engine.search(query, top_k=top_k, threshold=threshold)


def main():
    """命令行测试"""
    print("=" * 60)
    print("问答机器人服务")
    print("=" * 60)
    
    service = QAService()
    
    print("\n服务已启动，可以开始提问了！")
    print("输入 'quit' 或 'exit' 退出\n")
    
    while True:
        question = input("您的问题: ").strip()
        
        if not question:
            continue
        
        if question.lower() in ['quit', 'exit', '退出']:
            print("再见！")
            break
        
        result = service.ask(question)
        
        if result:
            print(f"\n【答案】")
            print(f"{result['answer']}")
            print(f"\n[匹配问题: {result['question']}]")
            print(f"[相似度: {result['similarity']:.3f}]")
        else:
            print("\n抱歉，没有找到相关答案。")
        
        print()


if __name__ == '__main__':
    main()
