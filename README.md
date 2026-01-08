
# 🧠 Hybrid RAG Agent: 基于向量+图谱的双脑记忆系统

> **全链路本地化 | 零 API 成本 | 混合检索增强生成**

这是一个基于 **Hybrid RAG (混合检索增强生成)** 架构的个性化 AI 智能体系统。它摒弃了单一的向量检索方案，创新性地融合了 **Mem0 (Vector)** 和 **Neo4j (Graph)**，能够在本地环境下实现对非结构化语义和结构化关系的双重记忆与推理。

![Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Neo4j](https://img.shields.io/badge/Database-Neo4j%20%2B%20Qdrant-green)
![LLM](https://img.shields.io/badge/Model-Qwen2.5%20%7C%20BGE--M3-orange)

## 📖 项目背景

传统 RAG 系统在处理复杂实体关系时往往存在局限性，且云端大模型方案面临数据隐私和成本挑战。本项目旨在构建一个**完全本地化**的 AI 记忆系统：
* **向量记忆 (Vector Memory)**：处理模糊意图和非结构化文本（基于 Mem0 + Qdrant）。
* **图谱记忆 (Graph Memory)**：处理实体关系和多跳推理（基于 LangChain + Neo4j）。

## 🌟 核心亮点 (Engineering Highlights)

### 1. 🛠️ 运行时热补丁 (Runtime Monkey Patching)
解决了 Mem0 库硬编码依赖 OpenAI (1536维) 与本地 BGE-M3 模型 (1024维) 的**维度不兼容死锁**问题。
* **方案**：不修改第三方库源码，通过 Python 动态拦截 `Embedding.embed` 方法。
* **实现**：注入 **Zero-Padding Adapter**，自动对 1024 维向量进行末尾补零填充至 1536 维，成功骗过数据库校验，打通数据流。

### 2. 🕸️ 鲁棒的图谱 ETL 管道
针对 7B 小参数模型指令遵循能力弱的问题：
* 利用 **LangChain LLMGraphTransformer** 标准化提取流程。
* 配合 Ollama **JSON Mode** 强制约束输出格式，消除格式幻觉，实现图谱自动化构建。

### 3. 🔍 双向模糊检索逻辑
重构了 Cypher 查询逻辑，将传统的“单向包含”升级为**双向模糊匹配** (`Query Contains Node` OR `Node Contains Query`)，并增加了对特殊字符的防注入处理，显著提升了召回率。

## 🏗️ 技术栈

* **LLM & Embedding**: Ollama (Qwen2.5-7B, BGE-M3)
* **Orchestration**: LangChain, LangChain-Experimental
* **Vector Store**: Mem0 (底层封装 Qdrant)
* **Graph Store**: Neo4j (Bolt Protocol)
* **Frontend**: Streamlit, Streamlit-Agraph
* **Language**: Python 3.x

## 🚀 快速开始

### 1. 环境准备

确保已安装以下基础设施：
* **Neo4j**: 启动服务并开放 Bolt 端口 (7687)。
* **Ollama**: 安装并拉取模型：
```bash
    ollama pull qwen2.5:7b
    ollama pull bge-m3
```

### 2. 安装依赖

```bash
pip install -r requirements.txt

```

*(如果未创建 requirements.txt，主要依赖为: `streamlit`, `streamlit-agraph`, `mem0ai`, `langchain`, `langchain_community`, `langchain_experimental`, `neo4j`, `qdrant-client`)*

### 3. 配置数据库

请在 `app.py` 或 `cli_demo.py` 中确认您的 Neo4j 配置：

```python
NEO4J_URL = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password123456" # 修改为您自己的密码

```

### 4. 运行应用

**启动可视化 Web 界面 (推荐):**

```bash
streamlit run app.py

```

访问浏览器 (默认端口 8501)，即可看到左侧对话窗口和右侧实时知识图谱。

**运行命令行演示版:**

```bash
python cli_demo.py

```

## 📂 项目结构

```text
.
├── app.py                      # Streamlit Web 应用主入口 (含核心补丁与可视化)
├── cli_demo.py                 # 命令行版本的演示脚本 (原 hybrid_agent_padding_final.py)
├── my_agent_vector_padding/    # 本地向量数据库存储目录 (自动生成)
├── requirements.txt            # 项目依赖列表
└── README.md                   # 项目说明文档

```

## 📝 使用指南

1. **写入记忆 (Write)**: 在对话框输入陈述句，如 *"Alex works as a Python Developer."*。系统会自动提取实体关系存入 Neo4j，并存入向量库。
2. **检索问答 (Read)**: 输入问题，如 *"What is Alex's job?"*。系统会同时检索向量和图谱上下文。
3. **可视化**: 右侧面板会实时渲染当前 Neo4j 数据库中的节点与关系网络。

## 🛡️ 常见问题 (FAQ)

* **Q: 为什么启动时提示维度不匹配？**
* A: 请确保运行的是 `app.py` 或 `cli_demo.py`，这些文件中包含了关键的 **Monkey Patch** 代码。如果运行原始未修补的代码将会报错。


* **Q: 图谱为空？**
* A: 请检查 Neo4j 服务是否已启动 (`neo4j status`)，以及密码配置是否正确。




