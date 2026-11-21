import time

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI

from src import config

NOT_FOUND_TEXT = "I could not find this in the documents"

PROMPT_TEMPLATE = """You answer questions using only the context below.
If the answer is not in the context, reply exactly: {not_found}

Context:
{context}

Question: {question}

Answer:"""

_vectorstore = None
_llm = None


def get_vectorstore():
    """Open the saved Chroma database once and reuse it."""
    global _vectorstore
    if _vectorstore is None:
        embeddings = HuggingFaceEmbeddings(model_name=config.EMBEDDING_MODEL)
        _vectorstore = Chroma(
            collection_name=config.COLLECTION_NAME,
            embedding_function=embeddings,
            persist_directory=str(config.CHROMA_DIR),
        )
    return _vectorstore


def get_llm():
    """Create the Gemini chat model once and reuse it."""
    global _llm
    if _llm is None:
        _llm = ChatGoogleGenerativeAI(
            model=config.CHAT_MODEL,
            google_api_key=config.GOOGLE_API_KEY,
            temperature=0,
        )
    return _llm


def retrieve(question, k=None):
    """Return the top-k most similar chunks. No Gemini call."""
    k = k or config.TOP_K
    return get_vectorstore().similarity_search(question, k=k)


def build_prompt(question, chunks):
    parts = []
    for chunk in chunks:
        name = chunk.metadata.get("file_name", "unknown")
        page = chunk.metadata.get("page_number", "?")
        parts.append(f"[{name}, page {page}]\n{chunk.page_content}")
    return PROMPT_TEMPLATE.format(
        not_found=NOT_FOUND_TEXT,
        context="\n\n".join(parts),
        question=question,
    )


def call_llm_with_retry(prompt, attempts=4):
    """Call Gemini. On busy or rate-limit errors, wait and try again."""
    wait = 5
    for attempt in range(1, attempts + 1):
        try:
            reply = get_llm().invoke(prompt)
            content = reply.content
            if isinstance(content, list):
                content = "".join(
                    part.get("text", "") if isinstance(part, dict) else str(part)
                    for part in content
                )
            return content.strip()
        except Exception as error:
            text = str(error)
            retryable = any(
                code in text for code in ("429", "503", "UNAVAILABLE", "RESOURCE_EXHAUSTED")
            )
            if retryable and attempt < attempts:
                print(f"  Gemini busy. Waiting {wait} seconds (try {attempt} of {attempts})...")
                time.sleep(wait)
                wait *= 2
            else:
                raise


def ask(question, k=None):
    """Main function: returns {"answer": ..., "sources": [...]}."""
    chunks = retrieve(question, k)
    prompt = build_prompt(question, chunks)
    answer = call_llm_with_retry(prompt)

    sources = []
    for chunk in chunks:
        item = {
            "file": chunk.metadata.get("file_name", "unknown"),
            "page": chunk.metadata.get("page_number", "?"),
        }
        if item not in sources:
            sources.append(item)
    return {"answer": answer, "sources": sources}


def main():
    print("Ask a question about your documents. Type 'quit' to stop.")
    while True:
        question = input("\nQuestion: ").strip()
        if question.lower() in ("quit", "exit", ""):
            break
        result = ask(question)
        print("\nAnswer:", result["answer"])
        print("Sources:")
        for source in result["sources"]:
            print(f"  - {source['file']}, page {source['page']}")


if __name__ == "__main__":
    main()