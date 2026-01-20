#!/usr/bin/env python
# _*_ coding:utf-8 _*_

"""
导入CSV文件到Neo4j数据库
根据图片要求，使用py2neo库导入数据
"""

from py2neo import Graph, Node, Relationship, NodeMatcher
import pandas as pd
import os
import sys

# Neo4j数据库连接配置
NEO4J_URI = "http://localhost:7474"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "xh050316"

# CSV文件路径（当前目录）
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


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
            print(f"尝试{method_name}...")
            graph = method()
            # 测试连接是否成功
            graph.run("RETURN 1")
            print(f"✓ 成功连接到Neo4j数据库: {NEO4J_URI}")
            return graph
        except Exception as e:
            print(f"  {method_name}失败: {str(e)[:100]}")
            continue
    
    # 所有方式都失败了
    print("\n" + "=" * 60)
    print("所有连接方式都失败了！")
    print("=" * 60)
    print("\n提示：")
    print("1. 请确保Neo4j服务已启动")
    print("2. 检查连接信息是否正确")
    print("3. 尝试在Neo4j Browser中连接验证服务是否正常")
    print(f"4. 当前尝试的连接URI: {NEO4J_URI}")
    print("5. 用户名: " + NEO4J_USERNAME)
    print("\n如果使用Neo4j 5.x版本，可能需要使用bolt://localhost:7687")
    sys.exit(1)


def clear_database(graph):
    '''
    清空数据库（可选，谨慎使用）
    :param graph: Graph对象
    :return:
    '''
    print("正在清空数据库...")
    try:
        graph.run("MATCH (n) DETACH DELETE n")
        print("数据库已清空")
    except Exception as e:
        print(f"清空数据库时出错: {e}")


def import_genre(graph):
    '''
    导入电影类型节点
    根据代码5.1的要求：导入节点电影类型 == 注意类型转换
    :param graph: Graph对象
    :return:
    '''
    csv_path = os.path.join(BASE_DIR, 'genre.csv')
    if not os.path.exists(csv_path):
        print(f"警告: 找不到文件 {csv_path}")
        return
    
    print(f"正在导入电影类型数据: {csv_path}")
    # 使用更健壮的CSV读取参数
    try:
        df = pd.read_csv(
            csv_path, 
            encoding='utf-8',
            quoting=1,
            quotechar='"',
            engine='python'
        )
    except Exception as e:
        print(f"使用Python引擎读取失败，尝试使用C引擎: {e}")
        df = pd.read_csv(
            csv_path, 
            encoding='utf-8',
            quoting=1,
            quotechar='"',
            engine='c',
            low_memory=False
        )
    
    count = 0
    for _, row in df.iterrows():
        try:
            gid = int(row['gid'])
            gname = str(row['gname']).strip()
            
            # 创建或更新Genre节点（注意类型转换）
            graph.run(
                "MERGE (g:Genre {gid: $gid}) "
                "SET g.name = $gname",
                gid=gid, gname=gname
            )
            count += 1
        except Exception as e:
            print(f"导入电影类型数据时出错 (gid={row.get('gid', 'N/A')}): {e}")
    
    print(f"成功导入 {count} 个电影类型节点")


def import_person(graph):
    '''
    导入演员节点
    根据代码5.1的要求：导入节点演员信息
    :param graph: Graph对象
    :return:
    '''
    csv_path = os.path.join(BASE_DIR, 'person.csv')
    if not os.path.exists(csv_path):
        print(f"警告: 找不到文件 {csv_path}")
        return
    
    print(f"正在导入演员数据: {csv_path}")
    # 使用更健壮的CSV读取参数
    try:
        df = pd.read_csv(
            csv_path, 
            encoding='utf-8', 
            na_values=['\\N'],
            quoting=1,
            quotechar='"',
            engine='python'
        )
    except Exception as e:
        print(f"使用Python引擎读取失败，尝试使用C引擎: {e}")
        df = pd.read_csv(
            csv_path, 
            encoding='utf-8', 
            na_values=['\\N'],
            quoting=1,
            quotechar='"',
            engine='c',
            low_memory=False
        )
    
    count = 0
    for _, row in df.iterrows():
        try:
            pid = int(row['pid'])
            birth = str(row['birth']) if pd.notna(row['birth']) else None
            death = str(row['death']) if pd.notna(row['death']) else None
            name = str(row['name']).strip() if pd.notna(row['name']) else ''
            biography = str(row['biography']).strip() if pd.notna(row['biography']) else ''
            birthplace = str(row['birthplace']).strip() if pd.notna(row['birthplace']) else ''
            
            # 创建或更新Person节点（注意类型转换）
            graph.run(
                "MERGE (p:Person {pid: $pid}) "
                "SET p.birth = $birth, "
                "    p.death = $death, "
                "    p.name = $name, "
                "    p.biography = $biography, "
                "    p.birthplace = $birthplace",
                pid=pid, birth=birth, death=death, name=name, 
                biography=biography, birthplace=birthplace
            )
            count += 1
        except Exception as e:
            print(f"导入演员数据时出错 (pid={row.get('pid', 'N/A')}): {e}")
    
    print(f"成功导入 {count} 个演员节点")


