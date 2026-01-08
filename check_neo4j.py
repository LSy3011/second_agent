from neo4j import GraphDatabase

# 配置连接信息
URI = "bolt://localhost:7687"
AUTH = ("neo4j", "password123456")

def check_connection():
    try:
        print(f"🚀 正在尝试连接 {URI} ...")
        # 建立驱动
        with GraphDatabase.driver(URI, auth=AUTH) as driver:
            # 验证连接
            driver.verify_connectivity()
            print("✅ 连接成功！数据库是通的！")
            
            # 顺便查一下版本，确保没问题
            with driver.session() as session:
                result = session.run("CALL dbms.components() YIELD name, versions")
                record = result.single()
                print(f"📦 数据库版本: {record['name']} {record['versions'][0]}")
                
    except Exception as e:
        print("\n❌ 连接失败！")
        print(f"错误信息: {e}")
        print("\n排查建议：")
        print("1. 确保 VS Code 端口转发了 7687 端口")
        print("2. 确保密码是 password123456 (如果没改过可能是 neo4j)")

if __name__ == "__main__":
    check_connection()
