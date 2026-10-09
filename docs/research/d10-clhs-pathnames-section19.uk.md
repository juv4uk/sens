# D10: систематичний перепис CLHS §19.4 — Pathnames (Filenames)

**Статус:** `RESEARCH-CENSUS-NOT-SELECTED`. Усі нові слова без D10 координат, без ратифікації; поточний канонічний D10 не змінювався. Це **друга предметна секція CLHS** після §9.2 Conditions, яку вже обробляє [#4901](https://github.com/juv4uk/sens/pull/4901). Межі зафіксовано в [#4896](https://github.com/juv4uk/sens/issues/4896).

## Джерельний охват

Первинний ANSI Common Lisp 19.4 dictionary index: https://franz.com/support/documentation/10.1/ansicl/section/diction5.htm — **17 номерів 19.4.1–19.4.17**, включно з об'єктними типами, функціями, змінною `*default-pathname-defaults*`, а також двома перевантаженими за роллю іменами `PATHNAME` та `LOGICAL-PATHNAME`.

- **17** словникових позицій (деякі є згрупованими посиланнями, наприклад усі шість `PATHNAME-*` accessor).
- **26** записів `source name × source role`, **24** різні написання.
- У зафіксованих ревізіях ratified D1–D9 і selected D10=630 — **0 точних збігів за назвою**. Це **НЕ** означає 24 нових семантичних функції.
- `knowledge/d10-clhs-pathnames-census-20261009.json` зберігає кожну позицію, природу (system-class/function/special-variable), дедуп-маркер на **історичному** знімку, категорію HOLD / REVIEW, та лише три поглиблені протоколи для оракула.

Першоджерела для перевірки:
- https://franz.com/support/documentation/ansicl.94/dictentr/merge-pa.htm — компоненти `MERGE-PATHNAMES`, успадкування від default та поєднання relative/absolute директорій.
- https://www.lispworks.com/documentation/HyperSpec/Body/f_pn_mat.htm — `PATHNAME-MATCH-P`, **не комутативна**, wildcard в першому аргументі не еквівалентний wildcard у другому; точні правила зіставлення залишені реалізації.
- https://examples.franz.com/support/documentation/ansicl/dictentr/namestri.htm — `ENOUGH-NAMESTRING`, тільки reconstruction invariant, не фіксований host string.
- https://franz.com/support/documentation/10.0/ansicl/dictentr/make-pat.htm — `MAKE-PATHNAME` та `:case` і компоненти.

## Три пріоритетні закони для перевірки

| Ім'я | Гіпотеза з поведінковим коренем | Чому ще HOLD |
|---|---|---|
| `MERGE-PATHNAMES` | Детерміноване злиття відсутніх структурних компонентів + приєднання `:relative` директорії до абсолютної бази | Шість компонентів і правила `:newest` потрібно відрізнити від загального record-merge; ім'я не доказ |
| `PATHNAME-MATCH-P` | Не-симетричний matcher компонентів wildcard; `wild` як *перший* аргумент не тотожний *другому* | Правила wildcard **implementation-defined**; не імпортувати Unix/Windows/host filesystem до семантики SENS |
| `ENOUGH-NAMESTRING` | Найкоротше обґрунтоване відносне представлення з гарантією відновлення через default | Спосіб серіалізації залежить від host; сам інваріант часто є похідністю `MERGE-PATHNAMES` |

**Що виключено зі слотів поки що:** клас `PATHNAME` — не інструкція сама по собі; `LOAD-LOGICAL-PATHNAME-TRANSLATIONS` може читати конфігурацію host; `*DEFAULT-PATHNAME-DEFAULTS*` є dynamic host-state; `PARSE-NAMESTRING`, `TRANSLATE-PATHNAME`, `HOST-NAMESTRING` залежать від mapping host/implementation. Вони можуть бути потрібні системі, але не доводять нові універсальні десятирозрядні значення.

## Виконуваний тест

`tests/oracles/d10_clhs_pathnames_sections19.lisp` запускається у **справжньому SBCL**, без `OPEN`/`PROBE-FILE` та без запису на диск. Свідчить про `MAKE-PATHNAME`, `MERGE-PATHNAMES`, спадковий тип, append relative-directory, `PATHNAME-MATCH-P` directional wildcard, `ENOUGH-NAMESTRING` reconstructibility і type-error. Скрипт `scripts/check_d10_clhs_pathnames_census.py --self-test` контролює точний scope й відкидає 8 цілеспрямованих пошкоджень даних.

**Обмеження:** SBCL — ANSI-сумісне сучасне свідчення, не доказ, що SENS уже має ці значення; не можна переносити mapping файлової системи чи глобальний *default-pathname-defaults* як новий мовний контролер поруч з D2. Окремо потрібно порівняти з потенційними структурами записів, наявним D10, робити додаткові witness на Chez/CLISP/CCL там, де переносимість взагалі допустима.

## Машинний порядок пропозицій

Паралельні [#4894](https://github.com/juv4uk/sens/pull/4894) і [#4895](https://github.com/juv4uk/sens/pull/4895) володіють `knowledge/d10-proposal-ledger.tsv`, growth-gate та конституцією позитивного шляху append/extend. Я **не змінював** їх файлів, не додавав фальшиві TSV-row і не називаю census selection. Коли станеться owner-reviewed перевірка нового непохідного закону, один ledger-row з точним donor/provenance/dedup має передувати зміні selected inventory. Гвардія захищає історичне SHA, а не заморожує SELECT=630.

**Координація:** #4896 (systematic donor pipeline), #4897 (CLHS chapters), #4463 (proposal rule), #4013 (selected research inventory). Жодних змін D1–D9, D2, D7, T5 або l0.42.0.
