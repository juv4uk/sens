# CURRENT — where the truth actually lives

Українською: це єдина точка входу для «що зараз чинне». Якщо будь-який інший документ, включно з архівом, застарілим планом чи старим рев'ю, суперечить джерелам нижче — **чинні джерела нижче перемагають**. `docs/archive/**` зберігає історію, але не є специфікацією.

This file exists per [`DOC-AUTHORITY-ARCHIVE`](https://github.com/juv4uk/ecosystem/issues/5): **one active truth, many preserved histories**. Read this first. Historical material may explain how SENS arrived here, but it cannot override current contract and executable evidence.

## Фізичні трійки Lisp → T5M → біти · облік 23.10.2026

На Git-знімку `main@799d0c7f0b7eefe912bb409277a432c328bb938c` є **1776** файлів `.lisp`, **1255** однойменних пар `.lisp`/`.sens` і **1254** трійки з файлом без розширення. Це лише наявність Git-шляхів: **521** Lisp-джерело не має однойменного `.sens`, а `lib/core4.lisp` має `.sens` без бітового перегляду. Найбільша черга — `tests/semantic/` (**235** файлів без фізичної пари). Наявність трьох файлів не доводить ні побайтової оберненості, ні семантичного виконання.

**Причини потрібно називати точно:** відсутній фізичний файл, відсутній або неточний бітовий перегляд, невідповідність D7/D24+, помилка коду, некоректний тест, нестача незалежного семантичного доказу. Таблиці доменів, архівні матеріали та перевірені схеми даних залишаються в повному обліку `.lisp`, але не отримують вигаданого статусу виконуваної програми. Для чинної програми потрібні SENS mint/paired execution, Zig T5M byte roundtrip і позитивний/негативний Lisp-свідок. Статус релізу з цього обліку не випливає.

## Перевірений стан реалізації · 19.10.2026

Цей розділ описує **виявлений код** за чинним Contract 12.0; відділяти нормативну владу від фактичного стану конкретних entrypoints.

- **D11 має 512 математично визначених похідних селекторів:** 256 ратифікованих селекторів D10 породжують по два точні 11-бітні визначення за законом `p(CAR(x))` / `p(CDR(x))`. Це **визначені функції**, не кандидати й не нові примітивні закони. [`knowledge/d11-selector-seed.json`](knowledge/d11-selector-seed.json) і [таблиця проєкцій](knowledge/d11/база-доступних-функцій/селектори-512-д11.tsv) задають похідні коди. Окремо [`lib/domains/d11.lisp`](lib/domains/d11.lisp) містить 43 нератифіковані тестові позначення (22.10.2026 власник заперечив їх ратифікацію; це не зайняті адреси функцій). Пряме виконання всіх 512 як окремих машинних opcode ще не підтверджене; їхня математична визначеність від цього не залежить.
- **Десяткові цілі у людському source:** [`crates/sens/src/source_projection.rs`](crates/sens/src/source_projection.rs) починають звичайну проєкцію зі знакових D12 значень і розширюють їх до найменшого потрібного D24/D48/D96/D192 домену. Явний профіль може задати ширший мінімум. Пов'язані D5-математичні дерева узгоджують домен; число розбирається по цифрах; вихід за signed D192 — явна помилка без host integer/float. Дробові source-літерали мають окремі обмеження.
- **Поверхня і файли:** нові виконувані `*.lisp` — повні `укр` викличні голови, українські клавіатурні символи й звичайні десяткові математичні значення, без `#d`/`#b`/`#q2` чи машинних голів. Фізичний `*.sens` містить байти T5M, а однойменний файл **без розширення** — лише похідний видимий exact-bit перегляд. Довести source→exact domain→physical→decoded identity та, окремо, SENS execution parity.
- **Історичний D8 не вигадується:** SID8/Sens8/Function8 перенести за датованою семантикою і відповідною новою `укр`-проєкцією; однакові 8 бітів не дають D8-ідентичності.
- **CI і ранери:** чинний [`.github/workflows/ci.yml`](.github/workflows/ci.yml) запускає звичайні перевірки на GitHub-hosted `ubuntu-24.04`; важкі 19 частин `runtime-shards` доступні **лише через ручний `workflow_dispatch` на `main`**, із `max-parallel: 1`. Автоматичні події `push` і `pull_request` не запускають цю матрицю. У чинному `ci.yml` немає власного блока `concurrency` та `cancel-in-progress`: сам цей workflow не задає автоматичного скасування попереднього запуску під час нового push. Це стан YAML, не підтвердження успішного виконання тестів. Фактичні `status`, `conclusion`, SHA та журнали завдань перевіряти окремо; нічого важкого не запускати без прямого дозволу власника.
- **Обсяг змін:** виправляти конкретні дефекти без самовільних HOLD/FREEZE; не розмножувати workflow чи формальні тести. [README](README.md) — поточний огляд, [docs/README.md](docs/README.md) — маршрутизатор; звіт від 12.10.2026 — **датований історичний зріз**.

<!-- OWNER-UKR-DECIMAL-T5M-20261018 -->
## Власницьке уточнення · 18.10.2026: український Lisp → точні домени → T5M

Чинна **людська** програма `*.lisp` записується символами української розкладки: викличні голови доменних функцій беруться з ратифікованої повної колонки `укр`, не з англійських назв, SID8 чи самих бітових кодів. У людській проєкції `*.lisp` не допускаються ні цифрові викличні голови, ні числові літерали. Математичні значення будуються з українських спискових даних та дозволеної арифметики; вони не є джерелом семантичної тотожності домену.

Числова межа відновлює **точну** ратифіковану D12+ числову сутність у вибраному source-профілі та exact-width слова, зберігаючи знак і дріб без float; D1–D10 залишаються окремими точнодоменними ідентичностями. **Zig/T5M тільки пакує вже утворені слова у фізичний `*.sens`**, не визначає значення й не створює callability. Непідтверджений випадок відхиляється *в межах відповідної операції*, а не заморожує весь `main`. Ніяких нових глобальних HOLD/FREEZE, дублювальних CI чи беззмістовних тестів. Старі формулювання нижче про «десятковий запис виключно для виводу» і заборону десяткового **людського** вводу — історичні та не переважають цього уточнення; заборона сирих машинних/доменних літералів зберігається.

## Authority order (highest wins)

1. **Machine-readable language authority**
   - [`language-contract.lisp`](language-contract.lisp) — compatibility entrypoint; current authority is [`contracts/language-contract-12.lisp`](contracts/language-contract-12.lisp), Contract 12.0, ratified 2026-10-25. Dated statements below that describe Contract 11.9 are historical snapshots.
   - [`lib/domains/d1.lisp`](lib/domains/d1.lisp) … [`lib/domains/d11.lisp`](lib/domains/d11.lisp) — human-readable domain projections. The active semantic authority is Contract 12.0, not the historical Contract 11.9 summaries retained below. Domain identity, admission to call, and physical execution are distinct; exact domain laws come from the ratified sources, not spelling or width alone. D7 keyboard v2 and D1–D11 inventory details remain in their ratified tables. No aggregate cross-domain table overrides them.
   - [`lib/surface/semantic-registry.lisp`](lib/surface/semantic-registry.lisp) — migration input only. Existing exact-eight-bit rows are historical crosswalk evidence, not an executable registry or a source of current identity. All live consumers are to move to generated exact-domain ownership; spelling never owns meaning.
   - [`tests/fixtures/conformance.lisp`](tests/fixtures/conformance.lisp) and other admitted executable conformance fixtures — behavior evidence independent of one host implementation.
   - SENS has no universal 256-slot function ontology. Canonical identity is `exact bits + exact domain + admitted/proved law`. Contract 12.0 preserves D1–D11 resident identities, D10 whole-domain authority, and the D12-first numeric decision. It does not claim implementation completeness; legacy SID8/Sens8 runtime removal remains to be verified.
   - Current generation boundary: Contract 12.0 preserves ratified D1–D11 resident identities, D10 whole-domain authority, and the D12-first numeric decision. Ratification does not establish implementation completeness; legacy SID8/Sens8 runtime paths are marked for removal. Physical `.sens` uses T5M; T5 is historical, not an active codec route.
2. **Ratified ADRs and accepted decisions** — [`docs/adr/`](docs/adr) records scoped decisions. McCarthy/Lisp names in historical ADRs describe provenance or Core1 compatibility; they do not create a second current function ontology.
3. **Reference implementation and substrates**
   - [`crates/sens`](crates/sens) — current Rust reference crate. Rust owns implementation mechanisms, not language meaning.
   - Independent substrates such as C, WASM, FPGA, GraalVM, Common Lisp, Prolog, Datalog, and CLIPS may execute or observe admitted behavior without becoming semantic authority.
4. **Active plans and standing doctrine** — [`AGENTS.md`](AGENTS.md), [`docs/agent-doctrine.md`](docs/agent-doctrine.md), [`PLAN.md`](PLAN.md), [`STATUS.md`](STATUS.md), [`ecosystem-status.md`](ecosystem-status.md), and the currently active scoped plans they reference.
5. **Tests and evidence** — `cargo test --workspace`, `--oracle-check`, focused witnesses, and CI prove what the implementation currently satisfies. A claim without executable or source evidence is a hypothesis, not a fact.
6. **Operational snapshot (2026-10-12)** — [`docs/project-reality-2026-10-12.uk.md`](docs/project-reality-2026-10-12.uk.md) tracks the benchmark-lab registry gap, measured Nano-SENS baseline and its open seed-closure gate, plus D10 runtime-admission boundaries. The pinned Nano-SENS Contract 11.8 run is not evidence of D10 execution under current Contract 11.9.

## Current identity rule

The language is **sens / СЕНС**.

```text
semantic object
=
exact binary word (0/1 digits)
+ exact domain
+ admitted / proved law
```

Current Core examples:

Канонічні людські таблиці доменів: [D1](lib/domains/d1.lisp), [D9](lib/domains/d9.lisp), [D10](lib/domains/d10.lisp); окрема числова authority D12+ — [`contracts/numeric-domains-ratification.lisp`](contracts/numeric-domains-ratification.lisp).

Написи проекцій — лише source/UI routing metadata: вони маршрутизують до доменно-кваліфікованого об'єкта, але не визначають його identity чи значення.

```text
D1  PredicateBit — exact 1-bit keys (2/2)
D2  racana2 structure — exact 2-bit keys (4/4)
D3  bīja3 foundation — exact 3-bit keys (8/8): 000 () … 111 CONS
D4  full compact bootstrap — exact 4-bit keys (16/16)
D5  full compact — exact 5-bit keys (32/32)
D6  full compact — exact 6-bit keys (64/64)
D7  v2 keyboard text/data — exact 7-bit keys (128/128); historical v1 126/128 is provenance only
D8  full compact — exact 8-bit keys (256/256)
D9  full compact — exact 9-bit keys (512/512)
D10 whole-domain catalogue — exact 10-bit keys (1024/1024 domain-level); resident-level mechanism/callability evidence remains separate; T5M transport does not imply it
D12+ owner-ratified numeric ladder D12/D24/D48/D96/D192/… — separate from function domains
```

**Bit axiom:** the binary key width *is* the domain address. A row whose bitstring length ≠ *n* is not a D*n* resident. Equal packed payloads across different widths are different coordinates.

**Позиційна граматика D1 · власницьке уточнення 15.10.2026:** **«Явність — для меж, не для середини. У граматиці ширину знає позиція; на кордоні — оголошення. Два записи однієї ширини — дрейф у зародку».** У канонічному бінарному SENS слово D1 є **голим одним бітом** `0` або `1`; тег `#d1:` **не** є канонічним синтаксисом і не додається до D2-потоку. Точна межа слова обов'язкова для **фізичного транспорту** (чинний T5M), але не дублюється в самому канонічному слові. Поточний canonical reader уже читає D2-фрейми й D1 без `#d1:`: `tests/oracles/d1-cond-law/proof.bits` → `proof.sens` → `parse_canonical_binary`; механічний позитивний/негативний round-trip: `cargo test --locked -p sens --test binary_sens_d1_cond_oracle -- --nocapture`. Не ототожнювати D1:`0` із D3:`000`.

**TEMPORARY · READER [#5605](https://github.com/juv4uk/sens/issues/5605) / lib [#5609](https://github.com/juv4uk/sens/issues/5609):** у **історичному Lisp-сорсі** `lib/*.lisp`, що читається `parse()`/`eval_program()` у режимі `LegacyCompatibility`, голі `0`/`1` іще є звичайними числами; `#d1:0`/`#d1:1` — лише явно маркована **тимчасова сумісна проєкція**, не закон канонічної мови. **Умова зняття:** відповідний споживач бібліотеки перейшов на canonical exact-domain reader/AST із позиційним D1, а SENS-native позитивний + однобітний негативний свідки та точний T5M round-trip підтвердили ту саму поведінку. До цього не робити механічне `#d1:1 → 1` у `lib/*.lisp`: це перетворює предикат на Number. Межу підтверджує `cargo test --locked -p sens --test d1_canonical_source_value -- --nocapture`. Ні `#d1:`, ні host Rust/C/Zig не отримують семантичної влади.

**Актуальне уточнення власника · 23.10.2026 — український `.lisp` без цифрових літералів.** Людська виконувана проєкція не містить ані цифрових викличних голів, ані числових атомів. Викличні голови D1–D10 беруться лише з повної ратифікованої колонки `укр`; числові значення утворюються з україномовних спискових даних та явних арифметичних визначень. Заборонені сирі бітові голови, SID8/Sens8-виклики та числові літерали в коді. Не змінювати значення або тип цитованих даних, рядків і D7-тексту. Фізичний `.sens` формує T5M з точних уже визначених доменних слів; T5M не ратифікує механізми й не вгадує домен. Історичні свідки та знімки походження можуть зберігати старі записи як дані доказу, але не є людською виконуваною проєкцією й не можуть використовуватися як активний код.

**Позиційна явність · 15.10.2026 (#5605):** «Не пиши того, що граматика вже знає. Явність — для меж, не для середини». У канонічному видимому двійковому SENS D1 записується тільки голим словом `0` або `1`: межа та довжина слова дають точну бітність, D2 — структуру, контекст COND — вимогу D1-результату (але guard може бути довільним виразом, не лише літералом). `#d1:` **не є** канонічним синтаксисом і не дублює бітність усередині граматики. На справжній межі без контексту оголошення `domain/width/bits` для Zig/host transport потрібне, але не додає значення чи callability. **LEGACY_MIGRATION_DEBT / READER #5605:** входження `#d1:0` / `#d1:1` у старих змішаних `lib/*.lisp` — вже наявний борг історичного `parse()`, де голі `0`/`1` сьогодні є числами, **не дозвіл писати такі літерали**. Прибирати теги пофайлово тільки після підтвердженого переходу конкретного завантажувача на канонічний/контекстний READER, позитивного та негативного D1/COND свідків і точного T5M round-trip через стерильний Zig-коридор; **не** замінювати їх на голі біти у старому `parse()` механічно. `docs/language-core-axioms.md` має статус чернетки, тому це чинне операційне уточнення, а не самовільна ратифікація всіх його G/S аксіом.

**Mathematical operand boundary (numeric ratification 2026-10-24, superseding only the first numeric rung of the 2026-10-12 D24-first clarification):** D1–D11 are domain-qualified binary words, not arithmetic operands. Only explicitly qualified D12/D24/D48/D96/... values and lawful numeric compositions admit `+ - * /` and numeric `< > =`. An operator may have a D5/D6 function identity without making that function identity a number. D3 EQ and D1 predicates are separate non-mathematical laws; old unqualified Number/Rational/BinaryNumber no longer grants arithmetic admission.

**Стан числового bridge, не твердження про зелений реліз:** загальна source-проєкція тепер D12-first; ширші профілі мають задавати мінімум явно. Повну фізичну відповідність CLI/REPL через SENS → Zig/T5M перевіряти на актуальному SHA. Не вводити неявної коерції між різними Dn.

**D7 current occupancy cutover:** `crates/sens/src/domain_ladder.rs`, `scripts/generate-domain-owner-registry.py`, and the generated Rust bitmap agree on the current 128/128 keyboard/data coordinates from `knowledge/d7-keyboard-v2-ratified.json`. No D7 slot is reserved in the active map; residency does not grant a callable mechanism. Other old consumers, if found, remain separately verifiable migration debt.

Owner foundation ratification #4008 extends the current chain through D9: D1 #1699, D2 #1702, D3 #3202, D4 #3272, D5 #3305/#3330, D6 #3393, D7 historical v1 #3572 / current table v2 keyboard, D8 #3960, D9 #4008. Intermediate clean-room maps remain research provenance only. Any current implementation or fixture that still uses the superseded ordering `011=COND, 100=CONS, 101=CAR, 110=CDR, 111=EQ` is migration debt tracked by #3203/#2055/#3205/#3206, not an alternate language law.

Чинна числова ратифікація від 24.10.2026: математичні домени починаються з D12, далі D24, D48, D96, D192 за законом подвоєння. Загальний T5M transport тепер має bit-granular round-trip свідки для D12; окремий typed wide-carrier профіль `research/zig-codecs/numeric_domains.zig` досі містить лише D24/D48/D96/D192. CI для нових свідків і глобальний CLI/REPL перехід залишаються NOT_VERIFIED. Єдине джерело — `contracts/numeric-domains-ratification.lisp`.

D10 ratification source: `knowledge/d10-owner-whole-domain-ratification-20261012.json`; current codebook pointer: `knowledge/d10-current-inventory.json`. Domain ratification does not fabricate resident-level proofs. **Чинна директива власника 24.10.2026:** усі ратифіковані домени SENS повинні бути операційно виконуваними згідно зі своєю роллю (D2 — структура, D7 — дані, D12+ — числа, функціональні Dn — виклики); усі функціональні резиденти D10 потрібно довести до справжнього SENS-виконання. Немає акта, що оголошує 1024 резиденти D10 невиконуваними. Відсутність конкретного механізму чи свідка класифікувати як недоведену перевірку або дефект реалізації з точним Dn:біти й командою відтворення, не як доказ неможливості. Статус `NOT_VERIFIED` не підміняти ні `PASS`, ні `UNEXECUTABLE`. Numeric acts: `contracts/numeric-domains-ratification.lisp` (єдине чинне джерело; JSON числової драбини вилучено).

Equal packed bits in two domains do not imply equal identity. In particular owner-ratified Core.D8 is not historical Sens8 merely because both occupy eight physical bits. Width alone does not mint meaning or callability. Ukrainian, English, Sanskrit, symbolic, and compatibility spellings remain source/UI projections only.

Owner direction (2026-10-12): remove active Sens8/SID8/Function8 runtime semantics across Rust, Lisp, scripts, tests, CLI and workflows; replace each call/data position with a width-qualified domain identity and explicit admitted mechanism. No new consumer may be added to the legacy carrier. Historical manifests and archived experiments remain provenance-only and must never be loaded as executable input.

**Виконаний полімовний зріз і конкретні невирішені причини:** [`docs/migration/domain-ladder-cutover-2026-10-12.uk.md`](docs/migration/domain-ladder-cutover-2026-10-12.uk.md) фіксує видалений старий guard, новий Rust/Python/C/Lisp CI, явні D1–D10 координати в Python і ще не перенесені AST/evaluator/capability та Lisp-шляхи. На одному candidate SHA повний green ще **не доведений**; автоматично ототожнювати історичний W8:10101000 INVOKE із чинним D8:10101000 ROUND заборонено.

Structural `()` is the admitted Core.D3 `000` object. It is not historical exact-eight-bit `00000000`, PredicateBit `0`, or Number zero; those equal-looking numeric payloads remain distinct across domains.

Historical McCarthy names remain useful when discussing the 1960 evaluator, Core1, migration evidence, or provenance. They do not create a second current identity ontology.

## What is explicitly NOT authoritative

- **`docs/archive/**`** — preserved superseded designs, completed plans, research spikes, historical audits, and reactions.
- Any dated report or PoC not explicitly promoted into the current authority chain.
- A host implementation detail merely because it is implemented in Rust, C, Java, Common Lisp, Prolog, Datalog, CLIPS, or another executor.
- A peer agent's report that something is fixed without a verifiable commit/test/CI witness.
- A human surface spelling as a substitute for the exact domain-qualified semantic object it routes to.

## For a new agent starting cold

1. Read `AGENTS.md` and `docs/agent-doctrine.md`.
2. Read `language-contract.lisp` and this file before trusting older design prose.
3. Read the relevant `lib/domains/dN.lisp` table and generated domain-owner registry for identity and law. Use `lib/surface/semantic-registry.lisp` only to migrate historical source spellings; never dispatch by an eight-bit row.
4. Inspect `crates/sens` for the current Rust reference mechanism and the relevant executable witnesses for the behavior being changed.
5. Run the focused tests for your slice and then the applicable repository gates before claiming the change works.
