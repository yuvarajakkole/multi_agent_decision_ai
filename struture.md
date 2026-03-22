# RA Agent System — Multi-Agent Decision Intelligence Platform
 here we use openai llm Api
## 1. Project Overview

**RA Agent System** is a modular **Agentic AI decision-making platform** designed to analyze complex business questions using a team of specialized AI agents orchestrated through **LangGraph**.

Instead of relying on a single LLM response, the system simulates a **collaborative decision process** between domain experts.

Example query:

> “Should RA Groups expand its AI-based SME lending platform into the UAE market?”

The system processes the request through multiple agents responsible for:

* Market research
* Financial analysis
* Internal company knowledge
* Strategic evaluation
* Executive communication

Each agent contributes structured insights that ultimately produce a **final business decision report**.

---

# 2. Core Technology Stack

## Backend

* Python
* FastAPI
* LangChain
* LangGraph
* WebSockets
* LangSmith (observability)
* OpenAI / LLM APIs

## AI Techniques

* ReAct prompting
* Tool-augmented reasoning
* Chain-of-Thought reasoning
* Multi-agent orchestration
* Structured JSON outputs

## Memory & State

* LangGraph checkpoint memory
* `MemorySaver` state persistence

## Frontend

* React
* LangChain Chat UI
* WebSocket streaming
* Agent execution timeline UI

---

# 3. System Architecture

```
User
 │
 ▼
Frontend (LangChain Chat UI)
 │
 ▼
WebSocket Connection
 │
 ▼
FastAPI Backend
 │
 ▼
LangGraph Execution Engine
 │
 ▼
Supervisor Agent
 │
 ├── Market Research Agent
 ├── Financial Risk Agent
 ├── Knowledge Agent
 │
 ▼
Strategy Agent
 │
 ▼
Communication Agent
 │
 ▼
Streaming Results → Frontend
```

The system processes queries **step-by-step**, streaming each agent’s reasoning process to the UI.

---

# 4. Project Directory Structure

```
intelligent_agent/

backend/
│
├── main.py
├── websocket_server.py
│
├── config/
│   ├── settings.py
│   ├── llm_config.py
│   └── langsmith_config.py
│
├── api/
│   ├── http_routes.py
│   └── websocket_routes.py
│
├── graph/
│   ├── decision_graph.py
│   ├── graph_runner.py
│   └── graph_state.py
│
├── supervisor/
│   ├── supervisor_agent.py
│   ├── supervisor_prompt.py
│   ├── supervisor_graph.py
│   ├── supervisor_tools.py
│   └── routing_logic.py
│
├── agents/
│
│   ├── market_agent/ # and this market agent will see analyse the market by user query- like user will meantion a location base on that location it will give me that product (which user want to plant in that location ) where it works or not and marksize and compitation of that product in location.
│   │   ├── agent.py # agent which handels this full work and 
│   │   ├── prompt.py # prompts for gathering informationa and geting work from llm
│   │   ├── tools.py # tools used for market data gathering add more tools
│   │   ├── graph.py # connecting the agent with tools in well strutured way 
│   │   └── schema.py # output struture and all, where this output will be used for other agents for agent to agent connect.
│
│   ├── financial_agent/ #here also all files hase there own respponsibility and role to get better answers
│   │   ├── agent.py 
│   │   ├── prompt.py
│   │   ├── tools.py
│   │   ├── graph.py
│   │   └── schema.py
│
│   ├── knowledge_agent/
│   │   ├── agent.py
│   │   ├── prompt.py
│   │   ├── tools.py
│   │   ├── graph.py
│   │   └── schema.py
│
│   ├── strategy_agent/
│   │   ├── agent.py
│   │   ├── prompt.py
│   │   ├── tools.py
│   │   ├── graph.py
│   │   └── schema.py
│
│   └── communication_agent/
│       ├── agent.py
│       ├── prompt.py
│       ├── tools.py
│       ├── graph.py
│       └── schema.py
│
├── memory/
│   ├── session_memory.py
│   └── conversation_store.py
│
├── streaming/
│   ├── websocket_manager.py
│   ├── agent_step_streamer.py
│   └── event_models.py
│
├── schemas/
│   ├── api_models.py
│   └── agent_state_schema.py
│
├── utils/
│   ├── request_id.py
│   └── json_helpers.py
│
└── tests/
    ├── graph_tests.py
    ├── agent_tests.py
    └── websocket_tests.py
# here we use 2 terminals like one for frontend and another one for backend
frontend/
│
└── langchain-chat-ui/
    │
    ├── components/
    │   ├── chat_window.tsx
    │   ├── agent_timeline.tsx
    │   ├── agent_card.tsx
    │   └── status_indicator.tsx
    │
    ├── hooks/
    │   └── useWebSocketStream.ts
    │
    ├── services/
    │   └── websocket_client.ts
    │
    └── pages/
        └── chat.tsx
```

