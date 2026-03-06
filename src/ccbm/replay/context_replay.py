"""
Context Replay Engine — Git для контекста.

Логирование каждого вызова LLM как event stream:
- hash(context)
- compression map
- context proof
- model version

Возможность replay reasoning:
- reconstruct exact prompt
- увидеть что было удалено при сжатии
- восстановить цепочку рассуждений
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from ccbm.contract.information_contract import InformationContract


class EventType(Enum):
    """Типы событий."""
    CONTEXT_CREATED = "context_created"
    CONTEXT_COMPRESSED = "context_compressed"
    LLM_CALL = "llm_call"
    LLM_RESPONSE = "llm_response"
    CONTRACT_VALIDATED = "contract_validated"
    ERROR = "error"


@dataclass
class ContextEvent:
    """Событие контекста."""
    event_id: str
    timestamp: int
    event_type: EventType
    context_hash: str
    data: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Сериализация в словарь."""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type.value,
            "context_hash": self.context_hash,
            "data": self.data,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Сериализация в JSON."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


@dataclass
class ContextSession:
    """
    Сессия контекста.

    Содержит полную историю:
    - original context
    - compressed context
    - removed segments
    - LLM calls
    - responses
    """
    session_id: str
    started_at: int
    events: list[ContextEvent] = field(default_factory=list)
    contract: InformationContract | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_event(self, event: ContextEvent):
        """Добавление события."""
        self.events.append(event)

    def get_events_by_type(self, event_type: EventType) -> list[ContextEvent]:
        """Получение событий по типу."""
        return [e for e in self.events if e.event_type == event_type]

    def reconstruct_prompt(self) -> str:
        """
        Реконструкция точного промпта.

        Returns:
            Последний сжатый контекст
        """
        compressed_events = self.get_events_by_type(EventType.CONTEXT_COMPRESSED)

        if not compressed_events:
            return ""

        return compressed_events[-1].data.get("compressed_text", "")

    def get_removed_segments(self) -> list[str]:
        """
        Получение удалённых сегментов.

        Returns:
            Список удалённых сегментов
        """
        contract_events = self.get_events_by_type(EventType.CONTRACT_VALIDATED)

        if not contract_events or not contract_events[-1].data.get("contract"):
            return []

        contract_data = contract_events[-1].data["contract"]
        removed = []

        for segment in contract_data.get("segments", []):
            if not segment.get("preserved", True):
                removed.append(segment.get("text", ""))

        return removed

    def to_dict(self) -> dict:
        """Сериализация в словарь."""
        return {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "events": [e.to_dict() for e in self.events],
            "contract": self.contract.to_dict() if self.contract else None,
            "metadata": self.metadata,
        }


