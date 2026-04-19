# DSW 服务器环境速查

## Second Agent

虚拟环境：

```text
/mnt/workspace/neo4j_agent_env/
```

项目目录：

```text
/mnt/workspace/neo4j_agent_env/second_agent/
```

进入环境：

```bash
cd /mnt/workspace/neo4j_agent_env/
source bin/activate
cd /mnt/workspace/neo4j_agent_env/second_agent/
```

更新并验证：

```bash
git pull origin master
cp .env.example .env  # 如果 .env 已存在，先人工对比
python health_check.py
python check_neo4j.py
python hybrid_agent_padding_final.py
python agent_v2_reasoning.py
```

重建向量库：

```bash
python hybrid_agent_padding_final.py --reset
```

## Paper Assistant

虚拟环境：

```text
/mnt/workspace/paper_assistant/paper_assistant/venv/
```

进入环境：

```bash
cd /mnt/workspace/paper_assistant/paper_assistant/
source venv/bin/activate
```

推荐在仓库根目录执行：

```bash
git pull origin master
cp .env.example .env  # 如果 .env 已存在，先人工对比
python paper_assistant/health_check.py
python paper_assistant/main.py
streamlit run paper_assistant/app.py
```

如果你的服务器当前仍是嵌套目录结构，也可以使用旧入口：

```bash
cd /mnt/workspace/paper_assistant/paper_assistant/
source venv/bin/activate
cd paper_assistant
python main.py
```

更推荐仓库根目录入口，因为配置文件和相对路径更稳定。

