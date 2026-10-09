# D10: історичні джерела, які ще НЕ вичерпані (2026-10-09)

**Research-only; жодної координати, ратифікації чи виконуваної ідентичності.** Причина: окремий донорний `EXHAUSTED-FOR-THIS-SLICE` не доводить повноти всієї історичної документації.

Наявний D10 = **625/1024 selected, 399 unselected, 256 law-forced selectors, 369 unplaced, 0 ratified**. MacLisp (21+12), early Lisp (6), Interlisp/PSL (13) і Flavors (8 поза inventory) — обмежені проходи, не індексне порівняння повних посібників.

**Справжній історичний недобір:**
- R4RS/R5RS/R6RS Scheme: DYNAMIC-WIND, PARAMETERIZE, MAKE-PARAMETER, SYNTAX-RULES, SYNTAX-CASE, DEFINE-SYNTAX. Це D2 syntax/control або перевірка derivability; не D10 за інерцією.
- CLOS/MOP: CHANGE-CLASS, UPDATE-INSTANCE-FOR-DIFFERENT-CLASS, FIND-METHOD, ADD-METHOD, REMOVE-METHOD, COMPUTE-APPLICABLE-METHODS. Останній уже має близького #4800 APPLICABLE-METHODS, тому HOLD-DUPLICATE.
- Interlisp-D/Medley: повний посібник описує генератори, корутини, pattern matching, структурний редактор, Masterscope; наявний #4795 проходить лише PSL і Interlisp-history підмножину. Із інструментів не робити вигадані opcode.
- Lisp Machine/Flavors: поряд з method combination історична система має whoppers/wrappers; потенційно керування D2, не D10 автономно.
- Французька/європейська й інші родини: Franz Lisp, NIL, Spice Lisp, S-1 Lisp, Le-Lisp, T, EuLisp, ISLISP, AutoLisp з `docs/DIALECT-COMPARISON.md` не мають повного manual-index-to-semantic coverage.

`knowledge/d10-historical-coverage-gap-audit-v1.json` містить докази й exact-name triage. **Name missing не означає semantic missing.** Первинна матриця не рахує нових D10 residents.

Гейт `python3 scripts/check_d10_historical_gap_audit.py --self-test` відхиляє вигадані коди, ратифікацію, дублікати вже наявних назв, незафіксовані історичні family gaps і статус `EXHAUSTIVE` без доказу. Пропозиції — тільки #4463; координація #4013 і #4182. Мовне/структурне керування — тільки D2.

Далі: по одному історичному першоджерелу за раз складати page/section-index census, зіставляти з D1-D9 + current D10, будувати oracle witnesses і falsifiers; тільки після цього вирішувати, що може стати новим значенням.
