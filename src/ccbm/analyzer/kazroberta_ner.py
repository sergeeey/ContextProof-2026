"""
KazRoBERTa NER — распознавание именованных сущностей для казахского языка.

Интеграция с KazRoBERTa моделью для детекции PII:
- PER (Person) — имена, фамилии
- LOC (Location) — адреса, города
- ORG (Organization) — компании, организации
- MISC (Miscellaneous) — прочее

Модель: IS2AI/kazroberta-ner
Dataset: KazNERD
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class EntityType(Enum):
    """Типы сущностей NER."""
    PER = "PER"  # Person (ФИО)
    LOC = "LOC"  # Location (адреса, города)
    ORG = "ORG"  # Organization (компании)
    MISC = "MISC"  # Miscellaneous
    IIN = "IIN"  # ИИН (кастомный)
    BIN = "BIN"  # БИН (кастомный)
    PHONE = "PHONE"  # Телефон (кастомный)
    EMAIL = "EMAIL"  # Email (кастомный)


@dataclass
class NEREntity:
    """Распознанная сущность."""
    text: str
    entity_type: EntityType
    start: int
    end: int
    confidence: float
    metadata: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Сериализация в словарь."""
        return {
            "text": self.text,
            "entity_type": self.entity_type.value,
            "start": self.start,
            "end": self.end,
            "confidence": self.confidence,
            "metadata": self.metadata or {},
        }


