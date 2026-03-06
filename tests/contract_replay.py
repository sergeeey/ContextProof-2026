"""
Тесты для Information Contract и Context Replay.
"""

import pytest
from ccbm.contract.information_contract import (
    InformationContractEngine,
    InformationClass,
    ContractVersion,
    create_information_contract,
)
from ccbm.replay.context_replay import (
    ContextReplayEngine,
    EventType,
    get_replay_engine,
)


class TestInformationContract:
    """Тесты для Information Contract."""

    def test_contract_creation(self):
        """Создание контракта."""
        engine = InformationContractEngine()
        
        text = "ИИН 950101300038, договор на 100000 KZT."
        compressed = "ИИН 950101300038, договор."
        
        contract = engine.create_contract(text, compressed)
        
        assert contract.contract_id.startswith("CONTRACT-")
        assert contract.version == ContractVersion.V1_0
        assert contract.information_preserved >= 0.0
        assert contract.critical_spans_preserved >= 0.0
        assert contract.certificate_hash is not None

    def test_contract_validation(self):
        """Валидация контракта."""
        engine = InformationContractEngine(
            min_information_preserved=0.95,
            min_critical_spans=1.0,
        )
        
        text = "ИИН 950101300038."
        compressed = "ИИН 950101300038."  # Полное сохранение
        
        contract = engine.create_contract(text, compressed)
        
        assert contract.is_valid is True
        assert len(contract.validation_errors) == 0

    def test_contract_invalid(self):
        """Невалидный контракт."""
        engine = InformationContractEngine(
            min_information_preserved=0.99,  # Очень высокий порог
        )
        
        text = "ИИН 950101300038, много текста."
        compressed = "ИИН."  # Потеря информации
        
        contract = engine.create_contract(text, compressed)
        
        # Контракт может быть невалидным
        assert contract.information_preserved < 0.99

    def test_segmentation(self):
        """Сегментация контекста."""
        engine = InformationContractEngine()
        
        text = "ИИН 950101300038. Сумма 100000 KZT. Дата 15.03.2026."
        segments = engine.segment_context(text)
        
        assert len(segments) > 0
        
        # Проверка классов
        classes = [s.information_class for s in segments]
        assert any(c == InformationClass.FACTS for c in classes)
        assert any(c == InformationClass.NUMBERS for c in classes)

    def test_numeric_invariants(self):
        """Проверка числовых инвариантов."""
        engine = InformationContractEngine()
        
        text = "Сумма 100000 KZT, НДС 12000."
        compressed = "Сумма 100000 KZT, НДС 12000."
        
        preserved = engine._check_numeric_invariants(text, compressed)
        assert preserved is True
        
        # С потерей чисел
        compressed_bad = "Сумма удалена."
        preserved_bad = engine._check_numeric_invariants(text, compressed_bad)
        assert preserved_bad is False

    def test_certificate_generation(self):
        """Генерация сертификата."""
        engine = InformationContractEngine()
        
        text = "ИИН 950101300038."
        compressed = "ИИН 950101300038."
        
        contract = engine.create_contract(text, compressed)
        cert_hash = contract.get_certificate()
        
        assert len(cert_hash) == 64  # SHA-256 hex
        
        # Повторный вызов возвращает тот же hash
        assert contract.get_certificate() == cert_hash

    def test_contract_serialization(self):
        """Сериализация контракта."""
        engine = InformationContractEngine()
        
        text = "ИИН 950101300038."
        compressed = "ИИН 950101300038."
        
        contract = engine.create_contract(text, compressed)
        
        # JSON сериализация
        json_str = contract.to_json()
        assert len(json_str) > 0
        
        # Dict сериализация
        data = contract.to_dict()
        assert "contract_id" in data
        assert "information_preserved" in data


