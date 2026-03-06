"""
Тесты для Audit Engine — деревья Меркла и верификация.

Тестируются:
- Построение дерева Меркла
- Генерация доказательств включения
- Верификация квитанций
- Консистентность данных
"""

from ccbm.audit import (
    AuditEngine,
    MerkleTree,
    VerificationReceipt,
    create_audit_report,
)


class TestMerkleTree:
    """Тесты для MerkleTree."""

    def test_empty_tree(self):
        """Пустое дерево."""
        tree = MerkleTree([])
        assert tree.root is not None
        assert tree.leaves == []

    def test_single_leaf(self):
        """Дерево с одним листом."""
        leaves = ["hash1"]
        tree = MerkleTree(leaves)
        assert tree.root is not None
        assert len(tree.leaves) == 1

    def test_two_leaves(self):
        """Дерево с двумя листьями."""
        leaves = ["hash1", "hash2"]
        tree = MerkleTree(leaves)
        assert tree.root is not None
        assert len(tree.leaves) == 2

    def test_multiple_leaves(self):
        """Дерево с множеством листьев."""
        leaves = [f"hash{i}" for i in range(10)]
        tree = MerkleTree(leaves)
        assert tree.root is not None
        assert len(tree.leaves) == 10

    def test_odd_number_of_leaves(self):
        """Нечётное количество листьев (должно дублироваться)."""
        leaves = ["hash1", "hash2", "hash3"]
        tree = MerkleTree(leaves)
        assert tree.root is not None
        assert len(tree.leaves) == 3

    def test_get_proof(self):
        """Получение доказательства включения."""
        leaves = ["hash1", "hash2", "hash3", "hash4"]
        tree = MerkleTree(leaves)

        proof = tree.get_proof(0)
        assert proof.leaf_hash == "hash1"
        assert proof.root_hash == tree.root
        assert proof.index == 0
        assert proof.total_leaves == 4
        assert len(proof.proof_hashes) > 0

    def test_verify_proof_valid(self):
        """Верификация валидного доказательства."""
        leaves = ["hash1", "hash2", "hash3", "hash4"]
        tree = MerkleTree(leaves)

        proof = tree.get_proof(0)
        assert MerkleTree.verify_proof(proof) is True

    def test_verify_proof_all_indices(self):
        """Верификация для всех индексов."""
        leaves = [f"hash{i}" for i in range(8)]
        tree = MerkleTree(leaves)

        for i in range(len(leaves)):
            proof = tree.get_proof(i)
            assert MerkleTree.verify_proof(proof) is True

    def test_root_changes_with_leaves(self):
        """Корень меняется при изменении листьев."""
        tree1 = MerkleTree(["a", "b", "c"])
        tree2 = MerkleTree(["a", "b", "d"])  # Изменён последний

        assert tree1.root != tree2.root

    def test_deterministic_root(self):
        """Одинаковые листья дают одинаковый корень."""
        leaves = ["hash1", "hash2", "hash3"]
        tree1 = MerkleTree(leaves)
        tree2 = MerkleTree(leaves)

        assert tree1.root == tree2.root


class TestAuditEngine:
    """Тесты для AuditEngine."""

    def test_add_transformation(self):
        """Добавление трансформации."""
        engine = AuditEngine()
        receipt = engine.add_transformation(
            original_data="original text",
            compressed_data="compressed",
            metadata={"type": "test"},
        )

        assert receipt.receipt_id is not None
        assert receipt.original_hash is not None
        assert receipt.compressed_hash is not None
        assert receipt.timestamp is not None

    def test_finalize_empty(self):
        """Финализация пустого двигателя."""
        engine = AuditEngine()
        root = engine.finalize()

        assert root is not None
        assert len(engine._leaves) == 0

    def test_finalize_with_data(self):
        """Финализация с данными."""
        engine = AuditEngine()
        engine.add_transformation("original", "compressed")
        root = engine.finalize()

        assert root is not None
        assert len(engine._leaves) == 1

    def test_finalize_updates_receipts(self):
        """Финализация обновляет квитанции."""
        engine = AuditEngine()
        receipt = engine.add_transformation("original", "compressed")

        assert receipt.merkle_root == ""
        assert receipt.merkle_proof is None

        engine.finalize()

        assert receipt.merkle_root is not None
        assert receipt.merkle_proof is not None

    def test_get_receipt(self):
        """Получение квитанции по ID."""
        engine = AuditEngine()
        receipt1 = engine.add_transformation("orig1", "comp1")
        receipt2 = engine.add_transformation("orig2", "comp2")
        engine.finalize()

        retrieved = engine.get_receipt(receipt1.receipt_id)
        assert retrieved is not None
        assert retrieved.receipt_id == receipt1.receipt_id

    def test_get_receipt_not_found(self):
        """Получение несуществующей квитанции."""
        engine = AuditEngine()

        retrieved = engine.get_receipt("nonexistent")
        assert retrieved is None

    def test_verify_receipt_valid(self):
        """Верификация валидной квитанции."""
        engine = AuditEngine()
        receipt = engine.add_transformation("original", "compressed")
        engine.finalize()

        assert engine.verify_receipt(receipt) is True

    def test_verify_receipt_invalid(self):
        """Верификация квитанции без финализации."""
        engine = AuditEngine()
        receipt = engine.add_transformation("original", "compressed")

        # До финализации proof = None
        assert engine.verify_receipt(receipt) is False

    def test_multiple_transformations(self):
        """Множество трансформаций."""
        engine = AuditEngine()

        for i in range(10):
            engine.add_transformation(f"orig{i}", f"comp{i}")

        root = engine.finalize()

        assert root is not None
        assert len(engine._receipts) == 10
        assert len(engine._leaves) == 10

    def test_audit_log(self):
        """Получение аудиторского лога."""
        engine = AuditEngine()
        engine.add_transformation("orig1", "comp1")
        engine.add_transformation("orig2", "comp2")
        engine.finalize()

        log = engine.get_audit_log()

        assert len(log) == 2
        assert all("receipt_id" in entry for entry in log)
        assert all("merkle_root" in entry for entry in log)

    def test_export_for_blockchain(self):
        """Экспорт для блокчейна."""
        engine = AuditEngine()
        engine.add_transformation("orig", "comp")
        export = engine.export_for_blockchain()

        assert "merkle_root" in export
        assert "timestamp" in export
        assert "total_leaves" in export
        assert "receipts_count" in export
        assert "leaf_hashes" in export


