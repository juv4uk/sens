# #2017 — перевірений ledger спростованих шляхів

Лише дослідження. Артефакт відділяє **спростовані гіпотези** від **замінених premises/design choices**.

## Результат

Перший аудит перевіряє дев’ять bounded falsification classes:

1. global Hamming-1 як semantic authority;
2. unordered dependency support як prefix authority;
3. named dependency depth як semantic rank;
4. transitive seed-support як semantic identity/rank;
5. evaluator SCC topology як semantic authority;
6. raw `00` як in-band delimiter для unrestricted packed words;
7. immediate selector-strength EQ children з NULL/EQUAL/MEMBER;
8. immediate selector-strength CONS children з LIST/APPEND/PAIR/PAIRLIS;
9. COND -> PredicateBit AND/OR за чинного закону `() != 0`.

Стара flat exact-8/256 ontology **не рахується falsification**. Вона позначена як `superseded-premise`: заміна design premise не є доказом, що теорему спростовано контрприкладом.

## Мінімальні контрприклади

Durable частиною ledger є не назва issue, а bounded witness/counterexample. Наприклад:
- semantic triangle не вкладається у Hamming-1 hypercube як глобальний graph;
- CADR і CDAR мають однаковий unordered support, але різний порядок;
- Lisp I та Lisp 1.5 дають різні evaluator SCC;
- COND AND/OR candidate повертає `()` там, де PredicateBit потребує `0`.

## Resurrection rule

Checker відхиляє повторне введення спростованого `concept_key`, доки не показано, що старий counterexample або його assumptions більше не діють.

## Scope discipline

Bounded negative result не можна переписувати як універсальну impossibility theorem. Наприклад, невдача конкретних EQ-candidates не означає «EQ ніколи не матиме descendants».

Артефакт: `scripts/research-2017-falsification-ledger.py`.
