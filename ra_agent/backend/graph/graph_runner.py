"""
graph/graph_runner.py

FIXES:
1. Do NOT initialize confidence fields to None/0.0 — let LangGraph use defaults.
   Agent graphs detect first run by retries==0, not by prev_conf value.
2. Duplicate execution: acquire() guard already works — but frontend sends
   both HTTP POST and WebSocket for same query. The execution_manager handles
   this correctly. Added logging to surface when duplicate is dropped.
3. Source labels read from quality_flags (set by agent graphs) not from log.
4. Budget/timeline: pass 0 as sentinel for "not provided by user" — supervisor
   extracts from query text.
"""

import logging
import time
from datetime import datetime, timezone

from graph.decision_graph import get_graph
from graph.execution_manager import acquire, release, get_cached, store_result
from core.reliability.confidence import compute_overall_confidence
from memory.outcome_tracker import save_decision, confidence_adjustment
from utils.request_id import new_id

log = logging.getLogger("graph_runner")

IGNORE_THRESHOLD = 0.50


async def run(
    user_query: str,
    market: str,
    budget: float = 0,
    timeline_months: int = 0,
    company_name: str = "RA Groups",
    request_id: str = None,
) -> dict:
    rid = request_id or new_id()

    acquired = await acquire(rid)
    if not acquired:
        log.warning("[runner] DUPLICATE request_id=%s dropped", rid)
        return {
            "request_id": rid,
            "error":       "duplicate_request",
            "message":     "This request is already processing.",
        }

    cached = await get_cached(user_query, market, float(budget), int(timeline_months))
    if cached:
        await release(rid)
        log.info("[runner] CACHE HIT '%s'", user_query[:50])
        return {**cached, "request_id": rid, "_from_cache": True}

    try:
        return await _execute(rid, user_query, market, budget, timeline_months, company_name)
    except Exception as exc:
        log.exception("[runner] UNHANDLED ERROR rid=%s: %s", rid, exc)
        return {"request_id": rid, "error": "execution_error", "message": str(exc)}
    finally:
        await release(rid)


async def _execute(rid, user_query, market, budget, timeline_months, company_name):
    t_start = time.time()
    log.info("[runner] START rid=%s market=%r budget=%.0f timeline=%dm",
             rid, market, budget, timeline_months)

    adj = confidence_adjustment(market)

    initial_state = {
        "request_id":        rid,
        "user_query":        user_query,
        "market":            market,
        "company_name":      company_name,
        "budget":            float(budget),
        "timeline_months":   int(timeline_months) if timeline_months else 12,
        "market_retries":    0,
        "financial_retries": 0,
        "knowledge_retries": 0,
        "strategy_retries":  0,
        "quality_flags":     {},
        "agent_errors":      {},
        "execution_log":     [],
        "_confidence_adj":   adj,
        # NOTE: Do NOT initialize confidence fields here.
        # Agent graphs detect first-run via retries==0, not prev_conf value.
        # If we put 0.0 here, LangGraph passes it to agents as prev_conf=0.0
        # which zeros out the MIN rule. Leave them absent from initial state.
    }

    result = await get_graph().ainvoke(initial_state)
    elapsed = round(time.time() - t_start, 2)
    log.info("[runner] GRAPH COMPLETE elapsed=%ss", elapsed)

    mc = float(result.get("market_confidence",    0.0) or 0.0)
    fc = float(result.get("financial_confidence", 0.0) or 0.0)
    kc = float(result.get("knowledge_confidence", 0.0) or 0.0)

    # Get source labels from quality_flags (set by agent graphs)
    qf = result.get("quality_flags", {})
    ms = qf.get("market_source",    "unknown")
    fs = qf.get("financial_source", "unknown")
    ks = qf.get("knowledge_source", "internal_json")

    # Additional penalties
    effective_adj = adj
    if float(budget) == 0.0:
        effective_adj -= 0.05   # small penalty — budget extracted from query
    resolved_market = result.get("market", market)
    if resolved_market in ("UNKNOWN", "", None):
        effective_adj -= 0.10

    conf_report = compute_overall_confidence(
        market_conf    = mc,
        financial_conf = fc,
        knowledge_conf = kc,
        market_source    = ms,
        financial_source = fs,
        knowledge_source = ks,
        learning_adj = effective_adj,
    )

    loop_summary = {
        "market_retries":    max(0, int(result.get("market_retries",    0)) - 1),
        "financial_retries": max(0, int(result.get("financial_retries", 0)) - 1),
        "knowledge_retries": max(0, int(result.get("knowledge_retries", 0)) - 1),
        "strategy_retries":  max(0, int(result.get("strategy_retries",  0)) - 1),
        "ignored_agents":    conf_report["ignored_agents"],
        "elapsed_seconds":   elapsed,
    }
    loop_summary["total_retries"] = sum(
        v for k, v in loop_summary.items() if k.endswith("_retries")
    )

    strategy  = result.get("strategy_decision", {})
    decision  = strategy.get("decision", "UNKNOWN")
    score     = strategy.get("adjusted_score", 0)
    wc        = conf_report["weighted_confidence"]

    log.info("[runner] RESULT decision=%s score=%.1f confidence=%.3f(%s) ignored=%s retries=%d elapsed=%ss",
             decision, score, wc, conf_report["label"],
             conf_report["ignored_agents"], loop_summary["total_retries"], elapsed)

    for agent, details in conf_report["per_agent"].items():
        log.info("[runner]   %s conf=%.3f source=%s weight=%.2f used=%s",
                 agent, details["confidence"], details["source"],
                 details["weight"], details["used"])

    supervisor_warnings = result.get("_supervisor_warnings", [])
    for w in supervisor_warnings:
        log.warning("[runner] supervisor: %s", w)

    if decision not in ("", "UNKNOWN", "ADVISORY") and not result.get("error"):
        save_decision(rid, user_query, resolved_market, decision,
                      wc, score, conf_report["per_agent"])

    response = {
        "request_id":          rid,
        "decision":            strategy,
        "confidence_report":   conf_report,
        "market_insights":     result.get("market_insights",    {}),
        "financial_analysis":  result.get("financial_analysis", {}),
        "knowledge_summary":   result.get("knowledge_summary",  {}),
        "final_report":        result.get("final_report",       ""),
        "execution_log":       result.get("execution_log",      []),
        "loop_summary":        loop_summary,
        "supervisor_warnings": supervisor_warnings,
        "is_final":            result.get("decision_is_final",  False),
        "elapsed_seconds":     elapsed,
        "timestamp":           datetime.now(timezone.utc).isoformat(),
    }

    await store_result(user_query, market, float(budget), int(timeline_months), response)
    return response
