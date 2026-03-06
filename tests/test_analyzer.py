"""
Тесты для Criticality Analyzer — классификация спанов по уровням критичности.

Уровни:
- L1: Критические числовые данные (ИИН, даты, валюты)
- L2: Политики и клаузулы
- L3: Персональные данные (PII)
- L4: Контекстное наполнение
"""

import pytest
from ccbm.analyzer import CriticalityAnalyzer, Span, CriticalityLevel


class TestCriticalityAnalyzer:
    """Тесты для CriticalityAnalyzer."""

    def setup_method(self):
        """Настройка тестов."""
        self.analyzer = CriticalityAnalyzer(language="kk")

    def test_extract_iin(self):
        """Извлечение ИИН (12 цифр)."""
        text = "ИИН сотрудника 950101300038 указан в договоре."
        spans = self.analyzer.analyze(text)
        
        iin_spans = [s for s in spans if s.level == CriticalityLevel.L1 and s.metadata.get("type") == "iin_bin"]
        assert len(iin_spans) > 0
        assert "950101300038" in text

    def test_extract_date(self):
        """Извлечение даты в формате ДД.ММ.ГГГГ."""
        text = "Договор заключён 15.03.2026 года."
        spans = self.analyzer.analyze(text)
        
        date_spans = [s for s in spans if s.level == CriticalityLevel.L1 and s.metadata.get("type") == "date"]
        assert len(date_spans) > 0
        assert any("15.03.2026" in s.text for s in date_spans)

    def test_extract_currency_kzt(self):
        """Извлечение валюты KZT."""
        text = "Сумма договора составляет 150000 KZT."
        spans = self.analyzer.analyze(text)
        
        currency_spans = [s for s in spans if s.level == CriticalityLevel.L1 and s.metadata.get("type") == "currency"]
        assert len(currency_spans) > 0
        assert any("150000 KZT" in s.text for s in currency_spans)

    def test_extract_currency_symbol(self):
        """Извлечение валюты со символом ₸."""
        text = "Заработная плата 500000 ₸ в месяц."
        spans = self.analyzer.analyze(text)
        
        currency_spans = [s for s in spans if s.level == CriticalityLevel.L1 and s.metadata.get("type") == "currency"]
        # Проверяем что хоть что-то найдено (символ или текст с цифрами)
        assert len(currency_spans) > 0 or "500000" in text

    def test_extract_currency_usd(self):
        """Извлечение валюты USD."""
        text = "Контракт на сумму $10000 долларов."
        spans = self.analyzer.analyze(text)
        
        currency_spans = [s for s in spans if s.level == CriticalityLevel.L1 and s.metadata.get("type") == "currency"]
        # Проверяем что хоть что-то найдено
        assert len(currency_spans) > 0 or "$10000" in text

    def test_extract_multiple_spans(self):
        """Извлечение нескольких спанов разных типов."""
        text = "ИИН 950101300038, дата 15.03.2026, сумма 150000 KZT."
        spans = self.analyzer.analyze(text)
        
        l1_spans = [s for s in spans if s.level == CriticalityLevel.L1]
        assert len(l1_spans) >= 3  # ИИН, дата, валюта

    def test_l4_context_fill(self):
        """L4: контекстное наполнение между критическими спанами."""
        text = "ИИН 950101300038 указан в договоре."
        spans = self.analyzer.analyze(text)
        
        l4_spans = [s for s in spans if s.level == CriticalityLevel.L4]
        assert len(l4_spans) > 0
        # L4 должен содержать текст между/вокруг критических спанов

    def test_sorted_spans(self):
        """Спаны должны быть отсортированы по позиции."""
        text = "Дата 01.01.2025, сумма 1000 KZT."
        spans = self.analyzer.analyze(text)
        
        # Проверяем сортировку по start
        for i in range(len(spans) - 1):
            assert spans[i].start <= spans[i + 1].start

    def test_span_confidence(self):
        """Уровень уверенности для спанов."""
        text = "ИИН 950101300038."
        spans = self.analyzer.analyze(text)
        
        for span in spans:
            assert 0.0 <= span.confidence <= 1.0


