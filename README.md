# Module 3 — Zepto Support Assistant

This is an offline-first RAG service. The required baseline is **mock mode**: leave `MOCK_LLM` unset (or set it to `1`). No LLM API key or provider request is used in that mode.

## Run locally

```bat
cd support_assistant
py -m pip install -r requirements.txt
py -m uvicorn main:app --host 127.0.0.1 --port 7860
```

On the first policy request, `sentence-transformers` downloads/caches the open-source `all-MiniLM-L6-v2` model, embeds all eight files in `docs/`, and upserts them into the persistent ChromaDB collection named `zepto_policy_chunks`. Later requests reuse `chroma_db/`.

In a second Command Prompt window, use these example calls:

```bat
curl -X POST "http://127.0.0.1:7860/ask" -H "Content-Type: application/json" -d "{\"query\": \"What is the delivery fee for an order below INR 149?\"}"
curl -X POST "http://127.0.0.1:7860/ask" -H "Content-Type: application/json" -d "{\"query\": \"What is the capital of India?\"}"
```

## Recorded mock-mode example responses

Policy question (retrieval path; the exact snippet may differ slightly by Chroma ranking):

```json
{
  "answer": "Based on the retrieved context: Zepto delivers grocery and household essentials to serviceable pin codes within 10 to 30 minutes of order confirmation, depending on the customer's delivery zone and current order volume. Standard delivery is free on orders over INR 149;",
  "sources": ["doc_01", "doc_05", "doc_03"],
  "confidence": 1.0
}
```

General question (direct-answer path):

```json
{
  "answer": "I can only answer questions about Zepto policies right now.",
  "sources": [],
  "confidence": 1.0
}
```

## Architecture: ingestion → embedding → retrieval → generation

1. **Ingestion:** `collection()` in `main.py` reads the eight exact policy files from `docs/doc_01.txt` through `docs/doc_08.txt`. Each complete document is one chunk with an ID such as `doc_01`.
2. **Embedding:** the same function uses the local `SentenceTransformer("all-MiniLM-L6-v2")` model to create normalized vectors. It upserts the vectors and source IDs into the persistent ChromaDB collection `zepto_policy_chunks` stored under `chroma_db/`.
3. **Retrieval:** LangGraph starts in `classify_intent`. Its conditional edge routes policy-keyword questions to `retrieve_and_answer`; this node embeds the query and retrieves the top three cosine-similar Chroma chunks. Other questions route to `direct_answer`.
4. **Generation:** in default mock mode, `retrieve_and_answer` returns `Based on the retrieved context: ...` from the top chunk and `direct_answer` returns a fixed policy-only message. Both are validated with `AskResponse` (`answer`, `sources`, `confidence`) before FastAPI returns JSON from `POST /ask`.

`MOCK_LLM` branches only inside the three LangGraph nodes' generation logic. With its default mock value, no LLM-provider network call occurs; intent classification is the specified keyword heuristic and answers are deterministic. With the optional `MOCK_LLM=0`, `GROQ_API_KEY` enables a Groq request using `STRUCTURED_PROMPT`, which visibly includes role, context, task, format, length, a negative constraint, and a few-shot example. The optional real-output code retries validation failures up to two additional times.

## Docker

Build and run the required local container baseline:

```bat
docker build -t zepto-support-assistant .
docker run -p 7860:7860 zepto-support-assistant
```

Then call `POST http://127.0.0.1:7860/ask` using the curl command above. Run this in mock mode (the default) for grading.
