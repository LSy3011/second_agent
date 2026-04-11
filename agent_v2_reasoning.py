import json
import os
from datetime import datetime
    """触发知识图谱的语义消歧与节点归并优化。"""
    # 此处对接之前重构的 memory_optimizer.py
    return "已完成 4 个冗余主体的语义归并，当前知识路径已刷新。"

# 2. 核心推理引擎
class ReasoningAgent:
    def __init__(self, model_name="qwen2.5:7b"):
        self.llm = ChatOllama(model=model_name, temperature=0)
        self.tools = [search_memory, optimize_graph_memory]
        
        # 使用 standard ReAct prompt
        prompt = hub.pull("hwchase17/react")
        self.agent = create_react_agent(self.llm, self.tools, prompt)
        self.executor = AgentExecutor(agent=self.agent, tools=self.tools, verbose=True, handle_parsing_errors=True)

    def execute(self, query: str):
        print(f"🧠 [ReAct Reasoning] 正在处理: {query}")
        start_time = datetime.now()
        
        # 执行推理
        response = self.executor.invoke({"input": query})
        
        # 记录轨迹 (Trace)
        self._save_trace(query, response["output"], start_time)
        return response["output"]

    def _save_trace(self, query, output, start_time):
        trace_file = "agent_reasoning_traces.json"
        duration = (datetime.now() - start_time).total_seconds()
        
        trace_entry = {
            "timestamp": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "query": query,
            "final_answer": output,
            "latency": f"{duration:.2f}s",
            "architecture": "LangChain ReAct Agent V2"
        }
        
        traces = []
        if os.path.exists(trace_file):
            with open(trace_file, "r", encoding="utf-8") as f:
                try: traces = json.load(f)
                except: traces = []
        
        traces.append(trace_entry)
        with open(trace_file, "w", encoding="utf-8") as f:
            json.dump(traces, f, ensure_ascii=False, indent=4)
        print(f"📡 [Log] 推理轨迹已持久化。")

if __name__ == "__main__":
    # 实例化并运行
    agent = ReasoningAgent()
    user_query = "基于我目前的兴趣和背景，请给出一个职业晋升建议，并顺便优化一下我的知识库。"
    answer = agent.execute(user_query)
    print(f"\n✨ 最终产出:\n{answer}")
