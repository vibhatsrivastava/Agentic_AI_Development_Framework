# 02 — ReAct Pattern Deep Dive

> **Audience:** Beginners in Agentic AI | **Focus:** Concepts + Technical Interview Prep  
> **References:** [ReAct Paper (Yao et al., 2022)](https://arxiv.org/abs/2210.03629) · [LangChain Agents Docs](https://docs.langchain.com/docs/concepts/agents) · [LangGraph Docs](https://langchain-ai.github.io/langgraph/)

---

## Table of Contents

1. [What is the ReAct Pattern?](#1-what-is-the-react-pattern)
2. [How ReAct Works — Step by Step](#2-how-react-works--step-by-step)
3. [ReAct vs Other Agent Patterns](#3-react-vs-other-agent-patterns)
4. [ReAct in LangChain](#4-react-in-langchain)
5. [ReAct in LangGraph](#5-react-in-langgraph)
6. [What Can Go Wrong — Failure Modes](#6-what-can-go-wrong--failure-modes)
7. [Interview Cheat Sheet](#7-interview-cheat-sheet)

---

## 1. What is the ReAct Pattern?

### Simple Definition

**ReAct** = **Re**asoning + **Act**ing

ReAct is a prompting and agent design pattern where an LLM **alternates between thinking** (reasoning about what to do next) **and acting** (calling a tool or taking an action), using the result of each action to inform its next thought.

It was introduced in the research paper:
> _"ReAct: Synergizing Reasoning and Acting in Language Models"_ — Yao et al., 2022 (Google Brain / Princeton)

### The Problem It Solves

Before ReAct, LLMs had two separate modes:
- **Chain-of-Thought (CoT):** Think step by step — but only using internal knowledge, no external tools
- **Action-only agents:** Call tools — but without structured reasoning about *why*

ReAct **combines both**: the LLM thinks out loud, acts, observes the result, and updates its reasoning — in a loop.

### One-Line Summary

> _ReAct lets an LLM reason about what to do, take an action, observe the result, and repeat until the task is complete._

---

## 2. How ReAct Works — Step by Step

### The Core Loop

```
┌─────────────────────────────────────────────────────────┐
│                    ReAct Agent Loop                     │
│                                                         │
│   User Input / Goal                                     │
│         │                                               │
│         ▼                                               │
│   ┌───────────┐                                         │
│   │  THOUGHT  │  ← LLM reasons: "What do I need to do?"│
│   └─────┬─────┘                                         │
│         │                                               │
│   ┌─────▼─────┐                                         │
│   │  ACTION   │  ← LLM picks a tool + arguments        │
│   └─────┬─────┘                                         │
│         │                                               │
│   ┌─────▼──────┐                                        │
│   │OBSERVATION │  ← Tool runs, result returned to LLM  │
│   └─────┬──────┘                                        │
│         │                                               │
│         ▼                                               │
│   ┌─────────────────┐                                   │
│   │ More steps      │                                   │
│   │ needed?         │──Yes──► Back to THOUGHT           │
│   └────────┬────────┘                                   │
│            │ No                                          │
│            ▼                                             │
│   ┌──────────────────┐                                  │
│   │  FINAL ANSWER    │                                  │
│   └──────────────────┘                                  │
└─────────────────────────────────────────────────────────┘
```

### Concrete Example — Trace

**User Goal:** _"What is the capital of Australia, and what is its current population?"_

```
Thought:   I need to find the capital of Australia.
Action:    web_search("capital of Australia")
Observation: "The capital of Australia is Canberra."

Thought:   Now I need to find Canberra's current population.
Action:    web_search("Canberra population 2025")
Observation: "Canberra's population is approximately 472,000 (2025 estimate)."

Thought:   I have all the information needed to answer the question.
Final Answer: The capital of Australia is Canberra, with an estimated population
              of approximately 472,000.
```

### What Each Step Means

| Step | Who Produces It | What It Contains |
|---|---|---|
| **Thought** | LLM | Internal reasoning — what the agent is thinking, what it needs to find out next |
| **Action** | LLM | The tool name + input arguments to call (e.g., `web_search("...")`)|
| **Observation** | Tool (external) | The raw result returned by the tool — passed back to the LLM as context |
| **Final Answer** | LLM | The agent's response to the original user goal, produced when no more actions are needed |

---

### Multi-Step Example — With an Error Recovery

**User Goal:** _"Calculate the square root of 144 and then tell me if that number is prime."_

```
Thought:   I need to calculate the square root of 144. I'll use the calculator tool.
Action:    calculator("sqrt(144)")
Observation: "12"

Thought:   The square root is 12. Now I need to check if 12 is a prime number.
           A prime number has no divisors other than 1 and itself.
           12 is divisible by 2, 3, 4, 6 — so it is NOT prime.
           I can reason this out directly without a tool.
Final Answer: The square root of 144 is 12. The number 12 is not a prime number
              because it has divisors other than 1 and itself (e.g., 2, 3, 4, 6).
```

> **Key insight:** The agent used a tool for the first step and **self-reasoned** for the second — it only calls tools when needed.

---

## 3. ReAct vs Other Agent Patterns

### Pattern Overview

| Pattern | How It Plans | Tool Use | Best For |
|---|---|---|---|
| **ReAct** | Interleaved Think + Act per step | After each thought | Most general tasks; default choice |
| **Chain-of-Thought (CoT)** | Think all steps first, then respond | None | Math reasoning, no external data needed |
| **Plan-and-Execute** | Plan all steps upfront, then execute each | After planning phase | Complex, predictable multi-step workflows |
| **MRKL** | Routes to specialized "expert" modules | Per module | Tasks that need specialist sub-agents |
| **Self-Ask** | Decomposes question into sub-questions recursively | Per sub-question | Research / fact-checking workflows |

### ReAct vs Chain-of-Thought (CoT)

```
Chain-of-Thought:
─────────────────
User: "What is 15% of 240?"
LLM:  Step 1: 15% = 15/100 = 0.15
      Step 2: 0.15 × 240 = 36
Answer: 36
(No tools — all internal reasoning)

ReAct:
──────
User: "What is the current stock price of Apple multiplied by 15%?"
LLM:  Thought: I need the current stock price of Apple.
      Action:  stock_price("AAPL")
      Observation: "$189.50"
      Thought: Now I calculate 15% of $189.50.
               0.15 × 189.50 = 28.425
      Final Answer: $28.43
(Tool used to get real-time data, then reasoned over it)
```

> **Rule of thumb:** Use CoT when the LLM's training data is sufficient. Use ReAct when real-time data, external APIs, or file system access is needed.

### ReAct vs Plan-and-Execute

```
ReAct (adaptive):
─────────────────
Step 1 → Observe → Step 2 → Observe → Step 3 ...
Each step is decided AFTER seeing the previous result.
Adapts if something unexpected happens.

Plan-and-Execute (structured):
───────────────────────────────
Plan:    [Step 1, Step 2, Step 3]  ← decided upfront
Execute: Step 1 → Step 2 → Step 3
Faster for known workflows, but less adaptive.
```

---

## 4. ReAct in LangChain

### How LangChain Implements ReAct

LangChain provides the `create_react_agent` function and `AgentExecutor` to run the ReAct loop:

```
create_react_agent(llm, tools, prompt)
         │
         ▼
AgentExecutor(agent, tools)
         │
         ▼
   .invoke({"input": "..."})
         │
    Runs the loop:
    LLM → parse action → call tool → feed observation → LLM → ...
         │
         ▼
   Final Answer returned
```

### Minimal Code Example

```python
from langchain import hub
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.tools import tool
from common.llm_factory import get_chat_llm

# 1. Define a tool
@tool
def multiply(a: int, b: int) -> int:
    """Multiply two integers together."""
    return a * b

# 2. Pull the standard ReAct prompt from LangChain Hub
#    (hwchase17/react is the canonical ReAct prompt template)
prompt = hub.pull("hwchase17/react")

# 3. Build the agent
llm = get_chat_llm()
agent = create_react_agent(llm=llm, tools=[multiply], prompt=prompt)

# 4. Wrap in AgentExecutor (handles the loop, retries, output parsing)
executor = AgentExecutor(agent=agent, tools=[multiply], verbose=True)

# 5. Run
result = executor.invoke({"input": "What is 23 multiplied by 47?"})
print(result["output"])
```

**What `verbose=True` prints (the ReAct trace):**
```
> Entering new AgentExecutor chain...
Thought: I need to multiply 23 by 47.
Action: multiply
Action Input: {"a": 23, "b": 47}
Observation: 1081
Thought: I now know the final answer.
Final Answer: 23 multiplied by 47 is 1081.
> Finished chain.
```

### The ReAct Prompt Structure

The `hwchase17/react` prompt from LangChain Hub instructs the LLM to follow this exact format:

```
Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}
```

> **Interview Tip:** The `{agent_scratchpad}` placeholder is where all previous Thought/Action/Observation steps are injected on each LLM call — this is how the LLM "remembers" what it has already done in the current loop.

---

## 5. ReAct in LangGraph

### Why LangGraph for ReAct?

`AgentExecutor` is LangChain's classic ReAct runner. **LangGraph is now the recommended approach** for new projects because it gives you:
- Explicit, inspectable state at every step
- Fine-grained control over the loop (add conditions, human pause points, retries)
- First-class streaming of intermediate steps
- Built-in persistence across sessions

### LangGraph ReAct Architecture

```
                         ┌─────────────────────┐
              ┌──────────►   agent node         │
              │          │  (LLM call)          │
              │          └──────────┬──────────┘
              │                     │
              │           ┌─────────▼──────────┐
              │           │  should_continue?   │
              │           │  (conditional edge) │
              │           └──┬──────────────────┘
              │              │                │
              │         tool calls?      no tool calls?
              │              │                │
              │   ┌──────────▼──────────┐     │
              └───┤   tools node        │     ▼
                  │  (execute tools)    │   END
                  └─────────────────────┘
```

### Minimal Code Example

```python
from langgraph.prebuilt import create_react_agent
from langchain_core.tools import tool
from common.llm_factory import get_chat_llm

# 1. Define tools
@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    # In a real project, call a weather API here
    return f"The weather in {city} is sunny and 22°C."

# 2. Build the ReAct agent graph (one line with LangGraph prebuilt)
llm = get_chat_llm()
graph = create_react_agent(model=llm, tools=[get_weather])

# 3. Run
result = graph.invoke({
    "messages": [{"role": "user", "content": "What is the weather in Sydney?"}]
})
print(result["messages"][-1].content)
# → "The weather in Sydney is sunny and 22°C."
```

### State Flow in LangGraph ReAct

LangGraph's ReAct agent uses a `MessagesState` — a list of messages that grows with each step:

```
Initial State:
  messages: [HumanMessage("What is the weather in Sydney?")]

After agent node (LLM decides to call tool):
  messages: [..., AIMessage(tool_calls=[{name: "get_weather", args: {city: "Sydney"}}])]

After tools node (tool executed):
  messages: [..., ToolMessage(content="The weather in Sydney is sunny and 22°C.")]

After agent node (LLM produces final answer):
  messages: [..., AIMessage(content="The weather in Sydney is sunny and 22°C.")]

→ No more tool calls → graph reaches END
```

### AgentExecutor vs LangGraph — Which to Use?

| Feature | `AgentExecutor` (LangChain) | `create_react_agent` (LangGraph) |
|---|---|---|
| **Setup complexity** | Low | Low (prebuilt available) |
| **Intermediate step visibility** | `verbose=True` logs | Full state object at every node |
| **Streaming** | Partial | Full token + step streaming |
| **Human-in-the-loop** | Not supported | `interrupt_before=["tools"]` |
| **Persistent memory** | External workarounds | Built-in `MemorySaver` checkpointer |
| **Custom control flow** | Limited | Full — add any node/edge/condition |
| **Recommended for new projects** | No (legacy) | ✅ Yes |

---

## 6. What Can Go Wrong — Failure Modes

Understanding failure modes is critical for both production development and interviews.

| Failure Mode | What Happens | How to Handle |
|---|---|---|
| **Tool call loop** | Agent keeps calling the same tool repeatedly without progress | Set `max_iterations` in `AgentExecutor`; use LangGraph's cycle detection |
| **Hallucinated tool name** | LLM invents a tool that doesn't exist | Provide clear tool descriptions; constrain output with structured tool schemas |
| **Malformed action input** | LLM passes wrong argument types/names to a tool | Use typed Pydantic schemas for tool inputs; validate at tool entry |
| **Observation ignored** | LLM doesn't use the tool result and reasons from memory instead | Include observation explicitly in the scratchpad; reduce model temperature |
| **Infinite reasoning** | Agent never concludes — keeps adding thoughts | Set `max_iterations` / `max_execution_time` limits |
| **Context overflow** | Scratchpad grows too large for the model's context window | Summarise older steps; use a model with a larger context window |
| **Premature final answer** | Agent answers after the first observation without checking completeness | Improve the system prompt to require thorough verification |

> **Interview Tip:** Mentioning `max_iterations` and context overflow shows practical production awareness — these are real problems, not just theoretical.

---

## 7. Interview Cheat Sheet

| Question | Key Answer |
|---|---|
| **What is ReAct?** | A pattern from Yao et al. (2022) that interleaves LLM reasoning (Thought) with tool use (Action) and result processing (Observation) in a loop until a final answer is reached |
| **What does the ReAct loop look like?** | Thought → Action → Observation → Thought → ... → Final Answer |
| **What is `agent_scratchpad`?** | A placeholder in the prompt that accumulates all previous Thought/Action/Observation steps so the LLM has memory of what it already did in the current task |
| **What is `AgentExecutor`?** | LangChain's class that runs the ReAct loop — it calls the LLM, parses the action, executes the tool, feeds the observation back, and repeats |
| **LangGraph vs AgentExecutor?** | Both run ReAct; LangGraph is preferred for new projects because it provides explicit state, streaming, human-in-the-loop, and persistent memory via checkpointing |
| **What is `create_react_agent` in LangGraph?** | A prebuilt function that creates a two-node graph (agent node + tools node) connected by a conditional edge that loops until no tool calls remain |
| **How do you prevent an agent from looping forever?** | Set `max_iterations` in `AgentExecutor`, or add a step-count condition / recursion limit in LangGraph |
| **What is `MessagesState` in LangGraph?** | A built-in state schema that holds the growing list of messages (Human, AI, Tool) — each node reads and appends to this list |
| **What is the difference between Thought and Observation?** | Thought is produced by the LLM (internal reasoning); Observation is produced by an external tool (ground truth data returned to the LLM) |
| **Can ReAct agents self-correct?** | Yes — if an Observation shows an error or unexpected result, the LLM's next Thought can adapt and try a different action |

---

*Previous: [01_What_Is_Agentic_AI.md](01_What_Is_Agentic_AI.md)*  
*Next in Quick-Reference → `03_RAG_Retrieval_Augmented_Generation.md`*
