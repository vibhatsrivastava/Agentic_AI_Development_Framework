# 03 — RAG: Retrieval-Augmented Generation

> **Audience:** Beginners in Agentic AI | **Focus:** Concepts + Technical Interview Prep  
> **References:** [LangChain RAG Docs](https://python.langchain.com/docs/concepts/rag/) · [LangChain Vectorstores](https://python.langchain.com/docs/concepts/vectorstores/) · [LangChain Retrievers](https://python.langchain.com/docs/concepts/retrievers/) · [LangChain Text Splitters](https://python.langchain.com/docs/concepts/text_splitters/)

---

## Table of Contents

1. [What is RAG?](#1-what-is-rag)
2. [Why Do We Need RAG?](#2-why-do-we-need-rag)
3. [How RAG Works — The Full Pipeline](#3-how-rag-works--the-full-pipeline)
4. [Core Components Explained](#4-core-components-explained)
5. [RAG in LangChain — Code Walkthrough](#5-rag-in-langchain--code-walkthrough)
6. [RAG vs Fine-Tuning vs Prompt Stuffing](#6-rag-vs-fine-tuning-vs-prompt-stuffing)
7. [Advanced RAG Patterns](#7-advanced-rag-patterns)
8. [What Can Go Wrong — Failure Modes](#8-what-can-go-wrong--failure-modes)
9. [Interview Cheat Sheet](#9-interview-cheat-sheet)

---

## 1. What is RAG?

### Simple Definition

**RAG (Retrieval-Augmented Generation)** is a technique that makes an LLM answer questions using **your own documents or data** — rather than relying only on what it learned during training.

It works in two phases:
1. **Retrieve** — search a knowledge base to find documents relevant to the user's question
2. **Generate** — pass those documents as context to the LLM so it can produce a grounded answer

### Everyday Analogy

> Imagine you ask a question to someone who has never read your company's internal policy manual. They'll guess based on general knowledge — possibly wrong.  
> Now imagine they can open the manual, search for the relevant page, and answer directly from it. That's RAG.

### One-Line Summary

> _RAG gives an LLM access to external knowledge at inference time by retrieving relevant documents and putting them in the prompt._

---

## 2. Why Do We Need RAG?

### The Core Problem with LLMs Alone

| Limitation | What It Means |
|---|---|
| **Knowledge cutoff** | LLMs are trained on data up to a certain date — they don't know about events after that |
| **No access to private data** | LLMs don't know your company's documents, codebase, or internal reports |
| **Hallucination** | When an LLM doesn't know something, it may confidently make up an answer |
| **Context window limits** | You can't paste an entire document library into every prompt |

### What RAG Solves

| With RAG | Without RAG |
|---|---|
| Answers grounded in your actual documents | Answers from training data only (may be outdated or wrong) |
| Works with private, proprietary data | Cannot access private data |
| Cites sources (which chunk was used) | No traceability |
| Scales to millions of documents | Context window limits how much text you can pass |
| No model retraining needed | Fine-tuning requires expensive GPU training |

---

## 3. How RAG Works — The Full Pipeline

RAG has two distinct phases: **Indexing** (done once, offline) and **Retrieval + Generation** (done at query time).

### Phase 1 — Indexing (Offline)

```
Your Documents (PDF, Word, Web, DB, etc.)
         │
         ▼
┌─────────────────────┐
│   Document Loader   │  ← Load raw content into LangChain Documents
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│    Text Splitter    │  ← Break large docs into smaller chunks
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Embedding Model    │  ← Convert each chunk into a dense vector
│  (get_embeddings()) │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│    Vector Store     │  ← Store vectors + original text for fast search
│  (ChromaDB, FAISS)  │
└─────────────────────┘
```

### Phase 2 — Retrieval + Generation (At Query Time)

```
User Question
      │
      ▼
┌─────────────────────┐
│  Embedding Model    │  ← Embed the question into a vector
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│    Vector Store     │  ← Find the top-K most similar chunks
│    (similarity      │     (cosine similarity search)
│     search)         │
└──────────┬──────────┘
           │  top-K chunks (context)
           ▼
┌──────────────────────────────────────────┐
│              LLM Prompt                  │
│                                          │
│  System: "Answer using only the context" │
│  Context: [chunk 1] [chunk 2] [chunk 3]  │
│  Question: "What is the refund policy?"  │
└──────────────────────┬───────────────────┘
                       │
                       ▼
                  LLM (ChatOllama)
                       │
                       ▼
                 Grounded Answer
```

### End-to-End in One Diagram

```
INDEXING (once)          QUERY TIME (every request)
────────────────         ──────────────────────────────────────────
Docs                     User Question
 │                              │
 ▼                              ▼
Load → Split → Embed → Store    Embed Question
                  │                    │
                  │             Similarity Search
                  │                    │
                  └──────► Top-K Chunks ──► LLM ──► Answer
```

---

## 4. Core Components Explained

### 4.1 Document Loaders

Load raw content from various sources into LangChain `Document` objects (each has `page_content` + `metadata`).

| Loader | Source | Example Use |
|---|---|---|
| `PyPDFLoader` | PDF files | Company policy docs, research papers |
| `TextLoader` | Plain `.txt` files | Logs, notes |
| `WebBaseLoader` | Web pages via URL | Documentation sites, news |
| `CSVLoader` | CSV files | Structured tabular data |
| `DirectoryLoader` | All files in a folder | Batch ingestion of a knowledge base |

```python
from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader("company_policy.pdf")
docs = loader.load()
# docs is a list of Document objects, one per page
print(docs[0].page_content)   # text of page 1
print(docs[0].metadata)       # {"source": "company_policy.pdf", "page": 0}
```

---

### 4.2 Text Splitters

LLMs have limited context windows. A 200-page PDF cannot be injected into a single prompt. Text splitters divide documents into smaller **chunks** that:
- Fit within the embedding model's token limit
- Are semantically focused enough to be retrieved precisely

| Splitter | Strategy | Best For |
|---|---|---|
| `RecursiveCharacterTextSplitter` | Splits on `\n\n`, `\n`, ` `, then characters | General text — **default recommendation** |
| `CharacterTextSplitter` | Splits on a single separator | Simple text with clear delimiters |
| `MarkdownHeaderTextSplitter` | Splits on Markdown headers | Structured Markdown docs |
| `TokenTextSplitter` | Splits by token count | Precise token-level control |

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,       # max characters per chunk
    chunk_overlap=50,     # overlap between chunks to preserve context
)
chunks = splitter.split_documents(docs)
print(f"{len(chunks)} chunks created")
```

> **Interview Tip:** `chunk_overlap` is important — without it, a sentence split across two chunks loses context in both. A typical overlap is 10–20% of `chunk_size`.

---

### 4.3 Embedding Models

An **embedding model** converts text into a fixed-size list of numbers (a **vector**). Texts with similar meaning produce vectors that are close together in vector space.

```
"What is LangChain?" ──► [0.12, -0.34, 0.87, ..., 0.05]  (1536 numbers)
"LangChain overview" ──► [0.11, -0.33, 0.85, ..., 0.06]  ← very close
"Recipe for pasta"   ──► [-0.78, 0.92, -0.21, ..., 0.44] ← very far
```

In this repo, embeddings come from Ollama via `get_embeddings()`:

```python
from common.llm_factory import get_embeddings

embeddings = get_embeddings()                          # nomic-embed-text
embeddings = get_embeddings(model="mxbai-embed-large") # higher quality
```

---

### 4.4 Vector Stores

A **vector store** is a database optimised to store vectors and run **similarity search** — finding the stored vectors most similar to a query vector.

| Vector Store | Type | Best For |
|---|---|---|
| `FAISS` | In-memory (local) | Fast prototyping, no server needed |
| `ChromaDB` | Embedded / server | Local development, small-medium scale |
| `Pinecone` | Cloud / managed | Production at scale |
| `pgvector` | PostgreSQL extension | Teams already using Postgres |
| `InMemoryVectorStore` | In-memory (LangChain) | Testing and demos |

```python
from langchain_chroma import Chroma
from common.llm_factory import get_embeddings

# Create and persist a vector store from chunks
vector_store = Chroma.from_documents(
    documents=chunks,
    embedding=get_embeddings(),
    persist_directory="./chroma_db",  # saved to disk
)

# Similarity search
results = vector_store.similarity_search("What is the refund policy?", k=3)
for doc in results:
    print(doc.page_content)
```

---

### 4.5 Retrievers

A **retriever** is an abstraction on top of a vector store — it has a single method: `get_relevant_documents(query)`. This allows the RAG chain to work with any retrieval backend without changing the chain code.

```python
retriever = vector_store.as_retriever(
    search_type="similarity",   # or "mmr" (Maximum Marginal Relevance)
    search_kwargs={"k": 4},     # return top 4 chunks
)

chunks = retriever.invoke("What is the return policy?")
```

**Search types:**

| Type | Description | Use When |
|---|---|---|
| `similarity` | Returns the `k` most similar chunks by cosine distance | Default — general use |
| `mmr` | Returns diverse chunks (avoids near-duplicates) | When top results are too similar to each other |
| `similarity_score_threshold` | Only returns chunks above a minimum similarity score | When you want to avoid returning irrelevant chunks |

---

## 5. RAG in LangChain — Code Walkthrough

### Complete Minimal RAG Pipeline

```python
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from common.llm_factory import get_chat_llm, get_embeddings

# ── STEP 1: Load documents ────────────────────────────────────────────────────
loader = TextLoader("knowledge_base.txt")
docs = loader.load()

# ── STEP 2: Split into chunks ─────────────────────────────────────────────────
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(docs)

# ── STEP 3: Embed and store ───────────────────────────────────────────────────
vector_store = Chroma.from_documents(chunks, embedding=get_embeddings())

# ── STEP 4: Create a retriever ────────────────────────────────────────────────
retriever = vector_store.as_retriever(search_kwargs={"k": 3})

# ── STEP 5: Build the RAG prompt ──────────────────────────────────────────────
prompt = ChatPromptTemplate.from_messages([
    ("system",
     "Answer the question using only the context below. "
     "If the answer is not in the context, say 'I don't know'.\n\n"
     "Context:\n{context}"),
    ("human", "{question}"),
])

# ── STEP 6: Compose the RAG chain ─────────────────────────────────────────────
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | get_chat_llm()
    | StrOutputParser()
)

# ── STEP 7: Ask a question ───────────────────────────────────────────────────
answer = rag_chain.invoke("What is the company's refund policy?")
print(answer)
```

### What Each Step Does

```
User Question: "What is the company's refund policy?"
      │
      ├──► retriever.invoke(question)
      │         │
      │         ▼
      │    [chunk 1: "Refunds are processed within 7 days..."]
      │    [chunk 2: "To request a refund, contact support..."]
      │    [chunk 3: "Non-refundable items include..."]
      │         │
      │    format_docs()  ──► single string of all 3 chunks
      │
      ├──► RunnablePassthrough()  ──► question passed through unchanged
      │
      ▼
  ChatPromptTemplate builds:
    system: "Answer using only the context... [chunks]"
    human:  "What is the company's refund policy?"
      │
      ▼
  ChatOllama (LLM)
      │
      ▼
  StrOutputParser  ──► plain string
      │
      ▼
  "Refunds are processed within 7 days of the return request..."
```

---

## 6. RAG vs Fine-Tuning vs Prompt Stuffing

These are the three main strategies for giving an LLM access to specific knowledge.

| Dimension | Prompt Stuffing | RAG | Fine-Tuning |
|---|---|---|---|
| **What it is** | Paste all documents directly into the prompt | Retrieve relevant chunks at query time | Retrain the model on your dataset |
| **Knowledge update** | Instant (change the text) | Instant (re-index documents) | Requires full retraining cycle |
| **Scales to large data** | ❌ Limited by context window | ✅ Scales to millions of docs | ✅ Baked into weights |
| **Private data** | ✅ | ✅ | ✅ |
| **Cost** | Low (just token cost) | Medium (embedding + storage) | High (GPU training) |
| **Hallucination risk** | Medium | Low (grounded in retrieved docs) | Medium (may still hallucinate) |
| **Traceability (which doc?)** | Hard | ✅ Know exactly which chunks were used | ❌ Not traceable |
| **Best for** | Short, known context (≤ 10 pages) | Q&A over large document collections | Changing model behaviour / tone |

### When to Use Each

```
Your knowledge base has 10,000 documents?
    └──► Use RAG

You need the model to change its tone or follow a specific style?
    └──► Use Fine-Tuning

You have a 2-page spec to reference in one prompt?
    └──► Use Prompt Stuffing (just paste it in)

You need both retrieval AND behaviour change?
    └──► RAG + Fine-Tuning combined
```

> **Interview Tip:** RAG and fine-tuning are complementary, not competing. A fine-tuned model can *still* use RAG for dynamic knowledge retrieval.

---

## 7. Advanced RAG Patterns

### 7.1 Naive RAG vs Advanced RAG

```
Naive RAG:
──────────
Question → Embed → Top-K chunks → LLM → Answer
(simple, but retrieval quality limits answer quality)

Advanced RAG adds improvements at three stages:
─────────────────────────────────────────────────
Pre-retrieval:   Better chunking, document enrichment, metadata filtering
Retrieval:       Re-ranking, hybrid search, MMR diversity
Post-retrieval:  Context compression, re-ordering, citation extraction
```

### 7.2 Key Advanced Techniques

| Technique | What It Does | Benefit |
|---|---|---|
| **Hybrid Search** | Combines vector similarity + keyword (BM25) search | Better recall — catches exact matches that vector search misses |
| **Re-ranking** | Uses a cross-encoder model to re-score retrieved chunks | Improves precision — puts the most relevant chunk first |
| **MMR (Max Marginal Relevance)** | Retrieves diverse chunks, not just the most similar ones | Avoids returning 3 near-identical chunks |
| **Contextual Compression** | Extracts only the relevant sentence from a retrieved chunk | Reduces noise in the LLM context |
| **Self-querying** | LLM generates a structured query + metadata filter from natural language | Enables filtering (e.g., "docs from 2024 only") |
| **Multi-query retrieval** | Generates multiple phrasings of the question, retrieves for each | Better recall when the original question is ambiguous |
| **HyDE (Hypothetical Document Embeddings)** | LLM generates a hypothetical answer, then embeds *that* for retrieval | Bridges vocabulary mismatch between question and documents |

### 7.3 RAG as a Tool in an Agent

In an agentic system, the retriever is wrapped as a **tool** so the agent can decide *when* to retrieve:

```python
from langchain_core.tools import create_retriever_tool

retriever_tool = create_retriever_tool(
    retriever,
    name="search_knowledge_base",
    description="Search the company knowledge base for information about policies, products, and procedures.",
)

# Agent now has RAG as one of its available tools
graph = create_react_agent(model=get_chat_llm(), tools=[retriever_tool])
```

> This is the key difference between a **RAG chain** (always retrieves) and a **RAG agent** (retrieves only when needed).

---

## 8. What Can Go Wrong — Failure Modes

| Failure Mode | Symptom | Fix |
|---|---|---|
| **Chunks too large** | Retrieved chunks contain too much unrelated text; LLM ignores the relevant part | Reduce `chunk_size`; use smaller, more focused chunks |
| **Chunks too small** | Retrieved chunks lack enough context to answer; answer is incomplete or misleading | Increase `chunk_size` or `chunk_overlap` |
| **Wrong chunks retrieved** | Answer is confidently wrong; retrieval misses the relevant document | Use hybrid search; add metadata filters; improve embedding model |
| **LLM ignores context** | LLM answers from training memory instead of the retrieved chunks | Strengthen the system prompt: "Answer **only** from the context below" |
| **Stale vector store** | Documents were updated but the index was not re-built | Implement incremental indexing; add document hash tracking |
| **Embedding model mismatch** | Querying with a different embedding model than was used during indexing | Always use the same embedding model for indexing and querying |
| **No relevant chunks found** | LLM says "I don't know" even when the answer exists | Lower similarity threshold; check chunking strategy; verify document was loaded |
| **Duplicate chunks** | Same information retrieved multiple times; context bloated | Use MMR retrieval; deduplicate at ingestion |

---

## 9. Interview Cheat Sheet

| Question | Key Answer |
|---|---|
| **What is RAG?** | A pattern that retrieves relevant documents from a vector store at query time and injects them as context into the LLM prompt, so answers are grounded in your data rather than training memory |
| **What are the two phases of RAG?** | Indexing (load → split → embed → store, done offline) and Retrieval+Generation (embed query → similarity search → prompt LLM, done at query time) |
| **What is a vector store?** | A database that stores text as dense numerical vectors and supports fast similarity search to find the most relevant chunks for a given query |
| **What is an embedding?** | A fixed-size vector of numbers that represents the semantic meaning of a piece of text — similar texts produce similar vectors |
| **Why do we split documents into chunks?** | LLMs have limited context windows; embedding models have token limits; smaller, focused chunks improve retrieval precision |
| **What is `chunk_overlap` and why is it important?** | The number of characters shared between adjacent chunks; it prevents a sentence from being cut in half and losing context at chunk boundaries |
| **What is the difference between a vector store and a retriever?** | A vector store is the storage layer; a retriever is an abstraction that wraps the vector store and exposes `get_relevant_documents(query)` — it decouples retrieval logic from chain logic |
| **RAG vs Fine-Tuning?** | RAG retrieves dynamic, up-to-date knowledge at inference time — no retraining, traceable to source documents. Fine-tuning bakes knowledge into model weights — expensive, not updateable without retraining |
| **What is MMR?** | Maximum Marginal Relevance — a retrieval strategy that balances relevance with diversity, avoiding returning near-duplicate chunks |
| **What is HyDE?** | Hypothetical Document Embeddings — the LLM generates a hypothetical answer to the question, then that answer is embedded and used for retrieval (bridges vocabulary gaps between question and documents) |
| **How do you prevent hallucination in RAG?** | Use a strict system prompt ("answer only from the context provided"); use a similarity score threshold to avoid retrieving irrelevant chunks; use `StrOutputParser` and validate citations |
| **What is the difference between a RAG chain and a RAG agent?** | A RAG chain always retrieves before every LLM call; a RAG agent uses the retriever as a tool, so the agent decides whether retrieval is needed for each step |

---

*Previous: [02_ReAct_Pattern_Deep_Dive.md](02_ReAct_Pattern_Deep_Dive.md)*  
*Next in Quick-Reference → `04_LangGraph_State_and_Memory.md`*
