import pytest
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import data_service as ds


@pytest.fixture(autouse=True)
def clean_data(tmp_path, monkeypatch):
    tmp_file = str(tmp_path / "finance_log.csv")
    monkeypatch.setattr(ds, "DATA_FILE", tmp_file)
    os.makedirs(os.path.dirname(tmp_file), exist_ok=True)
    yield


class TestAddEntry:
    def test_add_expense_basic(self):
        row = ds.add_entry("expense", "food", "Обед в кафе", 450.0, "2024-03-01")
        assert row["type"] == "expense"
        assert row["category"] == "food"
        assert row["description"] == "Обед в кафе"
        assert float(row["amount"]) == 450.0
        assert row["date"] == "2024-03-01"
        assert int(row["id"]) == 1

    def test_add_income_basic(self):
        row = ds.add_entry("income", "salary", "Зарплата за март", 75000.0, "2024-03-05")
        assert row["type"] == "income"
        assert float(row["amount"]) == 75000.0

    def test_add_strips_whitespace(self):
        row = ds.add_entry("expense", "food", "  Продукты  ", 300.0, "2024-03-01")
        assert row["description"] == "Продукты"

    def test_add_category_strips_whitespace(self):
        row = ds.add_entry("expense", "  food  ", "Кофе", 150.0, "2024-03-01")
        assert row["category"] == "food"

    def test_add_multiple_ids_increment(self):
        ds.add_entry("expense", "food", "Завтрак", 200.0, "2024-03-01")
        ds.add_entry("income", "salary", "Аванс", 20000.0, "2024-03-01")
        rows = ds.load_all()
        assert len(rows) == 2
        assert int(rows[0]["id"]) == 1
        assert int(rows[1]["id"]) == 2

    def test_add_invalid_type_raises(self):
        with pytest.raises(ValueError, match="income.*expense"):
            ds.add_entry("gift", "other", "Подарок", 1000.0, "2024-03-01")

    def test_add_empty_category_raises(self):
        with pytest.raises(ValueError, match="пустой"):
            ds.add_entry("expense", "", "Кофе", 100.0, "2024-03-01")

    def test_add_whitespace_category_raises(self):
        with pytest.raises(ValueError):
            ds.add_entry("expense", "   ", "Кофе", 100.0, "2024-03-01")

    def test_add_empty_description_raises(self):
        with pytest.raises(ValueError, match="пустым"):
            ds.add_entry("expense", "food", "", 100.0, "2024-03-01")

    def test_add_zero_amount_raises(self):
        with pytest.raises(ValueError, match="положительным"):
            ds.add_entry("expense", "food", "Кофе", 0, "2024-03-01")

    def test_add_negative_amount_raises(self):
        with pytest.raises(ValueError):
            ds.add_entry("income", "salary", "Зарплата", -5000.0, "2024-03-01")

    def test_amount_rounded_to_two_decimals(self):
        row = ds.add_entry("expense", "food", "Кофе", 99.999, "2024-03-01")
        assert float(row["amount"]) == pytest.approx(100.0)

    def test_default_date_is_today(self):
        from datetime import date
        row = ds.add_entry("expense", "food", "Снэк", 50.0)
        assert row["date"] == str(date.today())


class TestGetByDate:
    def test_filter_by_date(self):
        ds.add_entry("expense", "food", "Завтрак", 200.0, "2024-03-01")
        ds.add_entry("income", "salary", "Зарплата", 50000.0, "2024-03-05")
        ds.add_entry("expense", "transport", "Метро", 50.0, "2024-03-01")
        result = ds.get_by_date("2024-03-01")
        assert len(result) == 2
        assert all(r["date"] == "2024-03-01" for r in result)

    def test_empty_date_returns_empty_list(self):
        ds.add_entry("expense", "food", "Обед", 300.0, "2024-03-01")
        assert ds.get_by_date("2024-03-15") == []