---

# 5. Backend Workflow

## Step-by-Step Execution

1. User sends query from frontend.
2. Frontend opens WebSocket connection.
3. Backend receives query.
4. Supervisor agent analyzes intent.
5. Supervisor selects required agents.
6. Selected agents execute sequentially or in parallel.
7. Agents write outputs into shared state.
8. Strategy agent evaluates combined insights.
9. Communication agent produces final report.
10. Results stream back to UI.

---

# 6. Shared Graph State

All agents share a **global state object**.

Example:

```python
class AgentState(TypedDict):
    user_query: str
    market: str

    market_insights: dict
    financial_analysis: dict
    knowledge_summary: dict

    strategy_decision: dict
    final_report: str
```

Agents read/write this state to exchange information.

---

# 7. Orchestration Using LangGraph

## Graph Nodes

```
Supervisor
MarketAgent
FinancialAgent
KnowledgeAgent
StrategyAgent
CommunicationAgent
```

## Graph Edges

```
START → Supervisor

Supervisor → MarketAgent
Supervisor → FinancialAgent
Supervisor → KnowledgeAgent

MarketAgent → StrategyAgent
FinancialAgent → StrategyAgent
KnowledgeAgent → StrategyAgent

StrategyAgent → CommunicationAgent

CommunicationAgent → END
```

## Optional Cycles

Agents may re-execute if confidence is low.

Example loop:

```
StrategyAgent → MarketAgent → StrategyAgent
```

This improves decision quality.

---

# 8. Agent Responsibilities

## 8.1 Supervisor Agent

### Role

Acts as the **system orchestrator**.

### Responsibilities

* Understand user intent
* Select relevant agents
* Control graph routing
* Merge results

### Inputs

```
user_query
```

### Outputs

```
agents_to_run
execution_plan
```

### Tools

```
intent_classifier
query_parser
task_planner
```

---

# 8.2 Market Research Agent

### Role

Analyze external market conditions.

### Responsibilities

* Market size estimation
* Competitive landscape
* Regulatory environment
* Growth outlook

### Input

```
user_query
target_market
```

### Output

```json
{
 "market_size": "...",
 "growth_rate": "...",
 "competition": "...",
 "market_attractiveness": "High"
}
```

### Tools

```python
@tool
def fetch_market_news():
    pass

@tool
def get_fintech_trends():
    pass

@tool
def get_market_size_estimate():
    pass

@tool
def get_competitor_analysis():
    pass
```

---

# 8.3 Financial Risk Agent

### Role

Evaluate financial feasibility.

### Responsibilities

* ROI projections
* Investment analysis
* Economic indicators
* Credit risk

### Input

```
market_insights
budget
timeline
```

### Output

```json
{
 "expected_roi": "...",
 "risk_level": "Medium",
 "financial_attractiveness": "Strong"
}
```

### Tools

```python
@tool
def fetch_interest_rates():
    pass

@tool
def calculate_roi():
    pass

@tool
def analyze_macro_indicators():
    pass
```

---

# 8.4 Knowledge Agent

### Role

Use internal company data. file location = data/ra_groups_knowledge.json

### Responsibilities

* Retrieve company history
* Evaluate strategic alignment
* Review previous expansions

### Input

```
user_query
company_dataset
```

### Output

```json
{
 "company_strengths": [],
 "past_expansions": [],
 "strategic_fit": "High"
}
```

