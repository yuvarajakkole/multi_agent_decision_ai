/**
 * frontend_orchestrator/graph.js
 * LangGraph.js frontend orchestrator.
 *
 * Mirrors the Python backend graph in JavaScript so the React UI
 * can track agent status in real-time via WebSocket events.
 *
 * Install: npm install @langchain/langgraph @langchain/core
 */
import { StateGraph, START, END } from "@langchain/langgraph";
import { Annotation }             from "@langchain/langgraph";

// ─────────────────────────────────────────────────────────────────────────────
// STATE SCHEMA
// ─────────────────────────────────────────────────────────────────────────────
const AgentState = Annotation.Root({
  // Input
  request_id:      Annotation({ default: () => "" }),
  user_query:      Annotation({ default: () => "" }),
  market:          Annotation({ default: () => "" }),
  budget:          Annotation({ default: () => 1_000_000 }),
  timeline_months: Annotation({ default: () => 12 }),

  // UI status per agent  ("pending" | "running" | "complete" | "error")
  supervisor_status:            Annotation({ default: () => "pending" }),
  market_agent_status:          Annotation({ default: () => "pending" }),
  financial_agent_status:       Annotation({ default: () => "pending" }),
  knowledge_agent_status:       Annotation({ default: () => "pending" }),
  strategy_agent_status:        Annotation({ default: () => "pending" }),
  communication_agent_status:   Annotation({ default: () => "pending" }),

  // Outputs hydrated from backend WebSocket events
  market_insights:    Annotation({ default: () => null }),
  financial_analysis: Annotation({ default: () => null }),
  knowledge_summary:  Annotation({ default: () => null }),
  strategy_decision:  Annotation({ default: () => null }),
  final_report:       Annotation({ default: () => "" }),
  confidence_report:  Annotation({ default: () => null }),
  decision_trace:     Annotation({ default: () => null }),
  final_confidence:   Annotation({ default: () => 0 }),

  // Error & completion flags
  errors:            Annotation({ default: () => [] }),
  pipeline_complete: Annotation({ default: () => false }),
});

// ─────────────────────────────────────────────────────────────────────────────
// WEBSOCKET CLIENT
// ─────────────────────────────────────────────────────────────────────────────
let _ws = null;
const _listeners = new Map();

export async function connectWebSocket(url = "ws://localhost:8000/ws/decision") {
  _ws = new WebSocket(url);
  _ws.onmessage = (e) => {
    const data = JSON.parse(e.data);
    for (const [key, handlers] of _listeners) {
      if (key === data.event || key === "*") {
        handlers.forEach(fn => fn(data));
      }
    }
  };
  return new Promise((resolve, reject) => {
    _ws.onopen  = () => resolve(_ws);
    _ws.onerror = reject;
  });
}

export function onEvent(eventName, handler) {
  if (!_listeners.has(eventName)) _listeners.set(eventName, []);
  _listeners.get(eventName).push(handler);
}

export function sendQuery(payload) {
  if (_ws?.readyState === WebSocket.OPEN) _ws.send(JSON.stringify(payload));
}

// ─────────────────────────────────────────────────────────────────────────────
// GRAPH NODES  (UI state management, driven by backend WS events)
// ─────────────────────────────────────────────────────────────────────────────
function waitForEvent(agentName) {
  return new Promise(resolve => {
    const unsubStart = (d) => {
      if (d.agent === agentName) resolve({ [`${agentName}_status`]: "running" });
    };
    const unsubDone = (d) => {
      if (d.agent === agentName) {
        resolve({
          [`${agentName}_status`]: "complete",
          [agentName.replace("_agent","") + "_data"]: d.data || null,
        });
      }
    };
    onEvent("agent_start",    unsubStart);
    onEvent("agent_complete", unsubDone);
  });
}

async function supervisorNode(state) {
  sendQuery({
    user_query: state.user_query, market: state.market,
    budget: state.budget, timeline_months: state.timeline_months,
  });
  return { supervisor_status: "running" };
}

const marketAgentNode    = () => waitForEvent("market_agent");
const financialAgentNode = () => waitForEvent("financial_agent");
const knowledgeAgentNode = () => waitForEvent("knowledge_agent");
const strategyAgentNode  = () => waitForEvent("strategy_agent");

async function communicationAgentNode(state) {
  return new Promise(resolve => {
    onEvent("final_result", (d) => {
      resolve({
        communication_agent_status: "complete",
        final_report:       d.data?.final_report   || "",
        strategy_decision:  d.data?.decision        || state.strategy_decision,
        pipeline_complete:  true,
      });
    });
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// BUILD GRAPH
// ─────────────────────────────────────────────────────────────────────────────
function buildFrontendGraph() {
  const g = new StateGraph(AgentState);

  g.addNode("supervisor",          supervisorNode);
  g.addNode("market_agent",        marketAgentNode);
  g.addNode("financial_agent",     financialAgentNode);
  g.addNode("knowledge_agent",     knowledgeAgentNode);
  g.addNode("strategy_agent",      strategyAgentNode);
  g.addNode("communication_agent", communicationAgentNode);

  // Mirror backend parallel fan-out
  g.addEdge(START,        "supervisor");
  g.addEdge("supervisor", "market_agent");
  g.addEdge("supervisor", "financial_agent");
  g.addEdge("supervisor", "knowledge_agent");

  g.addEdge("market_agent",    "strategy_agent");
  g.addEdge("financial_agent", "strategy_agent");
  g.addEdge("knowledge_agent", "strategy_agent");

  g.addEdge("strategy_agent",      "communication_agent");
  g.addEdge("communication_agent", END);

  return g.compile();
}

export const frontendGraph = buildFrontendGraph();

// ─────────────────────────────────────────────────────────────────────────────
// USAGE (in your React component)
// ─────────────────────────────────────────────────────────────────────────────
/*
import { connectWebSocket, frontendGraph, onEvent } from "./graph.js";

// On mount:
await connectWebSocket();

// Subscribe to all events for your UI timeline:
onEvent("*", (event) => console.log("Agent event:", event));

// Run the frontend graph (tracks backend pipeline in real-time):
const result = await frontendGraph.invoke({
  user_query:      "Should RA Groups expand into UAE?",
  market:          "UAE",
  budget:          2_000_000,
  timeline_months: 18,
});

console.log("Pipeline complete:", result.strategy_decision);
*/
