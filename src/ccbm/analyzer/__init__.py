"""
Criticality Analyzer — классификация текстовых спанов по уровням важности.

Уровни критичности:
- L1: Критические числовые данные (валюты, ставки, даты, ИИН/БИН)
- L2: Политики и клаузулы (юридически значимые условия)
- L3: Персональные данные (PII — имена, адреса, телефоны)
- L4: Контекстное наполнение (общие описания, история)
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
import re

from .kazroberta_ner import KazRoBERTaNER, NEREntity, EntityType


class CriticalityLevel(Enum):
    """Уровни критичности спанов."""
    L1 = "critical_numbers"  # Числа, ИИН, даты
    L2 = "legal_policies"    # Юридические условия
    L3 = "pii"               # Персональные данные
    L4 = "context_fill"      # Контекстное наполнение


@dataclass(frozen=True)
class Span:
    """Текстовый спан с метаданными."""
    text: str
    start: int
    end: int
    level: CriticalityLevel
    confidence: float
    metadata: Optional[dict] = None


class CriticalityAnalyzer:
    """
    Анализатор критичности для классификации спанов.
    
    Использует гибридный подход:
    - Регулярные выражения для структурированных данных (ИИН, даты, числа)
    - NER модели для PII (KazRoBERTa для казахского языка)
    - Шаблонное сопоставление для юридических документов
    """
    
    # Паттерны для Казахстана
    IIN_PATTERN = re.compile(r'\b\d{12}\b')  # ИИН: 12 цифр
    BIN_PATTERN = re.compile(r'\b\d{12}\b')  # БИН: 12 цифр
    DATE_PATTERN = re.compile(r'\b\d{1,2}\.\d{1,2}\.\d{4}\b')  # Даты
    # Валюты: KZT, USD, EUR, ₸, $, € — с поддержкой разных форматов
    CURRENCY_PATTERN = re.compile(r'[\$€₸]?\s*\d+[.,]?\d*\s*(?:KZT|USD|EUR|₸|\$|€)?\b')
    
    def __init__(self, language: str = "kk"):
        """
        Инициализация анализатора.
        
        Args:
            language: Язык обработки ('kk' для казахского, 'ru' для русского)
        """
        self.language = language
        self.ner_model = None  # Будет загружен при необходимости
    
    def analyze(self, text: str) -> List[Span]:
        """
        Анализ текста и классификация спанов.
        
        Args:
            text: Входной текст для анализа
            
        Returns:
            Список спанов с уровнями критичности
        """
        # Пустой текст — пустой результат
        if not text or not text.strip():
            return []
        
        spans = []
        
        # L1: Числовые данные
        spans.extend(self._extract_numbers(text))

        # L2: Юридические шаблоны (требует загрузки базы)
        # spans.extend(self._extract_legal(text))

        # L3: PII (NER модель для казахского)
        spans.extend(self._extract_pii_ner(text))

        # L4: Остальной текст
        spans.extend(self._extract_context(text, spans))

        return sorted(spans, key=lambda s: s.start)
    
    def _extract_numbers(self, text: str) -> List[Span]:
        """Извлечение критических числовых данных (L1)."""
        spans = []
        
        # ИИН/БИН
        for match in self.IIN_PATTERN.finditer(text):
            spans.append(Span(
                text=match.group(),
                start=match.start(),
                end=match.end(),
                level=CriticalityLevel.L1,
                confidence=0.95,
                metadata={"type": "iin_bin"}
            ))
        
        # Даты
        for match in self.DATE_PATTERN.finditer(text):
            spans.append(Span(
                text=match.group(),
                start=match.start(),
                end=match.end(),
                level=CriticalityLevel.L1,
                confidence=0.9,
                metadata={"type": "date"}
            ))
        
        # Валюты
        for match in self.CURRENCY_PATTERN.finditer(text):
            spans.append(Span(
                text=match.group(),
                start=match.start(),
                end=match.end(),
                level=CriticalityLevel.L1,
                confidence=0.9,
                metadata={"type": "currency"}
            ))
        
        return spans
    
    def _extract_context(self, text: str, existing_spans: List[Span]) -> List[Span]:
        """Извлечение контекстного наполнения (L4)."""
        if not existing_spans:
            return [Span(
                text=text,
                start=0,
                end=len(text),
                level=CriticalityLevel.L4,
                confidence=1.0
            )]
        
        spans = []
        last_end = 0
        
        for span in sorted(existing_spans, key=lambda s: s.start):
            if span.start > last_end:
                spans.append(Span(
                    text=text[last_end:span.start],
                    start=last_end,
                    end=span.start,
                    level=CriticalityLevel.L4,
                    confidence=1.0
                ))
            last_end = span.end
        
        if last_end < len(text):
            spans.append(Span(
                text=text[last_end:],
                start=last_end,
                end=len(text),
                level=CriticalityLevel.L4,
                confidence=1.0
            ))
        
        return spans

    def _extract_pii_ner(self, text: str) -> List[Span]:
        """
        Извлечение PII через NER модель (KazRoBERTa).
        
        Args:
            text: Текст
            
        Returns:
            Список L3 спанов (PII)
        """
        spans = []
        
        # Lazy init NER модели
        if not hasattr(self, '_ner_model'):
            self._ner_model = KazRoBERTaNER()
            self._ner_model.load()  # Загрузка с fallback
        
        # Извлечение PII
        pii_entities = self._ner_model.extract_pii(text)
        
        for entity in pii_entities:
            spans.append(Span(
                text=entity.text,
                start=entity.start,
                end=entity.end,
                level=CriticalityLevel.L3,
                confidence=entity.confidence,
                metadata={
                    "type": entity.entity_type.value,
                    "ner_model": "KazRoBERTa",
                },
            ))
        
        return spans

    def validate_iin(self, iin: str) -> bool:
        """
        Валидация ИИН по алгоритму модуля 11.
        
        Args:
            iin: 12-значный ИИН
            
        Returns:
            True если ИИН валиден
        """
        if len(iin) != 12 or not iin.isdigit():
            return False
        
        weights = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
        digits = [int(d) for d in iin]
        
        # Первая контрольная сумма
        sum1 = sum(w * d for w, d in zip(weights[:11], digits[:11]))
        ctrl1 = sum1 % 11
        
        if ctrl1 == 10:
            return False
        
        if ctrl1 != digits[11]:
            return False
        
        # Вторая контрольная сумма (для юридических лиц)
        weights2 = [3, 4, 5, 6, 7, 8, 9, 10, 11, 1, 2, 3]
        sum2 = sum(w * d for w, d in zip(weights2, digits))
        ctrl2 = sum2 % 11
        
        return ctrl2 == digits[11] if ctrl2 != 10 else False


# TODO: Добавить загрузку KazRoBERTa для NER
# TODO: Добавить интеграцию с базой «Адилет» для юридических шаблонов
