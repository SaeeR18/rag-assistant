from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.rag import ask

app = FastAPI(title="RAG Assistant")


class Question(BaseModel):
    question: str


class Source(BaseModel):
    file: str
    page: int | str


class Answer(BaseModel):
    answer: str
    sources: list[Source]


@app.get("/health")
def health():
    """Report that the server is running."""
    return {"status": "ok"}


@app.post("/ask", response_model=Answer)
def ask_question(body: Question):
    """Take a question and return an answer with its sources."""
    question = body.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question must not be empty.")
    try:
        return ask(question)
    except Exception as error:
        # Report only the error type so no secrets or long traces leak to the caller.
        raise HTTPException(
            status_code=502,
            detail=f"Could not get an answer ({type(error).__name__}). Check the server terminal.",
        )