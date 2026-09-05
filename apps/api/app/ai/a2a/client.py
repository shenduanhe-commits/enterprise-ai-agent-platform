from __future__ import annotations

import logging

import httpx

from app.ai.a2a.protocol import A2AMessage, A2AReply

logger = logging.getLogger(__name__)

A2A_KEY_HEADER = "X-EAAP-A2A-Key"


async def send_a2a(
    url: str,
    message: A2AMessage,
    *,
    api_key: str,
    timeout: float = 30.0,
    client: httpx.AsyncClient | None = None,
) -> A2AReply:
    headers = {A2A_KEY_HEADER: api_key}
    if client is not None:
        response = await client.post(
            url, json=message.model_dump(), headers=headers, timeout=timeout
        )
        response.raise_for_status()
        return A2AReply.model_validate(response.json())

    async with httpx.AsyncClient() as owned:
        response = await owned.post(
            url, json=message.model_dump(), headers=headers, timeout=timeout
        )
        response.raise_for_status()
        return A2AReply.model_validate(response.json())
