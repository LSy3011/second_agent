# MCP 与 Skill 扩展设计

## 1. 总体背景重塑

这两个项目可以统一包装成一条更完整的 AI 应用工程链路：

```text
Paper Assistant
  -> 面向论文、技术报告、内部文档的知识服务层
  -> 负责把非结构化资料变成可检索、可解释、可调用的知识库

Second Agent
  -> 面向个人成长、科研调研、面试准备的 Agent 执行层
  -> 负责结合长期记忆、任务 Skill 和外部工具完成具体任务
```

简历里可以把它们写成两个项目，也可以在面试时讲成一个组合架构：

> 我先做了一个本地论文知识服务平台，把 PDF 论文转成 GraphRAG 知识库；随后又做了一个长期记忆 Agent，把用户背景、项目经历和学习目标沉淀到向量记忆与知识图谱中，并通过 Skill 和 MCP 调用外部知识服务，形成从知识构建到 Agent 执行的闭环。

更贴近公司业务的包装方式，是把它升级成“垂直行业可信顾问 Agent 平台”：

```text
行业资料/专家经验/案例数据
  -> Paper Assistant 负责沉淀成可检索知识服务
  -> MCP 负责把知识服务暴露给 Agent
  -> Second Agent 负责记住用户画像和目标
  -> Skill 负责不同业务场景的任务流程
  -> 最终交付个性化建议、方案生成、复盘和转化
```

这个定位比“我做了一个论文 RAG + 一个记忆 Agent”更像公司会买单的产品，因为它解决的是信息差、专家经验规模化、个性化交付和咨询服务降本。

## 2. MCP 放在哪里最合适

MCP 更适合放在 Paper Assistant。

原因：

- Paper Assistant 已经有明确的数据资产：论文 PDF、索引、知识图谱、评估结果。
- MCP 的价值是把这些能力暴露成标准工具，供外部 Agent 调用。
- 它能把 Paper Assistant 从“一个 Web demo”升级成“一个可被复用的知识服务”。

建议 MCP 工具：

```text
paper_search(query, top_k)
  检索论文片段，返回来源、片段、排序依据。

paper_ask(question, mode)
  调用 LightRAG，支持 local/global/hybrid 模式。

graph_neighbors(entity, depth)
  查询某个技术实体的图谱邻居，辅助解释技术关系。

list_papers()
  返回当前知识库内的论文列表。
```

已补充工具契约模板：

```text
docs/mcp_tool_contracts/paper_assistant_mcp_tools.md
```

MCP 在简历里的表达：

- 将本地论文 GraphRAG 能力封装为 MCP 工具服务，使外部 Agent 能通过标准协议调用论文检索、问答和图谱查询能力。
- 通过 MCP 将知识库能力与 Agent runtime 解耦，使论文知识服务可被 IDE Agent、面试准备 Agent 和自动调研工作流复用。

## 3. Skill 放在哪里最合适

Skill 更适合放在 Second Agent。

原因：

- Second Agent 的核心是“根据用户目标执行任务”，而不是只提供知识查询。
- Skill 可以把任务流程模块化，例如简历优化、面试陪练、论文解读。
- Skill 可以调用记忆和工具，但本身不负责存储数据。

建议 Skill 目录：

```text
skills/
├── resume-polisher/
│   └── SKILL.md
├── interview-coach/
│   └── SKILL.md
└── paper-digest/
    └── SKILL.md
```

Skill 模板已放在当前项目：

```text
skills/resume-polisher/SKILL.md
skills/interview-coach/SKILL.md
skills/paper-digest/SKILL.md
```

`resume-polisher` 示例：

```markdown
---
name: resume-polisher
description: Use when the agent needs to rewrite project experience, produce resume bullets, or tailor AI application engineer resumes based on user memory and target JD.
---

# Resume Polisher

1. Read the target role and user project memory.
2. Extract project impact, technical stack, engineering difficulty, and measurable outcomes.
3. Produce Chinese resume bullets first.
4. Add interview talking points using Problem-Solution-Difficulty-Result.
5. Avoid exaggerating unverified production metrics.
```

`interview-coach` 示例：

```markdown
---
name: interview-coach
description: Use when the agent needs to prepare AI application engineer interviews, generate likely questions, simulate follow-up questions, or build answer frameworks from user projects.
---

# Interview Coach

1. Identify the target position and company style if provided.
2. Select relevant memories and project facts.
3. Generate questions around RAG, Agent, MCP, vector database, graph database, evaluation, and deployment.
4. For each answer, use background, design, tradeoff, failure handling, and measurable result.
5. Include follow-up questions an interviewer may ask.
```

`paper-digest` 示例：

```markdown
---
name: paper-digest
description: Use when the agent needs to summarize papers, compare methods, extract technical claims, or call Paper Assistant/MCP tools for literature review.
---

# Paper Digest

1. Clarify the research question.
2. Call paper_search or paper_ask if MCP tools are available.
3. Extract problem, method, experiment setup, result, limitation, and reusable idea.
4. Compare papers by method, dataset, metric, and engineering implication.
5. Output a concise review that can be reused in notes or interviews.
```

