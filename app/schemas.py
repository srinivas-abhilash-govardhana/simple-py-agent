from pydantic import BaseModel


class CreateQueryRequest(BaseModel):
    query: str

