import os
from langchain_community.chat_models import ChatOllama
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools import Tool

# ================= 1. 定义推理工具 =================

def search_vector_memory(query: str):
    """搜索向量数据库中的个人偏好和非结构化记忆。"""
    print(f"🔍 [Tool] 正在检索向量记忆: {query}")
    # 此处对接原有的 mem0.search 逻辑
    return "Alex 喜欢使用 Python，并且对图数据库感兴趣。"

def search_graph_memory(query: str):
    """搜索图数据库中复杂的实体关系（如：谁在哪里工作，项目的隶属关系）。"""
    print(f"🕸️ [Tool] 正在检索图谱记忆: {query}")
    # 此处对接原有的 Neo4j Cypher 查询逻辑
    return "Alex 在科技公司工作，职业是 Python 开发者。"

tools = [
    Tool(
        name="VectorSearch",
        func=search_vector_memory,
        description="用于查询模糊的个人偏好、性格特点等非结构化信息。"
    ),
    Tool(
        name="GraphSearch",
        func=search_graph_memory,
        description="用于查询明确的实体间关系，如职业、工作地点、技能隶属等。"
    )
]

# ================= 2. 构建 ReAct Prompt =================

template = """尽可能回答以下问题。你可以使用以下工具：

{tools}

使用以下格式：
Question: 需要回答的问题
Thought: 我应该查找向量记忆还是图谱记忆？还是两者都需要？
Action: [{tool_names}] 中的一个
Action Input: 搜索关键词
Observation: 搜索结果
... (过程可以重复)
Thought: 我现在知道最终答案了
Final Answer: 对问题的最终回答

Question: {input}
Thought: {agent_scratchpad}"""

prompt = PromptTemplate.from_template(template)

# ================= 3. 初始化推理 Agent =================

llm = ChatOllama(model="qwen2.5:7b", temperature=0)

agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

def run_advanced_agent(query: str):
    print(f"\n🧠 [Agent V2] 启动复杂推理任务: {query}")
    response = agent_executor.invoke({"input": query})
    return response["output"]

if __name__ == "__main__":
    # 示例：一个需要结合两路记忆的问题
    queries = [
        "根据 Alex 的职业和兴趣，推荐一个他可能喜欢的技术栈项目。",
        "Alex 在哪工作？他最近提到过什么特别的偏好吗？"
    ]
    
    for q in queries:
        ans = run_advanced_agent(q)
        print(f"\n✨ 最终回答: {ans}\n" + "-"*30)
