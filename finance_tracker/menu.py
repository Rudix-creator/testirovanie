from datetime import date
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from data_service import (
    add_entry, get_all_entries, get_by_date,
    delete_entry, update_entry, clear_all,
    EXPENSE_CATEGORIES, INCOME_CATEGORIES, VALID_TYPES,
)
from logic import (
    monthly_summary, search_by_description, top_expense_categories,
    period_stats, category_breakdown,
    EXPENSE_CATEGORY_LABELS, INCOME_CATEGORY_LABELS,
)

VERSION = "1.0.2"
BANNER = f"  ЛИЧНЫЕ ФИНАНСЫ  v{VERSION}"

MAIN_MENU = """
[1] Добавить запись (доход / расход)
[2] Сводка за месяц
[3] Удалить запись
[4] Редактировать запись
[5] Поиск по описанию или категории
[6] Статистика за период
[7] Разбивка по категориям
[8] Все записи
[0] Выход
"""


def normalize_decimal(s: str) -> float:
    return float(s.replace(",", "."))


def _input(prompt: str) -> str:
    return input(prompt).strip()


def _float_input(prompt: str) -> float:
    while True:
        try:
            return normalize_decimal(_input(prompt))
        except ValueError:
            print("  Введите число (можно использовать , или .).")


def _int_input(prompt: str) -> int:
    while True:
        try:
            return int(_input(prompt))
        except ValueError:
            print("  Введите целое число.")


def _date_input(prompt: str, default: str = None) -> str:
    label = prompt + (f" [{default}]: " if default else ": ")
    val = _input(label)
    if not val and default:
        return default
    try:
        parts = val.split("-")
        assert len(parts) == 3
        date(int(parts[0]), int(parts[1]), int(parts[2]))
        return val
    except Exception:
        print("  Неверный формат. Используйте YYYY-MM-DD.")
        return _date_input(prompt, default)


def _choose_type() -> str:
    while True:
        t = _input("Тип (income — доход / expense — расход): ").lower()
        if t in VALID_TYPES:
            return t
        print("  Введите 'income' или 'expense'.")


def _choose_category(entry_type: str) -> str:
    cats = EXPENSE_CATEGORIES if entry_type == "expense" else INCOME_CATEGORIES
    labels = EXPENSE_CATEGORY_LABELS if entry_type == "expense" else INCOME_CATEGORY_LABELS
    print("  Доступные категории:")
    for c in cats:
        print(f"    {c:<15} — {labels.get(c, c)}")
    while True:
        cat = _input("Категория: ").lower()
        if cat in cats:
            return cat
        print(f"  Выберите категорию из списка выше.")


def action_add():
    print("\n-- Добавить запись --")
    entry_type = _choose_type()
    category = _choose_category(entry_type)
    description = _input("Описание: ")
    if not description:
        print("  Описание не может быть пустым.")
        return
    amount = _float_input("Сумма (руб.): ")
    today = str(date.today())
    d = _date_input("Дата", default=today)
    try:
        row = add_entry(entry_type, category, description, amount, entry_date=d)
        emoji = "💰" if entry_type == "income" else "💸"
        print(f"  {emoji} Добавлено: [{row['type']}] {row['description']} — "
              f"{row['amount']} руб. (ID {row['id']})")
    except ValueError as e:
        print(f"  Ошибка: {e}")


def action_month():
    print("\n-- Сводка за месяц --")
    today = date.today()
    year = _int_input(f"Год [{today.year}]: ") if _input(
        f"Год [{today.year}] (Enter — текущий): ") else today.year

    # Re-read in case user typed something for year
    year_str = _input(f"Год [{today.year}]: ")
    year = int(year_str) if year_str else today.year
    month_str = _input(f"Месяц (1-12) [{today.month}]: ")
    month = int(month_str) if month_str else today.month

    limit_str = _input("Лимит расходов (Enter — пропустить): ")
    limit = float(limit_str.replace(",", ".")) if limit_str else None

    try:
        s = monthly_summary(year, month, budget_limit=limit)
    except ValueError as e:
        print(f"  Ошибка: {e}")
        return

    print(f"\n  Период: {year:04d}-{month:02d}")
    print(f"  Доходы:  {s['income']:>10.2f} руб.")
    print(f"  Расходы: {s['expense']:>10.2f} руб.")
    balance_sign = "+" if s["balance"] >= 0 else ""
    print(f"  Баланс:  {balance_sign}{s['balance']:>9.2f} руб.")

    if s["savings_rate"] is not None:
        print(f"  Норма сбережений: {s['savings_rate']:.1f}%")

    if limit is not None:
        status = "🔴 ПРЕВЫШЕН" if s["over_budget"] else "🟢 В норме"
        print(f"  Бюджет: {limit} руб.  |  {status}")
        if s["over_budget"]:
            print(f"  Превышение: {s['over_budget_pct']}%")

    if s["entries"]:
        top = top_expense_categories(
            f"{year:04d}-{month:02d}-01",
            f"{year:04d}-{month:02d}-{__import__('calendar').monthrange(year, month)[1]:02d}",
            n=3
        )
        if top:
            print("\n  Топ-3 категории расходов:")
            for i, t in enumerate(top, 1):
                label = EXPENSE_CATEGORY_LABELS.get(t["category"], t["category"])
                print(f"    {i}. {label} — {t['total']:.2f} руб.")


