# D10 — уніфікація й область видимості: дев'ять доказових пропозицій, жодної ратифікації

**Нормативний D10 у `main`: 625/1024 відібрано, 256 координат за законом селекторів, 369 без координат, 399 ще не відібрано, 0 ратифіковано.** Ця гілка НЕ міняє `knowledge/d10-v1-semantic-inventory.json` або `knowledge/d10-fill-v1-state.json`.

Обидва донори мають зафіксовані Git blob SHA й рядки визначень у `knowledge/d10-unify-lexical-harvest-v1.json`. Дев'ять записів є **HOLD/pending-owner-review**; відсутність дубліката назви не є доказом нової семантики.

## Розбір агентських рекомендацій
- **П'ять підстановок і уніфікації:** `LOOKUP-SUBST`, `WALK-RESOLVED`, `FAILED-SUBST?`, `UNIFY-WALKED`, `UNIFY-VAR`: перевірка еквівалентності до ратифікованого D9 `UNIFY`, `WALK`, `OCCURS-CHECK?`, `APPLY-SUBST`. Не виділяти D10 координат.
- **Два проходи кон'юнкції:** `THREAD-CONJUNCTION`, `THREAD-CONJUNCTION-BRANCHES`: перевірити нуль умов → [state], порожню гілку → [], повторення та порядок X,X,Y. Зіставити з selected `MATCH-CONDITIONS` і `MAP-GOAL-RESULTS`; `APPEND` та recursion можуть бути достатні.
- **Два статичні правила області:** `COLLECT-FREE-VARS-LET*`, `COLLECT-FREE-VARS-LETREC`: розрізняють sequential/mutual lexical scope, але це поки аналіз linter, не універсальна функція виконання.

## Допуск
1. Відтворювані позитивні і негативні свідки на вихідному Lisp і поточному SENS.
2. Behavioral dedup проти D1–D9 та відібраних D10, включно з композиціями.
3. Рішення власника про незалежний закон та його домен, **без** автоматичної координати.
4. Лише потім оновлення machine inventory, окремий review і без порушення D2-only control.

Запуск перевірки: `python3 scripts/check-d10-unify-lexical-harvest-v1.py`. Вона лише перевіряє pinned sources, HOLD-статус і відсутність фальшивої селекції; не заявляє runtime/old-world parity. Координація: #4013, #4182, #4463; чернетка PR #4810.