def import_movie(graph):
    '''
    导入电影节点
    根据代码5.1的要求：导入节点电影信息
    :param graph: Graph对象
    :return:
    '''
    csv_path = os.path.join(BASE_DIR, 'movie.csv')
    if not os.path.exists(csv_path):
        print(f"警告: 找不到文件 {csv_path}")
        return
    
    print(f"正在导入电影数据: {csv_path}")
    # 使用更健壮的CSV读取参数，处理包含引号和换行符的长文本
    try:
        # 首先尝试使用Python引擎（更宽容，能处理复杂格式）
        df = pd.read_csv(
            csv_path, 
            encoding='utf-8',
            quoting=1,  # QUOTE_ALL
            quotechar='"',
            escapechar='\\',
            engine='python',  # 使用Python引擎，更宽容
            error_bad_lines=False,  # 旧版本pandas参数
            warn_bad_lines=False
        )
    except TypeError:
        # 如果error_bad_lines不支持，尝试新版本参数
        try:
            df = pd.read_csv(
                csv_path, 
                encoding='utf-8',
                quoting=1,
                quotechar='"',
                engine='python',
                on_bad_lines='skip'  # 新版本pandas参数
            )
        except Exception as e:
            print(f"使用Python引擎读取失败: {e}")
            # 最后尝试C引擎
            df = pd.read_csv(
                csv_path, 
                encoding='utf-8',
                quoting=1,
                quotechar='"',
                engine='c',
                low_memory=False
            )
    except Exception as e:
        print(f"读取CSV文件时出错: {e}")
        print("尝试使用更简单的读取方式...")
        # 最后尝试最简单的方式
        df = pd.read_csv(
            csv_path, 
            encoding='utf-8',
            engine='python',
            error_bad_lines=False,
            warn_bad_lines=False
        )
    
    count = 0
    for _, row in df.iterrows():
        try:
            mid = int(row['mid'])
            title = str(row['title']).strip() if pd.notna(row['title']) else ''
            introduction = str(row['introduction']).strip() if pd.notna(row['introduction']) else ''
            rating = float(row['rating']) if pd.notna(row['rating']) else None
            releasedate = str(row['releasedate']) if pd.notna(row['releasedate']) else None
            
            # 创建或更新Movie节点（注意类型转换）
            graph.run(
                "MERGE (m:Movie {mid: $mid}) "
                "SET m.title = $title, "
                "    m.introduction = $introduction, "
                "    m.rating = $rating, "
                "    m.releasedate = $releasedate",
                mid=mid, title=title, introduction=introduction, 
                rating=rating, releasedate=releasedate
            )
            count += 1
        except Exception as e:
            print(f"导入电影数据时出错 (mid={row.get('mid', 'N/A')}): {e}")
    
    print(f"成功导入 {count} 个电影节点")


def import_person_to_movie(graph):
    '''
    导入演员与电影之间的关系（actedin）
    根据代码5.1的要求：导入关系 actedin 电影是谁参演的1对多
    :param graph: Graph对象
    :return:
    '''
    csv_path = os.path.join(BASE_DIR, 'person_to_movie.csv')
    if not os.path.exists(csv_path):
        print(f"警告: 找不到文件 {csv_path}")
        return
    
    print(f"正在导入演员-电影关系数据: {csv_path}")
    # 使用更健壮的CSV读取参数
    try:
        df = pd.read_csv(
            csv_path, 
            encoding='utf-8',
            quoting=1,
            quotechar='"',
            engine='python'
        )
    except Exception as e:
        print(f"使用Python引擎读取失败，尝试使用C引擎: {e}")
        df = pd.read_csv(
            csv_path, 
            encoding='utf-8',
            quoting=1,
            quotechar='"',
            engine='c',
            low_memory=False
        )
    
    count = 0
    for _, row in df.iterrows():
        try:
            pid = int(row['pid'])
            mid = int(row['mid'])
            
            # 创建关系（注意类型转换）
            graph.run(
                "MATCH (from:Person {pid: $pid}), (to:Movie {mid: $mid}) "
                "MERGE (from)-[r:actedin {pid: $pid, mid: $mid}]->(to)",
                pid=pid, mid=mid
            )
            count += 1
        except Exception as e:
            print(f"导入演员-电影关系时出错 (pid={row.get('pid', 'N/A')}, mid={row.get('mid', 'N/A')}): {e}")
    
    print(f"成功导入 {count} 个演员-电影关系")


