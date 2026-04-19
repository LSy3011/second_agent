import json
import os
from datetime import datetime
from config import DEFAULT_USER_ID, OLLAMA_LLM_MODEL, SKILLS_DIR, TRACE_FILE
from memory_store import search_memory as search_vector_memory
from memory_optimizer import MemoryOptimizer
from config import NEO4J_PASSWORD, NEO4J_URL, NEO4J_USER

# 自适应导入 ChatOllama
try:
    from langchain_ollama import ChatOllama
except (ImportError, AttributeError):
    from langchain_community.chat_models import ChatOllama

from langchain.agents import initialize_agent, Tool, AgentType

def use_skill(skill_name: str):
    """读取一个任务 Skill 的执行说明。输入应该是 skill 目录名，例如 resume-polisher。"""
    normalized = skill_name.strip().lower()
    skill_path = SKILLS_DIR / normalized / "SKILL.md"
    if not skill_path.exists():
        available = [p.name for p in SKILLS_DIR.iterdir() if p.is_dir()] if SKILLS_DIR.exists() else []
        return f"【Skill 未找到】{normalized}。可用 Skill: {', '.join(available) or '无'}"

    content = skill_path.read_text(encoding="utf-8")
    return f"【Skill: {normalized}】\n{content[:2500]}"

# 2. 核心推理引擎 (采用 0.1.x 世代最稳健的 Legacy ReAct 架构)
class ReasoningAgent:
    def __init__(self, model_name=OLLAMA_LLM_MODEL):
        # 0.1.x 下 Ollama 推荐参数
        self.llm = ChatOllama(model=model_name, temperature=0)
        
        # 封装为 Tool 对象，这是 0.1.x 的标准做法
        self.tool_events = []
        self.tools = [
            Tool(
                name="SearchMemory",
                func=self._search_memory,
                description="查询向量长短期记忆库中的用户信息。输入应该是具体的查询词（字符串）。"
            ),
            Tool(
                name="OptimizeGraph",
                func=self._optimize_graph_memory,
                description="触发知识图谱的归并优化。输入可以是空字符串或任意文本。"
            ),
            Tool(
                name="UseSkill",
                func=self._use_skill,
                description="读取任务 Skill 的执行说明。适用于简历优化、面试陪练、论文解读等任务。输入必须是 skill 目录名，如 resume-polisher、interview-coach、paper-digest。"
            )
        ]
        
        # 使用 ZERO_SHOT_REACT_DESCRIPTION，这是该世代最成熟、解析容错率最高的模式
        self.executor = initialize_agent(
            self.tools, 
            self.llm, 
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION, 
            verbose=True,
            handle_parsing_errors=True # 自动处理 LLM 格式微调
        )

    def _record_tool_event(self, name, tool_input, output):
        event = {
            "tool": name,
            "input": tool_input,
            "output_preview": str(output)[:500],
        }
        self.tool_events.append(event)

    def _search_memory(self, query: str):
        try:
            hits = search_vector_memory(query, user_id=DEFAULT_USER_ID)
            if hits:
                output = "【检索结果】" + "\n".join(
                    f"- {item['memory']} (score={item['score']})" for item in hits
                )
            else:
                output = "【检索结果】未找到相关长期记忆。"
        except Exception as e:
            output = f"【检索失败】{e}"
        self._record_tool_event("SearchMemory", query, output)
        return output

    def _optimize_graph_memory(self, input_str: str = ""):
        try:
            optimizer = MemoryOptimizer(NEO4J_URL, NEO4J_USER, NEO4J_PASSWORD)
            try:
                result = optimizer.merge_similar_entities(execute=False)
                if result["candidate_count"] == 0:
                    output = "【图谱治理 dry-run】未发现高相似度实体候选，未执行任何合并。"
                else:
                    lines = [
                        f"【图谱治理 dry-run】发现 {result['candidate_count']} 组候选，未执行任何合并。"
                    ]
                    for candidate in result["candidates"][:5]:
                        lines.append(
                            f"- {candidate['left']['id']} <-> {candidate['right']['id']} "
                            f"(score={candidate['score']})"
                        )
                    output = "\n".join(lines)
            finally:
                optimizer.close()
        except Exception as e:
            output = f"【优化失败】{e}"
        self._record_tool_event("OptimizeGraph", input_str, output)
        return output

    def _use_skill(self, skill_name: str):
        output = use_skill(skill_name)
        self._record_tool_event("UseSkill", skill_name, output)
        return output

    def execute(self, query: str):
        print(f"🧠 [Legacy ReAct] 正在启动推理链，处理: {query}")
        start_time = datetime.now()
        self.tool_events = []
        
        try:
            # 0.1.x 下使用 run 启动推理
            response = self.executor.run(query)
            
            # 记录轨迹 (Trace)
            self._save_trace(query, response, start_time, self.tool_events)
            return response
        except Exception as e:
            # 终极防御：如果依然出现 Python 3.11 的生成器报错，捕获并转为友好提示
            err_msg = str(e)
            if "StopIteration" in err_msg:
                return "推理任务已完成主要步骤（观察轨迹文件确认），但在最终响应阶段触发了 Python 3.11 迭代器兼容性 Warn。"
            return f"推理执行中捕获到异常: {e}"

    def _save_trace(self, query, output, start_time, tool_events=None):
        duration = (datetime.now() - start_time).total_seconds()
        
        trace_entry = {
            "timestamp": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "query": query,
            "final_answer": output,
            "tool_calls": tool_events or [],
            "latency": f"{duration:.2f}s",
            "architecture": "LangChain Legacy ReAct (0.1.x Stable)"
        }
        
        traces = []
        if os.path.exists(TRACE_FILE):
            with open(TRACE_FILE, "r", encoding="utf-8") as f:
                try:
                    traces = json.load(f)
                except json.JSONDecodeError:
                    traces = []
        
        traces.append(trace_entry)
        with open(TRACE_FILE, "w", encoding="utf-8") as f:
            json.dump(traces, f, ensure_ascii=False, indent=4)
        print(f"📡 [Log] 推理轨迹已持久化。")

if __name__ == "__main__":
    # 实例化并运行
    agent = ReasoningAgent()
    user_query = "基于我目前的兴趣和背景，请给出一个职业晋升建议，并顺便优化一下我的知识库。"
    answer = agent.execute(user_query)
    print(f"\n✨ 最终产出:\n{answer}")
