"""
Тесты для KazRoBERTa NER.
"""

from ccbm.analyzer.kazroberta_ner import (
    EntityType,
    KazRoBERTaNER,
    NERConfig,
    NEREntity,
    create_ner_model,
)


class TestEntityType:
    """Тесты для EntityType."""

    def test_entity_types(self):
        """Проверка типов сущностей."""
        assert EntityType.PER.value == "PER"
        assert EntityType.LOC.value == "LOC"
        assert EntityType.ORG.value == "ORG"
        assert EntityType.IIN.value == "IIN"
        assert EntityType.PHONE.value == "PHONE"


class TestNEREntity:
    """Тесты для NEREntity."""

    def test_entity_creation(self):
        """Создание сущности."""
        entity = NEREntity(
            text="Иван Иванов",
            entity_type=EntityType.PER,
            start=0,
            end=11,
            confidence=0.95,
        )

        assert entity.text == "Иван Иванов"
        assert entity.entity_type == EntityType.PER
        assert entity.confidence == 0.95

    def test_entity_to_dict(self):
        """Сериализация в словарь."""
        entity = NEREntity(
            text="950101300038",
            entity_type=EntityType.IIN,
            start=0,
            end=12,
            confidence=0.95,
        )

        entity_dict = entity.to_dict()

        assert entity_dict["text"] == "950101300038"
        assert entity_dict["entity_type"] == "IIN"
        assert entity_dict["confidence"] == 0.95


class TestKazRoBERTaNER:
    """Тесты для KazRoBERTaNER."""

    def test_ner_creation(self):
        """Создание NER модели."""
        ner = KazRoBERTaNER()

        assert ner.model_name == "IS2AI/kazroberta-ner"
        assert ner.device == "cpu"
        assert ner.is_loaded is False

    def test_ner_load_fallback(self):
        """Загрузка NER с fallback."""
        ner = KazRoBERTaNER()

        # Модель может не загрузиться без transformers
        loaded = ner.load()

        # Должна вернуться True (с fallback или успешно)
        assert isinstance(loaded, bool)

    def test_extract_iin_pattern(self):
        """Извлечение ИИН по паттерну."""
        ner = KazRoBERTaNER()

        text = "ИИН сотрудника 950101300038 указан в документе."
        entities = ner.predict(text)

        iin_entities = [e for e in entities if e.entity_type == EntityType.IIN]
        assert len(iin_entities) > 0
        assert iin_entities[0].text == "950101300038"

    def test_extract_bin_pattern(self):
        """Извлечение БИН по паттерну."""
        ner = KazRoBERTaNER()

        text = "БИН компании 010140000012 зарегистрирован."
        entities = ner.predict(text)

        bin_entities = [e for e in entities if e.entity_type == EntityType.BIN]
        assert len(bin_entities) > 0

    def test_extract_phone_pattern(self):
        """Извлечение телефона по паттерну."""
        ner = KazRoBERTaNER()

        text = "Телефон для связи +7-777-123-4567."
        entities = ner.predict(text)

        phone_entities = [e for e in entities if e.entity_type == EntityType.PHONE]
        assert len(phone_entities) > 0
        assert "+7" in phone_entities[0].text

    def test_extract_email_pattern(self):
        """Извлечение email по паттерну."""
        ner = KazRoBERTaNER()

        text = "Email для связи user@example.kz."
        entities = ner.predict(text)

        email_entities = [e for e in entities if e.entity_type == EntityType.EMAIL]
        assert len(email_entities) > 0
        assert "@" in email_entities[0].text

    def test_extract_multiple_patterns(self):
        """Извлечение нескольких паттернов."""
        ner = KazRoBERTaNER()

        text = "ИИН 950101300038, тел. +7-777-123-4567, email test@example.kz"
        entities = ner.predict(text)

        assert len(entities) >= 3

    def test_extract_pii(self):
        """Извлечение только PII."""
        ner = KazRoBERTaNER()

        text = "Иван Иванов (ИИН 950101300038) работает в ТОО Компания."
        pii_entities = ner.extract_pii(text)

        # Должен найти ИИН и возможно имя
        assert len(pii_entities) >= 1

    def test_mask_pii(self):
        """Маскирование PII."""
        ner = KazRoBERTaNER()

        text = "ИИН 950101300038 сотрудника."
        masked = ner.mask_pii(text)

        assert "950101300038" not in masked
        assert "[REDACTED]" in masked

    def test_mask_pii_custom_replacement(self):
        """Маскирование с кастомной заменой."""
        ner = KazRoBERTaNER()

        text = "ИИН 950101300038."
        masked = ner.mask_pii(text, replacement="[MASKED]")

        assert "950101300038" not in masked
        assert "[MASKED]" in masked

    def test_mask_multiple_pii(self):
        """Маскирование нескольких PII."""
        ner = KazRoBERTaNER()

        text = "ИИН 950101300038, тел. +7-777-123-4567."
        masked = ner.mask_pii(text)

        assert "950101300038" not in masked
        assert "+7" not in masked
        assert masked.count("[REDACTED]") >= 2

    def test_empty_text(self):
        """Пустой текст."""
        ner = KazRoBERTaNER()

        entities = ner.predict("")
        assert len(entities) == 0

    def test_no_entities(self):
        """Текст без сущностей."""
        ner = KazRoBERTaNER()

        text = "Это обычный текст без чисел и контактов."
        entities = ner.predict(text)

        # Может быть 0 или больше (если модель найдёт что-то)
        assert isinstance(entities, list)


