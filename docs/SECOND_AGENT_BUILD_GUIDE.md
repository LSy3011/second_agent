# Second Agent 项目搭建与架构说明文档

## 1. 项目定位

Second Agent 可以包装成一个“企业知识助手 Agent Runtime”的执行层。它长期记录用户上下文、团队任务偏好、历史问题和项目知识关系，并在用户提问时调用记忆、图谱和任务 Skill 完成具体工作流。当前代码以研发知识助手为主线，职业发展、简历和面试类任务只作为可选验证样例，不作为项目本身的业务背景。

项目定位建议：

> 基于 LangChain ReAct、Mem0、Neo4j、Ollama 和 Skill 机制构建本地化长期记忆 Agent Runtime，面向企业知识助手、研发知识工作流和内部文档问答场景，实现向量记忆与图谱记忆融合、任务能力模块化、工具调用决策、推理轨迹持久化，并通过维度填充适配解决 BGE-M3 与 Mem0 默认 OpenAI 向量维度不兼容问题。

这个项目更适合体现 Agent 工程能力：工具封装、记忆系统、Skill 编排、ReAct 推理、图谱自愈、兼容性修复。公司层面可以理解为把“企业知识助手”的记忆、工具和任务流程产品化，而不是只做一个单轮聊天机器人。

## 2. 与 Paper Assistant 的差异

Paper Assistant 偏知识库基础设施，重点是“把论文变成可检索、可解释的知识”。

Second Agent 偏智能体运行时，重点是“让 Agent 根据任务自主使用记忆和工具”。

两者可以在项目叙事中形成层次：

- Paper Assistant：底层知识生产系统。
- Second Agent：上层 Agent 决策与记忆系统。
- 组合叙事：先构建可信知识，再让 Agent 基于记忆和工具完成任务。
- 公司叙事：用知识库沉淀企业 Know-how，用长期记忆沉淀用户/团队上下文，用 Skill 标准化研发、支持、培训等任务流程。

## 3. 当前代码结构

```text
F:\second_agent
├── agent_v2_reasoning.py          # ReAct 推理智能体
├── hybrid_agent_padding_final.py  # Mem0 + Neo4j 混合记忆验证链路
├── memory_optimizer.py            # 图谱实体归并与路径分析
├── check_neo4j.py                 # Neo4j 连接检查
├── debug_agent.py                 # 调试脚本
├── find_the_culprit_v2.py         # 问题定位脚本
├── agent_reasoning_traces.json    # 本地运行生成的推理轨迹，默认不提交
├── my_agent_vector_padding/       # 本地 Qdrant/Mem0 向量数据，默认不提交
├── skills/                        # 可扩展任务 Skill，例如知识工作流、论文解读、项目表达和技术问答
├── ENTITY_RESOLUTION.md           # 实体消歧说明
├── README.md
├── USAGE_GUIDE.md
└── requirements.txt
```

## 4. 服务器部署步骤

建议使用 Python 3.11。

### 4.1 DSW 服务器现有环境

你当前服务器上已经有 Second Agent 的独立虚拟环境，可以直接复用：

```bash
cd /mnt/workspace/neo4j_agent_env/
source bin/activate
cd /mnt/workspace/neo4j_agent_env/second_agent/
```

建议拉取最新代码后按顺序验证：

```bash
git pull origin master
cp .env.example .env  # 如果 .env 已存在，先人工对比后再改
python health_check.py
python check_neo4j.py
python hybrid_agent_padding_final.py
python agent_v2_reasoning.py
```

如果要重建本地向量库，再显式使用：

```bash
python hybrid_agent_padding_final.py --reset
```

关键原则：`neo4j_agent_env` 只跑 Second Agent，不要和 Paper Assistant 的虚拟环境混用。

### 4.2 通用新环境

```bash
cd /path/to/second_agent
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

复制配置模板并按服务器环境修改：

```bash
cp .env.example .env
```

常用配置项：

```text
NEO4J_URL=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
OLLAMA_LLM_MODEL=qwen2.5:7b
OLLAMA_EMBED_MODEL=bge-m3:latest
VECTOR_DB_PATH=./my_agent_vector_padding
```

启动 Ollama：

```bash
ollama serve
ollama pull qwen2.5:7b
ollama pull bge-m3:latest
```

启动 Neo4j，并确保：

- Bolt 地址：`bolt://localhost:7687`
- 用户名：`neo4j`
- 密码与代码一致，当前示例为 `password123456`
- 已安装 APOC 插件，供实体归并使用

运行混合记忆链路：

```bash
python hybrid_agent_padding_final.py
```

如果需要清空本地向量库重新验证，显式加 `--reset`：

```bash
python hybrid_agent_padding_final.py --reset
```

默认运行不会删除向量库，避免误删已有记忆数据。

运行 ReAct Agent：

```bash
python agent_v2_reasoning.py
```

运行图谱优化器：

```bash
python memory_optimizer.py
```

