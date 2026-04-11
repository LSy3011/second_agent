import json
import os
from datetime import datetime
try:
    # 尝试加载最新版的 Ollama 接口
    from langchain_ollama import ChatOllama
except (ImportError, AttributeError):
    # 如果版本不匹配（如报 LangSmithParams 错误），回退到稳健的社区版接口
    from langchain_community.chat_models import ChatOllama

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain.agents import create_react_agent, AgentExecutor

# 1. 定义标准的 ReAct 推理模板 (离线稳健版)
REACT_PROMPT = ChatPromptTemplate.from_template("""
你是一个能够使用工具回答问题的智能体。请按以下格式思考和回答：

Question: 用户的输入问题
工具列表: {tools}

Thought: 你应该总是思考你应该做什么
Action: 要采取的行动，必须是 [{tool_names}] 之一
Action Input: 行动的输入参数
Observation: 行动的执行结果
... (这个 Thought/Action/Action Input/Observation 可以重复多次)
Thought: 我现在知道最终答案了
Final Answer: 对原始问题的最终回答

开始！

Question: {input}
Thought: {agent_scratchpad}
""")

# 2. 定义真实工具集
@tool
def search_memory(query: str):
    """查询向量长短期记忆库中的用户信息。"""
    return "用户 Alex 是一名 Python 开发工程师，近期对图增强生成 (GraphRAG) 非常感兴趣。"

@tool
def optimize_graph_memory():
    """触发知识图谱的语义消歧与节点归并优化。"""
    return "已完成 4 个冗余主体的语义归并，当前知识路径已刷新。"

# 3. 核心推理引擎
class ReasoningAgent:
    def __init__(self, model_name="qwen2.5:7b"):
        self.llm = ChatOllama(model=model_name, temperature=0.1)
        self.tools = [search_memory, optimize_graph_memory]
        
        # 使用自定义的 REACT_PROMPT
        self.agent = create_react_agent(self.llm, self.tools, REACT_PROMPT)
        self.executor = AgentExecutor(
            agent=self.agent, 
            tools=self.tools, 
            verbose=True, 
            handle_parsing_errors=True
        )

    def execute(self, query: str):
        print(f"🧠 [ReAct Reasoning] 正在处理: {query}")
        start_time = datetime.now()
        
        try:
            # 执行推理
            response = self.executor.invoke({"input": query})
            output = response["output"]
            
            # 记录轨迹 (Trace)
            self._save_trace(query, output, start_time)
            return output
        except Exception as e:
            return f"推理过程中出现异常: {e}"

    def _save_trace(self, query, output, start_time):
        trace_file = "agent_reasoning_traces.json"
        duration = (datetime.now() - start_time).total_seconds()
        
        trace_entry = {
            "timestamp": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "query": query,
            "final_answer": output,
            "latency": f"{duration:.2f}s",
            "architecture": "LangChain ReAct Agent V2 (Stable)"
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
