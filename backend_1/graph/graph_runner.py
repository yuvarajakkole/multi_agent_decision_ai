from graph.decision_graph import build_decision_graph
from memory.session_memory import get_memory_saver
from streaming.agent_step_streamer import stream_error


graph = build_decision_graph()


async def run_graph(state):

    try:

        result = await graph.ainvoke(state)

        return result

    except Exception as e:

        request_id = state.get("request_id")

        if request_id:

            await stream_error(
                request_id,
                "graph_runner",
                str(e)
            )

        raise