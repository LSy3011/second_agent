# 项目运行与数据分析指南 (Second Agent)

## 1. 快速运行脚本清单

| 脚本名称 | 功能说明 | 运行命令 | 生成数据 |
| :--- | :--- | :--- | :--- |
| `agent_v2_reasoning.py` | **ReAct 推理链路测试** | `python agent_v2_reasoning.py` | `agent_reasoning_traces.json` |
| `memory_optimizer.py` | 图谱自愈与消歧优化 | `python memory_optimizer.py` | 终端日志输出 |
| `app.py` | Streamlit 交互界面 | `streamlit run app.py` | 交互式实时图谱 |

## 2. 数据产出与分析步骤

### 步骤 A：分析推理轨迹 (Traces)
运行 `agent_v2_reasoning.py` 后，打开 `agent_reasoning_traces.json`：
- 查看 `thought` 字段：Agent 是否正确识别了需要查询 Neo4j 还是向量库？
- 查看 `observation` 字段：检索到的信息是否足以支撑 `final_answer`？
- **面试点**：在面试时，你可以拿着这个 JSON 文件解释具体的 Agent 的决策链路（Case Study）。

### 步骤 B：解决维度冲突
如果你直接运行 `mem0` 报错，请务必使用项目中的逻辑（含 `OllamaEmbedding.embed` 的 Monkey Patch），这是解决本地模型不兼容的核心技术亮点。

## 3. 上传与反馈
运行产生的 `agent_reasoning_traces.json` 是非常有价值的“Badcase”来源。如果你发现回复不准确，请将该文件数据发给我，我会帮你调整 ReAct 的 Prompt 模版。
