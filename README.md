# 🧠 Hybrid RAG Agent: 基于向量+图谱的双脑记忆系统 (V2 Advanced)

> **全链路本地化 | 复杂推理 Agent | 具身记忆优化**

这是一个进阶版的 **Hybrid RAG** 智能体系统。在 V1 版本的混合检索基础上，V2 版本引入了 **ReAct 推理链** 和 **实体消歧归并** 技术，使其具备了更强的逻辑推理能力和知识库自愈能力。

## 🌟 核心亮点 (V2 New Features)

### 1. 🧠 ReAct 复杂推理架构 (New!)
引入了 **Reasoning-Action** 循环。Agent 不再只是简单的检索，而是会根据问题的复杂度，自主决定是查询向量记忆（偏好/性格）还是图谱记忆（硬性关系），并能进行多步推理。
- 详见：`agent_v2_reasoning.py`

### 2. 🕸️ 记忆消歧与路径分析 (New!)
解决了知识图谱在自动化构建过程中产生的节点冗余问题，并通过 Cypher 路径算法提供可解释的推理链。
- **实体归并**：利用语义距离自动合并相似实体。
- **路径解释**：解释 Agent 为何得出该结论（逻辑溯源）。
- 详见：`memory_optimizer.py` 和 `ENTITY_RESOLUTION.md`

### 3. 🛠️ 运行时热补丁 (Classic)
保留了 V1 中著名的 **Zero-Padding Adapter**，完美解决本地 BGE-M3 (1024维) 与 Mem0 硬编码 OpenAI (1536维) 的维度冲突。

## 🏗️ 技术栈升级
* **Reasoning**: LangChain (ReAct Agent)
* **LLM**: Ollama (Qwen2.5-7B)
* **Graph Database**: Neo4j + APOC Plugins
* **Memory Management**: Mem0 + Custom Optimizer

## 📂 项目结构
```text
.
├── agent_v2_reasoning.py       # [核心] V2 版本 ReAct 推理智能体逻辑
├── memory_optimizer.py         # [优化] 图谱实体归并与路径分析工具
├── ENTITY_RESOLUTION.md        # [文档] 实体消歧与推理技术原理说明
├── app.py                      # V1 版本 Streamlit Web 界面
├── hybrid_agent_padding_final.py # V1 版本核心逻辑（含热补丁）
```

## 🚀 进阶体验
运行 V2 推理 Agent：
```bash
python agent_v2_reasoning.py
```
运行记忆优化器：
```bash
python memory_optimizer.py
```


