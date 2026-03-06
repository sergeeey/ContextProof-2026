"""
Information Contract Engine — формальный контракт сохранённой информации.

Каждый оптимизированный контекст получает сертификат:
- information_preserved ≥ X%
- critical_spans_preserved = 100%
- numeric_invariants_preserved = true
- semantic_delta ≤ Y

Это превращает CCBM из dev tool в compliance инфраструктуру.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from ccbm.analyzer import CriticalityLevel, Span


class ContractVersion(Enum):
    """Версия контракта."""
    V1_0 = "1.0"  # Базовый контракт
    V1_1 = "1.1"  # С KL divergence


class InformationClass(Enum):
    """Классы информации."""
    FACTS = "facts"  # Факты (ИИН, даты, суммы)
    NUMBERS = "numbers"  # Числа
    RELATIONS = "relations"  # Связи между сущностями
    REASONING = "reasoning"  # Логические цепочки
    NOISE = "noise"  # Шум (можно удалить)


@dataclass
class InformationSegment:
    """Сегмент информации с весом."""
    segment_id: str
    information_class: InformationClass
    text: str
    weight: float  # 0.0 - 1.0 (важность)
    preserved: bool = True
    compressed_text: str | None = None

    def to_dict(self) -> dict:
        """Сериализация в словарь."""
        return {
            "segment_id": self.segment_id,
            "information_class": self.information_class.value,
            "text": self.text,
            "weight": self.weight,
            "preserved": self.preserved,
            "compressed_text": self.compressed_text,
        }


@dataclass
class InformationContract:
    """
    Контракт сохранённой информации.
    
    Сертификат который гарантирует:
    - information_preserved ≥ X%
    - critical_spans_preserved = 100%
    - numeric_invariants_preserved = true
    - semantic_delta ≤ Y
    """
    contract_id: str
    version: ContractVersion
    timestamp: int
    context_hash: str

    # Метрики сохранения
    information_preserved: float  # % сохранённой информации
    critical_spans_preserved: float  # % L1/L2 спанов
    numeric_invariants_preserved: bool  # Числа сохранены
    semantic_delta: float  # KL divergence / semantic drift

    # Сегменты
    segments: list[InformationSegment] = field(default_factory=list)

    # Сертификат
    certificate_hash: str | None = None
    is_valid: bool = True
    validation_errors: list[str] = field(default_factory=list)

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Сериализация в словарь."""
        return {
            "contract_id": self.contract_id,
            "version": self.version.value,
            "timestamp": self.timestamp,
            "context_hash": self.context_hash,
            "information_preserved": self.information_preserved,
            "critical_spans_preserved": self.critical_spans_preserved,
            "numeric_invariants_preserved": self.numeric_invariants_preserved,
            "semantic_delta": self.semantic_delta,
            "segments": [s.to_dict() for s in self.segments],
            "certificate_hash": self.certificate_hash,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
            "metadata": self.metadata,
        }

    def to_json(self) -> str:
        """Сериализация в JSON."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)

    def get_certificate(self) -> str:
        """
        Получение сертификата.
        
        Returns:
            Hash сертификата
        """
        if self.certificate_hash is None:
            # Создаём hash от всех ключевых полей
            data = json.dumps({
                "contract_id": self.contract_id,
                "context_hash": self.context_hash,
                "information_preserved": self.information_preserved,
                "critical_spans_preserved": self.critical_spans_preserved,
                "numeric_invariants_preserved": self.numeric_invariants_preserved,
                "timestamp": self.timestamp,
            }, sort_keys=True)

            self.certificate_hash = hashlib.sha256(data.encode('utf-8')).hexdigest()

        return self.certificate_hash


class InformationContractEngine:
    """
    Движок создания информационных контрактов.
    
    Использование:
    1. Сегментация контекста
    2. Присвоение весов
    3. Сжатие
    4. Верификация контракта
    5. Получение сертификата
    """

    def __init__(
        self,
        min_information_preserved: float = 0.95,
        min_critical_spans: float = 1.0,
        max_semantic_delta: float = 0.1,
    ):
        """
        Инициализация движка.
        
        Args:
            min_information_preserved: Мин. % сохранённой информации
            min_critical_spans: Мин. % критичных спанов
            max_semantic_delta: Макс. семантическое расхождение
        """
        self.min_information_preserved = min_information_preserved
        self.min_critical_spans = min_critical_spans
        self.max_semantic_delta = max_semantic_delta

        self._segment_counter = 0

    def segment_context(
        self,
        text: str,
        spans: list[Span] | None = None,
    ) -> list[InformationSegment]:
        """
        Сегментация контекста по классам информации.
        
        Args:
            text: Текст
            spans: Спаны от CriticalityAnalyzer
            
        Returns:
            Список сегментов
        """
        segments = []

        if spans:
            # Сегментация на основе спанов
            for span in spans:
                self._segment_counter += 1

                # Определение класса информации
                info_class = self._span_to_class(span)

                # Вес на основе критичности
                weight = self._span_to_weight(span)

                segment = InformationSegment(
                    segment_id=f"SEG-{self._segment_counter:04d}",
                    information_class=info_class,
                    text=span.text,
                    weight=weight,
                )

                segments.append(segment)
        else:
            # Простая сегментация по предложениям
            sentences = text.split('.')
            for i, sentence in enumerate(sentences):
                if not sentence.strip():
                    continue

                self._segment_counter += 1

                # Эвристическое определение класса
                info_class, weight = self._classify_sentence(sentence.strip())

                segment = InformationSegment(
                    segment_id=f"SEG-{self._segment_counter:04d}",
                    information_class=info_class,
                    text=sentence.strip(),
                    weight=weight,
                )

                segments.append(segment)

        return segments

    def _span_to_class(self, span: Span) -> InformationClass:
        """Конвертация спана в класс информации."""
        if span.level == CriticalityLevel.L1:
            if span.metadata and span.metadata.get("type") in ["iin_bin", "date"]:
                return InformationClass.FACTS
            elif span.metadata and span.metadata.get("type") == "currency":
                return InformationClass.NUMBERS
            return InformationClass.FACTS
        elif span.level == CriticalityLevel.L2:
            return InformationClass.RELATIONS
        elif span.level == CriticalityLevel.L3:
            return InformationClass.FACTS
        else:  # L4
            return InformationClass.NOISE

    def _span_to_weight(self, span: Span) -> float:
        """Конвертация спана в вес."""
        if span.level == CriticalityLevel.L1:
            return 1.0  # Критично
        elif span.level == CriticalityLevel.L2:
            return 0.8  # Важно
        elif span.level == CriticalityLevel.L3:
            return 0.6  # Средне
        else:  # L4
            return 0.3  # Шум

    def _classify_sentence(self, sentence: str) -> tuple[InformationClass, float]:
        """Классификация предложения."""
        import re

        # Числа
        if re.search(r'\d+[.,]?\d*\s*(KZT|USD|EUR|%)', sentence):
            return InformationClass.NUMBERS, 0.9

        # ИИН/БИН
        if re.search(r'\b\d{12}\b', sentence):
            return InformationClass.FACTS, 1.0

        # Даты
        if re.search(r'\b\d{1,2}\.\d{1,2}\.\d{4}\b', sentence):
            return InformationClass.FACTS, 0.9

        # Связи (предлоги, союзы)
        if any(word in sentence.lower() for word in ['между', 'с', 'между', 'отношение']):
            return InformationClass.RELATIONS, 0.7

        # По умолчанию шум
        return InformationClass.NOISE, 0.3

    def create_contract(
        self,
        text: str,
        compressed_text: str,
        spans: list[Span] | None = None,
    ) -> InformationContract:
        """
        Создание контракта.
        
        Args:
            text: Оригинальный текст
            compressed_text: Сжатый текст
            spans: Спаны от CriticalityAnalyzer
            
        Returns:
            InformationContract
        """
        # Сегментация
        segments = self.segment_context(text, spans)

        # Проверка сохранения сегментов
        for segment in segments:
            segment.preserved = segment.text in compressed_text
            if segment.preserved:
                segment.compressed_text = segment.text

        # Вычисление метрик
        information_preserved = self._compute_information_preserved(segments)
        critical_spans_preserved = self._compute_critical_spans_preserved(segments, spans)
        numeric_invariants_preserved = self._check_numeric_invariants(text, compressed_text)
        semantic_delta = self._compute_semantic_delta(text, compressed_text)

        # Хеш контекста
        context_hash = hashlib.sha256(text.encode('utf-8')).hexdigest()

        # Создание контракта
        contract = InformationContract(
            contract_id=f"CONTRACT-{int(time.time()):010d}",
            version=ContractVersion.V1_0,
            timestamp=int(time.time()),
            context_hash=context_hash,
            information_preserved=information_preserved,
            critical_spans_preserved=critical_spans_preserved,
            numeric_invariants_preserved=numeric_invariants_preserved,
            semantic_delta=semantic_delta,
            segments=segments,
            metadata={
                "original_length": len(text),
                "compressed_length": len(compressed_text),
                "compression_ratio": len(text) / max(1, len(compressed_text)),
            },
        )

        # Валидация
        self._validate_contract(contract)

        # Получение сертификата
        contract.get_certificate()

        return contract

    def _compute_information_preserved(
        self,
        segments: list[InformationSegment],
    ) -> float:
        """
        Вычисление % сохранённой информации.
        
        Формула:
        sum(weight * preserved for segment in segments) / sum(weight)
        """
        if not segments:
            return 1.0

        total_weight = sum(s.weight for s in segments)
        preserved_weight = sum(s.weight for s in segments if s.preserved)

        return preserved_weight / max(1, total_weight)

    def _compute_critical_spans_preserved(
        self,
        segments: list[InformationSegment],
        spans: list[Span] | None,
    ) -> float:
        """Вычисление % сохранённых критичных спанов."""
        if not spans:
            return 1.0

        critical_spans = [s for s in spans if s.level in [CriticalityLevel.L1, CriticalityLevel.L2]]

        if not critical_spans:
            return 1.0

        preserved_count = sum(
            1 for s in critical_spans
            if any(seg.text == s.text and seg.preserved for seg in segments)
        )

        return preserved_count / len(critical_spans)

    def _check_numeric_invariants(
        self,
        original: str,
        compressed: str,
    ) -> bool:
        """Проверка сохранения числовых инвариантов."""
        import re

        # Извлекаем все числа из оригинала
        original_numbers = set(re.findall(r'\b\d+[.,]?\d*\b', original))

        # Извлекаем все числа из сжатого
        compressed_numbers = set(re.findall(r'\b\d+[.,]?\d*\b', compressed))

        # Все числа из оригинала должны быть в сжатом
        return original_numbers.issubset(compressed_numbers)

    def _compute_semantic_delta(
        self,
        original: str,
        compressed: str,
    ) -> float:
        """
        Вычисление семантического расхождения.
        
        Пока простая эвристика на основе overlap.
        TODO: KL divergence / BERTScore
        """
        original_words = set(original.lower().split())
        compressed_words = set(compressed.lower().split())

        if not original_words:
            return 0.0

        overlap = len(original_words & compressed_words)
        delta = 1.0 - (overlap / len(original_words))

        return delta

    def _validate_contract(self, contract: InformationContract):
        """Валидация контракта."""
        errors = []

        if contract.information_preserved < self.min_information_preserved:
            errors.append(
                f"Information preserved {contract.information_preserved:.1%} "
                f"< {self.min_information_preserved:.1%}"
            )

        if contract.critical_spans_preserved < self.min_critical_spans:
            errors.append(
                f"Critical spans preserved {contract.critical_spans_preserved:.1%} "
                f"< {self.min_critical_spans:.1%}"
            )

        if not contract.numeric_invariants_preserved:
            errors.append("Numeric invariants not preserved")

        if contract.semantic_delta > self.max_semantic_delta:
            errors.append(
                f"Semantic delta {contract.semantic_delta:.3f} "
                f"> {self.max_semantic_delta:.3f}"
            )

        contract.validation_errors = errors
        contract.is_valid = len(errors) == 0


def create_information_contract(
    text: str,
    compressed_text: str,
    spans: list[Span] | None = None,
) -> InformationContract:
    """
    Быстрое создание контракта.
    
    Args:
        text: Оригинальный текст
        compressed_text: Сжатый текст
        spans: Спаны
        
    Returns:
        InformationContract
    """
    engine = InformationContractEngine()
    return engine.create_contract(text, compressed_text, spans)
