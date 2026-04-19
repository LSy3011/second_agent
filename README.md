# Second Agent

Second Agent 是一个本地化长期记忆 Agent 系统，融合 Mem0/Qdrant 向量记忆、Neo4j 图谱记忆、LangChain 工具调用和 Skill 工作流。项目目标是让本地大模型不仅能回答问题，还能检索用户长期记忆、读取任务 Skill、执行图谱治理 dry-run，并保存推理轨迹。

## 项目定位

Second Agent 解决的是“Agent 如何拥有长期记忆、工具调用能力和可维护任务流程”的问题。

它和 Paper Assistant 的分工是：

- Paper Assistant：沉淀论文/行业资料，提供可检索的领域知识服务。
- Second Agent：沉淀用户画像与任务过程，负责工具选择、Skill 调用和个性化推理。

## 已验证能力

服务器验证结果：

- Ollama 模型可用：`qwen2.5:7b`、`bge-m3:latest`。
- Neo4j 5.26.24 连接正常，APOC 插件可用。
- Mem0/Qdrant 本地向量记忆可写入和检索。
- Neo4j 图谱关系可写入和查询。
- `career-advancement`、`resume-polisher`、`interview-coach`、`paper-digest` Skill 可识别。
- Agent 推理链路、工具调用摘要和 trace 持久化可用。

## 技术栈

- Python
- LangChain
- Mem0
- Qdrant local
- Neo4j + APOC
- Ollama
- Qwen2.5-7B
- BGE-M3
- Skill workflow

## 目录结构

```text
.
├── agent_v2_reasoning.py          # ReAct Agent 推理入口
├── hybrid_agent_padding_final.py  # Mem0 + Neo4j 混合记忆写入验证
├── memory_store.py                # Mem0/Qdrant 记忆封装
├── memory_optimizer.py            # Neo4j 图谱治理 dry-run 与路径分析
├── embedding_patch.py             # BGE-M3 到目标维度的运行时适配
├── health_check.py                # 环境健康检查
├── check_neo4j.py                 # Neo4j 连接检查
├── skills/                        # Skill 工作流说明
├── docs/                          # 构建、服务器和扩展说明
├── .env.example
└── requirements.txt
```

## 快速运行

服务器已有虚拟环境时：

```bash
cd /mnt/workspace/neo4j_agent_env
source bin/activate
cd /mnt/workspace/neo4j_agent_env/second_agent
```

启动 Neo4j 和 Ollama 后检查：

```bash
python health_check.py
python check_neo4j.py
```

运行 Agent 推理演示：

```bash
python agent_v2_reasoning.py
```

运行混合记忆写入演示：

```bash
python hybrid_agent_padding_final.py
```

查询 Neo4j 图谱：

```bash
cypher-shell -u neo4j -p password123456 "MATCH (a)-[r]->(b) RETURN properties(a), type(r), properties(b) LIMIT 20;"
```

## 关键配置

复制 `.env.example` 为 `.env` 后可调整：

```env
NEO4J_URL=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123456
OLLAMA_LLM_MODEL=qwen2.5:7b
OLLAMA_EMBEDDING_MODEL=bge-m3:latest
SOURCE_EMBEDDING_DIM=1024
TARGET_EMBEDDING_DIM=1536
```

## Skill 列表

- `career-advancement`：职业晋升与 AI 应用工程师定位。
- `resume-polisher`：简历项目包装。
- `interview-coach`：面试问答准备。
- `paper-digest`：论文解读任务。

## 简历表述

> 基于 Mem0 + Qdrant + Neo4j 构建本地化长期记忆 Agent，支持向量记忆检索、图谱关系写入、Skill 工具调用和推理轨迹持久化；解决本地 BGE-M3 embedding 维度适配、Neo4j/APOC 部署、LangChain 依赖冲突等工程问题，并在服务器完成健康检查、Agent 推理、图谱写入和 Skill 调用验证。