Skill 在简历里的表达：

- 设计轻量 Skill 机制，将简历优化、面试陪练、论文解读拆分为可复用能力包，由 ReAct Agent 根据用户目标动态选择。
- 通过 Skill 将任务流程从大 Prompt 中解耦，提升 Agent 的可维护性、可扩展性和可调试性。

## 4. 两个项目如何联动

联动方式：

```text
用户问：帮我准备 AI 应用工程师面试，重点讲 GraphRAG 和 Agent。

Second Agent:
  1. 查询用户长期记忆，找到 Paper Assistant 和 Second Agent 项目经历。
  2. 调用 resume-polisher Skill，生成简历描述。
  3. 调用 interview-coach Skill，生成面试问答。
  4. 通过 MCP 调用 Paper Assistant，补充 GraphRAG 论文和技术细节。
  5. 保存本次准备结果和用户反馈到记忆系统。
```

这个联动让两个项目有真实业务闭环：

- Paper Assistant 提供可信知识。
- Second Agent 理解用户目标。
- Skill 负责结构化任务流程。
- MCP 负责跨系统工具调用。
- 记忆系统负责长期个性化。

当前代码落地点：

- `Paper Assistant` 已提供 `paper_assistant/mcp_server.py`，包含 `list_papers`、`paper_search`、`paper_ask`、`graph_neighbors` 的最小工具入口。
- `Second Agent` 已提供 `UseSkill` 工具，可读取 `skills/*/SKILL.md`。
- `Second Agent` 的 `SearchMemory` 已接入 Mem0/Qdrant 查询路径，并将工具调用记录到 trace。
- `Second Agent` 的 `OptimizeGraph` 已接入 Neo4j dry-run 实体候选召回，默认不会自动合并节点。

## 5. 推荐最终简历项目背景

### 项目一：本地论文知识服务平台

项目背景：

> 面向科研调研和技术路线分析场景，构建本地化论文知识服务平台，将 PDF 论文解析为结构化知识库，并通过 GraphRAG、知识图谱可视化和 MCP 工具接口提供可复用的论文检索与问答能力。

项目亮点：

- Docling 语义解析 + LightRAG 混合检索。
- 图谱可视化 + RAG 评估闭环。
- MCP 工具化暴露，支持外部 Agent 调用。
- 长论文本地推理稳定性排障。

### 项目二：长期记忆职业成长 Agent

项目背景：

> 面向个人学习、项目复盘和 AI 应用工程师面试准备场景，构建带长期记忆的本地 Agent，将用户背景、项目经历和目标岗位沉淀为向量记忆与图谱记忆，并通过 ReAct 和 Skill 机制完成简历优化、面试陪练和论文解读任务。

项目亮点：

- Mem0 + Qdrant + Neo4j 混合记忆。
- ReAct 工具调用和推理轨迹记录。
- Skill 能力包机制。
- BGE-M3 与 Mem0 向量维度兼容性修复。

## 6. 面试时的总叙事

可以这样讲：

> 这两个项目不是两个重复的 RAG demo。我把第一个项目定位为知识服务层，解决非结构化论文如何被解析、索引、评估和工具化调用；第二个项目定位为 Agent 执行层，解决 Agent 如何记住用户、选择工具、调用 Skill 并沉淀推理轨迹。MCP 负责把知识服务标准化暴露，Skill 负责把任务能力模块化，所以整体架构更接近真实 AI 应用系统。

## 7. 公司落地场景：职业规划/求职辅导

这是最适合你当前项目的商业化方向，因为它和“简历、面试、项目包装、行业信息差”天然贴合。

### 7.1 业务背景

市面上很多职业规划、求职辅导和面试陪跑服务，本质上依赖三类资产：

- 信息差：岗位要求、公司偏好、面试流程、薪资区间、行业趋势。
- 专家经验：如何包装项目、如何回答追问、如何解释技术难点。
- 个性化判断：用户背景不同，简历和面试策略不能一套模板打天下。

这些服务的问题是专家交付成本高、质量不稳定、知识沉淀弱。你的系统可以包装成一个 AI 职业规划 Copilot：把专家经验和岗位知识沉淀成知识库，再用长期记忆 Agent 给用户做持续辅导。

### 7.2 产品形态

```text
岗位 JD / 面经 / 公司信息 / 行业报告 / 用户简历 / 项目经历
  -> 知识服务层：岗位知识库、面试题库、行业趋势库
  -> 用户记忆层：教育背景、技术栈、项目经历、目标岗位、薄弱点
  -> Skill 层：简历优化、模拟面试、项目复盘、投递策略、Offer 决策
  -> 输出：简历 bullet、面试回答、学习计划、投递列表、复盘报告
```

### 7.3 可做的 Skill

```text
resume-polisher       简历优化
interview-coach       面试陪练
jd-analyzer           岗位 JD 拆解
project-story-builder 项目故事线包装
career-roadmap        职业路线规划
offer-advisor         Offer 对比和决策
```

### 7.4 可做的 MCP 工具

