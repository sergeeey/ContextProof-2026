"""
Optimization Engine — сжатие и фильтрация контекста.

Методы:
- Семантическая дедупликация (MinHash LSH)
- Иерархическая суммаризация (экстрактивная)
- Маскирование наблюдений (Observation Masking)
- Адаптивное управление бюджетом (FOCUS стратегия)
"""

from dataclasses import dataclass
from typing import List, Optional
from ccbm.analyzer import Span, CriticalityLevel


@dataclass
class OptimizationResult:
    """Результат оптимизации контекста."""
    original_text: str
    optimized_text: str
    compression_ratio: float
    spans_removed: int
    spans_preserved: int
    metadata: Optional[dict] = None


class OptimizationEngine:
    """
    Движок оптимизации контекста.
    
    Применяет различные стратегии сжатия в зависимости от уровня критичности:
    - L1: Zero-loss (без потерь)
    - L2: Template matching с сохранением семантики
    - L3: Masking / Anonymization
    - L4: Aggressive compression (extractive summarization)
    """
    
    def __init__(self, target_budget: int = 4000):
        """
        Инициализация движка оптимизации.
        
        Args:
            target_budget: Целевой бюджет токенов
        """
        self.target_budget = target_budget
        self.compression_stats = {
            "l1_preserved": 0,
            "l2_compressed": 0,
            "l3_masked": 0,
            "l4_summarized": 0,
        }
    
    def optimize(self, spans: List[Span]) -> OptimizationResult:
        """
        Оптимизация набора спанов.
        
        Args:
            spans: Список спанов от CriticalityAnalyzer
            
        Returns:
            Результат оптимизации
        """
        original_text = "".join(s.text for s in sorted(spans, key=lambda x: x.start))
        optimized_spans = []
        
        for span in spans:
            if span.level == CriticalityLevel.L1:
                # L1: Без потерь
                optimized_spans.append(span)
                self.compression_stats["l1_preserved"] += 1
                
            elif span.level == CriticalityLevel.L2:
                # L2: Сохранение с возможной компрессией
                optimized_spans.append(span)
                self.compression_stats["l2_compressed"] += 1
                
            elif span.level == CriticalityLevel.L3:
                # L3: Маскирование PII
                masked_span = self._mask_pii(span)
                optimized_spans.append(masked_span)
                self.compression_stats["l3_masked"] += 1
                
            elif span.level == CriticalityLevel.L4:
                # L4: Агрессивное сжатие
                compressed_span = self._compress_context(span)
                optimized_spans.append(compressed_span)
                self.compression_stats["l4_summarized"] += 1
        
        # Сборка оптимизированного текста
        optimized_spans_sorted = sorted(optimized_spans, key=lambda x: x.start)
        optimized_text = "".join(s.text for s in optimized_spans_sorted)
        
        original_len = len(original_text)
        optimized_len = len(optimized_text)
        compression_ratio = original_len / optimized_len if optimized_len > 0 else 1.0
        
        return OptimizationResult(
            original_text=original_text,
            optimized_text=optimized_text,
            compression_ratio=compression_ratio,
            spans_removed=len(spans) - len(optimized_spans),
            spans_preserved=len(optimized_spans),
            metadata=self.compression_stats.copy()
        )
    
    def _mask_pii(self, span: Span) -> Span:
        """Маскирование персональных данных."""
        # TODO: Интеграция с Presidio для умного маскирования
        masked_text = "[PII REDACTED]"
        return Span(
            text=masked_text,
            start=span.start,
            end=span.start + len(masked_text),
            level=span.level,
            confidence=span.confidence,
            metadata={"original_type": "pii", "masked": True}
        )
    
    def _compress_context(self, span: Span) -> Span:
        """
        Сжатие контекстного наполнения.
        
        TODO: Интеграция с LLMLingua для экстрактивной суммаризации
        """
        # Простая эвристика: удаление лишних пробелов и сокращение
        compressed = " ".join(span.text.split())
        
        # Если всё ещё длинный, берём первые предложения
        if len(compressed) > 500:
            sentences = compressed.split('.')
            compressed = '. '.join(sentences[:3]) + '.'
        
        return Span(
            text=compressed,
            start=span.start,
            end=span.start + len(compressed),
            level=span.level,
            confidence=span.confidence * 0.95,  # Немного снижаем уверенность
            metadata={"compressed": True, "original_len": len(span.text)}
        )
    
    def set_budget(self, budget: int):
        """Установка нового целевого бюджета токенов."""
        self.target_budget = budget


# TODO: Интеграция с LLMLingua
# TODO: Реализация MinHash LSH для дедупликации
# TODO: FOCUS стратегия для adaptive budget
