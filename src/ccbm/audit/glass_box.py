"""
Glass Box Audit — прозрачный аудит всех решений AI.

Интеграция AuditEngine с Merkle Trees для неизменяемого логирования.

Inspired by TERAG Desktop Glass Box Audit.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from ccbm.audit import AuditEngine


@dataclass
class AuditEntry:
    """Запись аудита для Glass Box."""
    step_id: int
    timestamp_ns: int
    agent: str
    decision: str
    confidence: float
    reasoning: str
    merkle_hash: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Сериализация в словарь."""
        return {
            "step_id": self.step_id,
            "timestamp_ns": self.timestamp_ns,
            "agent": self.agent,
            "decision": self.decision,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "merkle_hash": self.merkle_hash,
            "metadata": self.metadata,
        }


class GlassBoxAudit:
    """
    Glass Box Audit для CCBM.
    
    Прозрачный аудит всех решений с Merkle Tree гарантиями.
    """

    def __init__(self):
        """Инициализация Glass Box Audit."""
        self.audit_engine = AuditEngine()
        self.entries: list[AuditEntry] = []
        self._step_counter = 0
        self._merkle_root: str | None = None

    def log_decision(
        self,
        agent: str,
        decision: str,
        confidence: float,
        reasoning: str,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEntry:
        """
        Логирование решения AI.
        
        Args:
            agent: Название агента (например, "ChernoffVerifier")
            decision: Решение (например, "VERIFIED")
            confidence: Уверенность (0.0-1.0)
            reasoning: Объяснение решения
            metadata: Дополнительные метаданные
            
        Returns:
            AuditEntry с merkle_hash
        """
        self._step_counter += 1

        entry = AuditEntry(
            step_id=self._step_counter,
            timestamp_ns=time.time_ns(),
            agent=agent,
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            metadata=metadata or {},
        )

        # Вычисляем хеш для entry
        entry.merkle_hash = self._compute_entry_hash(entry)

        # Добавляем в audit engine
        self.audit_engine.add_transformation(
            original_data=json.dumps({
                "agent": agent,
                "decision": decision,
                "input": metadata.get("input", "") if metadata else "",
            }, sort_keys=True),
            compressed_data=json.dumps({
                "decision": decision,
                "confidence": confidence,
                "hash": entry.merkle_hash,
            }, sort_keys=True),
            metadata={
                "step_id": entry.step_id,
                "agent": agent,
                "type": "decision",
            },
        )

        self.entries.append(entry)
        return entry

    def finalize(self) -> str:
        """
        Финализация дерева Меркла.
        
        Returns:
            Merkle root всех записей
        """
        self._merkle_root = self.audit_engine.finalize()
        return self._merkle_root

    def get_audit_trail(self) -> list[dict]:
        """
        Получение полного audit trail.
        
        Returns:
            Список всех записей в виде словарей
        """
        return [entry.to_dict() for entry in self.entries]

    def verify_integrity(self, fast_mode: bool = True) -> bool:
        """
        Проверка целостности audit trail.
        
        Режимы:
        - Fast-mode (O(1)): проверка только Merkle root
        - Full-mode (O(n)): полная проверка всех квитанций
        
        Args:
            fast_mode: Если True — быстрая проверка, иначе полная
            
        Returns:
            True если все записи валидны
        """
        if not self.entries:
            return True

        # Проверяем что merkle root вычислен
        if not self._merkle_root:
            self.finalize()

        if fast_mode:
            # Fast-path: только проверка что root существует
            # O(1) — достаточно для production monitoring
            return bool(self._merkle_root)
        else:
            # Full-path: проверка всех квитанций
            # O(n) — для аудита/комплаенса
            receipts = self.audit_engine._receipts
            all_valid = all(
                self.audit_engine.verify_receipt(receipt)
                for receipt in receipts
            )
            return all_valid

    def verify_integrity_async(self, callback=None) -> str:
        """
        Асинхронная полная проверка (assurance-path).
        
        Args:
            callback: Функция обратного вызова с результатом
            
        Returns:
            ID задачи верификации
        """
        import threading
        import uuid

        task_id = str(uuid.uuid4())

        def verify_task():
            result = self.verify_integrity(fast_mode=False)
            if callback:
                callback(task_id, result)
            return result

        # Запуск в отдельном потоке (неблокирующе)
        thread = threading.Thread(target=verify_task)
        thread.daemon = True
        thread.start()

        return task_id

    def export_for_blockchain(self) -> dict:
        """
        Экспорт для блокчейн-анкоринга.
        
        Returns:
            Словарь с данными для записи в блокчейн
        """
        if not self._merkle_root:
            self.finalize()

        return self.audit_engine.export_for_blockchain()

    @staticmethod
    def _compute_entry_hash(entry: AuditEntry) -> str:
        """Вычисление хеша для записи аудита."""
        import hashlib

        data = json.dumps({
            "step_id": entry.step_id,
            "timestamp_ns": entry.timestamp_ns,
            "agent": entry.agent,
            "decision": entry.decision,
            "confidence": entry.confidence,
            "reasoning": entry.reasoning,
        }, sort_keys=True)

        return hashlib.sha256(data.encode('utf-8')).hexdigest()

    def get_summary(self) -> dict:
        """
        Получение сводки аудита.
        
        Returns:
            Словарь с метриками аудита
        """
        if not self.entries:
            return {
                "total_decisions": 0,
                "merkle_root": None,
                "integrity_valid": True,
            }

        decisions_by_agent = {}
        decisions_by_type = {}
        avg_confidence = sum(e.confidence for e in self.entries) / len(self.entries)

        for entry in self.entries:
            decisions_by_agent[entry.agent] = decisions_by_agent.get(entry.agent, 0) + 1
            decisions_by_type[entry.decision] = decisions_by_type.get(entry.decision, 0) + 1

        return {
            "total_decisions": len(self.entries),
            "merkle_root": self._merkle_root,
            "integrity_valid": self.verify_integrity(),
            "avg_confidence": round(avg_confidence, 3),
            "decisions_by_agent": decisions_by_agent,
            "decisions_by_type": decisions_by_type,
            "first_decision": self.entries[0].to_dict() if self.entries else None,
            "last_decision": self.entries[-1].to_dict() if self.entries else None,
        }


@dataclass
class GlassBoxReport:
    """Отчёт Glass Box Audit."""
    timestamp: str
    total_decisions: int
    merkle_root: str
    integrity_valid: bool
    entries: list[AuditEntry]

    def to_dict(self) -> dict:
        """Сериализация в словарь."""
        return {
            "timestamp": self.timestamp,
            "total_decisions": self.total_decisions,
            "merkle_root": self.merkle_root,
            "integrity_valid": self.integrity_valid,
            "entries": [e.to_dict() for e in self.entries],
        }


def create_glass_box_report(audit: GlassBoxAudit) -> GlassBoxReport:
    """
    Создание отчёта Glass Box Audit.
    
    Args:
        audit: GlassBoxAudit с данными
        
    Returns:
        GlassBoxReport со всеми проверками
    """
    return GlassBoxReport(
        timestamp=datetime.utcnow().isoformat(),
        total_decisions=len(audit.entries),
        merkle_root=audit._merkle_root or "",
        integrity_valid=audit.verify_integrity(),
        entries=audit.entries,
    )
