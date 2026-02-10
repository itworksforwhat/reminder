"""WebSocket 연결 관리 및 실시간 동기화.

Redis Pub/Sub을 활용하여 회사별 채널로 실시간 메시지를 전달합니다.
"""
import json
from uuid import UUID
from typing import Any
from fastapi import WebSocket
from collections import defaultdict


class ConnectionManager:
    """WebSocket 연결을 관리하는 클래스."""

    def __init__(self):
        # company_id -> list of WebSocket connections
        self._connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, websocket: WebSocket, company_id: UUID) -> None:
        await websocket.accept()
        key = str(company_id)
        self._connections[key].append(websocket)

    def disconnect(self, websocket: WebSocket, company_id: UUID) -> None:
        key = str(company_id)
        if websocket in self._connections[key]:
            self._connections[key].remove(websocket)
        if not self._connections[key]:
            del self._connections[key]

    async def broadcast_to_company(
        self, company_id: UUID, message: dict[str, Any], exclude: WebSocket | None = None
    ) -> None:
        """특정 회사의 모든 연결에 메시지를 브로드캐스트합니다."""
        key = str(company_id)
        disconnected = []

        for ws in self._connections.get(key, []):
            if ws == exclude:
                continue
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)

        for ws in disconnected:
            self.disconnect(ws, company_id)

    async def send_personal(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        """개인 메시지를 전송합니다."""
        try:
            await websocket.send_json(message)
        except Exception:
            pass

    @property
    def active_connections_count(self) -> int:
        return sum(len(conns) for conns in self._connections.values())


# 전역 ConnectionManager 인스턴스
manager = ConnectionManager()


def create_sync_message(
    event_type: str,
    entity_type: str,
    entity_id: str | None = None,
    data: dict | None = None,
) -> dict:
    """동기화 메시지를 생성합니다."""
    return {
        "event": event_type,  # created, updated, deleted
        "entity": entity_type,  # reminder, template
        "id": entity_id,
        "data": data,
    }