class TestAuditReport:
    """Тесты для AuditReport."""

    def test_create_report_empty(self):
        """Создание отчёта для пустого двигателя."""
        engine = AuditEngine()
        engine.finalize()

        report = create_audit_report(engine)

        assert report.total_transformations == 0
        assert report.all_verified is True

    def test_create_report_with_data(self):
        """Создание отчёта с данными."""
        engine = AuditEngine()
        engine.add_transformation("orig", "comp")
        engine.finalize()

        report = create_audit_report(engine)

        assert report.total_transformations == 1
        assert report.all_verified is True
        assert report.merkle_root is not None

    def test_report_serialization(self):
        """Сериализация отчёта."""
        engine = AuditEngine()
        engine.add_transformation("orig", "comp")
        engine.finalize()

        report = create_audit_report(engine)
        report_dict = report.to_dict()

        assert "timestamp" in report_dict
        assert "merkle_root" in report_dict
        assert "receipts" in report_dict


class TestVerificationReceipt:
    """Тесты для VerificationReceipt."""

    def test_receipt_to_dict(self):
        """Сериализация квитанции."""
        receipt = VerificationReceipt(
            receipt_id="test123",
            timestamp="2026-03-06T12:00:00",
            original_hash="orig_hash",
            compressed_hash="comp_hash",
            merkle_root="root_hash",
            merkle_proof=None,
            metadata={"key": "value"},
        )

        receipt_dict = receipt.to_dict()

        assert receipt_dict["receipt_id"] == "test123"
        assert receipt_dict["original_hash"] == "orig_hash"
        assert receipt_dict["metadata"]["key"] == "value"


class TestIntegration:
    """Интеграционные тесты."""

    def test_full_workflow(self):
        """Полный рабочий процесс."""
        # Создание двигателя
        engine = AuditEngine()

        # Добавление трансформаций
        transformations = [
            ("original text 1", "compressed 1", {"span_id": 1}),
            ("original text 2", "compressed 2", {"span_id": 2}),
            ("original text 3", "compressed 3", {"span_id": 3}),
        ]

        receipts = []
        for orig, comp, meta in transformations:
            receipt = engine.add_transformation(orig, comp, meta)
            receipts.append(receipt)

        # Финализация
        root = engine.finalize()
        assert root is not None

        # Верификация всех квитанций
        for receipt in receipts:
            assert engine.verify_receipt(receipt) is True

        # Создание отчёта
        report = create_audit_report(engine)
        assert report.all_verified is True
        assert report.total_transformations == 3

    def test_data_integrity(self):
        """Проверка целостности данных."""
        engine = AuditEngine()

        # Добавляем трансформацию
        original = "Критические данные: ИИН 950101300038, сумма 100000 KZT"
        compressed = "ИИН [REDACTED], сумма [REDACTED]"

        receipt = engine.add_transformation(
            original,
            compressed,
            {"type": "financial", "domain": "KZ"},
        )

        engine.finalize()

        # Проверяем что хеши разные
        assert receipt.original_hash != receipt.compressed_hash

        # Проверяем верификацию
        assert engine.verify_receipt(receipt) is True

    def test_consistency_check(self):
        """Проверка согласованности корней."""
        engine = AuditEngine()
        engine.add_transformation("orig1", "comp1")
        root1 = engine.finalize()

        # В реальной системе здесь было бы инкрементальное добавление
        # Для базовой версии просто проверяем что корни не пустые
        assert engine.verify_consistency(root1, root1) is True


class TestEdgeCases:
    """Тесты граничных случаев."""

    def test_large_number_of_leaves(self):
        """Большое количество листьев."""
        engine = AuditEngine()

        for i in range(1000):
            engine.add_transformation(f"orig{i}", f"comp{i}")

        root = engine.finalize()
        assert root is not None
        assert len(engine._leaves) == 1000

    def test_unicode_data(self):
        """Данные с Unicode (казахский, русский)."""
        engine = AuditEngine()

        original = "Мәтін қазақша текст на русском"
        compressed = "Сжатый текст"

        receipt = engine.add_transformation(original, compressed)
        engine.finalize()

        assert engine.verify_receipt(receipt) is True

    def test_empty_strings(self):
        """Пустые строки."""
        engine = AuditEngine()
        receipt = engine.add_transformation("", "")
        engine.finalize()

        assert engine.verify_receipt(receipt) is True

    def test_special_characters(self):
        """Специальные символы."""
        engine = AuditEngine()
        original = "Text with\nnewlines\ttabs and \"quotes\""
        compressed = "Compressed"

        receipt = engine.add_transformation(original, compressed)
        engine.finalize()

        assert engine.verify_receipt(receipt) is True