### Tools

```python
@tool
def search_internal_dataset():
    pass

@tool
def retrieve_company_strategy():
    pass
```

---

# 8.5 Strategy Agent

### Role

Combine all insights.

### Responsibilities

* Compare opportunities
* Evaluate risks
* Produce final decision

### Inputs

```
market_insights
financial_analysis
knowledge_summary
```

### Output 

```
GO
GO_WITH_CONDITIONS
WAIT
NO_GO
```

---

# 8.6 Communication Agent

### Role

Produce final decision report.

### Responsibilities

* Convert structured data into executive report
* Make decision easy to understand

### Output
output with well strutures answer from giving the full details to llm to genarate natural lagavage answers

```
Executive Summary
Market Analysis
Financial Insights
Risks
Recommendations
```

---

# 9. Prompting Strategy

Agents use **ReAct prompting**.

Structure:

```
System Prompt
Developer Prompt
User Prompt
Chain-of-Thought Reasoning
Tool Calls
Final Structured Output
```

Example template:

```
You are a financial risk analyst.

Context:
RA Groups expansion decision.

Instructions:
Evaluate ROI and risk.

Output JSON:
{
 "roi": "...",
 "risk_level": "...",
 "financial_attractiveness": "..."
}
```

---

# 10. Memory Management

Memory uses LangGraph checkpointing.

```
from langgraph.checkpoint.memory import MemorySaver
```

Responsibilities:

* preserve execution state
* allow retries
* enable loops

---

# 11. Streaming Layer

WebSocket streaming enables **real-time agent updates**.

Example event:

```json
{
 "event": "agent_start",
 "agent": "market_agent"
}
```

UI displays:

```
Supervisor thinking...
Market Agent analyzing...
Financial Agent running...
Strategy Agent deciding...
Communication Agent generating report...
```

---

# 12. Frontend Architecture

Frontend uses **LangChain Chat UI**.

Components:

```
chat_window
agent_timeline
agent_cards
status_indicators
```

---

# 13. Frontend → Backend Flow

```
User input
 ↓
React UI
 ↓
WebSocket request
 ↓
FastAPI backend
 ↓
LangGraph execution
 ↓
Streaming updates
 ↓
UI timeline update
 ↓
Final decision report
```

---

# 14. Final Output Format

Example response:

```json
{
 "decision": "GO_WITH_CONDITIONS",
 "confidence": 82,
 "summary": "Expansion into UAE is attractive but requires partnerships.",
 "rationale": [
  "Growing SME demand",
  "Moderate competition"
 ],
 "risks": [
  "Regulatory approval",
  "Currency volatility"
 ],
 "next_steps": [
  "Local partnerships",
  "Pilot launch"
 ]
}
```

---

# 15. Advantages of This Architecture

* Modular agent design
* Clear separation of responsibilities
* Streaming UI feedback
* Structured reasoning
* Scalable orchestration
* Enterprise-grade architecture

---

# 16. Future Improvements

Possible extensions:

* Dynamic agent selection
* Parallel agent execution
* RAG-based knowledge agents
* Reinforcement feedback loops
* Autonomous task planning

---

# 17. LLM Configuration & OpenAI Integration

This project relies on OpenAI large language models to power the reasoning capabilities of each agent.

The system uses different model sizes depending on the task complexity to balance cost, speed, and reasoning quality.

17.1 OpenAI API Key Configuration

The OpenAI API key is required to run the agents.

Store the key in an environment variable.

Example .env file:

OPENAI_API_KEY=your_openai_api_key_here
OPENAI_DEFAULT_MODEL=gpt-4o-mini
OPENAI_STRATEGY_MODEL=gpt-4o

Never commit the .env file to version control.

17.2 LLM Configuration File

File:

backend/config/llm_config.py

Purpose:

Centralizes model configuration for the entire system.

Example configuration:

from langchain_openai import ChatOpenAI
import os

DEFAULT_MODEL = os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini")
STRATEGY_MODEL = os.getenv("OPENAI_STRATEGY_MODEL", "gpt-4o")

def get_fast_llm():
    return ChatOpenAI(
        model=DEFAULT_MODEL,
        temperature=0.3
    )

