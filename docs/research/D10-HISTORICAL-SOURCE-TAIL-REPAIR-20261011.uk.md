# D10: provenance repair, 651→652→653

**Дата:** 2026-10-11. **Режим:** fail-closed, без зміни ратифікованих семантик.

Перевірка `main` виявила, що історичні записи у
`knowledge/d10-selection-transition-history.json` при переходах
651→652 та 652→653 помилково заявляли внесення нових елементів у
масив `inventory.sources`. Насправді канонічний інвентар цього не
робив: останнім джерелом залишається
`knowledge/d10-archive-admission-20261011.uk.md` (перехід 647→651).

Зроблено **бухгалтерське виправлення**, яке не змінює жодного байта
`knowledge/d10-v1-semantic-inventory.json` та його історичних Git SHA:
- Для 651→652 і 652→653 `appended_sources: []`, бо source-tail фізично незмінний.
- Першоджерела кандидатів не втрачаються: вони збережені у
  `transitions[].evidence` та в окремих source-grade досьє.
- Два відібрані закони `UNIQUE-BOUNDED-MODULAR-LIFT` і
  `PREFIX-FREE-KRAFT-CERTIFICATE` отримали в proposal-ledger точний
  Git SHA інвентарю **до** власного відбору та підтверджену незалежну
  `NO-MATCH` перевірку.
- Координати, Core D1–D9, ратифікація й фізичний T5 не змінені.

Перевіряти тільки оригінальними fail-closed скриптами, не вимикати CI:

```sh
python3 scripts/check_d10_selection_transition_history.py --self-test
python3 scripts/check-d10-proposal-ledger.py --self-test
python3 scripts/check_d10_completion_readiness.py
```

**Важливо:** Достовірність source-інвентарю зберігається відокремлено
від додавання source pointers у сам масив `inventory.sources`.
Вигадане додавання змінило б Git SHA і порушило б історичну спадковість.