def action_delete():
    print("\n-- Удалить запись --")
    eid = _int_input("ID записи: ")
    confirm = _input(f"Удалить запись #{eid}? (да/нет): ").lower()
    if confirm not in ("да", "yes", "y"):
        print("  Отменено.")
        return
    if delete_entry(eid):
        print(f"  Запись #{eid} удалена.")
    else:
        print(f"  Запись #{eid} не найдена.")


def action_update():
    print("\n-- Редактировать запись --")
    eid = _int_input("ID записи: ")
    print("  Оставьте поле пустым, чтобы не менять его.")
    type_new = _input("Новый тип (income/expense, Enter — пропустить): ") or None
    cat_new = _input("Новая категория (Enter — пропустить): ") or None
    desc_new = _input("Новое описание (Enter — пропустить): ") or None
    amt_str = _input("Новая сумма (Enter — пропустить): ")
    amt_new = float(amt_str.replace(",", ".")) if amt_str else None
    try:
        updated = update_entry(eid, entry_type=type_new, category=cat_new,
                               description=desc_new, amount=amt_new)
        if updated:
            print(f"  Обновлено: [{updated['type']}] {updated['description']} — "
                  f"{updated['amount']} руб.")
        else:
            print(f"  Запись #{eid} не найдена.")
    except ValueError as e:
        print(f"  Ошибка: {e}")


def action_search():
    print("\n-- Поиск по описанию / категории --")
    kw = _input("Ключевое слово: ")
    try:
        results = search_by_description(kw)
        if not results:
            print("  Ничего не найдено.")
            return
        print(f"\n  Найдено записей: {len(results)}")
        print(f"  {'ID':<5} {'Дата':<12} {'Тип':<9} {'Категория':<16} {'Описание':<20} {'Сумма'}")
        print("  " + "-" * 75)
        for e in results:
            print(f"  {e['id']:<5} {e['date']:<12} {e['type']:<9} {e['category']:<16} "
                  f"{e['description']:<20} {float(e['amount']):.2f}")
    except ValueError as e:
        print(f"  Ошибка: {e}")


def action_period():
    print("\n-- Статистика за период --")
    start = _date_input("Начало периода (YYYY-MM-DD)")
    end = _date_input("Конец периода (YYYY-MM-DD)")
    stats = period_stats(start, end)
    if not stats["entries"]:
        print("  Нет данных за выбранный период.")
        return
    print(f"\n  Период: {start} — {end}")
    print(f"  Дней с записями:   {stats['days']}")
    print(f"  Доходы:            {stats['income']:.2f} руб.")
    print(f"  Расходы:           {stats['expense']:.2f} руб.")
    print(f"  Баланс:            {stats['balance']:.2f} руб.")
    print(f"  Ср. расход/день:   {stats['avg_expense_per_day']:.2f} руб.")
    print(f"  Норма сбережений:  {stats['savings_rate']:.1f}%")


def action_breakdown():
    print("\n-- Разбивка по категориям --")
    start = _date_input("Начало периода (YYYY-MM-DD)")
    end = _date_input("Конец периода (YYYY-MM-DD)")
    bd = category_breakdown(start, end)

    if bd["income_by_category"]:
        print("\n  Доходы по категориям:")
        for cat, total in sorted(bd["income_by_category"].items(),
                                  key=lambda x: x[1], reverse=True):
            label = INCOME_CATEGORY_LABELS.get(cat, cat)
            print(f"    {label:<18} {total:.2f} руб.")
    else:
        print("\n  Нет доходов за период.")

    if bd["expense_by_category"]:
        print("\n  Расходы по категориям:")
        for cat, total in sorted(bd["expense_by_category"].items(),
                                  key=lambda x: x[1], reverse=True):
            label = EXPENSE_CATEGORY_LABELS.get(cat, cat)
            print(f"    {label:<18} {total:.2f} руб.")
    else:
        print("\n  Нет расходов за период.")


def action_all():
    print("\n-- Все записи --")
    entries = get_all_entries()
    if not entries:
        print("  Нет записей.")
        return
    print(f"\n  {'ID':<5} {'Дата':<12} {'Тип':<9} {'Категория':<16} "
          f"{'Описание':<22} {'Сумма'}")
    print("  " + "-" * 78)
    for e in entries:
        print(f"  {e['id']:<5} {e['date']:<12} {e['type']:<9} {e['category']:<16} "
              f"{e['description']:<22} {float(e['amount']):.2f}")
    print(f"\n  Всего записей: {len(entries)}")


def main():
    print(BANNER)
    actions = {
        "1": action_add,
        "2": action_month,
        "3": action_delete,
        "4": action_update,
        "5": action_search,
        "6": action_period,
        "7": action_breakdown,
        "8": action_all,
    }
    while True:
        print(MAIN_MENU)
        choice = _input("Выберите действие: ")
        if choice == "0":
            print("  До свидания!")
            break
        action = actions.get(choice)
        if action:
            action()
        else:
            print("  Неверный пункт меню.")


if __name__ == "__main__":
    main()
