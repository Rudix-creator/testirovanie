# US-01: добавление доходов и расходов
import csv
import os
from datetime import date

DATA_FILE = os.path.join(os.path.dirname(__file__), "data", "finance_log.csv")
FIELDNAMES = ["id", "date", "type", "category", "description", "amount"]

VALID_TYPES = ("income", "expense")

EXPENSE_CATEGORIES = (
    "food", "transport", "housing", "entertainment",
    "health", "clothing", "education", "other"
)
INCOME_CATEGORIES = (
    "salary", "freelance", "gift", "investment", "other"
)


def _ensure_file():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()


def _next_id(rows: list) -> int:
    if not rows:
        return 1
    return max(int(r["id"]) for r in rows) + 1


def load_all() -> list:
    _ensure_file()
    with open(DATA_FILE, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


def save_all(rows: list):
    _ensure_file()
    with open(DATA_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def add_entry(entry_type: str, category: str, description: str,
              amount: float, entry_date: str = None) -> dict:
    if entry_type not in VALID_TYPES:
        raise ValueError("Тип записи должен быть 'income' или 'expense'.")
    if not category or not category.strip():
        raise ValueError("Категория не может быть пустой.")
    if not description or not description.strip():
        raise ValueError("Описание не может быть пустым.")
    if amount <= 0:
        raise ValueError("Сумма должна быть положительным числом.")

    if entry_date is None:
        entry_date = str(date.today())

    rows = load_all()
    row = {
        "id": _next_id(rows),
        "date": entry_date,
        "type": entry_type,
        "category": category.strip(),
        "description": description.strip(),
        "amount": round(amount, 2),
    }
    rows.append(row)
    save_all(rows)
    return row


def get_all_entries() -> list:
    return load_all()


def get_by_date(target_date: str) -> list:
    return [r for r in load_all() if r["date"] == target_date]


def get_by_period(start_date: str, end_date: str) -> list:
    return [r for r in load_all() if start_date <= r["date"] <= end_date]


def delete_entry(entry_id: int) -> bool:
    rows = load_all()
    new_rows = [r for r in rows if int(r["id"]) != entry_id]
    if len(new_rows) == len(rows):
        return False
    save_all(new_rows)
    return True


def update_entry(entry_id: int, entry_type: str = None, category: str = None,
                 description: str = None, amount: float = None) -> dict:
    rows = load_all()
    updated = None
    for row in rows:
        if int(row["id"]) == entry_id:
            if entry_type is not None:
                if entry_type not in VALID_TYPES:
                    raise ValueError("Тип записи должен быть 'income' или 'expense'.")
                row["type"] = entry_type
            if category is not None:
                if not category.strip():
                    raise ValueError("Категория не может быть пустой.")
                row["category"] = category.strip()
            if description is not None:
                if not description.strip():
                    raise ValueError("Описание не может быть пустым.")
                row["description"] = description.strip()
            if amount is not None:
                if amount <= 0:
                    raise ValueError("Сумма должна быть положительным числом.")
                row["amount"] = round(amount, 2)
            updated = row
            break
    if updated:
        save_all(rows)
    return updated


def clear_all():
    save_all([])
