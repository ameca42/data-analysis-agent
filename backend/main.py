from fastapi import FastAPI

# 创建 FastAPI 应用
app = FastAPI(title="数据分析 Agent")

# 定义一个测试接口
@app.get("/")
def read_root():
    return {"message": "Hello! 数据分析 Agent 启动成功！"}