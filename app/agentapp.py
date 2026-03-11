from fastapi import FastAPI

app = FastAPI()

@app.get("/heartbeat")
def heartbeat():
    return {"message": "Agent is running"}

@app.post("/query")
def query(query: str):
    return {"message": f"Query: {query}"}