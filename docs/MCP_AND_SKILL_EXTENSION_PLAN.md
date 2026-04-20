# MCP 与 Skill 扩展设计

## 1. 总体定位

这两个项目可以组合成一套“企业私有知识库 + 长期记忆 Agent + Skill 工作流”的 Agentic RAG 架构。

```text
Paper Assistant
  -> 知识服务层
  -> 负责把论文、技术报告、研发文档、产品资料和内部知识库转成可检索、可问答、可视化、可被 Agent 调用的知识服务

Second Agent
  -> Agent 执行层
  -> 负责记录用户/团队上下文、选择工具、调用 Skill、保存推理轨迹并完成具体任务工作流
```

AI 应用工程师求职准备可以作为一个验证样例，但不作为项目本身的业务背景。更稳妥的项目背景是：

> 面向企业私有知识场景，构建本地化 Agentic RAG 系统：底层将非结构化文档沉淀为可调用知识服务，上层 Agent 结合长期记忆和 Skill 工作流完成研发知识问答、技术调研、售前支持、内部培训和文档分析等任务。

## 2. MCP 放在 Paper Assistant

MCP 更适合放在 Paper Assistant，因为 Paper Assistant 已经有稳定的知识资产和查询能力：

- PDF 与长文档解析。
- LightRAG 向量索引与知识图谱索引。
- GraphRAG 问答。
- GraphML 图谱可视化。
- Streamlit 人工交互入口。

MCP 的作用是把这些能力标准化暴露给外部 Agent，让上层系统不需要关心 LightRAG 索引目录、Ollama 调用方式和图谱文件结构。

当前工具：

```text
list_papers()
  返回当前知识库中的文档列表。

paper_search(query, top_k)
  对已处理文本做轻量检索，适合作为低成本 fallback。

paper_ask(question, mode)
  调用 LightRAG，支持 local/global/hybrid 查询。

graph_neighbors(entity, depth)
  基于 GraphML 查询实体邻居，辅助解释技术关系。
```

当前实现位置：

```text
F:\paper_assistant_backup\paper_assistant\mcp_server.py
F:\paper_assistant_backup\docs\mcp_tool_contracts\paper_assistant_mcp_tools.md
```

实现状态：

- 已支持 CLI fallback，服务器上可直接运行验证。
- 已支持 FastMCP 注册逻辑，安装 MCP SDK 后可作为 MCP Server 暴露工具。
- 下一步可补充正式 MCP client，与 Second Agent 自动联动。

## 3. Skill 放在 Second Agent

Skill 更适合放在 Second Agent，因为 Second Agent 的核心是“根据用户目标执行任务”，而不是只提供知识查询。

Skill 的作用：

- 把任务流程从大 Prompt 中拆出来。
- 让不同工作流可以独立迭代。
- 让 Agent 根据任务选择合适的能力包。
- 为后续参数校验、输出模板、执行结果追踪打基础。

当前推荐 Skill：

```text
knowledge-workflow
  企业知识工作流规划，适合研发知识助手、内部文档问答、售前知识支持。

paper-digest
  论文解读、方法对比、技术 claim 提取。

resume-polisher / interview-coach / career-advancement
  可选个人效率与求职准备验证样例，不作为项目主背景。
```

当前实现位置：

```text
skills/
agent_v2_reasoning.py
```

实现状态：

- `UseSkill` 已注册为 LangChain Tool。
- Agent 可以读取 `skills/<skill-name>/SKILL.md`。
- 工具调用会记录到 trace，便于复盘。
- 下一步可把 Skill 扩展为 `SKILL.md + input_schema.json + output_template.md + examples.json`。

## 4. 两个项目如何联动

理想链路：

```text
用户问题：
  帮我分析某个研发主题，并形成团队内部知识工作流。

Second Agent:
  1. SearchMemory 查询用户/团队上下文。
  2. UseSkill 调用 knowledge-workflow，确定任务结构。
  3. 通过 MCP 调用 Paper Assistant 的 paper_ask 或 graph_neighbors。
  4. 汇总知识库结果、长期记忆和任务约束。
  5. 输出工作流方案、风险清单和评估指标。
  6. 保存本次任务 trace，必要时更新长期记忆。
```

这让两个项目的边界非常清晰：

- Paper Assistant 提供可信知识。
- MCP 负责跨系统工具调用。
- Second Agent 负责上下文、记忆和工具调度。
- Skill 负责结构化任务流程。
- Trace 负责可调试和可复盘。

## 5. 推荐项目表达

Paper Assistant：

> 面向科研调研和企业技术知识管理场景，构建本地化 GraphRAG 知识服务，将 PDF 论文和长文档解析为文本块、实体和关系图谱，并通过 Streamlit、MCP/CLI 和 GraphML 可视化提供可复用的知识查询能力。

Second Agent：

> 面向企业知识助手和研发知识工作流场景，构建本地化长期记忆 Agent Runtime，融合 Mem0/Qdrant 向量记忆、Neo4j 图谱记忆、LangChain ReAct 工具调用和 Skill 工作流，实现可追踪、可扩展的个性化任务执行。

组合叙事：

> 我把系统拆成知识服务层和 Agent 执行层。Paper Assistant 负责把非结构化资料沉淀成可检索、可问答、可工具化调用的知识服务；Second Agent 负责长期记忆、工具选择和 Skill 工作流。MCP 解决跨系统工具调用，Skill 解决任务流程模块化，因此整体更接近真实企业 Agentic RAG 应用，而不是单一 RAG demo。

## 6. 可迁移业务场景

优先选择“私有知识密集 + 需要长期上下文 + 需要稳定交付流程”的场景：

```text
研发知识助手：论文、技术报告、代码设计文档、故障复盘。
售前知识支持：产品资料、客户案例、竞品分析、方案库。
企业内训：课程资料、岗位能力模型、员工学习路径。
技术支持：FAQ、工单、故障手册、历史解决方案。
投研/行业研究：研报、公告、新闻、公司资料。
法务/合规辅助：合同模板、法规条款、内部制度。
```

求职准备、简历优化和面试陪练可以作为个人验证样例。对外解释时可以说：

> 我用求职准备做过验证，因为它天然需要长期记忆、项目理解、知识检索和结构化输出。但系统并没有绑定到求职场景，而是抽象成了私有知识服务 + 长期记忆 Agent + Skill 工作流，换知识库和 Skill 后可以迁移到研发、售前、培训和技术支持等企业场景。
