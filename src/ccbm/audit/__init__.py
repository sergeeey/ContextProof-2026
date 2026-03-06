"""
Audit Engine — неизменяемое логирование через деревья Меркла.

Режимы верификации:
- Fast-path: только hash verification (O(1))
- Full-path: полная проверка всех записей (O(n))

Обеспечивает:
- Криптографическую целостность всех трансформаций контекста
- Построение деревьев Меркла для аудита
- Генерацию доказательств включения (inclusion proofs)
- Верификацию квитанций (verification receipts)

Использует SHA-256 для хеширования.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class MerkleProof:
    """
    Доказательство включения для дерева Меркла.
    
    Содержит путь от листа до корня с_sibling хешами.
    """
    leaf_hash: str                    # Хеш верифицируемого элемента
    proof_hashes: List[str]           # Путь хешей до корня
    root_hash: str                    # Корень дерева
    index: int                        # Индекс листа
    total_leaves: int                 # Общее количество листьев
    
    def to_dict(self) -> Dict:
        """Сериализация в словарь."""
        return {
            "leaf_hash": self.leaf_hash,
            "proof_hashes": self.proof_hashes,
            "root_hash": self.root_hash,
            "index": self.index,
            "total_leaves": self.total_leaves,
        }


@dataclass
class VerificationReceipt:
    """
    Квитанция верификации для аудита.
    
    Содержит всю информацию для независимой проверки целостности.
    """
    receipt_id: str                   # Уникальный ID квитанции
    timestamp: str                    # Временная метка ISO
    original_hash: str                # Хеш оригинальных данных
    compressed_hash: str              # Хеш сжатых данных
    merkle_root: str                  # Корень дерева Меркла
    merkle_proof: Optional[MerkleProof]  # Доказательство включения
    metadata: Dict[str, Any]          # Дополнительные метаданные
    signature: Optional[str] = None   # Опциональная подпись
    
    def to_dict(self) -> Dict:
        """Сериализация в словарь."""
        return {
            "receipt_id": self.receipt_id,
            "timestamp": self.timestamp,
            "original_hash": self.original_hash,
            "compressed_hash": self.compressed_hash,
            "merkle_root": self.merkle_root,
            "merkle_proof": self.merkle_proof.to_dict() if self.merkle_proof else None,
            "metadata": self.metadata,
            "signature": self.signature,
        }


class MerkleTree:
    """
    Реализация дерева Меркла.
    
    Поддерживает:
    - Построение дерева из списка хешей
    - Генерацию доказательств включения
    - Верификацию доказательств
    """
    
    def __init__(self, leaves: List[str]):
        """
        Инициализация дерева Меркла.
        
        Args:
            leaves: Список хешей листьев (предварительно хешированные данные)
        """
        if not leaves:
            self._root = self._hash_empty()
            self._tree = []
            self._leaves = []
        else:
            self._leaves = leaves
            self._tree = self._build_tree(leaves)
            self._root = self._tree[-1][0] if self._tree else self._hash_empty()
    
    @staticmethod
    def _hash_empty() -> str:
        """Хеш пустого дерева."""
        return hashlib.sha256(b"EMPTY").hexdigest()
    
    @staticmethod
    def _hash_pair(left: str, right: str) -> str:
        """Хеширование пары узлов."""
        combined = left + right
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()
    
    def _build_tree(self, leaves: List[str]) -> List[List[str]]:
        """
        Построение дерева Меркла.
        
        Returns:
            Список уровней дерева (снизу вверх)
        """
        tree = [leaves[:]]  # Уровень 0 — листья
        
        current_level = leaves[:]
        
        # Если нечётное количество, дублируем последний
        if len(current_level) % 2 == 1:
            current_level.append(current_level[-1])
        
        while len(current_level) > 1:
            next_level = []
            
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1] if i + 1 < len(current_level) else left
                parent = self._hash_pair(left, right)
                next_level.append(parent)
            
            # Если нечётное, дублируем
            if len(next_level) % 2 == 1 and len(next_level) > 1:
                next_level.append(next_level[-1])
            
            tree.append(next_level)
            current_level = next_level
        
        return tree
    
    @property
    def root(self) -> str:
        """Корень дерева Меркла."""
        return self._root
    
    @property
    def leaves(self) -> List[str]:
        """Список листьев."""
        return self._leaves
    
    def get_proof(self, index: int) -> MerkleProof:
        """
        Получение доказательства включения для листа.
        
        Args:
            index: Индекс листа
            
        Returns:
            MerkleProof с путём до корня
        """
        if index < 0 or index >= len(self._leaves):
            raise ValueError(f"Индекс {index} вне диапазона [0, {len(self._leaves)})")
        
        proof_hashes = []
        current_index = index
        
        for level in range(len(self._tree) - 1):
            current_level = self._tree[level]
            
            # Определяем sibling
            if current_index % 2 == 0:
                sibling_index = current_index + 1
                if sibling_index < len(current_level):
                    proof_hashes.append(current_level[sibling_index])
                else:
                    proof_hashes.append(current_level[current_index])
            else:
                sibling_index = current_index - 1
                proof_hashes.append(current_level[sibling_index])
            
            current_index //= 2
        
        return MerkleProof(
            leaf_hash=self._leaves[index],
            proof_hashes=proof_hashes,
            root_hash=self._root,
            index=index,
            total_leaves=len(self._leaves),
        )
    
    @staticmethod
    def verify_proof(proof: MerkleProof) -> bool:
        """
        Верификация доказательства включения.
        
        Args:
            proof: Доказательство для проверки
            
        Returns:
            True если доказательство валидно
        """
        current_hash = proof.leaf_hash
        current_index = proof.index  # Копируем индекс для локального использования
        
        for sibling_hash in proof.proof_hashes:
            # Определяем порядок конкатенации по индексу
            if current_index % 2 == 0:
                current_hash = hashlib.sha256((current_hash + sibling_hash).encode('utf-8')).hexdigest()
            else:
                current_hash = hashlib.sha256((sibling_hash + current_hash).encode('utf-8')).hexdigest()
            
            current_index //= 2
        
        return current_hash == proof.root_hash


class AuditEngine:
    """
    Движок аудита для CCBM.
    
    Обеспечивает неизменяемое логирование всех трансформаций контекста:
    1. Хеширование оригинальных спанов
    2. Хеширование сжатых спанов
    3. Построение дерева Меркла
    4. Генерация квитанций верификации
    """
    
    def __init__(self):
        """Инициализация Audit Engine."""
        self._leaves: List[str] = []
        self._receipts: List[VerificationReceipt] = []
        self._merkle_tree: Optional[MerkleTree] = None
        self._root_hash: Optional[str] = None
    
    def add_transformation(
        self,
        original_data: str,
        compressed_data: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> VerificationReceipt:
        """
        Добавление записи о трансформации.
        
        Args:
            original_data: Оригинальные данные (до сжатия)
            compressed_data: Сжатые данные (после оптимизации)
            metadata: Дополнительные метаданные
            
        Returns:
            VerificationReceipt для этой трансформации
        """
        # Хешируем данные
        original_hash = self._hash_data(original_data)
        compressed_hash = self._hash_data(compressed_data)
        
        # Создаём лист дерева: хеш от комбинации
        leaf_data = json.dumps({
            "original": original_hash,
            "compressed": compressed_hash,
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata or {},
        }, sort_keys=True)
        leaf_hash = hashlib.sha256(leaf_data.encode('utf-8')).hexdigest()
        
        self._leaves.append(leaf_hash)
        
        # Создаём квитанцию
        receipt_id = self._generate_receipt_id()
        receipt = VerificationReceipt(
            receipt_id=receipt_id,
            timestamp=datetime.utcnow().isoformat(),
            original_hash=original_hash,
            compressed_hash=compressed_hash,
            merkle_root="",  # Будет установлен после финализации
            merkle_proof=None,  # Будет установлено после финализации
            metadata=metadata or {},
        )
        
        self._receipts.append(receipt)
        
        return receipt
    
    def finalize(self) -> str:
        """
        Финализация дерева Меркла.
        
        Returns:
            Корень дерева Меркла
        """
        if not self._leaves:
            self._merkle_tree = MerkleTree([])
        else:
            self._merkle_tree = MerkleTree(self._leaves)
        
        self._root_hash = self._merkle_tree.root
        
        # Обновляем все квитанции с proof
        for i, receipt in enumerate(self._receipts):
            proof = self._merkle_tree.get_proof(i)
            receipt.merkle_proof = proof
            receipt.merkle_root = self._root_hash
        
        return self._root_hash
    
    def get_receipt(self, receipt_id: str) -> Optional[VerificationReceipt]:
        """
        Получение квитанции по ID.
        
        Args:
            receipt_id: ID квитанции
            
        Returns:
            VerificationReceipt или None
        """
        for receipt in self._receipts:
            if receipt.receipt_id == receipt_id:
                return receipt
        return None
    
    def verify_receipt(self, receipt: VerificationReceipt) -> bool:
        """
        Верификация квитанции.
        
        Args:
            receipt: Квитанция для проверки
            
        Returns:
            True если квитанция валидна
        """
        if not receipt.merkle_proof:
            return False
        
        return MerkleTree.verify_proof(receipt.merkle_proof)
    
    def verify_consistency(self, old_root: str, new_root: str) -> bool:
        """
        Проверка согласованности корней (для инкрементального добавления).
        
        Args:
            old_root: Предыдущий корень
            new_root: Новый корень
            
        Returns:
            True если корни согласованы
        """
        # TODO: Реализовать proof of consistency
        # Для базовой версии просто проверяем что корни не пустые
        return bool(old_root) and bool(new_root)
    
    def get_audit_log(self) -> List[Dict]:
        """
        Получение полного аудиторского лога.
        
        Returns:
            Список всех квитанций в виде словарей
        """
        return [receipt.to_dict() for receipt in self._receipts]
    
    def export_for_blockchain(self) -> Dict:
        """
        Экспорт данных для анкоринга в блокчейн.
        
        Returns:
            Словарь с root hash и метаданными для записи в блокчейн
        """
        if not self._root_hash:
            self.finalize()
        
        return {
            "merkle_root": self._root_hash,
            "timestamp": datetime.utcnow().isoformat(),
            "total_leaves": len(self._leaves),
            "receipts_count": len(self._receipts),
            "leaf_hashes": self._leaves,
        }
    
    @staticmethod
    def _hash_data(data: str) -> str:
        """Хеширование данных через SHA-256."""
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    @staticmethod
    def _generate_receipt_id() -> str:
        """Генерация уникального ID квитанции."""
        timestamp = str(time.time())
        random_suffix = str(time.time_ns())
        return hashlib.sha256((timestamp + random_suffix).encode('utf-8')).hexdigest()[:16]


@dataclass
class AuditReport:
    """
    Отчёт аудита для CCBM.
    """
    timestamp: str
    total_transformations: int
    merkle_root: str
    receipts: List[VerificationReceipt]
    all_verified: bool
    
    def to_dict(self) -> Dict:
        """Сериализация в словарь."""
        return {
            "timestamp": self.timestamp,
            "total_transformations": self.total_transformations,
            "merkle_root": self.merkle_root,
            "all_verified": self.all_verified,
            "receipts": [r.to_dict() for r in self.receipts],
        }


def create_audit_report(engine: AuditEngine) -> AuditReport:
    """
    Создание полного отчёта аудита.
    
    Args:
        engine: AuditEngine с данными
        
    Returns:
        AuditReport со всеми проверками
    """
    receipts = engine._receipts
    all_verified = all(engine.verify_receipt(r) for r in receipts) if receipts else True
    
    return AuditReport(
        timestamp=datetime.utcnow().isoformat(),
        total_transformations=len(receipts),
        merkle_root=engine._root_hash or "",
        receipts=receipts,
        all_verified=all_verified,
    )
