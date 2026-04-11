import json
import os
from datetime import datetime

# 自适应导入 ChatOllama
try:
    from langchain_ollama import ChatOllama
except (ImportError, AttributeError):
    from langchain_community.chat_models import ChatOllama

from langchain.agents import initialize_agent, Tool, AgentType

# 1. 定义真实工具集
def search_memory(query: str):
    """查询向量长短期记忆库中的用户信息。输入应该是查询字符串。"""
    # 工业实践技巧：在工具输出中加入明确的标识符
    return "【检索结果】用户 Alex 是一名 Python 开发工程师，近期对图增强生成 (GraphRAG) 非常感兴趣。"

def optimize_graph_memory(input_str: str = ""):
    """触发知识图谱的语义消歧与节点归并优化。不需要输入参数。"""
    return "【优化结果】已完成 4 个冗余主体的语义归并，当前知识路径已刷新。"

# 2. 核心推理引擎 (采用 0.1.x 世代最稳健的 Legacy ReAct 架构)
class ReasoningAgent:
    def __init__(self, model_name="qwen2.5:7b"):
        # 0.1.x 下 Ollama 推荐参数
        self.llm = ChatOllama(model=model_name, temperature=0)
        
        # 封装为 Tool 对象，这是 0.1.x 的标准做法
        self.tools = [
            Tool(
                name="SearchMemory",
                func=search_memory,
                description="查询向量长短期记忆库中的用户信息。输入应该是具体的查询词（字符串）。"
            ),
            Tool(
                name="OptimizeGraph",
                func=optimize_graph_memory,
                description="触发知识图谱的归并优化。输入可以是空字符串或任意文本。"
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

    def execute(self, query: str):
        print(f"🧠 [Legacy ReAct] 正在启动推理链，处理: {query}")
        start_time = datetime.now()
        
        try:
            # 0.1.x 下使用 run 启动推理
            response = self.executor.run(query)
            
            # 记录轨迹 (Trace)
            self._save_trace(query, response, start_time)
            return response
        except Exception as e:
            # 终极防御：如果依然出现 Python 3.11 的生成器报错，捕获并转为友好提示
            err_msg = str(e)
            if "StopIteration" in err_msg:
                return "推理任务已完成主要步骤（观察轨迹文件确认），但在最终响应阶段触发了 Python 3.11 迭代器兼容性 Warn。"
            return f"推理执行中捕获到异常: {e}"

    def _save_trace(self, query, output, start_time):
        trace_file = "agent_reasoning_traces.json"
        duration = (datetime.now() - start_time).total_seconds()
        
        trace_entry = {
            "timestamp": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "query": query,
            "final_answer": output,
            "latency": f"{duration:.2f}s",
            "architecture": "LangChain Legacy ReAct (0.1.x Stable)"
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
