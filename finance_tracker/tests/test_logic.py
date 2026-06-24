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


class TestCalculateBalance:
    def test_empty_entries_returns_zeros(self):
        result = logic.calculate_balance([])
        assert result == {"income": 0, "expense": 0, "balance": 0}

    def test_only_income(self):
        ds.add_entry("income", "salary", "Зарплата", 50000.0, "2024-03-05")
        entries = ds.get_all_entries()
        bal = logic.calculate_balance(entries)
        assert bal["income"] == pytest.approx(50000.0)
        assert bal["expense"] == pytest.approx(0.0)
        assert bal["balance"] == pytest.approx(50000.0)

    def test_only_expense(self):
        ds.add_entry("expense", "food", "Продукты", 3000.0, "2024-03-01")
        entries = ds.get_all_entries()
        bal = logic.calculate_balance(entries)
        assert bal["income"] == pytest.approx(0.0)
        assert bal["expense"] == pytest.approx(3000.0)
        assert bal["balance"] == pytest.approx(-3000.0)

    def test_mixed_entries(self):
        ds.add_entry("income", "salary", "Зарплата", 60000.0, "2024-03-05")
        ds.add_entry("expense", "food", "Еда", 10000.0, "2024-03-10")
        ds.add_entry("expense", "transport", "Транспорт", 2000.0, "2024-03-15")
        entries = ds.get_all_entries()
        bal = logic.calculate_balance(entries)
        assert bal["income"] == pytest.approx(60000.0)
        assert bal["expense"] == pytest.approx(12000.0)
        assert bal["balance"] == pytest.approx(48000.0)


class TestMonthlySummary:
    def test_empty_month_returns_zeros(self):
        s = logic.monthly_summary(2024, 3)
        assert s["income"] == 0
        assert s["expense"] == 0
        assert s["balance"] == 0

    def test_correct_totals(self):
        ds.add_entry("income", "salary", "Зарплата", 80000.0, "2024-03-05")
        ds.add_entry("expense", "food", "Еда", 15000.0, "2024-03-10")
        ds.add_entry("expense", "transport", "Транспорт", 3000.0, "2024-03-20")
        s = logic.monthly_summary(2024, 3)
        assert s["income"] == pytest.approx(80000.0)
        assert s["expense"] == pytest.approx(18000.0)
        assert s["balance"] == pytest.approx(62000.0)

    def test_excludes_other_months(self):
        ds.add_entry("income", "salary", "Зарплата", 80000.0, "2024-03-05")
        ds.add_entry("expense", "food", "Еда в феврале", 5000.0, "2024-02-20")
        s = logic.monthly_summary(2024, 3)
        assert s["income"] == pytest.approx(80000.0)
        assert s["expense"] == pytest.approx(0.0)

    def test_budget_not_exceeded(self):
        ds.add_entry("expense", "food", "Продукты", 8000.0, "2024-03-10")
        s = logic.monthly_summary(2024, 3, budget_limit=20000.0)
        assert s["over_budget"] is False
        assert s["over_budget_pct"] == pytest.approx(0.0)

    def test_budget_exceeded(self):
        ds.add_entry("expense", "food", "Продукты", 25000.0, "2024-03-10")
        s = logic.monthly_summary(2024, 3, budget_limit=20000.0)
        assert s["over_budget"] is True
        assert s["over_budget_pct"] == pytest.approx(25.0)

    def test_budget_none_no_over_budget_field(self):
        s = logic.monthly_summary(2024, 3, budget_limit=None)
        assert s["over_budget"] is None
        assert s["over_budget_pct"] is None

    def test_savings_rate_calculated(self):
        ds.add_entry("income", "salary", "Зарплата", 100000.0, "2024-03-05")
        ds.add_entry("expense", "food", "Продукты", 30000.0, "2024-03-10")
        s = logic.monthly_summary(2024, 3)
        assert s["savings_rate"] == pytest.approx(70.0)

    def test_savings_rate_none_when_no_income(self):
        ds.add_entry("expense", "food", "Продукты", 5000.0, "2024-03-10")
        s = logic.monthly_summary(2024, 3)
        assert s["savings_rate"] is None

    def test_invalid_month_raises(self):
        with pytest.raises(ValueError, match="1 до 12"):
            logic.monthly_summary(2024, 13)

    def test_zero_month_raises(self):
        with pytest.raises(ValueError):
            logic.monthly_summary(2024, 0)

    def test_negative_year_raises(self):
        with pytest.raises(ValueError, match="положительным"):
            logic.monthly_summary(-1, 3)

    def test_negative_budget_limit_raises(self):
        with pytest.raises(ValueError, match="положительным"):
            logic.monthly_summary(2024, 3, budget_limit=-1000)


