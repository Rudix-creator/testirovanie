# US-06: поиск по описанию и категории

import calendar
from data_service import get_by_period, get_all_entries

EXPENSE_CATEGORY_LABELS = {
    "food":          "Питание",
    "transport":     "Транспорт",
    "housing":       "Жильё",
    "entertainment": "Развлечения",
    "health":        "Здоровье",
    "clothing":      "Одежда",
    "education":     "Образование",
    "other":         "Прочее",
}

INCOME_CATEGORY_LABELS = {
    "salary":     "Зарплата",
    "freelance":  "Фриланс",
    "gift":       "Подарок",
    "investment": "Инвестиции",
    "other":      "Прочее",
}


def calculate_balance(entries: list) -> dict:
    """Рассчитать доходы, расходы и баланс по списку записей."""
    income = round(sum(float(e["amount"]) for e in entries if e["type"] == "income"), 2)
    expense = round(sum(float(e["amount"]) for e in entries if e["type"] == "expense"), 2)
    balance = round(income - expense, 2)
    return {"income": income, "expense": expense, "balance": balance}


def monthly_summary(year: int, month: int, budget_limit: float = None) -> dict:
    """Сводка за месяц с опциональной проверкой бюджетного лимита."""
    if year <= 0:
        raise ValueError("Год должен быть положительным числом.")
    if not (1 <= month <= 12):
        raise ValueError("Месяц должен быть в диапазоне от 1 до 12.")
    if budget_limit is not None and budget_limit <= 0:
        raise ValueError("Бюджетный лимит должен быть положительным числом.")

    last_day = calendar.monthrange(year, month)[1]
    start = f"{year:04d}-{month:02d}-01"
    end = f"{year:04d}-{month:02d}-{last_day:02d}"

    entries = get_by_period(start, end)
    bal = calculate_balance(entries)

    result = {
        "entries": entries,
        "year": year,
        "month": month,
        "income": bal["income"],
        "expense": bal["expense"],
        "balance": bal["balance"],
        "budget_limit": budget_limit,
        "over_budget": None,
        "over_budget_pct": None,
        "savings_rate": None,
    }

    if budget_limit is not None:
        result["over_budget"] = bal["expense"] > budget_limit
        pct = max(0.0, round((bal["expense"] / budget_limit * 100) - 100, 2))
        result["over_budget_pct"] = pct

    if bal["income"] > 0:
        savings_rate = round((bal["balance"] / bal["income"]) * 100, 2)
        result["savings_rate"] = savings_rate

    return result


def search_by_description(keyword: str) -> list:
    """Поиск записей по описанию или категории (регистронезависимый)."""
    if not keyword or not keyword.strip():
        raise ValueError("Ключевое слово не может быть пустым.")
    kw = keyword.strip().lower()
    return [
        e for e in get_all_entries()
        if kw in e["description"].lower() or kw in e["category"].lower()
    ]


def top_expense_categories(start_date: str, end_date: str, n: int = 3) -> list:
    """Топ-N категорий расходов за период."""
    entries = get_by_period(start_date, end_date)
    expenses = [e for e in entries if e["type"] == "expense"]

    cat_totals: dict = {}
    for e in expenses:
        cat = e["category"]
        cat_totals[cat] = round(cat_totals.get(cat, 0) + float(e["amount"]), 2)

    sorted_cats = sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)
    return [{"category": cat, "total": total} for cat, total in sorted_cats[:n]]

# US-07: статистика за период
def period_stats(start_date: str, end_date: str) -> dict:
    """Статистика доходов и расходов за произвольный период."""
    entries = get_by_period(start_date, end_date)
    if not entries:
        return {
            "entries": [],
            "income": 0,
            "expense": 0,
            "balance": 0,
            "days": 0,
            "avg_expense_per_day": 0,
            "savings_rate": 0,
        }
# US-08: топ категорий расходов
    bal = calculate_balance(entries)
    days = len({e["date"] for e in entries})
    avg = round(bal["expense"] / days, 2) if days else 0
    savings_rate = round((bal["balance"] / bal["income"]) * 100, 2) if bal["income"] > 0 else 0

    return {
        "entries": entries,
        "income": bal["income"],
        "expense": bal["expense"],
        "balance": bal["balance"],
        "days": days,
        "avg_expense_per_day": avg,
        "savings_rate": savings_rate,
    }

# US-09: разбивка по категориям
def category_breakdown(start_date: str, end_date: str) -> dict:
    """Разбивка сумм по категориям за период."""
    entries = get_by_period(start_date, end_date)

    income_by_cat: dict = {}
    expense_by_cat: dict = {}

    for e in entries:
        cat = e["category"]
        amount = float(e["amount"])
        if e["type"] == "income":
            income_by_cat[cat] = round(income_by_cat.get(cat, 0) + amount, 2)
        else:
            expense_by_cat[cat] = round(expense_by_cat.get(cat, 0) + amount, 2)

    return {
        "income_by_category": income_by_cat,
        "expense_by_category": expense_by_cat,
    }