```text
job_search(query, city, level)
  检索岗位，提取共性要求。

jd_analyze(jd_text)
  分析岗位技能要求、隐性要求和简历匹配点。

interview_case_search(company, role)
  查询公司/岗位相关面经。

salary_reference(role, city, years)
  返回薪资参考区间和影响因素。
```

### 7.5 商业价值

- 降低职业顾问的重复劳动，把“简历初改、JD 匹配、基础问答”自动化。
- 将专家经验沉淀成结构化知识库，避免顾问离职后经验流失。
- 用长期记忆跟踪用户成长路径，支持持续服务和复购。
- 可以从 C 端求职辅导扩展到 B 端高校就业中心、培训机构、企业内转岗平台。

### 7.6 面试表达

> 我把这个项目进一步抽象成职业规划 Agent。传统求职辅导依赖顾问经验和信息差，但交付成本高、标准化弱。我用 RAG/MCP 把岗位知识、面经和行业信息沉淀成可调用知识服务，用长期记忆记录用户背景和目标，再用 Skill 拆分简历优化、模拟面试、JD 分析等任务流程。这样既能做个性化交付，也能把专家经验规模化。

## 8. 可迁移场景：旅游顾问 Agent

旅游场景和职业规划很像，也依赖信息差和个性化偏好。

### 8.1 业务背景

旅游规划服务依赖目的地经验、预算判断、路线设计、避坑经验和实时约束。用户真正需要的不是“景点列表”，而是根据预算、时间、同行人、体力、偏好生成可执行行程。

### 8.2 架构映射

```text
目的地攻略 / 酒店政策 / 景点信息 / 交通规则 / 用户偏好
  -> 旅游知识库
  -> MCP 暴露景点查询、路线查询、预算估算
  -> 用户记忆记录预算、偏好、忌口、同行人、历史旅行反馈
  -> Skill 生成行程、避坑清单、预算表、每日路线
```

### 8.3 可做 Skill

```text
trip-planner       多日行程规划
budget-estimator   预算估算
local-guide        本地避坑和餐饮推荐
family-trip        亲子/家庭旅行适配
travel-reviewer    行程复盘和下次偏好更新
```

### 8.4 简历表达

> 该架构可迁移到旅游规划场景，通过目的地知识库 + 用户长期偏好记忆 + 行程规划 Skill，为用户生成个性化、可执行、可复盘的旅行方案。

## 9. 可迁移场景：美妆/护肤顾问 Agent

美妆护肤也是典型的信息差行业，用户愿意为“少踩坑、适合我”付费。

### 9.1 业务背景

用户买护肤品时面对大量成分、肤质、功效、价格和营销信息，很难判断什么适合自己。专业博主和柜姐提供建议，但存在主观性、利益相关和不可规模化问题。

### 9.2 架构映射

```text
产品成分表 / 用户肤质 / 过敏史 / 使用反馈 / 达人测评 / 皮肤科知识
  -> 产品和成分知识库
  -> MCP 暴露成分查询、产品对比、风险提示
  -> 用户记忆记录肤质、预算、过敏源、历史使用效果
  -> Skill 生成护肤方案、产品对比、购买建议、使用复盘
```

### 9.3 可做 Skill

```text
skin-profile-builder  肤质画像构建
ingredient-checker    成分风险分析
routine-planner       护肤流程规划
product-comparator    产品对比
feedback-tracker      使用反馈追踪
```

### 9.4 简历表达

> 该架构可迁移到美妆护肤场景，通过成分知识库、用户肤质记忆和产品对比 Skill，为用户提供个性化护肤建议和风险提示。

## 10. 其他可扩展行业

这套架构适合“知识密集 + 个性化 + 高信息差 + 可持续服务”的行业：

```text
教育升学：志愿填报、留学申请、课程规划
保险顾问：产品条款解释、家庭风险画像、方案对比
法律咨询：合同审查、案例检索、风险提示
医疗健康：慢病管理、体检报告解读、健康习惯追踪
房产顾问：城市板块分析、预算匹配、购房风险提示
B2B 销售：客户画像、话术生成、商机推进策略
企业内训：岗位能力模型、学习路径、员工成长建议
```

选场景时，优先考虑三点：

- 是否有大量非结构化知识需要沉淀。
- 是否需要长期用户画像。
- 是否能通过 Skill 形成稳定交付流程。

## 11. 更适合简历的最终定位

如果你面试 AI 应用工程师，建议不要只写“职业规划 Agent”，可以写得更抽象、更企业化：

> 垂直行业可信顾问 Agent 平台：基于 RAG/MCP 构建行业知识服务层，基于长期记忆构建用户画像层，基于 Skill 构建可复用任务交付层，可迁移到职业规划、旅游规划、美妆护肤等高信息差咨询场景。

这个标题的好处是：

- 不局限于求职辅导，显得产品想象力更大。
- 能解释为什么需要 MCP：跨系统调用行业知识服务。
- 能解释为什么需要 Skill：不同业务场景有不同交付流程。
- 能解释为什么需要记忆：个性化服务和长期复购。
