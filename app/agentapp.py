from fastapi import FastAPI

from app import agent_service
from app.schemas import CreateQueryRequest

app = FastAPI()

@app.get("/heartbeat")
def heartbeat():
    return {"message": "Agent is running"}

@app.post("/query")
async def query(query: CreateQueryRequest):
    print(f"Query: {query.query}")
    response = await agent_service.execute_search_query(query.query)
    return {"message": response}