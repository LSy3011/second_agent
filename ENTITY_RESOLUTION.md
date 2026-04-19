# 实体消歧与多跳推理技术文档 (Entity Resolution & Multi-hop Reasoning)

## 1. 核心挑战
在构建个性化 AI 智能体时，用户输入通常具有高度的随意性。例如：
- 提到 "Python Developer" 
- 随后提到 "Alex 是个写 Python 的"
在原始图谱中，这会产生两个独立的节点 "Python Developer" 和 "写 Python 的"，导致知识碎片化。

## 2. 解决方案：基于语义距离的实体合并
本项目引入了自动化实体归并逻辑：
1. **触发时机**：在 Agent 闲时（或定时任务）启动。
2. **计算策略**：当前代码使用名称规范化 + `SequenceMatcher` 做第一阶段候选召回，后续可扩展为向量余弦相似度（Cosine Similarity）和 LLM 二次判定。
3. **安全策略**：默认 dry-run，只输出候选实体对和相似度，不修改图谱。
4. **执行引擎**：只有显式传入 `--execute` 时，才调用 Neo4j APOC 插件的 `mergeNodes` 函数，将冗余节点的边（Relationships）自动重定向到主节点上。

## 3. 多跳推理 (Multi-hop Reasoning) 的应用
通过 Cypher 的 `shortestPath` 或 `allShortestPaths` 进行路径分析。
- **示例场景**：
  - 用户问："为什么 Alex 对这个项目感兴趣？"
  - 推理链：`Alex --[SKILLS]--> Python --[REQUIRED_BY]--> Project_A`
- **优势**：相比向量检索，这种推理提供了 100% 的**可解释性 (Explainability)**，这是 NLP 工业界（尤其是金融、医疗领域）极度看重的能力。

## 4. 简历加分点
在面试中，可以重点描述如何通过**图论算法（Graph Algorithms）**弥补**大模型生成随机性**的不足，体现出你不仅会调用 API，更懂得如何通过传统算法优化神经网络系统的鲁棒性。