class TestGetByPeriod:
    def test_period_includes_boundary_dates(self):
        ds.add_entry("expense", "food", "A", 100.0, "2024-03-01")
        ds.add_entry("expense", "food", "B", 200.0, "2024-03-15")
        ds.add_entry("expense", "food", "C", 300.0, "2024-03-31")
        result = ds.get_by_period("2024-03-01", "2024-03-31")
        assert len(result) == 3

    def test_period_excludes_outside_dates(self):
        ds.add_entry("expense", "food", "Before", 100.0, "2024-02-28")
        ds.add_entry("expense", "food", "Inside", 200.0, "2024-03-10")
        ds.add_entry("expense", "food", "After", 300.0, "2024-04-01")
        result = ds.get_by_period("2024-03-01", "2024-03-31")
        assert len(result) == 1
        assert result[0]["description"] == "Inside"


class TestDeleteEntry:
    def test_delete_existing(self):
        row = ds.add_entry("expense", "food", "Обед", 300.0, "2024-03-01")
        eid = int(row["id"])
        assert ds.delete_entry(eid) is True
        assert ds.get_all_entries() == []

    def test_delete_nonexistent_returns_false(self):
        assert ds.delete_entry(999) is False

    def test_delete_correct_entry_among_multiple(self):
        r1 = ds.add_entry("expense", "food", "Завтрак", 200.0, "2024-03-01")
        r2 = ds.add_entry("income", "salary", "Зарплата", 50000.0, "2024-03-01")
        ds.delete_entry(int(r1["id"]))
        rows = ds.get_all_entries()
        assert len(rows) == 1
        assert rows[0]["description"] == "Зарплата"


class TestUpdateEntry:
    def test_update_description(self):
        row = ds.add_entry("expense", "food", "Обед", 300.0, "2024-03-01")
        updated = ds.update_entry(int(row["id"]), description="Ужин в ресторане")
        assert updated["description"] == "Ужин в ресторане"

    def test_update_amount(self):
        row = ds.add_entry("expense", "food", "Обед", 300.0, "2024-03-01")
        updated = ds.update_entry(int(row["id"]), amount=450.0)
        assert float(updated["amount"]) == pytest.approx(450.0)

    def test_update_type(self):
        row = ds.add_entry("expense", "other", "Перевод", 1000.0, "2024-03-01")
        updated = ds.update_entry(int(row["id"]), entry_type="income")
        assert updated["type"] == "income"

    def test_update_category(self):
        row = ds.add_entry("expense", "food", "Такси", 500.0, "2024-03-01")
        updated = ds.update_entry(int(row["id"]), category="transport")
        assert updated["category"] == "transport"

    def test_update_nonexistent_returns_none(self):
        result = ds.update_entry(999, description="Что-то")
        assert result is None

    def test_update_invalid_type_raises(self):
        row = ds.add_entry("expense", "food", "Кофе", 100.0, "2024-03-01")
        with pytest.raises(ValueError):
            ds.update_entry(int(row["id"]), entry_type="unknown")

    def test_update_empty_description_raises(self):
        row = ds.add_entry("expense", "food", "Кофе", 100.0, "2024-03-01")
        with pytest.raises(ValueError):
            ds.update_entry(int(row["id"]), description="")

    def test_update_zero_amount_raises(self):
        row = ds.add_entry("expense", "food", "Кофе", 100.0, "2024-03-01")
        with pytest.raises(ValueError):
            ds.update_entry(int(row["id"]), amount=0)


class TestPersistence:
    def test_data_persists_between_calls(self):
        ds.add_entry("income", "salary", "Зарплата", 70000.0, "2024-03-05")
        loaded = ds.load_all()
        assert len(loaded) == 1
        assert loaded[0]["description"] == "Зарплата"

    def test_clear_all(self):
        ds.add_entry("expense", "food", "Обед", 300.0, "2024-03-01")
        ds.clear_all()
        assert ds.load_all() == []
