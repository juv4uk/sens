# Гвардія має мати шлях росту

**Статус:** правило tooling/CI; не доповнює `language-contract.lisp`, не змінює D1–D9, D2, фізичний T5, D10-резидентів або ратифікацію.

> Кожна fail-closed перевірка незмінності корпусу мусить описувати й тестувати **окремий, доказовий append/extend перехід**; вона блокує непояснену мутацію, але не має забороняти легітимний ріст лише через зміну історично закріпленого SHA.

## Практичний контракт

1. **Immutable history:** старий snapshot і його Git blob SHA залишаються незмінним історичним фактом. Немає silent repin, suppress, auto-waiver, `|| true` чи «тимчасового» обходу тесту.
2. **Машинна подія росту:** записати `previous_SHA`, `resulting_SHA`, додані ідентичності, джерела, свідків, фальсифікатори, `coordinate=null`, `ratified=false`. Перевірити повну тотожність старого префіксу.
3. **Реальний канал пропозиції:** якщо додаються вибрані D10 meanings, повинні існувати відповідні записи в `knowledge/d10-proposal-ledger.tsv`. Вони можуть бути створені раніше на окремому review-PR або разом з selection-PR, але не можуть виникнути *заднім числом* як твердження без доказу.
4. **Growth gate:** `scripts/check_d10_proposal_growth_gate.py` порівнює PR/push відносно Git base, вимагає ledger match за `semantic_name`, не дозволяє зміну раніше вибраних rows або видалення/редагування попередніх рядків ledger. `scripts/check_d10_selection_transition_history.py` окремо доводить ланцюжок SHA.
5. **Точна відмова:** невідоме або непідтверджене залишити `BLOCK/HOLD` зі шляхом подальшої перевірки, а не кодувати мовчазну заглушку чи втрачати попередню роботу.
6. **Негативні тести:** спроби видалити старий рядок, підробити доказ, обійти ledger, змінити координату, ратифікувати без власника та обійти джерело повинні падати; базовий state без росту проходить.

## Чому старий D10 ledger поки пустий

Історичні п'ять selection meanings 625→627→630 уже мають source-pinned **transition history**, але були відібрані до того, як ledger став обов'язковим CI-шляхом. Це архівний борг, а не дозвіл сфабрикувати `donor_provenance`, `dedup_check` або `blocked_source`. Див. `knowledge/d10-ledger-backfill-audit-v1.json` (окрема черга). Змінювати старі selected row чи історичний SHA заради backfill заборонено.

Пізніший selection має пройти валідатор леджера, append-only історію та growth gate. Якщо первинна специфікація не є реальним Git-файлом, отримати відтворюваний pinned reference/дзеркало законно й явно; **не вигадувати** path:line чи коміт. Для історичного стандарту без заблокованої міграції використовувати `NO-MIGRATION-BLOCK`, а не фіктивний `.lisp` blocker.

### Перевірка

```sh
python3 scripts/check-d10-proposal-ledger.py --self-test
python3 scripts/check_d10_selection_transition_history.py --self-test
python3 scripts/check_d10_proposal_growth_gate.py --self-test
# У CI: ті самі перевірки + порівняння base/head immutable Git SHA
```

**Точна межа:** append-only selected research `!=` ратифікація D10; `selected=630, ratified=0` на зафіксованому snapshot; жодних нових кодів чи релізних обіцянок.
