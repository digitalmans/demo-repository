# Neo4j数据导入说明

## 文件说明

### 1. `import_to_neo4j.py` (推荐使用)
使用Python和py2neo库直接导入CSV文件到Neo4j数据库。

**优点：**
- 不需要将CSV文件复制到Neo4j的import目录
- 自动处理数据类型转换
- 更好的错误处理
- 可以自动查找CSV文件位置

**使用方法：**
```bash
python import_to_neo4j.py
```

**CSV文件位置：**
- 优先查找：`chap05/data/import/` 目录
- 备选路径：`chap06/Movie-KBQA/data/import/` 目录

### 2. `import_cypher.py`
使用Cypher的LOAD CSV命令导入数据。

**注意：**
- 需要将CSV文件放在Neo4j的import目录下
- Neo4j默认import目录通常在：`NEO4J_HOME/import/`

**使用方法：**
1. 将CSV文件复制到Neo4j的import目录
2. 运行脚本：
```bash
python import_cypher.py
```

## 数据库连接配置

所有脚本使用以下连接信息：
- URI: `http://localhost:7474`
- Username: `neo4j`
- Password: `xh050316`

如需修改，请编辑脚本中的以下变量：
```python
NEO4J_URI = "http://localhost:7474"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "xh050316"
```

## 导入的数据结构

### 节点类型

1. **Genre (电影类型)**
   - gid: 类型ID
   - name: 类型名称

2. **Person (演员)**
   - pid: 演员ID
   - birth: 出生日期
   - death: 逝世日期（\N表示未逝世）
   - name: 演员姓名
   - biography: 个人简介
   - birthplace: 出生地

3. **Movie (电影)**
   - mid: 电影ID
   - title: 电影名称
   - introduction: 电影简介
   - rating: 电影评分
   - releasedate: 上映日期

### 关系类型

1. **actedin** (Person -> Movie)
   - 表示演员参演电影
   - 属性：pid, mid

2. **is** (Movie -> Genre)
   - 表示电影属于某个类型
   - 属性：mid, gid

## CSV文件格式要求

### genre.csv
```csv
gid,gname
12,冒险
14,奇幻
...
```

### person.csv
```csv
pid,birth,death,name,biography,birthplace
643,1965-12-31,\N,巩俐,简介...,Shenyang, Liaoning Province, China
...
```

### movie.csv
```csv
mid,title,introduction,rating,releasedate
13,Forrest Gump,简介...,8.3,1994-07-06
...
```

### person_to_movie.csv
```csv
pid,mid
163441,13
240171,24
...
```

### movie_to_genre.csv
```csv
mid,gid
79,12
82,12
...
```

## 导入步骤

1. **确保Neo4j服务已启动**
   ```bash
   # 检查Neo4j服务状态
   # Windows: 在服务管理器中查看
   # Linux/Mac: sudo systemctl status neo4j
   ```

2. **检查CSV文件是否存在**
   - 确保所有5个CSV文件都已准备好
   - 文件编码应为UTF-8

3. **运行导入脚本**
   ```bash
   python import_to_neo4j.py
   ```

4. **验证导入结果**
   - 脚本会自动显示统计信息
   - 也可以在Neo4j Browser中查询：
     ```cypher
     MATCH (n) RETURN count(n)
     MATCH ()-[r]->() RETURN count(r)
     ```

## 清空数据库（可选）

如果需要重新导入数据，可以取消注释脚本中的 `clear_database(graph)` 行。

**警告：** 这将删除数据库中的所有数据！

## 常见问题

### 1. 连接失败
- 检查Neo4j服务是否启动
- 检查端口是否正确（默认7474）
- 检查用户名和密码是否正确

### 2. CSV文件找不到
- 检查文件路径是否正确
- 确保文件编码为UTF-8
- 可以手动指定CSV文件路径

### 3. 导入速度慢
- 大量数据导入可能需要较长时间
- 可以分批导入或使用事务优化

## 依赖包

确保已安装以下Python包：
```bash
pip install py2neo pandas
```
