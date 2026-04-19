# Second Agent 使用指南

## 1. 服务器启动

```bash
cd /mnt/workspace/neo4j_agent_env
source bin/activate
cd /mnt/workspace/neo4j_agent_env/second_agent
```

启动 Neo4j：

```bash
neo4j start
ss -lntp | grep 7687
```

启动或检查 Ollama：

```bash
ollama list
```

## 2. 健康检查

```bash
python health_check.py
python check_neo4j.py
```

理想状态：

- Ollama 有 `qwen2.5:7b` 和 `bge-m3:latest`。
- Neo4j 连接成功。
- skills 目录包含 `career-advancement`、`resume-polisher`、`interview-coach`、`paper-digest`。

## 3. Agent 推理演示

```bash
python agent_v2_reasoning.py
```

该脚本会展示：

- Skill 调用。
- 长期记忆检索。
- 图谱治理 dry-run。
- 推理轨迹保存到 `agent_reasoning_traces.json`。

查看原始 LangChain ReAct 链：

```bash
python agent_v2_reasoning.py --verbose
```

## 4. 混合记忆写入演示

```bash
python hybrid_agent_padding_final.py
```

该脚本会验证：

- Mem0/Qdrant 向量记忆写入。
- Neo4j 图谱关系写入。
- LLMGraphTransformer 关系抽取。
- fallback 图谱写入。

如果要重建本地向量库：

```bash
python hybrid_agent_padding_final.py --reset
```

## 5. Neo4j 验证命令

检查 APOC：

```bash
cypher-shell -u neo4j -p password123456 "RETURN apoc.version();"
```

查看节点：

```bash
cypher-shell -u neo4j -p password123456 "MATCH (n) RETURN labels(n), properties(n) LIMIT 20;"
```

查看关系：

```bash
cypher-shell -u neo4j -p password123456 "MATCH (a)-[r]->(b) RETURN properties(a), type(r), properties(b) LIMIT 20;"
```

## 6. 图谱治理

只做 dry-run，不修改数据库：

```bash
python memory_optimizer.py
```

确认候选实体合理后再执行合并：

```bash
python memory_optimizer.py --execute
```

分析两个实体的最短路径：

```bash
python memory_optimizer.py --path Alex Neo4j
```

## 7. 运行产物

以下文件属于运行产物，不建议提交到 Git：

- `agent_reasoning_traces.json`
- `my_agent_vector_padding/`
- `__pycache__/`

服务器运行时会自动生成这些文件。