def import_movie_to_genre(graph):
    '''
    导入电影与类型之间的关系（is）
    根据代码5.1的要求：导入关系 电影是什么类型== 1对多
    :param graph: Graph对象
    :return:
    '''
    csv_path = os.path.join(BASE_DIR, 'movie_to_genre.csv')
    if not os.path.exists(csv_path):
        print(f"警告: 找不到文件 {csv_path}")
        return
    
    print(f"正在导入电影-类型关系数据: {csv_path}")
    # 使用更健壮的CSV读取参数
    try:
        df = pd.read_csv(
            csv_path, 
            encoding='utf-8',
            quoting=1,
            quotechar='"',
            engine='python'
        )
    except Exception as e:
        print(f"使用Python引擎读取失败，尝试使用C引擎: {e}")
        df = pd.read_csv(
            csv_path, 
            encoding='utf-8',
            quoting=1,
            quotechar='"',
            engine='c',
            low_memory=False
        )
    
    count = 0
    for _, row in df.iterrows():
        try:
            mid = int(row['mid'])
            gid = int(row['gid'])
            
            # 创建关系（注意类型转换）
            graph.run(
                "MATCH (from:Movie {mid: $mid}), (to:Genre {gid: $gid}) "
                "MERGE (from)-[r:is {mid: $mid, gid: $gid}]->(to)",
                mid=mid, gid=gid
            )
            count += 1
        except Exception as e:
            print(f"导入电影-类型关系时出错 (mid={row.get('mid', 'N/A')}, gid={row.get('gid', 'N/A')}): {e}")
    
    print(f"成功导入 {count} 个电影-类型关系")


def main():
    '''
    主函数：执行数据导入
    根据图片要求，按照代码5.1的顺序导入数据
    '''
    print("=" * 60)
    print("开始导入数据到Neo4j数据库")
    print("=" * 60)
    print(f"数据库连接: {NEO4J_URI}")
    print(f"用户名: {NEO4J_USERNAME}")
    print("=" * 60)
    
    # 连接数据库
    graph = connect_neo4j()
    
    # 询问是否清空数据库（可选）
    # clear_database(graph)  # 取消注释以清空数据库
    
    # 导入节点（按照代码5.1的顺序）
    print("\n" + "=" * 60)
    print("步骤1: 导入节点")
    print("=" * 60)
    print("1.1 导入电影类型节点...")
    import_genre(graph)
    print("\n1.2 导入演员节点...")
    import_person(graph)
    print("\n1.3 导入电影节点...")
    import_movie(graph)
    
    # 导入关系（按照代码5.1的顺序）
    print("\n" + "=" * 60)
    print("步骤2: 导入关系")
    print("=" * 60)
    print("2.1 导入演员-电影关系（actedin）...")
    import_person_to_movie(graph)
    print("\n2.2 导入电影-类型关系（is）...")
    import_movie_to_genre(graph)
    
    # 统计信息
    print("\n" + "=" * 60)
    print("导入完成！统计信息：")
    print("=" * 60)
    
    try:
        # 统计节点数量
        genre_count = graph.run("MATCH (g:Genre) RETURN count(g) as count").data()[0]['count']
        person_count = graph.run("MATCH (p:Person) RETURN count(p) as count").data()[0]['count']
        movie_count = graph.run("MATCH (m:Movie) RETURN count(m) as count").data()[0]['count']
        
        # 统计关系数量
        actedin_count = graph.run("MATCH ()-[r:actedin]->() RETURN count(r) as count").data()[0]['count']
        is_count = graph.run("MATCH ()-[r:is]->() RETURN count(r) as count").data()[0]['count']
        
        print(f"Genre节点: {genre_count}")
        print(f"Person节点: {person_count}")
        print(f"Movie节点: {movie_count}")
        print(f"actedin关系: {actedin_count}")
        print(f"is关系: {is_count}")
        print("=" * 60)
        
        # 显示示例数据（类似图片5.14）
        print("\n示例查询（显示前25个电影节点）:")
        print("MATCH (n:Movie) RETURN n LIMIT 25")
        result = graph.run("MATCH (n:Movie) RETURN n LIMIT 25").data()
        print(f"已显示 {len(result)} 个电影节点")
        
    except Exception as e:
        print(f"获取统计信息时出错: {e}")
    
    print("\n数据导入完成！")
    print("可以在Neo4j Browser中查看导入的数据。")


if __name__ == '__main__':
    main()