def get_reasoning_llm():
    return ChatOpenAI(
        model=STRATEGY_MODEL,
        temperature=0.2
    )
17.3 Model Selection Strategy

Different agents use different models depending on reasoning requirements.

Supervisor Agent → gpt-4o-mini
Market Agent → gpt-4o-mini
Financial Agent → gpt-4o-mini
Knowledge Agent → gpt-4o-mini

Strategy Agent → gpt-4o
Communication Agent → gpt-4o

Reason:

Most agents perform information analysis

Strategy and communication require deep synthesis and decision making

Using larger models only where needed improves:

cost efficiency

response latency

system scalability

17.4 OpenAI Structured Output

Agents must return structured JSON responses to ensure reliable downstream processing.

Example structured output schema:

{
 "market_size": "Large",
 "growth_rate": "12%",
 "competition": "Moderate",
 "market_attractiveness": "High"
}

Example implementation:

response = llm.invoke(prompt)

structured_output = json.loads(response.content)

Benefits:

easier agent-to-agent communication

reliable graph state updates

predictable UI rendering

17.5 Using OpenAI with Tools (ReAct Pattern)

Agents use the ReAct reasoning pattern.

ReAct stands for:

Reason → Act → Observe → Repeat

The agent first reasons about the problem, then decides whether to call a tool.

Example reasoning flow:

Thought: I need market size data.
Action: call get_market_size tool
Observation: market size is $25B
Thought: now evaluate competition
Action: call competitor_analysis tool
Observation: competition moderate
Final Answer: market attractiveness high

Example tool definition:

from langchain.tools import tool

@tool
def fetch_market_news(country: str) -> str:
    """Fetch recent fintech news for a specific country."""

Agent tool usage:

agent = create_react_agent(
    llm,
    tools=[fetch_market_news]
)
18.6 Tool Caching Strategy

External API calls can be expensive.

The system caches tool outputs whenever possible.

Example:

from functools import lru_cache

@lru_cache(maxsize=128)
def fetch_market_data(country):
    ...

Benefits:

reduces API cost

improves response speed

avoids repeated tool calls

17.7 Avoiding Infinite Reasoning Loops

Agent loops are limited by a maximum iteration count.

Example configuration:

max_iterations = 4

LangGraph enforces this limit to prevent:

infinite tool loops

unnecessary token usage

17.8 LLM Prompting Strategy

Agents follow a multi-layer prompt structure.

System Prompt

Defines the role of the agent.

Example:

You are a senior financial analyst specializing in fintech investments.
Developer Prompt

Defines task instructions.

Example:

Evaluate the financial feasibility of the expansion using ROI and risk analysis.
User Prompt

Contains the user query.

Example:

Should RA Groups launch AI SME lending in UAE?
Chain-of-Thought Reasoning

Encourages step-by-step reasoning.

Example:

Think step-by-step before giving the final answer.
Tool Prompts

Specify when tools should be used.

Example:

If market data is missing, use the market_data tool.
Planning Prompt

Used mainly by the supervisor.

Example:

Break this decision problem into sub-tasks and assign agents.
17.9 Model Temperature Strategy

Agents use low temperature settings for deterministic reasoning.

Supervisor → 0.2
Market Agent → 0.3
Financial Agent → 0.2
Knowledge Agent → 0.2
Strategy Agent → 0.1
Communication Agent → 0.1

This ensures consistent outputs.

17.10 LLM Performance Optimization

Several techniques are used to optimize performance.

Model tiering

Use smaller models where possible.

Tool caching

Avoid repeated API calls.

Loop limits

Prevent infinite reasoning.

Structured outputs

Avoid unnecessary token generation.

17.11 LangSmith Integration

All agent executions are automatically traced using LangSmith.

LangSmith records:

prompts

responses

tool calls

token usage

latency

This allows developers to debug agent behavior.



# 18. Summary

This system represents a **modern agentic AI architecture** combining:

* multi-agent reasoning
* tool-based decision making
* graph orchestration
* real-time streaming
* structured executive reporting

The design is similar to architectures used in **enterprise AI decision platforms**.

---

End of documentation.