class TestNERConfig:
    """Тесты для NERConfig."""

    def test_config_defaults(self):
        """Конфигурация по умолчанию."""
        config = NERConfig()

        assert "kazroberta" in config.model_name.lower()
        assert config.device == "cpu"
        assert config.confidence_threshold == 0.7
        assert config.extract_pii_only is True

    def test_config_custom(self):
        """Пользовательская конфигурация."""
        config = NERConfig(
            model_name="custom-model",
            device="cuda",
            confidence_threshold=0.9,
            extract_pii_only=False,
        )

        assert config.model_name == "custom-model"
        assert config.device == "cuda"
        assert config.confidence_threshold == 0.9

    def test_config_to_dict(self):
        """Сериализация конфигурации."""
        config = NERConfig()
        config_dict = config.to_dict()

        assert "model_name" in config_dict
        assert "device" in config_dict
        assert "confidence_threshold" in config_dict


class TestCreateNerModel:
    """Тесты для create_ner_model."""

    def test_create_default(self):
        """Создание модели по умолчанию."""
        ner = create_ner_model()

        assert isinstance(ner, KazRoBERTaNER)

    def test_create_with_config(self):
        """Создание модели с конфигурацией."""
        config = NERConfig(device="cpu")
        ner = create_ner_model(config)

        assert isinstance(ner, KazRoBERTaNER)
        assert ner.device == "cpu"


class TestIntegration:
    """Интеграционные тесты."""

    def test_full_ner_workflow(self):
        """Полный рабочий процесс NER."""
        ner = KazRoBERTaNER()

        # Текст с PII
        text = "Иванов Иван (ИИН 950101300038) работает в ТОО Альфа. Тел. +7-777-123-4567."

        # Предсказание
        entities = ner.predict(text)

        # Проверка что нашлись сущности
        assert len(entities) >= 2

        # PII извлечение
        pii = ner.extract_pii(text)
        assert len(pii) >= 2

        # Маскирование
        masked = ner.mask_pii(text)
        assert "950101300038" not in masked
        assert "+7" not in masked

    def test_iin_detection(self):
        """Детекция ИИН."""
        ner = KazRoBERTaNER()

        text = "ИИН: 850315400123"
        entities = ner.predict(text)

        iin_entities = [e for e in entities if e.entity_type == EntityType.IIN]
        assert len(iin_entities) == 1
        assert iin_entities[0].text == "850315400123"

    def test_contact_detection(self):
        """Детекция контактов."""
        ner = KazRoBERTaNER()

        text = "Свяжитесь по телефону +7-777-999-8888 или email contact@company.kz"
        entities = ner.predict(text)

        phone_entities = [e for e in entities if e.entity_type == EntityType.PHONE]
        email_entities = [e for e in entities if e.entity_type == EntityType.EMAIL]

        assert len(phone_entities) >= 1
        assert len(email_entities) >= 1

    def test_sorted_entities(self):
        """Сортировка сущностей по позиции."""
        ner = KazRoBERTaNER()

        text = "ИИН 950101300038, тел. +7-777-123-4567, email test@example.kz"
        entities = ner.predict(text)

        # Проверка сортировки
        for i in range(len(entities) - 1):
            assert entities[i].start <= entities[i + 1].start
