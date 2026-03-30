# RA Agent System — Multi-Agent Decision Intelligence

A production-grade autonomous decision system using **LangGraph** (real graph,
not a chain), **LangChain**, and **OpenAI**.  Five specialised agents work
concurrently, loop back when data quality is poor, and synthesise an honest
GO / GO_WITH_CONDITIONS / WAIT / NO_GO decision.

---

## Project Structure

```
ra_agent/
├── backend/                  ← FastAPI + LangGraph
│   ├── main.py               ← FastAPI app, HTTP + WebSocket routes
│   ├── requirements.txt
│   ├── .env.example
│   │
│   ├── config/
│   │   ├── settings.py       ← All env vars, paths, limits
│   │   ├── llm_config.py     ← Cached LLM instances (fast vs reason models)
│   │   └── langsmith_config.py
│   │
│   ├── schemas/
│   │   ├── graph_state.py    ← Shared TypedDict with Annotated reducers
│   │   └── api_models.py     ← Pydantic request/response models
│   │
│   ├── core/
│   │   ├── calculations/
│   │   │   └── financial.py  ← Deterministic ROI/IRR/payback maths
│   │   └── reliability/
│   │       └── market_data.py ← Static fallbacks for 20+ countries
│   │
│   ├── agents/
│   │   ├── market_agent/
│   │   │   ├── prompt.py     ← All prompt templates
│   │   │   ├── tools.py      ← REST Countries, World Bank, DuckDuckGo
│   │   │   ├── agent.py      ← ReAct tool-calling loop
│   │   │   ├── graph.py      ← LangGraph node + quality assessment
│   │   │   └── schema.py     ← Pydantic output schema
│   │   ├── financial_agent/  ← World Bank rates, yfinance ETF sentiment
│   │   ├── knowledge_agent/  ← Internal RA Groups JSON + web search
│   │   ├── strategy_agent/   ← Scoring rubric, hard overrides, retry
│   │   └── communication_agent/ ← Natural language executive report
│   │
│   ├── supervisor/
│   │   └── supervisor_graph.py ← Query analysis, routing signals
│   │
│   ├── graph/
│   │   ├── decision_graph.py ← THE GRAPH: nodes, edges, conditional routers
│   │   └── graph_runner.py   ← Invokes graph, builds final response
│   │
│   ├── streaming/
│   │   └── streamer.py       ← WebSocket connection registry + event senders
│   │
│   ├── memory/
│   │   └── outcome_tracker.py ← Learning loop: saves decisions, adjusts confidence
│   │
│   └── data/
│       └── ra_groups_knowledge.json
│
└── frontend/                 ← React + Vite + Tailwind
    ├── src/
    │   ├── store/
    │   │   └── useAgentStore.js  ← Zustand global state
    │   ├── services/
    │   │   ├── wsService.js      ← WebSocket client
    │   │   └── apiService.js     ← HTTP API client
    │   ├── hooks/
    │   │   └── useDecision.js    ← Orchestrates WS + HTTP + store
    │   ├── components/
    │   │   ├── timeline/         ← Real-time agent execution timeline
    │   │   ├── decision/         ← Decision card with score breakdown
    │   │   ├── chat/             ← Messages + query form
    │   │   └── ui/               ← Header, confidence panel, welcome screen
    │   └── pages/
    │       └── ChatPage.jsx      ← Main layout (chat + sidebar)
    └── package.json
```

---

## Graph Architecture

```
START
  │
supervisor                       ← Extracts product/market, sets routing
  │
  ├─────────────────────────┐
  │           │              │   ← PARALLEL (same LangGraph superstep)
market      financial     knowledge
  │           │              │
  └─────┬─────┘──────────────┘
        │
   quality_router                ← Conditional edge — reads quality_flags
        │
   ┌────┴──────────────────────┐
   │                           │
retry_market / _financial /  strategy_agent
retry_knowledge                  │
(backward loops)            quality_router_2
                                 │
                    ┌────────────┴──────────┐
                    │                       │
              strategy_retry         communication_agent
              (backward loop)               │
                                           END
```

**Key design properties:**

- Both GO and NO_GO are equal-value outcomes — confidence reflects *accuracy*, not positivity
- Negative decisions with 90%+ confidence are as correct as positive ones
- `quality_router` reads `quality_flags` from state — if any agent's confidence < MIN_CONFIDENCE, it loops back
- Hard overrides (inflation >30%, deeply negative IRR) force NO_GO before the LLM even runs
- Strategy agent's score is verified by code — if LLM says GO but score=45, code overrides to GO_WITH_CONDITIONS
- LLMs never compute financial numbers — those are always deterministic Python code

