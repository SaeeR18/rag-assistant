# RAG Assistant with Evaluation

A question-answering assistant over Azure and AWS documentation. You ask a question in plain English. The assistant searches 12 documentation PDFs, picks the most relevant passages, and asks Gemini to answer using only those passages. Every answer comes with its source file and page numbers.

The project also includes an evaluation: 25 test questions, a retrieval test, an answer-accuracy test, and a comparison of three chunk sizes. All numbers in this file come from my own runs.

Built on a free stack: local embeddings, Chroma, and the Gemini free tier.

## How it works

```
PDFs (12 files, 111 pages)
   |
   v
Split into chunks (1500 characters, 200 overlap)
   |
   v
Turn each chunk into an embedding (local sentence-transformers model)
   |
   v
Store in Chroma (local vector database)

Question
   |
   v
Embed the question, fetch the top 4 most similar chunks
   |
   v
Send question + 4 chunks to Gemini ("answer only from this context")
   |
   v
Answer + source files and page numbers
```

If the chunks do not contain the answer, the assistant replies "I could not find this in the documents" instead of guessing.

## Tech stack

- Python 3.12
- LangChain (PDF loading, text splitting)
- sentence-transformers (local embeddings)
- Chroma (vector database)
- Gemini API, free tier (answer generation)
- FastAPI (HTTP endpoint)

## Project layout

```
src/
  config.py      settings (paths, chunk size, model names)
  ingest.py      load PDFs, split, embed, save to Chroma
  rag.py         search + ask Gemini + return answer with sources
  api.py         FastAPI app with a POST /ask endpoint
tests/
  test_questions.json   25 questions with expected keywords
  evaluate.py           retrieval and answer evaluation
  results.md            full results and failure analysis
test_gemini.py   quick check that the API key works
```

## Run it yourself

1. Create and activate a virtual environment, then install the requirements:

   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and put in your own Gemini API key. A free key is available from Google AI Studio.

3. Put your PDFs in `data/docs/`. The PDFs are not included in this repository because they are Microsoft and AWS documentation. I used 12 single documentation pages saved as PDF: S3, VPC, IAM, EC2, Lambda, RDS and DynamoDB from AWS, and Storage, Networking, Identity, Database and Virtual Machines from Azure.

4. Build the database:

   ```
   python -m src.ingest --chunk-size 1500 --overlap 200
   ```

5. Ask questions in the terminal:

   ```
   python -m src.rag
   ```

6. Or start the API and open `http://127.0.0.1:8000/docs` to test the `/ask` endpoint:

   ```
   python -m uvicorn src.api:app
   ```

7. Run the evaluation:

   ```
   python -m tests.evaluate retrieval
   python -m tests.evaluate answers --label my-run
   ```

## Example

Question: How long are container names?

Answer: Container names can be between 3 and 63 characters long.

Sources: `AzureStorage.pdf` pages 3 and 4.

## Evaluation

The test set has 25 questions: 22 answerable and 3 unanswerable (for example, "What is the capital of France?"). The questions were written once and not changed to improve scores.

### Retrieval test (top-4 chunks)

| Chunk size / overlap | Right file found | Keywords found in retrieved text |
|---|---|---|
| 300 / 50 | 100% | 86% |
| 800 / 100 | 100% | 82% |
| 1500 / 200 | 100% | 95% |

### Answer accuracy (Gemini, top-4 chunks)

| Chunk size / overlap | Accuracy |
|---|---|
| 800 / 100 | 19/25 = 76% |
| 1500 / 200 | 21/25 = 84% |

I chose 1500 / 200 because it scored higher in both tests. With 25 questions, the improvement is modest, not large. Bigger chunks also send more text to the model, so part of the gain may come from extra context, not better search.

The assistant answered "I could not find this in the documents" for all 3 unanswerable questions, in both settings. It did not make up answers.

Full tables, per-question failure analysis and notes are in [`tests/results.md`](tests/results.md).

## Limitations

- The accuracy check is strict. It looks for exact keywords, so a correct answer in different words can fail.
- The test set is small. One question changes the score by 4 points.
- One failure (Blobfuse) is a real retrieval miss. The search found the right file but not the right passage.
- Web pages saved as PDF carry menu and header text, which adds noise to some chunks.
- When the answer is "not found", the assistant still lists source pages. It would be better to hide them.

## What I would improve

- Hide the sources when the answer is "not found".
- Try a re-ranking step so the best passages come first.
- Add more test questions and score answers with a more flexible check.
- Add a simple web interface.