class ContextReplayEngine:
    """
    Движок для replay контекста.

    Использование:
    1. Логирование событий
    2. Сохранение сессии
    3. Replay по session_id
    """

    def __init__(self, storage_path: str | None = None):
        """
        Инициализация движка.

        Args:
            storage_path: Путь к хранилищу (None = in-memory)
        """
        self.storage_path = Path(storage_path) if storage_path else None
        self.sessions: dict[str, ContextSession] = {}
        self._event_counter = 0

        if self.storage_path:
            self.storage_path.mkdir(parents=True, exist_ok=True)

    def create_session(
        self,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ContextSession:
        """
        Создание сессии.

        Args:
            session_id: ID сессии (auto-generated если None)
            metadata: Метаданные

        Returns:
            ContextSession
        """
        if session_id is None:
            session_id = f"SESSION-{int(time.time()):010d}-{self._event_counter:04d}"

        session = ContextSession(
            session_id=session_id,
            started_at=int(time.time()),
            metadata=metadata or {},
        )

        self.sessions[session_id] = session

        return session

    def log_context_created(
        self,
        session: ContextSession,
        context: str,
        metadata: dict[str, Any] | None = None,
    ) -> ContextEvent:
        """Логирование создания контекста."""
        self._event_counter += 1

        context_hash = hashlib.sha256(context.encode('utf-8')).hexdigest()

        event = ContextEvent(
            event_id=f"EVENT-{self._event_counter:06d}",
            timestamp=int(time.time()),
            event_type=EventType.CONTEXT_CREATED,
            context_hash=context_hash,
            data={"text": context},
            metadata=metadata or {},
        )

        session.add_event(event)
        return event

    def log_context_compressed(
        self,
        session: ContextSession,
        original: str,
        compressed: str,
        compression_ratio: float,
        metadata: dict[str, Any] | None = None,
    ) -> ContextEvent:
        """Логирование сжатия контекста."""
        self._event_counter += 1

        original_hash = hashlib.sha256(original.encode('utf-8')).hexdigest()
        compressed_hash = hashlib.sha256(compressed.encode('utf-8')).hexdigest()

        event = ContextEvent(
            event_id=f"EVENT-{self._event_counter:06d}",
            timestamp=int(time.time()),
            event_type=EventType.CONTEXT_COMPRESSED,
            context_hash=compressed_hash,
            data={
                "original_text": original,
                "original_hash": original_hash,
                "compressed_text": compressed,
                "compressed_hash": compressed_hash,
                "compression_ratio": compression_ratio,
            },
            metadata=metadata or {},
        )

        session.add_event(event)
        return event

    def log_llm_call(
        self,
        session: ContextSession,
        model: str,
        prompt: str,
        metadata: dict[str, Any] | None = None,
    ) -> ContextEvent:
        """Логирование вызова LLM."""
        self._event_counter += 1

        prompt_hash = hashlib.sha256(prompt.encode('utf-8')).hexdigest()

        event = ContextEvent(
            event_id=f"EVENT-{self._event_counter:06d}",
            timestamp=int(time.time()),
            event_type=EventType.LLM_CALL,
            context_hash=prompt_hash,
            data={
                "model": model,
                "prompt": prompt,
            },
            metadata=metadata or {},
        )

        session.add_event(event)
        return event

    def log_llm_response(
        self,
        session: ContextSession,
        response: str,
        metadata: dict[str, Any] | None = None,
    ) -> ContextEvent:
        """Логирование ответа LLM."""
        self._event_counter += 1

        response_hash = hashlib.sha256(response.encode('utf-8')).hexdigest()

        event = ContextEvent(
            event_id=f"EVENT-{self._event_counter:06d}",
            timestamp=int(time.time()),
            event_type=EventType.LLM_RESPONSE,
            context_hash=response_hash,
            data={"response": response},
            metadata=metadata or {},
        )

        session.add_event(event)
        return event

    def log_contract_validated(
        self,
        session: ContextSession,
        contract: InformationContract,
    ) -> ContextEvent:
        """Логирование валидации контракта."""
        self._event_counter += 1

        event = ContextEvent(
            event_id=f"EVENT-{self._event_counter:06d}",
            timestamp=int(time.time()),
            event_type=EventType.CONTRACT_VALIDATED,
            context_hash=contract.context_hash,
            data={
                "contract": contract.to_dict(),
                "is_valid": contract.is_valid,
                "validation_errors": contract.validation_errors,
            },
            metadata={},
        )

        session.contract = contract
        session.add_event(event)
        return event

    def replay(self, session_id: str) -> ContextSession | None:
        """
        Replay сессии.

        Args:
            session_id: ID сессии

        Returns:
            ContextSession или None
        """
        if session_id in self.sessions:
            return self.sessions[session_id]

        # Загрузка из storage
        if self.storage_path:
            session_file = self.storage_path / f"{session_id}.json"

            if session_file.exists():
                with open(session_file) as f:
                    data = json.load(f)

                return self._load_session(data)

        return None

    def reconstruct_prompt(self, session_id: str) -> str:
        """
        Реконструкция промпта.

        Args:
            session_id: ID сессии

        Returns:
            Промпт
        """
        session = self.replay(session_id)

        if not session:
            return ""

        return session.reconstruct_prompt()

    def get_removed_segments(self, session_id: str) -> list[str]:
        """
        Получение удалённых сегментов.

        Args:
            session_id: ID сессии

        Returns:
            Список удалённых сегментов
        """
        session = self.replay(session_id)

        if not session:
            return []

        return session.get_removed_segments()

    def save_session(self, session: ContextSession):
        """
        Сохранение сессии.

        Args:
            session: Сессия для сохранения
        """
        if not self.storage_path:
            return

        session_file = self.storage_path / f"{session.session_id}.json"

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)

    def _load_session(self, data: dict) -> ContextSession:
        """Загрузка сессии из данных."""
        session = ContextSession(
            session_id=data["session_id"],
            started_at=data["started_at"],
            metadata=data.get("metadata", {}),
        )

        for event_data in data["events"]:
            event = ContextEvent(
                event_id=event_data["event_id"],
                timestamp=event_data["timestamp"],
                event_type=EventType(event_data["event_type"]),
                context_hash=event_data["context_hash"],
                data=event_data["data"],
                metadata=event_data.get("metadata", {}),
            )
            session.add_event(event)

        if data.get("contract"):
            session.contract = InformationContract(**data["contract"])

        return session


# Global instance
_replay_engine: ContextReplayEngine | None = None


def get_replay_engine(storage_path: str | None = None) -> ContextReplayEngine:
    """Получение глобального replay engine."""
    global _replay_engine
    if _replay_engine is None:
        _replay_engine = ContextReplayEngine(storage_path)
    return _replay_engine
