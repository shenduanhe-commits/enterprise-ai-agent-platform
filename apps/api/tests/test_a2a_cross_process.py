import os
import socket
import subprocess
import sys
import time
from pathlib import Path

import httpx
import pytest

from app.ai.llm.gateway import LLMGateway
from app.ai.llm.providers.mock import MockLLMProvider
from app.ai.runtime.supervisor import SupervisorGraph
from tests.test_supervisor import FakeRetriever, _agent

API_ROOT = Path(__file__).resolve().parents[1]
A2A_KEY = "cross-process-a2a-key"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_health(base: str, timeout: float = 20.0) -> None:
    deadline = time.time() + timeout
    last = None
    while time.time() < deadline:
        try:
            response = httpx.get(f"{base}/api/v1/health", timeout=1.0)
            if response.status_code == 200:
                return
            last = response.status_code
        except httpx.HTTPError as exc:
            last = exc
        time.sleep(0.2)
    raise AssertionError(f"writer process did not become healthy: {last}")


@pytest.mark.asyncio
async def test_supervisor_writes_via_other_process():
    port = _free_port()
    base = f"http://127.0.0.1:{port}"
    env = os.environ.copy()
    env["A2A_INTERNAL_KEY"] = A2A_KEY
    env["A2A_WRITER_URL"] = ""
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.ai.a2a.standalone:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=API_ROOT,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_health(base)
        graph = SupervisorGraph(
            LLMGateway({"mock": MockLLMProvider()}),
            _agent(),
            knowledge_retriever=FakeRetriever(),
            user_id=7,
            agent_id=3,
            writer_url=f"{base}/api/v1/a2a/message",
            a2a_key=A2A_KEY,
        )
        result = await graph.run("根据知识库写一页年假简报")
        assert result.status == "completed"
        assert result.agents == ["knowledge", "writer"]
        assert "简报" in (result.message.content or "")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=8)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