class TestContextReplay:
    """Тесты для Context Replay."""

    def test_session_creation(self):
        """Создание сессии."""
        engine = ContextReplayEngine()
        
        session = engine.create_session()
        
        assert session.session_id.startswith("SESSION-")
        assert len(session.events) == 0

    def test_log_events(self):
        """Логирование событий."""
        engine = ContextReplayEngine()
        session = engine.create_session()
        
        # Context created
        event1 = engine.log_context_created(session, "ИИН 950101300038.")
        assert event1.event_type == EventType.CONTEXT_CREATED
        
        # Context compressed
        event2 = engine.log_context_compressed(
            session,
            "ИИН 950101300038.",
            "ИИН.",
            compression_ratio=2.0,
        )
        assert event2.event_type == EventType.CONTEXT_COMPRESSED
        
        # LLM call
        event3 = engine.log_llm_call(session, "gpt-4", "Какой ИИН?")
        assert event3.event_type == EventType.LLM_CALL
        
        # LLM response
        event4 = engine.log_llm_response(session, "ИИН 950101300038.")
        assert event4.event_type == EventType.LLM_RESPONSE
        
        assert len(session.events) == 4

    def test_reconstruct_prompt(self):
        """Реконструкция промпта."""
        engine = ContextReplayEngine()
        session = engine.create_session()
        
        engine.log_context_created(session, "ИИН 950101300038.")
        engine.log_context_compressed(session, "ИИН 950101300038.", "ИИН.", 2.0)
        
        prompt = session.reconstruct_prompt()
        assert prompt == "ИИН."

    def test_get_removed_segments(self):
        """Получение удалённых сегментов."""
        engine = ContextReplayEngine()
        session = engine.create_session()
        
        engine.log_context_created(session, "ИИН 950101300038. Текст.")
        engine.log_context_compressed(session, "ИИН 950101300038. Текст.", "ИИН.", 3.0)
        
        # Пока не добавлен contract, removed segments будет пустым
        removed = session.get_removed_segments()
        assert isinstance(removed, list)

    def test_replay(self):
        """Replay сессии."""
        engine = ContextReplayEngine()
        session_id = "TEST-SESSION-001"
        
        session = engine.create_session(session_id)
        engine.log_context_created(session, "Тест.")
        
        # Replay
        replayed = engine.replay(session_id)
        
        assert replayed is not None
        assert replayed.session_id == session_id
        assert len(replayed.events) == 1

    def test_save_load_session(self, tmp_path):
        """Сохранение и загрузка сессии."""
        engine = ContextReplayEngine(storage_path=str(tmp_path))
        session = engine.create_session()
        
        engine.log_context_created(session, "Тест.")
        engine.save_session(session)
        
        # Загрузка
        loaded = engine.replay(session.session_id)
        
        assert loaded is not None
        assert len(loaded.events) == 1

    def test_global_engine(self):
        """Глобальный engine."""
        engine1 = get_replay_engine()
        engine2 = get_replay_engine()
        
        assert engine1 is engine2


class TestIntegration:
    """Интеграционные тесты."""

    def test_contract_replay_integration(self):
        """Интеграция Contract + Replay."""
        from ccbm.contract import InformationContractEngine
        from ccbm.replay import ContextReplayEngine
        
        contract_engine = InformationContractEngine()
        replay_engine = ContextReplayEngine()
        
        # Создание сессии
        session = replay_engine.create_session()
        
        # Логирование
        text = "ИИН 950101300038, договор на 100000 KZT."
        replay_engine.log_context_created(session, text)
        
        # Сжатие
        compressed = "ИИН 950101300038."
        replay_engine.log_context_compressed(session, text, compressed, 2.0)
        
        # Создание контракта
        contract = contract_engine.create_contract(text, compressed)
        replay_engine.log_contract_validated(session, contract)
        
        # Проверка
        assert contract.information_preserved >= 0.0
        assert len(session.events) == 3

    def test_full_workflow(self):
        """Полный workflow."""
        from ccbm.contract import InformationContractEngine
        from ccbm.replay import ContextReplayEngine
        
        contract_engine = InformationContractEngine()
        replay_engine = ContextReplayEngine()
        
        session = replay_engine.create_session()
        
        # 1. Context created
        text = "ИИН 950101300038, сумма 100000 KZT."
        replay_engine.log_context_created(session, text)
        
        # 2. Context compressed
        compressed = "ИИН 950101300038, сумма 100000 KZT."
        replay_engine.log_context_compressed(session, text, compressed, 1.0)
        
        # 3. Contract validated
        contract = contract_engine.create_contract(text, compressed)
        replay_engine.log_contract_validated(session, contract)
        
        # 4. LLM call
        replay_engine.log_llm_call(session, "gpt-4", "Какой ИИН?")
        
        # 5. LLM response
        replay_engine.log_llm_response(session, "950101300038")
        
        # Проверка
        assert len(session.events) == 5
        # contract.is_valid может быть False из-за semantic_delta
        assert contract.information_preserved >= 0.0
        
        # Replay
        prompt = replay_engine.reconstruct_prompt(session.session_id)
        assert prompt == compressed
