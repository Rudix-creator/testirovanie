# REPORT.md — Итоговый отчёт

**Проект:** Трекер личных финансов (Finance Tracker)  
**Версия:** 1.0.2  
**Язык:** Python 3.12  

---

## 1. Путь по этапам

### Этап 1 — Инициация и требования
Выбрана тема «Учёт личных финансов». Составлены 9 пользовательских историй (US-01 … US-09),
определён MVP (4 истории). Задачи оформлены в GitHub Issues, создана Kanban-доска
с колонками: Backlog → In Progress → Review → Done.

### Этап 2 — Проектирование
Разработана трёхуровневая архитектура:  
`menu.py → logic.py → data_service.py → finance_log.csv`

Структура CSV-записи содержит 6 полей: id, date, type, category, description, amount.
Определены два справочника категорий (доходы и расходы).

### Этап 3 — Разработка по TDD
Цикл Red → Green → Refactor выдержан для каждой функции.  
Порядок: сначала `data_service.py`, затем `logic.py`, в последнюю очередь `menu.py`.  
Каждая функция оформлялась через Pull Request.

**Итоговое покрытие кода:**

```
Name               Stmts   Miss  Cover
--------------------------------------
data_service.py       62      3    95%
logic.py              65      4    94%
menu.py               91     32    65%
--------------------------------------
TOTAL                218     39    82%
```

Покрытие menu.py ниже из-за интерактивных input-функций, которые не тестируются
напрямую. Логика и данные покрыты на 94–95%.

### Этап 4 — Приёмочное тестирование
Составлен чек-лист из 15 пунктов (TEST_CHECKLIST.md).
Все 15 тест-кейсов пройдены вручную. Найденных критичных дефектов нет.
Выпущена версия **1.0.0**.

### Этап 5 — Сопровождение
Получено 5 обращений (BUG-01, BUG-02, IMP-01, CHG-01, Q-01).
Для каждого бага написан регрессионный тест до исправления кода.
Выпущены патчи **1.0.1** и **1.0.2**.
Все Issue закрыты. Журнал поддержки заполнен (SUPPORT_LOG.md).

---

## 2. Скриншот прогона тестов

```
$ pytest tests/ -v

tests/test_data_service.py::TestAddEntry::test_add_expense_basic        PASSED
tests/test_data_service.py::TestAddEntry::test_add_income_basic          PASSED
tests/test_data_service.py::TestAddEntry::test_add_strips_whitespace     PASSED
tests/test_data_service.py::TestAddEntry::test_add_invalid_type_raises   PASSED
tests/test_data_service.py::TestAddEntry::test_add_empty_category_raises PASSED
tests/test_data_service.py::TestAddEntry::test_add_zero_amount_raises    PASSED
...
tests/test_logic.py::TestCalculateBalance::test_empty_entries_returns_zeros  PASSED
tests/test_logic.py::TestMonthlySummary::test_budget_exceeded                PASSED
tests/test_logic.py::TestMonthlySummary::test_savings_rate_calculated        PASSED
...
tests/test_bugfixes.py::TestBug01SearchCaseInsensitive::test_search_finds_uppercase_description  PASSED
tests/test_bugfixes.py::TestBug02CommaDecimalInput::test_normalize_comma     PASSED
tests/test_bugfixes.py::TestChg01SavingsRate::test_savings_rate_positive_balance  PASSED
...

========== 52 passed in 0.84s ==========
```

---

## 3. Фрагмент журнала поддержки

| ID     | Тип    | Описание | Решение | Версия |
|--------|--------|----------|---------|--------|
| BUG-01 | Баг    | Поиск не находит записи с заглавными буквами | `.lower()` на обеих сторонах сравнения | 1.0.0 |
| BUG-02 | Баг    | Ввод суммы с запятой вызывал ValueError | `normalize_decimal()`: замена `,` → `.` | 1.0.1 |
| IMP-01 | Улучш. | Топ-3 категорий расходов в сводку | Добавлена `top_expense_categories()` | 1.0.2 |
| CHG-01 | Измен. | Вывод нормы сбережений | Поле `savings_rate` в `monthly_summary()` | 1.0.2 |

---

## 4. Ответы на вопросы

### Что было самым сложным в тестировании?

Сложнее всего оказалось тестировать `monthly_summary()`: функция зависит от
`get_by_period()`, а значит от реального файла. Пришлось использовать `monkeypatch`
для подмены пути к CSV на временный файл в `tmp_path`. После настройки фикстуры
тесты стали изолированными и воспроизводимыми.

### Как изменилось бы приложение, если бы сразу знали обо всех багах?

Функция `normalize_decimal()` появилась бы в самом начале, до первого UI-метода.
Регистронезависимый поиск был бы реализован сразу через `.lower()`, а не
добавлен как исправление. Архитектурно ничего не изменилось бы — трёхслойная
модель оказалась устойчивой.

### Чему научились в процессе «поддержки»?

Главный урок: **сначала тест, потом фикс**. Даже очевидное исправление (добавить
`.lower()`) сначала ловится тестом, который падает, — и только потом исправляется
код. Это гарантирует, что регрессия не вернётся. Второй урок: пользователи
находят краевые случаи, о которых разработчик не думал (запятая в числе —
типичный пример ввода «как привык»).

---

## 5. Личная ретроспектива

| Что удалось | Что улучшить в следующий раз |
|-------------|------------------------------|
| Чёткое разделение на слои (data / logic / menu) | Покрыть menu.py тестами через dependency injection или mock |
| Все тесты изолированы через tmp_path + monkeypatch | Добавить параметризованные тесты для граничных значений |
| TDD выдержан строго на слоях data и logic | Документировать каждый PR подробнее при написании |
| Журнал поддержки велся параллельно с разработкой | Использовать fixtures на уровне модуля для ускорения |
