import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import data_service as ds
import logic


@pytest.fixture(autouse=True)
def clean_data(tmp_path, monkeypatch):
    tmp_file = str(tmp_path / "finance_log.csv")
    monkeypatch.setattr(ds, "DATA_FILE", tmp_file)
    os.makedirs(os.path.dirname(tmp_file), exist_ok=True)
    yield


# ── BUG-01: Поиск не находил записи с заглавными буквами ─────────────────────

class TestBug01SearchCaseInsensitive:
    def test_search_finds_uppercase_description(self):
        ds.add_entry("expense", "food", "ПРОДУКТЫ В МАГАЗИНЕ", 1500.0, "2024-03-01")
        results = logic.search_by_description("продукты")
        assert len(results) == 1

    def test_search_finds_mixed_case(self):
        ds.add_entry("income", "salary", "Зарплата За Март", 70000.0, "2024-03-05")
        results = logic.search_by_description("ЗАРПЛАТА")
        assert len(results) == 1

    def test_search_category_case_insensitive(self):
        ds.add_entry("expense", "transport", "Такси", 800.0, "2024-03-01")
        results = logic.search_by_description("TRANSPORT")
        assert len(results) == 1


# ── BUG-02: Ввод суммы с запятой вызывал ошибку ──────────────────────────────

class TestBug02CommaDecimalInput:
    def test_normalize_comma(self):
        from menu import normalize_decimal
        assert normalize_decimal("1500,50") == 1500.50

    def test_normalize_dot_unchanged(self):
        from menu import normalize_decimal
        assert normalize_decimal("1500.50") == 1500.50

    def test_normalize_integer_string(self):
        from menu import normalize_decimal
        assert normalize_decimal("5000") == 5000.0

    def test_normalize_small_amount_comma(self):
        from menu import normalize_decimal
        assert normalize_decimal("99,9") == pytest.approx(99.9)


# ── IMP-01: Топ-3 категорий расходов за месяц ────────────────────────────────

class TestImp01TopExpenseCategories:
    def test_top_returns_correct_order(self):
        ds.add_entry("expense", "housing", "Аренда", 25000.0, "2024-03-01")
        ds.add_entry("expense", "food", "Продукты", 12000.0, "2024-03-05")
        ds.add_entry("expense", "entertainment", "Кино и рестораны", 8000.0, "2024-03-10")
        top = logic.top_expense_categories("2024-03-01", "2024-03-31", n=3)
        assert top[0]["category"] == "housing"
        assert top[1]["category"] == "food"
        assert top[2]["category"] == "entertainment"

    def test_top_n_limits_results(self):
        ds.add_entry("expense", "housing", "Аренда", 25000.0, "2024-03-01")
        ds.add_entry("expense", "food", "Продукты", 12000.0, "2024-03-05")
        ds.add_entry("expense", "entertainment", "Кино", 8000.0, "2024-03-10")
        top = logic.top_expense_categories("2024-03-01", "2024-03-31", n=2)
        assert len(top) == 2

    def test_top_empty_period_returns_empty_list(self):
        top = logic.top_expense_categories("2024-03-01", "2024-03-31")
        assert top == []


# ── CHG-01: Вывод нормы сбережений (savings_rate) ────────────────────────────

class TestChg01SavingsRate:
    def test_savings_rate_when_positive_balance(self):
        ds.add_entry("income", "salary", "Зарплата", 100000.0, "2024-03-05")
        ds.add_entry("expense", "food", "Расходы", 25000.0, "2024-03-10")
        s = logic.monthly_summary(2024, 3)
        assert s["savings_rate"] == pytest.approx(75.0)

    def test_savings_rate_zero_when_all_spent(self):
        ds.add_entry("income", "salary", "Зарплата", 50000.0, "2024-03-05")
        ds.add_entry("expense", "food", "Расходы", 50000.0, "2024-03-10")
        s = logic.monthly_summary(2024, 3)
        assert s["savings_rate"] == pytest.approx(0.0)

    def test_savings_rate_negative_when_over_income(self):
        ds.add_entry("income", "salary", "Зарплата", 30000.0, "2024-03-05")
        ds.add_entry("expense", "housing", "Аренда", 40000.0, "2024-03-01")
        s = logic.monthly_summary(2024, 3)
        assert s["savings_rate"] == pytest.approx(-33.33, abs=0.1)

    def test_savings_rate_none_when_no_income(self):
        ds.add_entry("expense", "food", "Расходы", 5000.0, "2024-03-10")
        s = logic.monthly_summary(2024, 3)
        assert s["savings_rate"] is None

    def test_savings_rate_in_period_stats(self):
        ds.add_entry("income", "salary", "Зарплата", 80000.0, "2024-03-05")
        ds.add_entry("expense", "food", "Еда", 16000.0, "2024-03-10")
        stats = logic.period_stats("2024-03-01", "2024-03-31")
        assert stats["savings_rate"] == pytest.approx(80.0)
