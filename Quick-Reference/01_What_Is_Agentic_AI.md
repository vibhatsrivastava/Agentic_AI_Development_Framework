> **Audience:** Beginners in AI/ML development | **Focus:** Concepts + Technical Interview Prep  
> **References:** [LangChain Docs](https://docs.langchain.com/) · [LangGraph Docs](https://langchain-ai.github.io/langgraph/) · [OpenAI Platform Docs](https://platform.openai.com/docs/)

---

## Table of Contents

1. [What is Agentic AI?](#1-what-is-agentic-ai)
2. [Agentic AI vs Generative AI vs Predictive AI](#2-agentic-ai-vs-generative-ai-vs-predictive-ai)
3. [What We Do in Agentic AI Development](#3-what-we-do-in-agentic-ai-development)
4. [Tools and Components Required](#4-tools-and-components-required)
5. [How LangChain and LangGraph Empower Agentic AI](#5-how-langchain-and-langgraph-empower-agentic-ai)

---

## 1. What is Agentic AI?

### Short Summary

**Agentic AI** refers to AI systems that can autonomously **plan**, **decide**, and **act** across multiple steps to complete a goal — rather than simply responding to a single prompt.

A traditional LLM answers one question at a time. An **agent** wraps an LLM with:
- A **goal** or task description
- Access to **tools** (e.g., web search, code execution, databases)
- A **reasoning loop** that decides what to do next based on previous results

> _"Agents use an LLM as a reasoning engine to determine which actions to take and in what order."_  
> — LangChain Documentation

### The Core Idea

```
User Goal
   │
   ▼
┌──────────────────────────────┐
│           AGENT              │
│                              │
│  Think → Act → Observe       │  ← repeated until goal is met
│     (ReAct Loop)             │
│                              │
│  Tools: Search, Code, DB...  │
└──────────────────────────────┘
   │
   ▼
Final Answer / Action
```

### Key Properties of an Agentic System

| Property | Description |
|---|---|
| **Autonomy** | Takes actions without requiring a human prompt at every step |
| **Goal-directed** | Works toward a defined objective across multiple steps |
| **Tool use** | Calls external tools, APIs, or other agents to gather information or act |
| **Memory** | Maintains context across steps (short-term) or across sessions (long-term) |
| **Planning** | Breaks a complex task into sub-tasks and executes them in order |
| **Self-correction** | Observes tool results and adjusts its approach if something fails |

### Interview Quick Answer

> **Q: What is an AI Agent?**  
> An AI agent is a system that uses an LLM as a reasoning engine to autonomously execute multi-step tasks by selecting and calling tools, observing results, and deciding next steps — without a human directing each action.

---

## 2. Agentic AI vs Generative AI vs Predictive AI

### Plain-English Definitions

| Term | What It Does | Key Question It Answers |
|---|---|---|
| **Predictive AI** | Learns patterns from historical data to forecast future values or classify inputs | _"What will happen?"_ / _"What category is this?"_ |
| **Generative AI** | Generates new content (text, images, audio, code) from a prompt | _"Create something new based on this input."_ |
| **Agentic AI** | Uses an LLM to plan and execute multi-step tasks using tools and memory | _"Complete this goal for me, figure out the steps yourself."_ |

---

### Comparison Table

| Dimension | Predictive AI | Generative AI | Agentic AI |
|---|---|---|---|
| **Core task** | Predict / classify | Generate content | Plan & act autonomously |
| **Input** | Structured data (numbers, labels) | Natural language prompt | High-level goal or instruction |
| **Output** | A label, score, or forecast | Text, image, code, audio | Actions taken + final answer |
| **Decision making** | None (pattern matching) | None (single generation) | Yes — multi-step reasoning loop |
| **Tool use** | No | No | Yes (search, code, APIs, DBs) |
| **Memory** | Stateless | Stateless per call | Stateful across steps |
| **Number of LLM calls** | 0 (uses ML models, not LLMs) | 1 | Many (one per reasoning step) |
| **Example** | Predict house price | Write a blog post | Research a topic, summarise it, send an email |

---

### Side-by-Side Examples

**Scenario:** _"Find the top 3 Python frameworks for web development, compare them, and save the result to a file."_

| AI Type | What Happens |
|---|---|
| **Predictive AI** | Not applicable — this is not a classification or forecasting task |
| **Generative AI** | LLM generates a comparison based on its training data in **one response** — may be outdated, cannot save to file |
| **Agentic AI** | Agent **searches the web** for current data → **reasons** over results → **writes comparison** → **calls a file-write tool** to save it — all autonomously |

---

**Scenario:** _"Is this email spam?"_

| AI Type | What Happens |
|---|---|
| **Predictive AI** | Trained classifier returns `spam` or `not spam` — fast, efficient, no LLM needed |
| **Generative AI** | LLM reads the email and generates a verdict in natural language |
| **Agentic AI** | Overkill for this task — agent would be used if follow-up actions are needed (e.g., also quarantine it, notify user, log it) |

> **Interview Tip:** Agentic AI does not replace Generative or Predictive AI — it *orchestrates* them. An agent might call a Generative AI model to draft text and a Predictive model to classify sentiment in the same workflow.

---

## 3. What We Do in Agentic AI Development

### Core Development Activities

| Activity | Description | Example |
|---|---|---|
| **Define the agent's goal** | Write a clear system prompt describing what the agent is responsible for | _"You are a research assistant. Given a topic, search the web and produce a structured summary."_ |
| **Select and build tools** | Create Python functions decorated as tools that the agent can call | Web search tool, calculator, database query, code executor |
| **Design the reasoning loop** | Choose the agent pattern: ReAct, Plan-and-Execute, Multi-agent, etc. | ReAct loop: Thought → Action → Observation → repeat |
| **Manage state and memory** | Decide what the agent remembers across steps or sessions | Store conversation history, intermediate results, or retrieved documents |
| **Connect to a vector store** | Enable RAG so the agent can retrieve relevant documents as context | Embed docs → store in vector DB → retrieve on query |
| **Handle errors and retries** | Define what happens when a tool fails or the LLM produces a bad response | Retry with a corrected prompt, fall back to a different tool |
| **Test and evaluate** | Verify the agent produces correct, safe, and consistent outputs | Check tool call accuracy, answer faithfulness, latency |

### The ReAct Reasoning Pattern (Most Common)

ReAct = **Re**asoning + **Act**ing — the most widely used agent loop:

```
Thought:   "I need to find the current Python version."
Action:    web_search("latest Python version 2025")
Observation: "Python 3.13 was released in October 2024."
Thought:   "I now have the answer."
Final Answer: "The latest Python version is 3.13."
```

Each iteration: the LLM **thinks**, **acts** (calls a tool), and **observes** the result — looping until it can produce a final answer.

> **Interview Tip:** Be ready to explain ReAct. It was introduced in the paper _"ReAct: Synergizing Reasoning and Acting in Language Models"_ (Yao et al., 2022) and is the foundation for most LangChain/LangGraph agent patterns.

---

## 4. Tools and Components Required

### Component Map

```
┌─────────────────────────────────────────────────────────┐
│                     AGENTIC SYSTEM                      │
│                                                         │
│  ┌──────────┐    ┌──────────┐    ┌───────────────────┐  │
│  │   LLM    │    │  Tools   │    │  Memory / State   │  │
│  │(Reasoning│◄──►│(Actions) │    │(Short / Long term)│  │
│  │ Engine)  │    └──────────┘    └───────────────────┘  │
│  └──────────┘                                           │
│       │                                                 │
│  ┌────▼──────────────────────────────────────────────┐  │
│  │        Orchestration Framework (LangChain /       │  │
│  │        LangGraph)                                 │  │
│  └───────────────────────────────────────────────────┘  │
│       │                                                 │
│  ┌────▼──────┐  ┌────────────┐  ┌────────────────────┐  │
│  │Vector Store│  │External APIs│  │ Prompt Templates   │  │
│  │  (RAG)    │  │ / Databases │  │  / Instructions    │  │
│  └───────────┘  └────────────┘  └────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### Required Components

| Component | Purpose | Examples |
|---|---|---|
| **LLM / Chat Model** | The reasoning brain of the agent | Ollama (`gpt-oss:20b`, `llama3.1`), OpenAI GPT-4, Anthropic Claude |
| **Prompt Template** | Structures instructions given to the LLM | `ChatPromptTemplate`, `PromptTemplate` (LangChain) |
| **Tools** | Functions the agent can call to take actions | Web search, Python REPL, SQL query, file I/O, API calls |
| **Agent Executor / Graph** | Runs the reasoning loop and manages tool calls | `AgentExecutor` (LangChain), `StateGraph` (LangGraph) |
| **Memory** | Persists context across steps or sessions | `ConversationBufferMemory`, `MemorySaver` (LangGraph) |
| **Vector Store** | Stores embeddings for semantic retrieval (RAG) | ChromaDB, FAISS, Pinecone, pgvector |
| **Embeddings Model** | Converts text to vectors for similarity search | Ollama (`nomic-embed-text`), OpenAI `text-embedding-3-small` |
| **Document Loaders** | Ingest data from various sources | PDF, CSV, web pages, Notion, Confluence (LangChain loaders) |
| **Text Splitters** | Splits large documents into chunks for embedding | `RecursiveCharacterTextSplitter` (LangChain) |
| **Orchestration Framework** | Ties everything together | LangChain, LangGraph |

### Minimum Setup to Run an Agent

```
1. LLM (local via Ollama or remote via API)
2. At least one Tool
3. An Orchestration framework (LangChain or LangGraph)
4. A Python environment with dependencies installed
```

> **Interview Tip:** Know the difference between **tools** (specific callable functions) and **agents** (LLM + reasoning loop that decides which tool to call). An agent without tools is just a chat model.

---

## 5. How LangChain and LangGraph Empower Agentic AI

### LangChain — The Foundation Layer

> _"LangChain is a framework for developing applications powered by language models."_  
> — LangChain Documentation

LangChain provides the **building blocks** for agentic systems:

| LangChain Feature | What It Provides |
|---|---|
| **LLM / Chat Model wrappers** | Unified interface to 50+ LLM providers (Ollama, OpenAI, Anthropic, etc.) |
| **Prompt Templates** | Reusable, parameterised prompt structures with variable injection |
| **Chains (`\|` operator)** | Composable pipelines: `prompt \| llm \| output_parser` |
| **Tools & Tool decorators** | `@tool` decorator turns any Python function into an agent-callable tool |
| **Document Loaders** | Load data from PDFs, URLs, databases, cloud storage into LangChain Documents |
| **Text Splitters** | Chunk documents for embedding and retrieval |
| **Vector Store integrations** | Out-of-the-box support for ChromaDB, FAISS, Pinecone, pgvector, and more |
| **Retrievers** | Abstract interface to fetch relevant documents from any store |
| **AgentExecutor** | Runs the ReAct loop: calls tools, passes observations back to LLM, repeats |
| **Memory classes** | Short-term (`ConversationBufferMemory`) and long-term memory integrations |

**LangChain's LCEL (LangChain Expression Language)** uses the `|` pipe operator to compose chains cleanly:

```python
from langchain_core.prompts import ChatPromptTemplate
from common.llm_factory import get_chat_llm

chain = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{question}"),
]) | get_chat_llm()

response = chain.invoke({"question": "What is RAG?"})
```

---

### LangGraph — The Orchestration Layer for Complex Agents

> _"LangGraph is a library for building stateful, multi-actor applications with LLMs, used to create agent and multi-agent workflows."_  
> — LangGraph Documentation

While LangChain handles individual components and simple chains, **LangGraph adds the ability to build agents with explicit control flow, state, and cycles**.

LangGraph models an agent as a **directed graph**:
- **Nodes** = processing steps (LLM calls, tool calls, logic)
- **Edges** = transitions between steps
- **State** = a shared data object passed between nodes

```
   ┌──────────┐
   │  START   │
   └────┬─────┘
        │
   ┌────▼─────┐        ┌──────────────┐
   │  Agent   │──────► │  Tool Node   │
   │  (LLM)   │◄───────│  (Execute)   │
   └────┬─────┘        └──────────────┘
        │ (no more tool calls)
   ┌────▼─────┐
   │   END    │
   └──────────┘
```

### LangChain vs LangGraph — When to Use Which

| Scenario | Use LangChain | Use LangGraph |
|---|---|---|
| Simple prompt → response chain | ✅ | Not needed |
| Single-agent with tools (ReAct) | ✅ `AgentExecutor` | ✅ Preferred for new projects |
| Agent with conditional branching | ❌ Limited | ✅ Define conditional edges |
| Multi-agent systems | ❌ Not built for this | ✅ Each agent is a node in the graph |
| Agent with human-in-the-loop pauses | ❌ | ✅ `interrupt_before` / `interrupt_after` |
| Streaming intermediate steps | Partial | ✅ Full streaming support |
| Persistent state across sessions | Limited | ✅ Built-in checkpointing (`MemorySaver`) |
| Complex workflows with loops and retries | ❌ | ✅ Native cycle support |

> **Interview Tip:** LangGraph is built **on top of** LangChain — it uses LangChain components (LLMs, tools, prompts) inside its nodes. They are complementary, not competing. For production agentic systems, LangGraph is the recommended orchestration layer.

### Combined Architecture in This Repo

```
common/llm_factory.py
    get_llm()          → OllamaLLM       → used in simple chains (LangChain LCEL)
    get_chat_llm()     → ChatOllama      → used in agents and LangGraph nodes
    get_embeddings()   → OllamaEmbeddings → used in RAG vector store pipelines

projects/
    01_hello_langchain/   → LangChain chains (get_llm, PromptTemplate, LCEL)
    02_...                → LangGraph agent (get_chat_llm, StateGraph, tools)
    03_...                → RAG pipeline   (get_embeddings, vector store, retriever)
```

---

## Interview Cheat Sheet

| Question | Key Answer Points |
|---|---|
| What is an AI Agent? | LLM + tools + reasoning loop; autonomously plans and acts to complete a goal |
| What is the ReAct pattern? | Thought → Action (tool call) → Observation → repeat; from Yao et al. 2022 |
| LangChain vs LangGraph? | LangChain = components + simple chains; LangGraph = stateful, cyclic, multi-agent orchestration |
| What is RAG? | Retrieval-Augmented Generation — retrieve relevant docs from a vector store and inject as LLM context |
| What is a Tool in LangChain? | A Python function decorated with `@tool` that an agent can call; must have a name, description, and typed inputs |
| What is State in LangGraph? | A typed dictionary (`TypedDict`) shared across all nodes in the graph; updated by each node |
| How does memory work in agents? | Short-term: message history in the graph state; Long-term: external DB + `MemorySaver` checkpointer |
| What is LCEL? | LangChain Expression Language — the `\|` pipe syntax for composing chains: `prompt \| llm \| parser` |

---

*Next in Quick-Reference → `02_ReAct_Pattern_Deep_Dive.md`*