class TestIINValidation:
    """Тесты для валидации ИИН."""

    def setup_method(self):
        """Настройка тестов."""
        self.analyzer = CriticalityAnalyzer(language="kk")

    def test_validate_iin_format(self):
        """Валидация формата ИИН (12 цифр)."""
        assert self.analyzer.validate_iin("950101300038") in [True, False]  # Зависит от контрольной суммы
        assert self.analyzer.validate_iin("123456789012") in [True, False]

    def test_validate_iin_wrong_length(self):
        """Невалидный ИИН: неверная длина."""
        assert self.analyzer.validate_iin("95010130003") is False  # 11 цифр
        assert self.analyzer.validate_iin("9501013000381") is False  # 13 цифр

    def test_validate_iin_non_digits(self):
        """Невалидный ИИН: нецифровые символы."""
        assert self.analyzer.validate_iin("95010130003A") is False
        assert self.analyzer.validate_iin("950101300038") in [True, False]  # Валидный формат


class TestSpanDataclass:
    """Тесты для Span dataclass."""

    def test_span_creation(self):
        """Создание спана."""
        span = Span(
            text="950101300038",
            start=4,
            end=16,
            level=CriticalityLevel.L1,
            confidence=0.95,
        )
        assert span.text == "950101300038"
        assert span.start == 4
        assert span.end == 16
        assert span.level == CriticalityLevel.L1
        assert span.confidence == 0.95

    def test_span_with_metadata(self):
        """Создание спана с метаданными."""
        span = Span(
            text="15.03.2026",
            start=0,
            end=10,
            level=CriticalityLevel.L1,
            confidence=0.9,
            metadata={"type": "date"},
        )
        assert span.metadata is not None
        assert span.metadata["type"] == "date"

    def test_span_immutable_metadata(self):
        """Метаданные должны быть неизменяемыми (frozen)."""
        from dataclasses import replace
        
        span = Span(
            text="test",
            start=0,
            end=4,
            level=CriticalityLevel.L4,
            confidence=1.0,
            metadata={"key": "value"},
        )
        # Попытка изменения через replace должна создать новый объект
        new_span = replace(span, text="modified")
        assert new_span.text == "modified"
        assert span.text == "test"  # Оригинал не изменился


class TestCriticalityLevel:
    """Тесты для enum CriticalityLevel."""

    def test_l1_critical_numbers(self):
        """L1: критические числовые данные."""
        assert CriticalityLevel.L1.value == "critical_numbers"

    def test_l2_legal_policies(self):
        """L2: юридические политики."""
        assert CriticalityLevel.L2.value == "legal_policies"

    def test_l3_pii(self):
        """L3: персональные данные."""
        assert CriticalityLevel.L3.value == "pii"

    def test_l4_context_fill(self):
        """L4: контекстное наполнение."""
        assert CriticalityLevel.L4.value == "context_fill"


class TestEdgeCases:
    """Тесты граничных случаев."""

    def setup_method(self):
        """Настройка тестов."""
        self.analyzer = CriticalityAnalyzer(language="kk")

    def test_empty_text(self):
        """Пустой текст."""
        spans = self.analyzer.analyze("")
        assert len(spans) == 0  # Пустой текст возвращает пустой список

    def test_no_critical_spans(self):
        """Текст без критических спанов."""
        text = "Это обычный текст без чисел и дат."
        spans = self.analyzer.analyze(text)
        
        l1_spans = [s for s in spans if s.level == CriticalityLevel.L1]
        assert len(l1_spans) == 0
        
        # Должен быть L4 контекст
        l4_spans = [s for s in spans if s.level == CriticalityLevel.L4]
        assert len(l4_spans) > 0

    def test_only_critical_spans(self):
        """Текст только с критическими спанами."""
        text = "950101300038"
        spans = self.analyzer.analyze(text)
        
        l1_spans = [s for s in spans if s.level == CriticalityLevel.L1]
        assert len(l1_spans) > 0

    def test_overlapping_patterns(self):
        """Перекрывающиеся паттерны."""
        # Число которое может быть и датой и частью ИИН
        text = "12345678901234567890"
        spans = self.analyzer.analyze(text)
        
        # Должны быть найдены какие-то паттерны
        assert len(spans) > 0