class TestSearchByDescription:
    def test_search_found(self):
        ds.add_entry("expense", "food", "Обед в столовой", 200.0, "2024-03-01")
        ds.add_entry("expense", "transport", "Метро", 50.0, "2024-03-01")
        results = logic.search_by_description("столовой")
        assert len(results) == 1
        assert results[0]["description"] == "Обед в столовой"

    def test_search_case_insensitive(self):
        ds.add_entry("income", "salary", "ЗАРПЛАТА ЗА МАРТ", 70000.0, "2024-03-05")
        results = logic.search_by_description("зарплата")
        assert len(results) == 1

    def test_search_partial_match(self):
        ds.add_entry("expense", "food", "Завтрак", 150.0, "2024-03-01")
        ds.add_entry("expense", "food", "Завтрак деловой", 500.0, "2024-03-02")
        results = logic.search_by_description("завт")
        assert len(results) == 2

    def test_search_by_category(self):
        ds.add_entry("expense", "transport", "Такси до аэропорта", 1500.0, "2024-03-01")
        ds.add_entry("expense", "food", "Ужин", 600.0, "2024-03-01")
        results = logic.search_by_description("transport")
        assert len(results) == 1

    def test_search_no_results(self):
        ds.add_entry("expense", "food", "Обед", 300.0, "2024-03-01")
        results = logic.search_by_description("кино")
        assert results == []

    def test_search_empty_keyword_raises(self):
        with pytest.raises(ValueError, match="пустым"):
            logic.search_by_description("")

    def test_search_whitespace_keyword_raises(self):
        with pytest.raises(ValueError):
            logic.search_by_description("   ")


class TestTopExpenseCategories:
    def test_top_sorted_by_total(self):
        ds.add_entry("expense", "food", "Еда", 10000.0, "2024-03-01")
        ds.add_entry("expense", "housing", "Аренда", 30000.0, "2024-03-01")
        ds.add_entry("expense", "transport", "Транспорт", 5000.0, "2024-03-01")
        top = logic.top_expense_categories("2024-03-01", "2024-03-31", n=3)
        assert top[0]["category"] == "housing"
        assert top[1]["category"] == "food"
        assert top[2]["category"] == "transport"

    def test_top_n_limits_results(self):
        ds.add_entry("expense", "food", "Еда", 10000.0, "2024-03-01")
        ds.add_entry("expense", "housing", "Аренда", 30000.0, "2024-03-01")
        ds.add_entry("expense", "transport", "Транспорт", 5000.0, "2024-03-01")
        top = logic.top_expense_categories("2024-03-01", "2024-03-31", n=2)
        assert len(top) == 2

    def test_top_ignores_income(self):
        ds.add_entry("income", "salary", "Зарплата", 100000.0, "2024-03-05")
        ds.add_entry("expense", "food", "Еда", 5000.0, "2024-03-10")
        top = logic.top_expense_categories("2024-03-01", "2024-03-31")
        assert all(t["category"] != "salary" for t in top)

    def test_top_aggregates_same_category(self):
        ds.add_entry("expense", "food", "Обед", 300.0, "2024-03-01")
        ds.add_entry("expense", "food", "Ужин", 500.0, "2024-03-02")
        top = logic.top_expense_categories("2024-03-01", "2024-03-31")
        assert top[0]["category"] == "food"
        assert top[0]["total"] == pytest.approx(800.0)

    def test_top_empty_period(self):
        top = logic.top_expense_categories("2024-03-01", "2024-03-31")
        assert top == []


class TestPeriodStats:
    def test_period_totals(self):
        ds.add_entry("income", "salary", "Зарплата", 60000.0, "2024-03-05")
        ds.add_entry("expense", "food", "Еда", 10000.0, "2024-03-10")
        ds.add_entry("expense", "transport", "Метро", 2000.0, "2024-03-15")
        stats = logic.period_stats("2024-03-01", "2024-03-31")
        assert stats["income"] == pytest.approx(60000.0)
        assert stats["expense"] == pytest.approx(12000.0)
        assert stats["balance"] == pytest.approx(48000.0)

    def test_period_empty_returns_zeros(self):
        stats = logic.period_stats("2024-03-01", "2024-03-31")
        assert stats["income"] == 0
        assert stats["days"] == 0

    def test_avg_expense_per_day(self):
        ds.add_entry("expense", "food", "День1", 1000.0, "2024-03-01")
        ds.add_entry("expense", "food", "День2", 3000.0, "2024-03-02")
        stats = logic.period_stats("2024-03-01", "2024-03-02")
        assert stats["avg_expense_per_day"] == pytest.approx(2000.0)

    def test_savings_rate_positive_balance(self):
        ds.add_entry("income", "salary", "Зарплата", 50000.0, "2024-03-05")
        ds.add_entry("expense", "food", "Еда", 10000.0, "2024-03-10")
        stats = logic.period_stats("2024-03-01", "2024-03-31")
        assert stats["savings_rate"] == pytest.approx(80.0)


class TestCategoryBreakdown:
    def test_breakdown_separates_income_and_expense(self):
        ds.add_entry("income", "salary", "Зарплата", 60000.0, "2024-03-05")
        ds.add_entry("expense", "food", "Еда", 10000.0, "2024-03-10")
        bd = logic.category_breakdown("2024-03-01", "2024-03-31")
        assert "salary" in bd["income_by_category"]
        assert "food" in bd["expense_by_category"]

    def test_breakdown_aggregates_same_category(self):
        ds.add_entry("expense", "food", "Завтрак", 200.0, "2024-03-01")
        ds.add_entry("expense", "food", "Ужин", 400.0, "2024-03-02")
        ds.add_entry("expense", "transport", "Метро", 100.0, "2024-03-03")
        bd = logic.category_breakdown("2024-03-01", "2024-03-31")
        assert bd["expense_by_category"]["food"] == pytest.approx(600.0)
        assert bd["expense_by_category"]["transport"] == pytest.approx(100.0)

    def test_breakdown_empty_period(self):
        bd = logic.category_breakdown("2024-03-01", "2024-03-31")
        assert bd["income_by_category"] == {}
        assert bd["expense_by_category"] == {}
