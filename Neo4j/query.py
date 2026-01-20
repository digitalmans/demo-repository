#!/usr/bin/env python
# _*_ coding:utf-8 _*_

from py2neo import Graph, Node, Relationship, NodeMatcher
import sys

# Neo4j数据库连接配置
NEO4J_URI = "http://localhost:7474"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "xh050316"


def connect_neo4j():
    '''
    连接Neo4j数据库
    支持多种连接方式以兼容不同版本的py2neo
    :return: Graph对象
    '''
    # 尝试多种连接方式
    connection_methods = [
        # 方式1: 使用auth参数（推荐，兼容性最好）
        ("使用auth参数连接", lambda: Graph(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))),
        # 方式2: 使用username和password参数（HTTP协议）
        ("使用username/password参数连接", lambda: Graph(NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)),
        # 方式3: 使用bolt协议
        ("使用Bolt协议连接", lambda: Graph("bolt://localhost:7687", auth=(NEO4J_USERNAME, NEO4J_PASSWORD))),
    ]
    
    for method_name, method in connection_methods:
        try:
            graph = method()
            # 测试连接是否成功
            graph.run("RETURN 1")
            return graph
        except Exception as e:
            continue
    
    # 所有方式都失败了
    print("连接Neo4j数据库失败！")
    print("请确保Neo4j服务已启动")
    sys.exit(1)


def query(query_SQL):
    '''
    查询Neo4j数据库
    :param query_SQL: 查询命令
    :return: 查询结果列表
    '''
    # 连接数据库
    graph = connect_neo4j()
    # 存储查询结果
    result = []
    # 执行查询语句
    try:
        query_result = graph.run(query_SQL)
        for i in query_result:
            # 获取查询结果的第一列值
            if i.items():
                result.append(i.items()[0][1])
    except Exception as e:
        print(f"查询执行失败: {e}")
        return []
    return result


if __name__ == '__main__':
    # 查询电影《英雄》的电影简介信息
    query_SQL = "match (m:Movie)-[]->() where m.title='英雄' return m.introduction"
    result = query(query_SQL)
    print('query result:', result)