默认是 dry-run，只会输出相似实体候选，不会修改 Neo4j。确认候选无误后才执行合并：

```bash
python memory_optimizer.py --threshold 0.86 --max-pairs 20
python memory_optimizer.py --threshold 0.86 --max-pairs 20 --execute
```

路径分析：

```bash
python memory_optimizer.py --path Alex Python
```

运行健康检查：

```bash
python health_check.py
```

## 5. 核心技术链路

混合记忆写入链路：

```text
用户输入
  -> Mem0 向量记忆
  -> BGE-M3 Embedding
  -> Zero Padding Adapter: 1024 维补齐到 1536 维
  -> 本地 Qdrant 存储
  -> LangChain LLMGraphTransformer
  -> Neo4j 图谱写入
```

Agent 推理链路：

```text
用户问题
  -> LangChain ReAct Agent
  -> Thought: 判断问题类型
  -> Action: 调用 SearchMemory、OptimizeGraph 或某个 Skill
  -> Observation: 获取工具结果
  -> Final Answer: 输出工作流方案或任务结果
  -> agent_reasoning_traces.json: 保存推理轨迹
```

图谱治理链路：

```text
图谱实体节点
  -> 从 Neo4j 读取实体节点
  -> 基于名称规范化 + SequenceMatcher 做候选召回
  -> dry-run 输出候选实体对和相似度
  -> 显式 --execute 时调用 Neo4j APOC mergeNodes 合并节点
  -> shortestPath 做路径解释
```

## 6. 关键工程亮点

### 6.1 BGE-M3 与 Mem0 维度不兼容修复

BGE-M3 的向量维度通常是 1024，而部分 Mem0/OpenAI 默认链路会按 1536 维处理。如果直接混用，向量库写入或检索可能报维度不一致。

项目中的 `hybrid_agent_padding_final.py` 使用 Monkey Patch 包装 `OllamaEmbedding.embed`：

- 接收 Mem0 可能传入的额外参数。
- 调用原始 Ollama embedding。
- 如果维度不足 1536，则补零。
- 让本地 BGE-M3 可以兼容默认 1536 维向量配置。

项目讲法：

> 这个问题不是 Prompt 问题，而是向量数据库 schema 和 embedding 模型维度不一致。我通过适配器层解决，保证上层 Mem0 不需要大改，同时让本地模型链路跑通。

### 6.2 ReAct 工具选择

`agent_v2_reasoning.py` 把记忆检索和图谱优化封装为 LangChain Tool：

- `SearchMemory`：查询用户背景、偏好、兴趣等软信息。
- `OptimizeGraph`：触发图谱实体归并和关系整理。

Agent 使用 ZERO_SHOT_REACT_DESCRIPTION，根据问题自主选择工具。这个设计比固定流程更像真实 Agent，因为工具调用由任务驱动。

### 6.3 推理轨迹持久化

`agent_reasoning_traces.json` 用来记录 query、final answer、latency 和架构信息。它可以作为 Badcase 分析材料，也可以用于展示 Agent 的决策过程。该文件属于本地运行产物，默认不提交到 Git。

建议后续增强：

- 记录完整 Thought/Action/Observation。
- 给每次工具调用加 trace id。
- 将 Observation 和最终答案的引用关系保存下来，方便调试幻觉。

### 6.4 图谱实体消歧

`memory_optimizer.py` 展示了图谱记忆的自愈思路：

- 自动从 Neo4j 读取实体节点。
- 基于字符串相似度 dry-run 发现潜在重复实体。
- 默认不修改图谱，只有显式 `--execute` 才调用 APOC `mergeNodes` 合并节点和关系。
- 使用 shortestPath 分析两个实体之间的多跳路径。

这能回答一个很实际的工程问题：长期记忆写多了以后，脏数据怎么办？

### 6.5 Skill 机制扩展

Skill 更适合放在 Second Agent，而不是 Paper Assistant。Paper Assistant 的核心是知识库服务，能力边界比较稳定；Second Agent 的核心是任务执行，天然需要把不同任务拆成可组合能力包。

建议把 `skills/` 目录设计成轻量能力包，每个 Skill 至少包含一个 `SKILL.md`：

```text
skills/
├── knowledge-workflow/
│   └── SKILL.md
├── resume-polisher/
│   └── SKILL.md
├── interview-coach/
│   └── SKILL.md
└── paper-digest/
    └── SKILL.md
```

当前项目已经提供了可用 Skill 模板：

```text
skills/resume-polisher/SKILL.md
skills/interview-coach/SKILL.md
skills/paper-digest/SKILL.md
skills/knowledge-workflow/SKILL.md
```

当前 Skill 的定位：

- `knowledge-workflow`：根据企业知识源、目标用户和任务约束，规划研发知识助手或内部文档问答工作流。
- `paper-digest`：调用 Paper Assistant 的论文知识服务，对论文做结构化摘要、方法对比和可复述结论。
- `resume-polisher`：根据用户项目经历和已有记忆，生成项目表达和材料整理，作为可选个人效率样例。
- `interview-coach`：生成技术问答和追问路径，作为可选验证样例。

