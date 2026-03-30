"""
schemas/graph_state.py

The single shared state object that flows through every node in the LangGraph.
This is the backbone of the agentic system — every agent reads from and writes
to this TypedDict. LangGraph merges writes automatically across parallel nodes.

Key design decisions:
- `retry_count` per agent enables backward loops when quality is low
- `quality_flags` lets the strategy node reject and loop back
- `routing_decision` tells the graph where to go next (forward, loop, end)
- Both GO and NO_GO are equal-value decisions — confidence reflects accuracy
"""

from typing import Annotated, Dict, List, Optional, Any
from typing_extensions import TypedDict
import operator


# ─── Reducer helpers ─────────────────────────────────────────────────────────
# LangGraph uses these to merge state from parallel nodes

def _last_write(a, b):
    """Last writer wins — used for scalar fields."""
    return b if b is not None else a


def _merge_dict(a: dict, b: dict) -> dict:
    """Deep merge two dicts — used for structured agent outputs."""
    if not a:
        return b or {}
    if not b:
        return a or {}
    merged = dict(a)
    merged.update(b)
    return merged


def _append_list(a: list, b: list) -> list:
    """Append items — used for audit trail and loop history."""
    return (a or []) + (b or [])


# ─── Main State ───────────────────────────────────────────────────────────────

class AgentState(TypedDict, total=False):

    # ── Input ────────────────────────────────────────────────────────────────
    request_id:        Annotated[str,  _last_write]
    user_query:        Annotated[str,  _last_write]
    market:            Annotated[str,  _last_write]
    company_name:      Annotated[str,  _last_write]
    budget:            Annotated[float, _last_write]
    timeline_months:   Annotated[int,  _last_write]
    product_type:      Annotated[str,  _last_write]  # extracted by supervisor

    # ── Supervisor routing ───────────────────────────────────────────────────
    supervisor_plan:        Annotated[Dict,         _last_write]
    next_node:              Annotated[str,          _last_write]   # routing signal
    routing_decision:       Annotated[str,          _last_write]   # "parallel_research" | "strategy" | "retry_market" | etc.

    # ── Agent outputs (written by each agent node) ───────────────────────────
    market_insights:        Annotated[Dict,         _merge_dict]
    financial_analysis:     Annotated[Dict,         _merge_dict]
    knowledge_summary:      Annotated[Dict,         _merge_dict]
    strategy_decision:      Annotated[Dict,         _last_write]
    final_report:           Annotated[str,          _last_write]

    # ── Quality & confidence per agent ───────────────────────────────────────
    # Each agent writes its own confidence score. Strategy reads all of them.
    market_confidence:      Annotated[float,        _last_write]   # 0.0 – 1.0
    financial_confidence:   Annotated[float,        _last_write]
    knowledge_confidence:   Annotated[float,        _last_write]
    strategy_confidence:    Annotated[float,        _last_write]

    # ── Loop control ─────────────────────────────────────────────────────────
    # Agents that need to retry increment their counter
    market_retries:         Annotated[int,          _last_write]
    financial_retries:      Annotated[int,          _last_write]
    knowledge_retries:      Annotated[int,          _last_write]
    strategy_retries:       Annotated[int,          _last_write]

    # ── Quality flags (set by strategy node to request specific retries) ─────
    quality_flags:          Annotated[Dict,         _merge_dict]
    # e.g. {"market_data_insufficient": True, "need_deeper_financial": True}

    # ── Audit trail (append-only) ─────────────────────────────────────────────
    execution_log:          Annotated[List,         _append_list]
    # Each agent appends one entry: {agent, timestamp, action, result_summary}

    # ── Error tracking ────────────────────────────────────────────────────────
    agent_errors:           Annotated[Dict,         _merge_dict]
    # e.g. {"market_agent": "World Bank timeout", "financial_agent": None}

    # ── Final confidence (set by communication node) ─────────────────────────
    weighted_confidence:    Annotated[float,        _last_write]
    confidence_label:       Annotated[str,          _last_write]   # "High" | "Medium" | "Low"
    decision_is_final:      Annotated[bool,         _last_write]
