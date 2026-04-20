import json
import argparse
import warnings
from datetime import datetime

from config import DEFAULT_USER_ID, NEO4J_PASSWORD, NEO4J_URL, NEO4J_USER, OLLAMA_LLM_MODEL, SKILLS_DIR, TRACE_FILE
from memory_optimizer import MemoryOptimizer
from memory_store import close_memory, search_memory as search_vector_memory

try:
    from langchain_core._api import LangChainDeprecationWarning
except Exception:
    LangChainDeprecationWarning = DeprecationWarning

warnings.filterwarnings("ignore", category=LangChainDeprecationWarning)
warnings.filterwarnings("ignore", message=".*LangChain agents.*")
warnings.filterwarnings("ignore", message=".*Chain.run.*")

try:
    from langchain_ollama import ChatOllama
except (ImportError, AttributeError):
    from langchain_community.chat_models import ChatOllama

from langchain.agents import AgentType, Tool, initialize_agent


def use_skill(skill_name: str):
    """Read a task skill instruction file by directory name."""
    normalized = skill_name.strip().lower()
    skill_path = SKILLS_DIR / normalized / "SKILL.md"
    if not skill_path.exists():
        available = [p.name for p in SKILLS_DIR.iterdir() if p.is_dir()] if SKILLS_DIR.exists() else []
        return f"[Skill not found] {normalized}. Available skills: {', '.join(available) or 'none'}"

    content = skill_path.read_text(encoding="utf-8")
    return f"[Skill: {normalized}]\n{content[:2500]}"


class ReasoningAgent:
    def __init__(self, model_name=OLLAMA_LLM_MODEL, verbose=False):
        self.llm = ChatOllama(model=model_name, temperature=0)
        self.tool_events = []
        self.tools = [
            Tool(
                name="SearchMemory",
                func=self._search_memory,
                description=(
                    "Search the user's long-term vector memory. "
                    "Input should be a concrete search query string."
                ),
            ),
            Tool(
                name="OptimizeGraph",
                func=self._optimize_graph_memory,
                description=(
                    "Run a dry-run knowledge graph entity cleanup check. "
                    "Input can be an empty string or a short task description."
                ),
            ),
            Tool(
                name="UseSkill",
                func=self._use_skill,
                description=(
                    "Read a task Skill instruction. Use this for enterprise knowledge workflows, "
                    "paper digest, career advancement, resume polishing, and interview coaching tasks. "
                    "Input must be a skill directory name, such as knowledge-workflow, paper-digest, "
                    "career-advancement, resume-polisher, or interview-coach."
                ),
            ),
        ]

        self.executor = initialize_agent(
            self.tools,
            self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=verbose,
            handle_parsing_errors=True,
        )

    def _record_tool_event(self, name, tool_input, output):
        self.tool_events.append(
            {
                "tool": name,
                "input": tool_input,
                "output_preview": str(output)[:500],
            }
        )

    def _search_memory(self, query: str):
        try:
            hits = search_vector_memory(query, user_id=DEFAULT_USER_ID)
            if hits:
                output = "[Search results]\n" + "\n".join(
                    f"- {item['memory']} (score={item['score']})" for item in hits
                )
            else:
                output = "[Search results] No related long-term memory found."
        except Exception as exc:
            output = f"[Search failed] {exc}"
        self._record_tool_event("SearchMemory", query, output)
        return output

    def _optimize_graph_memory(self, input_str: str = ""):
        try:
            optimizer = MemoryOptimizer(NEO4J_URL, NEO4J_USER, NEO4J_PASSWORD)
            try:
                result = optimizer.merge_similar_entities(execute=False)
                if result["candidate_count"] == 0:
                    output = "[Graph cleanup dry-run] No high-similarity entity candidates found."
                else:
                    lines = [
                        f"[Graph cleanup dry-run] Found {result['candidate_count']} candidates. "
                        "No merge was executed."
                    ]
                    for candidate in result["candidates"][:5]:
                        lines.append(
                            f"- {candidate['left']['id']} <-> {candidate['right']['id']} "
                            f"(score={candidate['score']})"
                        )
                    output = "\n".join(lines)
            finally:
                optimizer.close()
        except Exception as exc:
            output = f"[Graph cleanup failed] {exc}"
        self._record_tool_event("OptimizeGraph", input_str, output)
        return output

    def _use_skill(self, skill_name: str):
        output = use_skill(skill_name)
        self._record_tool_event("UseSkill", skill_name, output)
        return output

    def execute(self, query: str):
        print("=== Second Agent 推理演示 ===")
        print(f"任务: {query}")
        start_time = datetime.now()
        self.tool_events = []

        try:
            response = self.executor.run(query)
            self._save_trace(query, response, start_time, self.tool_events)
            self.print_tool_summary()
            return response
        except Exception as exc:
            err_msg = str(exc)
            if "StopIteration" in err_msg:
                return (
                    "The reasoning task completed the main steps, but the final response stage hit "
                    "a Python 3.11 iterator compatibility warning. Check the trace file for details."
                )
            return f"Reasoning failed: {exc}"

    def _save_trace(self, query, output, start_time, tool_events=None):
        duration = (datetime.now() - start_time).total_seconds()
        trace_entry = {
            "timestamp": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "query": query,
            "final_answer": output,
            "tool_calls": tool_events or [],
            "latency": f"{duration:.2f}s",
            "architecture": "LangChain Legacy ReAct with Mem0, Neo4j, and Skill tools",
        }

        traces = []
        if TRACE_FILE.exists():
            try:
                traces = json.loads(TRACE_FILE.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                traces = []

        traces.append(trace_entry)
        TRACE_FILE.write_text(json.dumps(traces, ensure_ascii=False, indent=4), encoding="utf-8")
        print(f"轨迹文件: {TRACE_FILE}")

    def print_tool_summary(self):
        if not self.tool_events:
            print("工具调用: 无")
            return

        print("\n--- 工具调用摘要 ---")
        for idx, event in enumerate(self.tool_events, start=1):
            print(f"{idx}. {event['tool']}")
            print(f"   输入: {event['input']}")
            preview = event["output_preview"].replace("\n", "\n   ")
            print(f"   输出预览: {preview}")


def parse_args():
    parser = argparse.ArgumentParser(description="Run the Second Agent reasoning demo")
    parser.add_argument("--verbose", action="store_true", help="show raw LangChain ReAct trace")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    agent = ReasoningAgent(verbose=args.verbose)
    user_query = (
        "请基于当前 Paper Assistant 与 Second Agent 的能力，使用 knowledge-workflow skill "
        "设计一个面向企业研发团队的本地化知识助手工作流。请严格按照以下 6 个部分输出："
        "1. 业务场景与用户；2. 知识服务设计；3. 记忆与个性化设计；"
        "4. Tool/MCP 集成计划；5. Skill 工作流设计；6. 可靠性与评估清单。"
        "如果需要，请顺便做一次知识图谱 dry-run 优化检查。"
    )
    try:
        answer = agent.execute(user_query)
        print(f"\n=== 最终输出 ===\n{answer}")
    finally:
        close_memory()