Skill 和普通 Prompt 的区别：

- Prompt 是一次性的指令。
- Skill 是可复用的任务流程，包含触发条件、输入要求、输出格式和质量标准。
- Agent 可以先用记忆判断用户目标，再选择合适 Skill 执行任务。

项目讲法：

> 我把 Agent 的任务能力拆成 Skill，而不是把所有规则写进一个超长 Prompt。这样知识工作流规划、论文解读、项目表达、技术问答可以独立迭代，Agent 只负责根据上下文选择合适的 Skill，相当于一个轻量的能力编排层。

当前代码中的最小实现：

- `agent_v2_reasoning.py` 已注册 `UseSkill` 工具。
- Agent 可以读取 `skills/<skill-name>/SKILL.md`，把对应任务流程作为工具观察结果使用。
- 这是轻量实现，后续可以继续扩展为 Skill 参数校验、输出模板和执行结果追踪。
- `SearchMemory` 已接入 `memory_store.py`，会尝试通过 Mem0/Qdrant 查询本地长期记忆。
- `OptimizeGraph` 已接入 `memory_optimizer.py` 的 dry-run 模式，会返回相似实体候选但不会自动合并。
- trace 中会保存 `tool_calls`，便于复盘 Agent 实际调用过哪些工具。

## 7. 项目讲法

问题：

> 普通聊天机器人没有稳定长期记忆，也缺少可复用任务能力。RAG 通常只会召回文本，难以管理用户上下文、团队任务偏好、历史问题、项目关系和多跳逻辑。

方案：

> 我把系统拆成三层：向量记忆负责语义召回，Neo4j 图谱记忆负责实体关系和路径推理，Skill 负责可复用任务流程；再用 ReAct Agent 作为调度层，让模型根据任务选择查记忆、优化图谱或调用某个 Skill。

难点：

> 本地 BGE-M3 embedding 和 Mem0 默认向量维度不一致，导致链路无法直接跑通。我写了 Zero-Padding Adapter，在不改 Mem0 主体逻辑的情况下完成兼容。

结果：

> Agent 能完成基于用户上下文的知识工作流规划、论文解读、工具调用、推理轨迹记录、图谱实体归并和路径解释，形成了一个本地化、可调试、可扩展的长期记忆 Agent Runtime 原型。

## 8. 项目 bullet 建议

- 基于 LangChain ReAct 架构构建本地化长期记忆 Agent，将用户问题动态路由到向量记忆检索、图谱记忆优化和路径分析工具。
- 面向企业知识助手和研发知识工作流场景，将用户上下文、项目知识关系和任务历史结合，支持个性化知识问答与工作流规划。
- 集成 Mem0、Qdrant、Neo4j、Ollama 和 BGE-M3，实现用户偏好、项目上下文和知识关系的混合记忆存储。
- 设计 Skill 能力包机制，将知识工作流规划、论文解读、项目表达和技术问答拆分为可复用任务模块，降低 Prompt 耦合并提升 Agent 可维护性。
- 抽象出可迁移的企业知识 Agent 架构，可扩展到研发知识库、售前支持、企业内训、技术支持和内部文档问答等场景。
- 设计 Zero-Padding Adapter，将 BGE-M3 1024 维向量补齐适配至 1536 维 schema，解决本地 embedding 与 Mem0 默认向量配置不兼容问题。
- 基于 Neo4j APOC 实现实体归并思路，通过语义相似度候选召回和 LLM 判定降低长期记忆中的节点冗余。
- 记录 Agent 推理轨迹，沉淀 Thought/Action/Observation/Final Answer 分析样例，用于 Badcase 复盘和 Prompt/工具策略优化。

## 9. 服务器验证清单

- `python --version` 为 3.11。
- `ollama list` 中存在 `qwen2.5:7b` 和 `bge-m3:latest`。
- Neo4j Bolt 端口 `7687` 可访问。
- Neo4j 密码与代码配置一致。
- APOC 插件可用。
- `python hybrid_agent_padding_final.py` 能成功写入 Mem0/Qdrant 和 Neo4j。
- `python agent_v2_reasoning.py` 能生成或更新 `agent_reasoning_traces.json`。
- `python memory_optimizer.py` 能完成示例实体治理输出。

## 10. 后续优化建议

为了让项目更像生产级 AI 应用，可以继续补三件事：

- 将 `OptimizeGraph` 继续增强为向量相似度 + LLM 二次判定，降低纯字符串相似度误合并风险。
- 将 `UseSkill` 扩展为带输入参数校验、输出模板和执行结果记录的 Skill runtime。
- Trace 继续增强：捕获完整 ReAct Thought/Action/Observation，形成可调试的 Agent 运行记录。
