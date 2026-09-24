"""Offline-first Zepto policy RAG assistant.

Default (MOCK_LLM unset or 1) makes no LLM-provider calls. Local embeddings and
ChromaDB retrieval still run for every policy question.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Literal, TypedDict

import chromadb
from fastapi import FastAPI, HTTPException
from groq import Groq
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field, ValidationError
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).parent
DOCS = ROOT / "docs"
DB_PATH = ROOT / "chroma_db"
COLLECTION_NAME = "zepto_policy_chunks"
KEYWORDS = ("delivery", "return", "refund", "membership", "tracking", "cancel", "gift card", "support hours")

# Role–Context–Task–Format–Length prompt, including a negative constraint and few-shot example.
STRUCTURED_PROMPT = """ROLE: You are Zepto's careful policy support assistant.
CONTEXT: {context}
TASK: Answer the user's question using only the provided context.
FORMAT: Return exactly valid JSON with answer (string), sources (list of source ids), and confidence (number 0 to 1).
LENGTH: Keep the answer to at most 80 words.
NEGATIVE CONSTRAINT: Do not answer using information not present in the provided context. Do not invent a policy.
FEW-SHOT EXAMPLE:
Context: [doc_01] Standard delivery is free on orders over INR 149.
User question: When is standard delivery free?
JSON answer: {{"answer":"Standard delivery is free on orders over INR 149.","sources":["doc_01"],"confidence":0.95}}

User question: {query}
"""


class AskRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)


class AskResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: float = Field(ge=0.0, le=1.0)


class GraphState(TypedDict, total=False):
    query: str
    intent: Literal["policy_question", "general_question"]
    retrieved_ids: list[str]
    retrieved_texts: list[str]
    response: AskResponse


_model: SentenceTransformer | None = None
_collection = None


def mock_mode() -> bool:
    """MOCK_LLM is mock unless explicitly set to zero."""
    return os.getenv("MOCK_LLM", "1") != "0"


def embedding_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def collection():
    """Create/load ChromaDB and embed all eight per-document chunks once."""
    global _collection
    if _collection is not None:
        return _collection
    client = chromadb.PersistentClient(path=str(DB_PATH))
    _collection = client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})
    documents = sorted(DOCS.glob("doc_*.txt"))
    if len(documents) != 8:
        raise RuntimeError("Expected exactly 8 policy documents in docs/.")
    ids = [path.stem for path in documents]
    texts = [path.read_text(encoding="utf-8").strip() for path in documents]
    # upsert means repeat starts are deterministic and do not duplicate records.
    vectors = embedding_model().encode(texts, normalize_embeddings=True).tolist()
    _collection.upsert(ids=ids, documents=texts, embeddings=vectors, metadatas=[{"source": item} for item in ids])
    return _collection


def real_llm_json(query: str, context: str, sources: list[str], retry_label: str) -> AskResponse:
    """Optional Groq path: two correction retries if Pydantic validation fails."""
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("MOCK_LLM=0 requires GROQ_API_KEY for the optional real-LLM extension.")
    client = Groq(api_key=key)
    prompt = STRUCTURED_PROMPT.format(context=context, query=query)
    last_error = "unknown validation error"
    for attempt in range(3):
        if attempt:
            prompt += "\nCorrective instruction: Return only JSON matching the requested schema; no markdown."
        raw = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        ).choices[0].message.content or "{}"
        try:
            parsed = json.loads(raw)
            parsed["sources"] = parsed.get("sources", sources)
            return AskResponse.model_validate(parsed)
        except (json.JSONDecodeError, ValidationError) as error:
            last_error = str(error)
    return AskResponse(answer=f"ERROR: {retry_label} output failed schema validation after 3 attempts: {last_error}", sources=sources, confidence=0.0)


def classify_intent(state: GraphState) -> GraphState:
    query = state["query"]
    if mock_mode():
        intent: Literal["policy_question", "general_question"] = (
            "policy_question" if any(word in query.lower() for word in KEYWORDS) else "general_question"
        )
    else:  # Optional generation branch.
        result = real_llm_json(query, "Classify only as policy_question or general_question.", [], "classification")
        intent = "policy_question" if "policy_question" in result.answer.lower() else "general_question"
    return {"intent": intent}


def retrieve_and_answer(state: GraphState) -> GraphState:
    query_vector = embedding_model().encode([state["query"]], normalize_embeddings=True).tolist()
    found = collection().query(query_embeddings=query_vector, n_results=3, include=["documents"])
    ids = found["ids"][0]
    texts = found["documents"][0]
    if mock_mode():
        # Required deterministic mock generation branch: no external LLM call.
        answer = f"Based on the retrieved context: {texts[0][:200]}"
        response = AskResponse(answer=answer, sources=ids, confidence=1.0)
    else:
        context = "\n\n".join(f"[{source}] {text}" for source, text in zip(ids, texts))
        response = real_llm_json(state["query"], context, ids, "retrieval answer")
    return {"retrieved_ids": ids, "retrieved_texts": texts, "response": response}


def direct_answer(state: GraphState) -> GraphState:
    if mock_mode():
        # Required deterministic mock generation branch: no external LLM call.
        response = AskResponse(answer="I can only answer questions about Zepto policies right now.", sources=[], confidence=1.0)
    else:
        response = real_llm_json(state["query"], "No policy context was retrieved.", [], "direct answer")
    return {"response": response}


def route_intent(state: GraphState) -> Literal["retrieve_and_answer", "direct_answer"]:
    return "retrieve_and_answer" if state["intent"] == "policy_question" else "direct_answer"


def build_graph():
    graph = StateGraph(GraphState)
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("retrieve_and_answer", retrieve_and_answer)
    graph.add_node("direct_answer", direct_answer)
    graph.add_edge(START, "classify_intent")
    graph.add_conditional_edges("classify_intent", route_intent)
    graph.add_edge("retrieve_and_answer", END)
    graph.add_edge("direct_answer", END)
    return graph.compile()


app = FastAPI(title="Zepto Support Assistant", version="1.0.0")
workflow = build_graph()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "mock" if mock_mode() else "real-llm"}


@app.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    try:
        result = workflow.invoke({"query": request.query})
        return result["response"]
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