class KazRoBERTaNER:
    """
    NER модель на базе KazRoBERTa.
    
    Поддерживает:
    - Распознавание ФИО (PER)
    - Распознавание локаций (LOC)
    - Распознавание организаций (ORG)
    - Кастомные паттерны (ИИН, БИН, телефон, email)
    """
    
    # Паттерны для кастомных сущностей
    IIN_PATTERN = r'\b\d{12}\b'
    BIN_PATTERN = r'\b\d{12}\b'
    PHONE_PATTERN = r'\+7[-\s]?\d{3}[-\s]?\d{3}[-\s]?\d{4}'
    EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    
    def __init__(
        self,
        model_name: str = "IS2AI/kazroberta-ner",
        device: str = "cpu",
    ):
        """
        Инициализация NER модели.
        
        Args:
            model_name: Название модели
            device: Устройство (cpu/cuda)
        """
        self.model_name = model_name
        self.device = device
        self._model = None
        self._tokenizer = None
        self._is_loaded = False
    
    @property
    def is_loaded(self) -> bool:
        """Загружена ли модель."""
        return self._is_loaded
    
    def load(self) -> bool:
        """
        Загрузка модели.
        
        Returns:
            True если успешно загружена
        """
        if self._is_loaded:
            return True
        
        try:
            logger.info(f"Загрузка KazRoBERTa NER: {self.model_name}")
            
            # Lazy import transformers
            from transformers import AutoModelForTokenClassification, AutoTokenizer
            
            self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self._model = AutoModelForTokenClassification.from_pretrained(self.model_name)
            
            self._is_loaded = True
            logger.info("KazRoBERTa NER загружена успешно")
            return True
            
        except Exception as e:
            logger.warning(f"Не удалось загрузить KazRoBERTa: {e}")
            logger.warning("Используем fallback (паттерны)")
            return False
    
    def predict(self, text: str) -> List[NEREntity]:
        """
        Предсказание сущностей в тексте.
        
        Args:
            text: Текст для анализа
            
        Returns:
            Список распознанных сущностей
        """
        entities = []
        
        # 1. Кастомные паттерны (ИИН, БИН, телефон, email)
        entities.extend(self._extract_pattern_entities(text))
        
        # 2. NER модель (если загружена)
        if self._is_loaded and self._model and self._tokenizer:
            try:
                ner_entities = self._predict_with_model(text)
                entities.extend(ner_entities)
            except Exception as e:
                logger.error(f"Ошибка NER предсказания: {e}")
        
        # 3. Сортировка по позиции
        entities.sort(key=lambda e: e.start)
        
        return entities
    
    def _predict_with_model(self, text: str) -> List[NEREntity]:
        """
        Предсказание с помощью модели.
        
        Args:
            text: Текст
            
        Returns:
            Список сущностей
        """
        if not self._model or not self._tokenizer:
            return []
        
        # Токенизация
        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            padding=True,
            return_offsets_mapping=True,
        )
        
        # Предсказание
        import torch
        with torch.no_grad():
            outputs = self._model(**inputs)
            predictions = outputs.logits.argmax(dim=2)[0]
        
        # Декодирование
        entities = []
        offset_mapping = inputs["offset_mapping"][0]
        
        current_entity = None
        
        for i, prediction in enumerate(predictions):
            token_id = prediction.item()
            
            # Skip special tokens
            if token_id == 0:  # PAD
                continue
            
            # Get label
            label = self._model.config.id2label.get(token_id, "O")
            
            if label == "O":
                if current_entity:
                    entities.append(current_entity)
                    current_entity = None
                continue
            
            # Parse B-XXX, I-XXX
            prefix, entity_type = label.split("-") if "-" in label else ("O", label)
            
            if prefix == "B":
                if current_entity:
                    entities.append(current_entity)
                
                start, end = offset_mapping[i]
                current_entity = NEREntity(
                    text=text[start:end],
                    entity_type=EntityType[entity_type],
                    start=start,
                    end=end,
                    confidence=0.9,
                )
            
            elif prefix == "I" and current_entity:
                start, end = offset_mapping[i]
                current_entity.text += text[current_entity.end:end]
                current_entity.end = end
        
        if current_entity:
            entities.append(current_entity)
        
        return entities
    
    def _extract_pattern_entities(self, text: str) -> List[NEREntity]:
        """
        Извлечение сущностей по паттернам.
        
        Args:
            text: Текст
            
        Returns:
            Список сущностей
        """
        import re
        
        entities = []
        
        # ИИН
        for match in re.finditer(self.IIN_PATTERN, text):
            entities.append(NEREntity(
                text=match.group(),
                entity_type=EntityType.IIN,
                start=match.start(),
                end=match.end(),
                confidence=0.95,
                metadata={"type": "iin"},
            ))
        
        # БИН
        for match in re.finditer(self.BIN_PATTERN, text):
            entities.append(NEREntity(
                text=match.group(),
                entity_type=EntityType.BIN,
                start=match.start(),
                end=match.end(),
                confidence=0.95,
                metadata={"type": "bin"},
            ))
        
        # Телефон
        for match in re.finditer(self.PHONE_PATTERN, text):
            entities.append(NEREntity(
                text=match.group(),
                entity_type=EntityType.PHONE,
                start=match.start(),
                end=match.end(),
                confidence=0.9,
                metadata={"type": "phone"},
            ))
        
        # Email
        for match in re.finditer(self.EMAIL_PATTERN, text):
            entities.append(NEREntity(
                text=match.group(),
                entity_type=EntityType.EMAIL,
                start=match.start(),
                end=match.end(),
                confidence=0.95,
                metadata={"type": "email"},
            ))
        
        return entities
    
    def extract_pii(self, text: str) -> List[NEREntity]:
        """
        Извлечение только PII сущностей.
        
        Args:
            text: Текст
            
        Returns:
            Список PII сущностей
        """
        all_entities = self.predict(text)
        
        pii_types = {
            EntityType.PER,
            EntityType.IIN,
            EntityType.BIN,
            EntityType.PHONE,
            EntityType.EMAIL,
        }
        
        return [e for e in all_entities if e.entity_type in pii_types]
    
    def mask_pii(self, text: str, replacement: str = "[REDACTED]") -> str:
        """
        Маскирование PII в тексте.
        
        Args:
            text: Текст
            replacement: Замена для PII
            
        Returns:
            Текст с замаскированными PII
        """
        pii_entities = self.extract_pii(text)
        
        # Сортировка по позиции (от конца к началу)
        pii_entities.sort(key=lambda e: e.start, reverse=True)
        
        masked_text = text
        
        for entity in pii_entities:
            masked_text = (
                masked_text[:entity.start] +
                replacement +
                masked_text[entity.end:]
            )
        
        return masked_text


@dataclass
class NERConfig:
    """Конфигурация для NER."""
    model_name: str = "IS2AI/kazroberta-ner"
    device: str = "cpu"
    confidence_threshold: float = 0.7
    extract_pii_only: bool = True
    
    def to_dict(self) -> Dict:
        """Сериализация в словарь."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "confidence_threshold": self.confidence_threshold,
            "extract_pii_only": self.extract_pii_only,
        }


def create_ner_model(config: Optional[NERConfig] = None) -> KazRoBERTaNER:
    """
    Создание NER модели.
    
    Args:
        config: Конфигурация
        
    Returns:
        KazRoBERTaNER
    """
    if config is None:
        config = NERConfig()
    
    return KazRoBERTaNER(
        model_name=config.model_name,
        device=config.device,
    )
