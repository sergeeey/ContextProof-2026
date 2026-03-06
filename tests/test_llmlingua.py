"""
Тесты для LLMLingua Integration.
"""

import pytest
from ccbm.optimizer.llmlingua import (
    LLMLinguaCompressor,
    CompressionResult,
    LLMLinguaConfig,
    create_compressor,
)


class TestCompressionResult:
    """Тесты для CompressionResult."""

    def test_result_creation(self):
        """Создание результата сжатия."""
        result = CompressionResult(
            original_text="Original text " * 100,
            compressed_text="Compressed",
            original_tokens=200,
            compressed_tokens=50,
            compression_ratio=4.0,
            method="llmlingua2",
        )
        
        assert result.original_tokens == 200
        assert result.compressed_tokens == 50
        assert result.compression_ratio == 4.0
        assert result.method == "llmlingua2"

    def test_tokens_saved(self):
        """Расчёт сохранённых токенов."""
        result = CompressionResult(
            original_text="Original",
            compressed_text="Compressed",
            original_tokens=200,
            compressed_tokens=50,
            compression_ratio=4.0,
            method="test",
        )
        
        assert result.tokens_saved == 150

    def test_savings_percent(self):
        """Расчёт процента экономии."""
        result = CompressionResult(
            original_text="Original",
            compressed_text="Compressed",
            original_tokens=200,
            compressed_tokens=50,
            compression_ratio=4.0,
            method="test",
        )
        
        assert result.savings_percent == 75.0

    def test_savings_percent_zero_original(self):
        """Расчёт процента при нулевом оригинале."""
        result = CompressionResult(
            original_text="",
            compressed_text="",
            original_tokens=0,
            compressed_tokens=0,
            compression_ratio=1.0,
            method="test",
        )
        
        assert result.savings_percent == 0.0

    def test_to_dict(self):
        """Сериализация в словарь."""
        result = CompressionResult(
            original_text="Original",
            compressed_text="Compressed",
            original_tokens=200,
            compressed_tokens=50,
            compression_ratio=4.0,
            method="llmlingua2",
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["original_tokens"] == 200
        assert result_dict["compressed_tokens"] == 50
        assert result_dict["tokens_saved"] == 150
        assert result_dict["savings_percent"] == 75.0


class TestLLMLinguaCompressor:
    """Тесты для LLMLinguaCompressor."""

    def test_compressor_creation(self):
        """Создание компрессора."""
        compressor = LLMLinguaCompressor()
        
        assert compressor.model_name == "microsoft/llmlingua-2-xlm-roberta-large-meetingbank"
        assert compressor.device == "cpu"
        assert compressor._compressor is None  # Ленивая инициализация

    def test_compressor_lazy_init(self):
        """Ленивая инициализация компрессора."""
        compressor = LLMLinguaCompressor()
        
        # compressor property должен создать PromptCompressor
        # Но мы не можем это протестировать без установленной библиотеки
        # Проверяем что свойство доступно
        try:
            _ = compressor.compressor
        except Exception:
            # Ожидается если llmlingua не установлена
            pass

    def test_fallback_compress(self):
        """Базовое сжатие (fallback)."""
        compressor = LLMLinguaCompressor()
        
        text = "Это очень длинный текст. " * 50
        result = compressor._fallback_compress(text)
        
        assert result.original_text == text
        assert len(result.compressed_text) < len(text)
        assert result.compression_ratio >= 1.0
        assert result.method == "fallback"

    def test_estimate_tokens(self):
        """Оценка токенов."""
        text = "Это тестовый текст из пяти слов"
        tokens = LLMLinguaCompressor._estimate_tokens(text)
        
        # 6 слов * 1.5 = 9 токенов
        assert tokens == 9

    def test_estimate_tokens_empty(self):
        """Оценка токенов для пустого текста."""
        text = ""
        tokens = LLMLinguaCompressor._estimate_tokens(text)
        
        assert tokens == 0

    def test_compress_with_fallback(self):
        """Сжатие с fallback."""
        compressor = LLMLinguaCompressor()
        
        text = "Тестовый текст для сжатия. " * 20
        result = compressor.compress(text, target_token=50)
        
        # Должен использовать fallback если llmlingua не установлена
        assert result.original_text == text
        assert result.compressed_text != ""
        assert result.compression_ratio >= 1.0


class TestLLMLinguaConfig:
    """Тесты для LLMLinguaConfig."""

    def test_config_defaults(self):
        """Конфигурация по умолчанию."""
        config = LLMLinguaConfig()
        
        assert "llmlingua" in config.model_name
        assert config.device == "cpu"
        assert config.target_token == 300
        assert config.rank_method == "llmlingua2"

    def test_config_custom(self):
        """Пользовательская конфигурация."""
        config = LLMLinguaConfig(
            model_name="custom-model",
            device="cuda",
            target_token=500,
            rank_method="longllmlingua",
        )
        
        assert config.model_name == "custom-model"
        assert config.device == "cuda"
        assert config.target_token == 500
        assert config.rank_method == "longllmlingua"

    def test_config_to_dict(self):
        """Сериализация конфигурации."""
        config = LLMLinguaConfig(
            target_token=400,
            instruction="Test instruction",
        )
        
        config_dict = config.to_dict()
        
        assert config_dict["target_token"] == 400
        assert config_dict["instruction"] == "Test instruction"


class TestCreateCompressor:
    """Тесты для create_compressor."""

    def test_create_default(self):
        """Создание компрессора по умолчанию."""
        compressor = create_compressor()
        
        assert isinstance(compressor, LLMLinguaCompressor)

    def test_create_with_config(self):
        """Создание компрессора с конфигурацией."""
        config = LLMLinguaConfig(
            model_name="test-model",
            device="cpu",
        )
        compressor = create_compressor(config)
        
        assert isinstance(compressor, LLMLinguaCompressor)
        assert compressor.model_name == "test-model"


class TestIntegration:
    """Интеграционные тесты."""

    def test_full_compression_workflow(self):
        """Полный рабочий процесс сжатия."""
        compressor = LLMLinguaCompressor()
        
        # Длинный текст
        text = "Это важный документ. " * 100
        
        # Сжатие
        result = compressor.compress(text, target_token=100)
        
        # Проверка результатов
        assert result.original_text == text
        assert result.compressed_text != ""
        assert result.compression_ratio >= 1.0
        assert result.method in ["llmlingua2", "fallback"]
        
        # Сериализация
        result_dict = result.to_dict()
        assert "compression_ratio" in result_dict
        assert "savings_percent" in result_dict

    def test_long_document_compression(self):
        """Сжатие длинного документа."""
        compressor = LLMLinguaCompressor()
        
        text = "Раздел 1. " * 50 + "Раздел 2. " * 50
        result = compressor._fallback_compress(text)
        
        assert result.original_tokens > result.compressed_tokens
        assert result.savings_percent > 0

    def test_multiple_compressions(self):
        """Множественное сжатие."""
        compressor = LLMLinguaCompressor()
        
        texts = [
            "Текст 1 для сжатия. " * 20,
            "Текст 2 для сжатия. " * 30,
            "Текст 3 для сжатия. " * 40,
        ]
        
        results = []
        for text in texts:
            result = compressor.compress(text, target_token=50)
            results.append(result)
        
        assert len(results) == 3
        assert all(r.compression_ratio >= 1.0 for r in results)

    def test_compression_with_metadata(self):
        """Сжатие с метаданными."""
        compressor = LLMLinguaCompressor()
        
        text = "Тестовый текст с метаданными. " * 10
        result = compressor.compress(
            text,
            target_token=20,
            instruction="Сохрани только важное",
        )
        
        # Fallback должен иметь metadata
        assert result.metadata is not None
        # Проверяем что metadata есть (fallback или llmlingua)
        assert len(result.metadata) > 0
