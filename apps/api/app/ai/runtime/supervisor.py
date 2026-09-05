from __future__ import annotations

import logging
import operator
import uuid
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from typing import Annotated, Any

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from app.ai.a2a.client import send_a2a
from app.ai.a2a.protocol import A2AMessage
from app.ai.a2a.writer import write_brief
from app.ai.knowledge.retriever import KnowledgeRetriever, format_knowledge_message
from app.ai.llm.gateway import LLMGateway
from app.ai.runtime.agent_graph import GraphRunResult, SpanRecorder, iter_token_chunks
from app.ai.type import AIMessage
from app.core.config import settings
from app.schemas.chat import Citation

logger = logging.getLogger(__name__)

_BRIEF_HINTS = ("简报", "写一页")


def wants_supervisor(user_message: str) -> bool:
    text = user_message or ""
    return any(hint in text for hint in _BRIEF_HINTS)


class SupervisorState(TypedDict):
    user_message: str
    notes: str
    brief: str
    agents: Annotated[list[str], operator.add]
    error: str


class SupervisorGraph:
    """Deterministic router: knowledge specialist then Writer (A2A or in-process)."""

    def __init__(
        self,
        llm_gateway: LLMGateway,
        agent: Any,
        *,
        knowledge_retriever: KnowledgeRetriever | None,
        user_id: int,
        agent_id: int,
        span_recorder: SpanRecorder | None = None,
        writer_url: str | None = None,
        a2a_key: str | None = None,
        a2a_send=None,
    ):
        self.llm_gateway = llm_gateway
        self.agent = agent
        self.knowledge_retriever = knowledge_retriever
        self.user_id = user_id
        self.agent_id = agent_id
        self._span_recorder = span_recorder
        self._writer_url = (
            writer_url if writer_url is not None else settings.A2A_WRITER_URL
        )
        self._a2a_key = (
            a2a_key if a2a_key is not None else (settings.A2A_INTERNAL_KEY or "")
        )
        self._a2a_send = a2a_send or send_a2a
        self._citations: list[Citation] = []
        self._last_agents: list[str] = []
        self._graph = self._build()

    @property
    def citations(self) -> list[Citation]:
        return list(self._citations)

    @property
    def agents(self) -> list[str]:
        return list(self._last_agents)

    def _build(self):
        builder = StateGraph(SupervisorState)
        builder.add_node("knowledge", self._knowledge)
        builder.add_node("writer", self._writer)
        builder.add_edge(START, "knowledge")
        builder.add_edge("knowledge", "writer")
        builder.add_edge("writer", END)
        return builder.compile()

    async def run(self, user_message: str) -> GraphRunResult:
        final = await self._graph.ainvoke(
            {
                "user_message": user_message,
                "notes": "",
                "brief": "",
                "agents": [],
                "error": "",
            }
        )
        agents = list(final.get("agents") or [])
        self._last_agents = agents
        if final.get("error"):
            return GraphRunResult(
                status="failed",
                message=AIMessage(role="assistant", content=final["error"]),
                agents=agents,
            )
        return GraphRunResult(
            status="completed",
            message=AIMessage(role="assistant", content=final.get("brief") or ""),
            agents=agents,
        )

    async def stream(self, user_message: str) -> AsyncIterator[tuple[str, dict]]:
        outcome = await self.run(user_message)
        for name in outcome.agents:
            yield "agent", {"name": name}
        text = outcome.message.content if outcome.message else ""
        if outcome.status == "failed":
            yield "error", {"message": text}
            return
        for chunk in iter_token_chunks(text or ""):
            yield "token", {"text": chunk}

    async def _knowledge(self, state: SupervisorState) -> dict:
        started = datetime.now(UTC)
        query = state["user_message"]
        hits = []
        if self.knowledge_retriever is not None:
            hits = await self.knowledge_retriever.retrieve(
                query, user_id=self.user_id, agent_id=self.agent_id
            )
        self._citations = [
            Citation(
                document_id=hit.document_id,
                title=hit.source,
                chunk_id=hit.chunk_id,
            )
            for hit in hits
        ]
        notes = format_knowledge_message(hits) if hits else "（知识库无命中）"
        await self._record_span("knowledge", started, error=None)
        return {"notes": notes, "agents": ["knowledge"]}

    async def _writer(self, state: SupervisorState) -> dict:
        started = datetime.now(UTC)
        try:
            brief = await self._call_writer(state["user_message"], state["notes"])
        except Exception as exc:
            logger.exception("writer failed")
            await self._record_span("writer", started, error=str(exc))
            return {"error": f"writer failed: {exc}", "agents": ["writer"]}
        await self._record_span("writer", started, error=None)
        return {"brief": brief, "agents": ["writer"]}

    async def _call_writer(self, user_message: str, notes: str) -> str:
        if self._writer_url:
            logger.info("writer via A2A HTTP %s", self._writer_url)
            reply = await self._a2a_send(
                self._writer_url,
                A2AMessage(
                    from_agent="supervisor",
                    to_agent="writer",
                    task_id=str(uuid.uuid4()),
                    content=notes,
                    metadata={
                        "provider": self.agent.provider,
                        "model": self.agent.model_name,
                        "user_message": user_message,
                    },
                ),
                api_key=self._a2a_key,
            )
            if reply.status != "completed":
                raise RuntimeError(reply.content or "writer failed")
            return reply.content
        logger.info("writer in-process")
        return await write_brief(
            self.llm_gateway,
            provider=self.agent.provider,
            model=self.agent.model_name,
            user_message=user_message,
            notes=notes,
        )

    async def _record_span(
        self, node: str, started_at: datetime, *, error: str | None
    ) -> None:
        duration_ms = max(
            0, int((datetime.now(UTC) - started_at).total_seconds() * 1000)
        )
        if self._span_recorder is None:
            return
        try:
            await self._span_recorder(
                node=node,
                started_at=started_at,
                duration_ms=duration_ms,
                tool_name=None,
                status="error" if error else "ok",
                error=error,
            )
        except Exception:
            logger.exception("failed to persist run_span node=%s", node)