---

## Setup

### Backend

```bash
cd ra_agent/backend

# 1. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env — add your OPENAI_API_KEY

# 4. Copy data file from your existing project
cp ~/Desktop/multi_agent_ai/backend_v2/data/ra_groups_knowledge.json data/

# 5. Run
uvicorn main:app --reload
```

Backend runs at: http://localhost:8000
API docs at:     http://localhost:8000/docs

### Frontend

```bash
cd ra_agent/frontend

# 1. Install
npm install

# 2. Run
npm run dev
```

Frontend runs at: http://localhost:3000

---

## API Endpoints

| Method | Path            | Description                           |
|--------|-----------------|---------------------------------------|
| GET    | /api/health     | Health check                          |
| POST   | /api/decision   | Run full agent pipeline (HTTP)        |
| GET    | /api/history    | Decision history summary              |
| POST   | /api/outcome    | Record real outcome (learning loop)   |
| WS     | /ws/decision    | WebSocket — same pipeline + streaming |

### POST /api/decision

```json
{
  "user_query":      "Should RA Groups expand SME lending into UAE?",
  "market":          "UAE",
  "budget":          2000000,
  "timeline_months": 18
}
```

### Response

```json
{
  "request_id": "req_1234567_abc",
  "decision": {
    "decision":         "GO_WITH_CONDITIONS",
    "adjusted_score":   56.4,
    "confidence_pct":   78,
    "market_component": 28,
    "financial_component": 18,
    "strategic_component": 16,
    "rationale":    ["..."],
    "key_risks":    ["..."],
    "conditions":   ["..."],
    "next_steps":   ["..."],
    "summary":      "..."
  },
  "confidence_report": {
    "weighted_confidence": 0.87,
    "label": "High",
    "per_agent": { "market_agent": {"confidence": 0.90}, ... }
  },
  "market_insights":    { ... },
  "financial_analysis": { ... },
  "knowledge_summary":  { ... },
  "final_report":       "# Decision Report: ...",
  "loop_summary": {
    "market_retries": 1,
    "financial_retries": 0,
    "total_attempts": 2
  }
}
```

---

## Environment Variables

| Variable               | Default         | Description                     |
|------------------------|-----------------|---------------------------------|
| OPENAI_API_KEY         | required        | OpenAI API key                  |
| OPENAI_DEFAULT_MODEL   | gpt-4o-mini     | Fast agents model               |
| OPENAI_STRATEGY_MODEL  | gpt-4o          | Strategy + comms model          |
| LANGSMITH_API_KEY      | optional        | LangSmith tracing               |
| MAX_AGENT_RETRIES      | 2               | Max backward loop iterations    |
| MIN_CONFIDENCE         | 0.55            | Below this → retry agent        |
| API_PORT               | 8000            | Backend port                    |
| CORS_ORIGINS           | localhost:3000  | Frontend origins                |

---

## How Decisions Are Made

The strategy agent applies a strict rubric that the code then verifies:

| Score Range | Decision            |
|-------------|---------------------|
| ≥ 68        | GO                  |
| 50 – 67     | GO_WITH_CONDITIONS  |
| 33 – 49     | WAIT                |
| < 33        | NO_GO               |

Score = Market(0-40) + Financial(0-40) + Strategic(0-20)

**Hard overrides (bypass scoring entirely):**
- Inflation > 30% → NO_GO
- IRR < -20% → NO_GO  
- Budget exceeds policy AND risk = Very High → NO_GO
- All agent confidence < 0.45 → WAIT (data too poor to decide)

---

## Why Different Queries Get Different Answers

| Query                            | Expected Result       | Why                                      |
|----------------------------------|-----------------------|------------------------------------------|
| UAE SME lending $2M 18mo         | GO_WITH_CONDITIONS    | Good market, adequate financials         |
| Nigeria $500k 18mo               | WAIT                  | High inflation (28%), very high risk     |
| Africa branch $200k              | NO_GO                 | Too small, no experience, high risk      |
| India (proven expansion)         | GO                    | Past success, high market score          |
| Singapore (Very High competition) | WAIT/NO_GO           | Mature market, hard entry                |
