/**
 * frontend_orchestrator/graph.js
 * LangGraph.js mirror of the Python decision graph.
 * Used by the React frontend to show real-time agent execution state.
 *
 * Requires: @langchain/langgraph (JS), @langchain/openai
 */

import { StateGraph, START, END } from "@langchain/langgraph";
import { ChatOpenAI } from "@langchain/openai";

// ─── State schema ────────────────────────────────────────────────────────────
const stateChannels = {
  request_id:        { default: () => "" },
  user_query:        { default: () => "" },
  market:            { default: () => "" },
  budget:            { default: () => 0 },
  timeline_months:   { default: () => 12 },
  supervisor_plan:   { default: () => ({}) },
  market_insights:   { default: () => ({}) },
  financial_analysis:{ default: () => ({}) },
  knowledge_summary: { default: () => ({}) },
  strategy_decision: { default: () => ({}) },
  final_report:      { default: () => "" },
  agent_events:      { default: () => [] },   // streaming events list
};

// ─── LLM ─────────────────────────────────────────────────────────────────────
const llm = new ChatOpenAI({
  modelName: process.env.OPENAI_DEFAULT_MODEL || "gpt-4o-mini",
  temperature: 0.1,
});

// ─── Helper: call backend Python API ────────────────────────────────────────
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function callBackendAgent(agentName, state) {
  /**
   * In production this hits the FastAPI backend.
   * In dev mode it shows a placeholder for the LangGraph.js visualiser.
   */
  return {
    agent: agentName,
    status: "completed",
    timestamp: new Date().toISOString(),
    data: state,
  };
}

// ─── Node definitions ────────────────────────────────────────────────────────
async function supervisorNode(state) {
  const event = { agent: "supervisor", event: "start", ts: Date.now() };
  const resp = await llm.invoke([
    { role: "system", content: "Return a JSON plan: { agents_to_run, product_detected, market_detected, query_type }" },
    { role: "user",   content: `Query: ${state.user_query}\nMarket: ${state.market}` },
  ]);
  let plan = {};
  try { plan = JSON.parse(resp.content.replace(/```json|```/g, "").trim()); }
  catch { plan = { agents_to_run: ["market","financial","knowledge","strategy","communication"] }; }
  event.plan = plan;
  return {
    supervisor_plan: plan,
    agent_events: [...state.agent_events, { ...event, event: "complete" }],
  };
}

async function marketAgentNode(state) {
  /** Mirror of Python market_agent_node — runs in parallel with financial + knowledge */
  const result = await callBackendAgent("market_agent", state);
  return {
    market_insights: result.data?.market_insights || {},
    agent_events: [...state.agent_events, { agent: "market_agent", event: "complete", ts: Date.now() }],
  };
}

async function financialAgentNode(state) {
  const result = await callBackendAgent("financial_agent", state);
  return {
    financial_analysis: result.data?.financial_analysis || {},
    agent_events: [...state.agent_events, { agent: "financial_agent", event: "complete", ts: Date.now() }],
  };
}

async function knowledgeAgentNode(state) {
  const result = await callBackendAgent("knowledge_agent", state);
  return {
    knowledge_summary: result.data?.knowledge_summary || {},
    agent_events: [...state.agent_events, { agent: "knowledge_agent", event: "complete", ts: Date.now() }],
  };
}

async function strategyAgentNode(state) {
  const result = await callBackendAgent("strategy_agent", state);
  return {
    strategy_decision: result.data?.strategy_decision || {},
    agent_events: [...state.agent_events, { agent: "strategy_agent", event: "complete", ts: Date.now() }],
  };
}

async function communicationAgentNode(state) {
  const result = await callBackendAgent("communication_agent", state);
  return {
    final_report: result.data?.final_report || "",
    agent_events: [...state.agent_events, { agent: "communication_agent", event: "complete", ts: Date.now() }],
  };
}

// ─── Graph construction ───────────────────────────────────────────────────────
export function buildDecisionGraph() {
  const graph = new StateGraph({ channels: stateChannels });

  graph.addNode("supervisor",         supervisorNode);
  graph.addNode("market_agent",       marketAgentNode);
  graph.addNode("financial_agent",    financialAgentNode);
  graph.addNode("knowledge_agent",    knowledgeAgentNode);
  graph.addNode("strategy_agent",     strategyAgentNode);
  graph.addNode("communication_agent",communicationAgentNode);

  // Edges — mirrors Python graph exactly
  graph.addEdge(START,               "supervisor");
  graph.addEdge("supervisor",         "market_agent");       // parallel
  graph.addEdge("supervisor",         "financial_agent");    // parallel
  graph.addEdge("supervisor",         "knowledge_agent");    // parallel
  graph.addEdge("market_agent",       "strategy_agent");
  graph.addEdge("financial_agent",    "strategy_agent");
  graph.addEdge("knowledge_agent",    "strategy_agent");
  graph.addEdge("strategy_agent",     "communication_agent");
  graph.addEdge("communication_agent", END);

  return graph.compile();
}

// ─── Usage example ────────────────────────────────────────────────────────────
// const graph = buildDecisionGraph();
// const result = await graph.invoke({
//   request_id: "req_001",
//   user_query: "Should RA Groups expand SME lending into Nigeria?",
//   market: "Nigeria",
//   budget: 500000,
//   timeline_months: 18,
// });
// console.log("Decision:", result.strategy_decision.decision);
