from fastapi import FastAPI

from app.schemas import CreateQueryRequest

app = FastAPI()

@app.get("/heartbeat")
def heartbeat():
    return {"message": "Agent is running"}

@app.post("/query")
def query(query: CreateQueryRequest):
    return {"message": f"Query: {query.query}"}