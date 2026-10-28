# Архів доказів релізу SENS s0.42.1

> `s0.42.1` опублікований 2026-10-28. Цей документ зберігає історичний леджер і його старі діагностичні зрізи; його поля `UNSET` та `NO-GO` нижче не описують стан уже опублікованого випуску. Актуальна підготовка наступного кандидата ведеться в [RELEASE-EVIDENCE-s0.42.2.md](RELEASE-EVIDENCE-s0.42.2.md).

> **DRAFT · NO-GO · оновлено 2026-10-26 16:08 UTC.** Це журнал стану, не дозвіл на публікацію. Кандидатний SHA та owner GO залишаються незаданими до завершення всіх обов'язкових перевірок на одному SHA.
>
> **Контрольна точка перед цим оновленням:** `main@03f94435af4b12a3bc70df1d64fe45d6e0dd96cd`. Короткий CI `40355649643` завершився успішно; він перевіряє лише охоронця. Повний Release Preflight на цій точці ще не завершився.
>
> **Зміни release gate в main:** tagged release workflow викликає reusable `release-preflight.yml` як обов'язкову залежність; publisher перевіряє найновіші обов'язкові check-runs на точному SHA до стадіювання артефактів і повторно перед публікацією. Перевірка виконана через `gh api` та Bash, без Python у publisher.
>
> **Цей checkpoint запускає повний preflight:** коміт має маркер `SENS_RELEASE_PREFLIGHT`. Після push потрібно зафіксувати його точний SHA та фактичний результат CI; статус із батьківського SHA не переноситься на новий коміт.
>
> **Релізний стан:** candidate SHA — **UNSET**; owner authorization — **UNSET**; тег `s0.42.1` не створювати до завершення preflight, точних перевірок, артефактів і явного owner GO. Вердикт: **NO-GO**.

**Додаток 2026-10-26:** неопублікований тег `l0.42.1` не переміщується. Префікс релізу змінено на `s`, тому кандидат продовжується як `s0.42.1` (`Cargo 0.42.1`); записи нижче з давнішими датами лишаються історичними доказами своїх SHA.

**Чинний зріз:** Contract 12.0 у `contracts/language-contract-12.lisp` зберігає ідентичності D1–D11, D10 whole-domain authority та D12-first числове рішення; реалізаційна повнота не засвідчена. Для фізичних `.sens` використовується T5M; історичний T5 не є активним маршрутом. Roundtrip сам по собі не доводить виконання. Записи нижче з датами до 25.10.2026 — історичні докази стану на свої SHA, а не опис чинної норми.

## 2026-10-14 · Точковий meta-eval non-atom proof

- [d92fde6](https://github.com/juv4uk/sens/commit/d92fde6d7fe3c1f13aeeb15bb01801c810597d86): захист D3:101 EQ від неатомарного імені без нового мовного дозволу.
- [8a8d84f](https://github.com/juv4uk/sens/commit/8a8d84fb0e05999c0b05ca63f171a34b8b84ebcc) і [зелений точковий CI](https://github.com/juv4uk/sens/actions/runs/38498178993): 2 SENS-owned self-verdicts і негативний однобітний mutant. Rust — транспорт, не оракул.
- Це не доказ повного meta-eval або релізного Cargo: [попередній full-Cargo red](https://github.com/juv4uk/sens/actions/runs/38496532282) показав 4 падіння Canon. Подальший full-Cargo встановить актуальний стан на новому SHA.
- Застаріле відображення Canon surface через W8 історичної таблиці не означає ідентичності D8; потрібна незалежно перевірена точна проєкція. Не змінювати доменні аксіоми заради зеленого тесту.


## Точка фіксації (заповнити лише після freeze)

| Поле | Значення |
|---|---|
| Candidate tag | `s0.42.1` |
| Candidate Git SHA (40 hex) | **UNSET** |
| Date/time UTC | **UNSET** |
| Contract source identity (Git commit) | **UNSET until candidate freeze** |
| Contract generation | **12.0** (`contracts/language-contract-12.lisp`; implementation completeness not asserted) |
| Rust toolchain | Rust `1.99.0` pinned in `rust-toolchain.toml` and release/CI workflows; native run on exact candidate SHA **UNVERIFIED** |
| Cargo.lock package/version parity | **UNVERIFIED until exact candidate tests** |
| CI run ID and immutable logs | **UNSET** |
| OS, CPU arch, container/runner image identifiers | **UNSET** |
| Owner release authorization | **UNSET** |
| Verdict | **NO-GO** |

## Мовна ратифікація ≠ виконуваний механізм

| Модель | Authority / задекларований рівень | Виконуваність / незалежний релізний свідок |
|---|---|---|
| D1–D11 | Ратифіковані резидентні ідентичності; виконання не випливає з ратифікації | **NOT VERIFIED ON CANDIDATE SHA** |
| D10 | Цілісний каталог 1024/1024 ратифіковано 2026-10-12 | Runtime/callability witnesses: **NOT VERIFIED**, не називати всі 1024 виконуваними |
| D12+ | Чинна числова драбина починається з D12 | Загальна реалізація та виконання: **NOT VERIFIED ON CANDIDATE SHA** |
| T5M (`.sens`) | Чинний типовий фізичний носій; Zig пакує точні слова, але не встановлює семантику | Оберненість усього виконуваного корпусу та незалежний SENS runtime parity: **PENDING** |
| Історичний T5 | Архівна provenance, не активний codec route | Не є дозволом на виконання чи свідком релізу |
| F3C (`.senc`) | Explicit tiny compact route | Exact-candidate byte-level roundtrip and corrupted-input refusal: **PENDING** |
| F3M (`.f3m`) | Bounded enumerative research | НЕ general-production release promise |

Authority: [CURRENT.md](CURRENT.md), [language-contract.lisp](language-contract.lisp), [проектна реальність](docs/project-reality-2026-10-12.uk.md).

## Core4 → D24+ — атомарний облік блокера, не дозвіл на неявні літерали

- **Підтверджений структурний зріз:** у `lib/core4.lisp` є 13 прямих числових аргументів D5/D6 математичних викликів і 1 seed `length-onto` (`lib/core4.lisp:188,193`). **14 — не число всіх непрямих залежностей**, не число мігрованих значень і не сертифікат виконання.
- **Пінований exact-multiset:** `tests/data/core4-d24-direct-operand-baseline.json`, ключ = клас / доменний код голови / номер аргументу / числовий source token. Перевірка `scripts/check-core4-d24-migration.py --self-test` та `--check` у двох основних Core CI; зміна source + леджер має бути синхронною після незалежних свідків.
- **Жодного вигаданого дозволу:** цей облік не конвертує `0`, `1`, `#d10` чи `2` в D24, не змінює reader, FASL, фізичний T5 чи ратифіковані закони. Виконувана міграція лишається **BLOCKED**, доки існує підтверджений безлітеральний механізм явного D24 object construction та проходять runtime parity tests.
- **Стан виконання:** структурний облік незалежно перераховано за актуальним файлом: 14/14 ключів збігаються; `cargo test` і Python `--self-test` на GitHub runner ще **UNVERIFIED**. Не підміняти читання джерела пройденими тестами.
### Безлітеральні виконувані кандидати для Lisp-owned Core4

У `crates/sens/tests/math_domain_exclusivity.rs` додані **не запущені на підтвердженому CI SHA** Lisp-owned позитивні/негативні тести майбутньої міграції без нової арифметичної граматики:

- `lisp_owned_d24_length_fold_uses_ratified_d6_add1_without_number_literals` — D3/D4 рекурсія, `001110` D6 ADD1 замість `(01010 acc 1)`, seed як точно кваліфікований D24 Value; перевіряє 0–9 елементів, D24→D48 carry та відмову для legacy Rational(0).
- `lisp_owned_d24_nth_uses_d3_identity_and_d6_sub1_without_number_literals` — D3 `101` EQ з явно кваліфікованим нулем і D6 `001111` SUB1 замість `(01011 i 1)`; індекси 0–2 та відмова для бездоменного індексу.

**Захист точності аудиту:** `scripts/check-core4-d24-migration.py` тепер пропускає вкладені дані в явних `D3 QUOTE`/`quote`/історичній W8 QUOTE, щоб не рахувати інертний код виконуваною арифметикою. Самотести мають негативні приклади всіх трьох форм. Незалежний структурний підрахунок на актуальному `lib/core4.lisp` лишається **14/14**, без drift; обидва вбудовані Lisp SOURCE-фрагменти нових Rust-свідків мають збалансовані дужки. Це **не** Rust/Python CI PASS; скорочена апострофна quote-поверхня й непрямі числові виклики не входять у вузьку область аудиту.

**Умовне приймання, не автоматична міграція:** тести передають D24(0)/D24(1) через explicit `Environment::define` у proof session. Вони **не** дають нового SENS source-literal/T5/FASL формату й **не** міняють `lib/core4.lisp`/збережений `.fasl`. Core4 `length` досі викликає `length-onto` із бездоменним `0`; для зміни canonical source потрібні легітимний D24 seed mechanism, регенерація FASL, чинний exact-SHA Core CI та негативні свідки. Реліз **NO-GO**.
### Полімовний демонтаж старого восьмибітного runtime identity — поточний зріз

- ВИДАЛЕНО з активного дерева `scripts/sid-binary-identity-guard.sh` (`e397a5b`); у головному pipeline його замінено на `scripts/check-domain-ladder-identity.py`, також додано до Core/Hosted CI.
- Python `research-2077-binary-word-law.py` використовує явний `DomainCoordinate(width,payload)` замість восьмибітних `to_sens8/from_sens8`. Історичне статичне читання GitHub (зріз 12.10.2026) наводило **2/4/8/16/32/64/126/256/512/1024** рядків без дубльованих координат: `126` належить **історичному D7 v1 (126/128)**, а не чинному D7. За [CURRENT.md](CURRENT.md) і Contract 11.9 сучасна точнодоменна драбина D1–D10 має **2/4/8/16/32/64/128/256/512/1024** ратифікованих координат; **D7 v2 = 128/128**. Це облік резидентів, не доказ callable/runtime/T5 admission, і статичний перегляд не є CI PASS.
- **Історична міграційна provenance, не чинний D8 release gate:** у старому CLI/host фізичне `10101000` означало INVOKE, тоді як сучасна координата D8:`10101000` означає ROUND. Це **різні семантичні ідентичності** попри однакові вісім бітів. Архівні позначки `MECHANISM-HOLD` / `current_target=null` не дозволяють механічно переприсвоїти історичний код чинному D8, але й **не створюють глобального HOLD або нормативної ретро-колізійної перевірки**. Чинний D8 уперше ратифіковано 06.10.2026 ([#3960](https://github.com/juv4uk/sens/issues/3960)); залишаються обов'язковими незалежні сучасні exact-width/identity, D8↔D9, T5/D2 та нативні SENS-свідки. Історичну інформацію збережено лише для provenance.
- Інші чинні AST/evaluator/codec/CLI та Lisp/міграційні шляхи ще містять стару compatibility-реалізацію. Точний статус і конкретні файли — `docs/migration/domain-ladder-cutover-2026-10-12.uk.md`. **Повне видалення ще НЕ завершене**, а `cargo test`, незалежні source→T5 свідки та full release CI на одному SHA лишаються **UNVERIFIED**; реліз **NO-GO**.

## D10: наявні докази — чесний розподіл по рівнях

Поелементний аудит [усіх 1024 D10 записів](docs/research/D10-PROOF-COVERAGE-AUDIT-20261012.uk.md) (pinned Git blob `7e6acb2531308ae5f63600d4e0042111cc3ec59c`) підтверджує:

- **256/256** селекторів мають конструктивну алгебраїчну перевірку на моделі повного дерева пар і 256 попарно різних адрес; усі їхні координати й батьківські зв'язки збігаються з поточним D10/D9. Це **математичний**, а не T5/runtime доказ.
- **768** інших заповнених D10 координат не означають 768 виконаних функцій. **720** рядків мають `provenance`, **376** — позитивні та негативні описи/приклади; **349** явно очікують незалежності свідка.
- У **326** рядках поле `independent_oracle` прямо не заявляє SENS PASS; у v18 **0** явних `independent_oracle=VERIFIED` / `F2 PASS` і **0** `physical_t5_authorized=true`. Водночас спеціалізовані математичні та донорські оракули реально існують; їхні *тисячі test cases* не слід плутати з тисячами D10 residents.
- Тому **«800 функцій D10 доведені як фізично виконувані»** на цьому SHA не підтверджено. Наступний крок — прив'язати існуючі незалежні джерела до кожного stable_id і вести F1, F2 donor, F2 SENS, F3 global, F4 T5 окремо.

Це уточнення **не скасовує** whole-domain ратифікацію 1024/1024 і не переводить статус релізу з NO-GO у GO.

## Обов'язкові спостережувані ворота на тому самому SHA

| Gate | Evidence to attach | Verdict |
|---|---|---|
| `cargo test --locked --workspace` | URL, runner, SHA, raw log | UNKNOWN |
| `cargo clippy --locked --workspace --all-targets -- -D warnings` | URL, runner, SHA | UNKNOWN |
| Release package/tag version alignment | Seven Cargo crates and `Cargo.lock`, `guix.scm`, `packaging/install.sh`; current line is `0.42.1` / `s0.42.1`; native gates are `release_parity` + `release_tag_guard` | **UNKNOWN until both pass on a frozen candidate SHA** |
| D1–D9 exact-width / COND/ATOM/EQ negative controls | Source+binary/oracle parity & run URL | UNKNOWN |
| D1–D10 binary-word ≠ Number; D12+-only mathematical operands | `crates/sens/tests/math_domain_exclusivity.rs` (D1–D9 operands, D10 unadmitted call heads, D12+ admission negatives); `eval::d6_arithmetic::tests` (D12 signed boundaries/widening plus D24→D48 ADD1 carry); `scripts/check-numeric-domain-ratification.py --self-test`; exact candidate SHA and Core/Hosted CI logs | **UNKNOWN** — focused Rust execution not verified on candidate SHA |
| Core4 exact-domain FASL and bootstrap-dependent arithmetic | `core4_bootstrap_cache_tests::valid_fasl_path_selects_core4_and_evaluates_current_core`; matching-hash wrong-reader negative witness; migrate `lib/core4.lisp` LENGTH accumulator (`acc + 1`, seed `0`) using explicitly admitted D24+ objects | **BLOCKED** — legacy literals lack D24+ domain admission |
| D10 owner-ratification metadata and proof limits | Owner-ratification source plus negative callable witnesses; no generated digest receipt | UNKNOWN |
| T5 and F3C roundtrip + corrupted input refusal | Physical byte golden fixtures | UNKNOWN |
| All release-scope `.lisp` ↔ `.sens` ↔ extensionless triples | Full corpus inventory + independent Ukrainian oracle ledger | UNKNOWN |
| T5 authority, quantity witness, exact-width blockers | [#5406](https://github.com/juv4uk/sens/issues/5406), [#5408](https://github.com/juv4uk/sens/issues/5408), [#2170](https://github.com/juv4uk/sens/issues/2170) | OPEN |
| Filesystem runtime and exact-domain admission | Earlier [#5603](https://github.com/juv4uk/sens/issues/5603) / [run 38176345658](https://github.com/juv4uk/sens/actions/runs/38176345658): `content_store` 22/24 tests failed. Newer visible [run 38228581929](https://github.com/juv4uk/sens/actions/runs/38228581929) still fails overall: filesystem macro/alist path-bound witnesses, obsolete COND/ATOM/EQ scanner regressions, time-source witnesses and stale core-logic audit are red; its `content-store integration` step is green. | BLOCKED; rerun after fixes |
| `release-preflight.yml` + mandatory hosted/native jobs | Exact SHA, all required checks | UNKNOWN |
| Linux/Windows/macOS CLI + Windows MSI | Platform-specific install/smoke results | UNKNOWN |
| Release asset bytes and independent clean replay | `release-publish.yml` stages the built assets, downloads the draft release independently, compares file sets and every file with `cmp`; no SHA256SUMS generation | IMPLEMENTED ON MAIN; **NOT RUN / UNKNOWN** |
| Clean release publication (no incomplete visible release) | Single `release-publish` job; exact current-main Git commit + explicit owner GO; five CLI/MSI assets; byte-equal draft replay via `cmp`; no Python/JSON/JS publisher or digest manifest | PENDING new workflow CI and exact-candidate replay |

**GO iff** всі потрібні gates на **одному** Git SHA позитивні, усі обіцяні платформи й файли перевірені, без жодного невирішеного `UNKNOWN/BLOCKED/FAIL`. Не підміняти невиконані platform gates успішними локальними тестами.

## Бенчмарки: модель доказів, не рекламні коефіцієнти

У релізному пакунку для **кожного** твердження про швидкість/розмір потрібні: workload та вхідні дані; точний source/runner SHA; точна версія toolchain; warm/cold; машина й фонове навантаження; raw виміри; результат parity; порівняльний engine і версія; спосіб розрахунку медіани/довірчих меж.

- [Звіт поточного project reality](docs/project-reality-2026-10-12.uk.md) містить чітко обмежені доказові приклади; це **не** еквівалент бенчмарку всього випуску.
- [`docs/benchmarks.md`](docs/benchmarks.md) — історичний my-lisp, серпень/вересень 2026, не Contract 11.9 і не новий exact-SHA бенчмарк.
- Риторика «60× старт» або «99,9%» **не переходить** у релізний факт без контрольованого актуального відтворення.

## Журнал рішення

- **2026-10-12:** створено шаблон доказового пакунка; жоден candidate SHA не заморожено, жодного підпису чи GO не засвідчено.
- Після кожної зміни релізних байтів: попередній verdict кандидата недійсний; новий SHA → повний повтор перевірок.

Документи: [release scope](RELEASE.md), [операційний runbook](docs/release-readiness-contract-11-9-2026-10-12.uk.md), [#4198 exact-SHA cut](https://github.com/juv4uk/sens/issues/4198).

## Операційний журнал підготовки — 2026-10-12 (M0 / Cargo release)

Це **доказ вузьких виконаних задач**, не сертифікат `l0.42.0`; `candidate SHA = UNSET`, випуск залишається **NO-GO**.

| Робота | Факт | Межа доказу |
|---|---|---|
| M0 physical-T5 producer/consumer manifest | Закрито drift `benchmarks/physical-binary-performance/test_word_projection.py`; [атомарний коміт 4b9adf8](https://github.com/juv4uk/sens/commit/4b9adf824ccfa71868820eee224745232f279e03), наступні синхронізації agentів; [зелений CI 38232293478](https://github.com/juv4uk/sens/actions/runs/38232293478) на `ef96318e78e4dd67a0af140ac5918eceaf43421e` | Успішний **M0 inventory**, не semantic/oracle admission і не випуск на цьому SHA |
| `release.yml` Cargo dependency resolution | Сім додаткових `cargo test/build` команд отримали `--locked`; [коміт 7c0dffb](https://github.com/juv4uk/sens/commit/7c0dffbb7653ce759441c416923527d447dfa199) | Синтаксичний аудит у `main` підтверджує `--locked` для команд Cargo; **реальний tagged asset build ще не проводився** |
| `release-preflight.yml` | Додано `push`-тригер для релізних змін `main`, focused `clippy --locked`; [коміт 80b6f6d](https://github.com/juv4uk/sens/commit/80b6f6d8c5d9fe8d6832e7ca91bf7425d515e12e) | Конфігурація збережена; **успішного workflow run не зафіксовано** під час цього аудиту, тому gate залишається UNKNOWN |
| Інші обов'язкові CI | Latest checked `Hosted CI`, native vertical smoke, T5 file-authority на сусідніх HEAD ще мають FAIL | Не переносити чужий/старий verdict на майбутній release candidate; **NO-GO** |

Усі наступні докази замінюють лише відповідні UNKNOWN/FAIL після перевірки **одного** `main@<40-hex SHA>`. Release-публікація лишається з незалежним явним owner-GO та strict triplet admission.

## Latest exact-head action sample — 2026-10-12, not a release certificate

The last inspected full workflow batch is tied to `main@`[`e2d6f798215434f5127bab43e6c8cb40de90d643`](https://github.com/juv4uk/sens/commit/e2d6f798215434f5127bab43e6c8cb40de90d643). It is a diagnostic snapshot only; subsequent `main` commits invalidate its SHA as a release candidate.

| Workflow | Result on that SHA | Observed failure / boundary |
|---|---|---|
| [README current SENS owner and triplet contract](https://github.com/juv4uk/sens/actions/runs/38234492757) | **FAIL** | Six README contract unittests passed, then invoking `sens scripts/verify-repo.lisp` failed at line 8 because the `str+` form was reported as not callable (`#q2:1011/1`). This is an executable language/runtime failure, not a reason to bypass the guard. |
| [Vertical Day immutable L0 and native smoke](https://github.com/juv4uk/sens/actions/runs/38234492564) | **FAIL** | `bounded_eq_cond_native_execution_follows_generated_cmp_jnz_branches` fails with a non-callable numeric-carrier expression at span `8830..8853`. |
| [Vertical Day non-cancelling smoke](https://github.com/juv4uk/sens/actions/runs/38234492701) | **FAIL** | `native_pair_car_cdr_match_the_interpreter_reference_witness` fails during Lisp-owned CONS+CAR admission at span `8830..8853`; the explicit unadmitted-UD2 rejection test passes. |
| [Hosted CI](https://github.com/juv4uk/sens/actions/runs/38234492771) and [physical T5 file-authority oracle](https://github.com/juv4uk/sens/actions/runs/38234492469) | **IN PROGRESS at last observation** | No final result on this SHA was recorded in this audit. |
| [Binary executable T5 end-to-end](https://github.com/juv4uk/sens/actions/runs/38234492752) and [Hosted runner routing policy](https://github.com/juv4uk/sens/actions/runs/38234492474) | **PASS** | Narrow successes only; they do not override red native/runtime gates. |

Current `main` has moved beyond this diagnostic SHA; the current ref observed during this update is `c55e2c17cd2681702ec69659b2fa4406bbec3a99`. No set of mandatory CI proofs has yet been attached to that newer exact SHA in this audit. Consequently, do not transfer a green or red verdict from `e2d6f79` to the current head. Keep candidate SHA unset, do not create `l0.42.0`, and rerun all mandatory workflows on one frozen current SHA before any GO review.

## Version and compiler preparation update

- All seven canonical Cargo crate versions and their `Cargo.lock` records are now `0.42.0`.
- `scripts/release.lisp`, `guix.scm`, and active `packaging/install.sh` asset/version references now target `0.42.0` / `l0.42.0`.
- Rust compiler/toolchain is pinned to `1.99.0` in `rust-toolchain.toml` and explicit release/CI workflow configuration. The hosted runner confirmed `rustc 1.99.0 (b940084d7 2026-09-28)` in the diagnostic batch.
- Exact Rust distribution / runner-image digests and the final candidate's successful `release_parity`, installer tests, full workspace tests/Clippy, independent T5-oracle admission and platform asset replay remain **UNKNOWN**, not PASS.

## Newest completed GitHub Actions snapshot — 2026-10-12

The newest complete diagnostic batch currently observed for main is SHA `b1a43d41402794f511426bd3f4e733b158f53866`. This is a **diagnostic snapshot only**, not a release-candidate freeze; any later commit invalidates its verdict for release use.

| Gate on this exact SHA | Result | Evidence |
|---|---|---|
| Hosted runner routing policy | **PASS** | [run 38235487536](https://github.com/juv4uk/sens/actions/runs/38235487536) |
| Triple projection gate | **PASS** | [run 38235487342](https://github.com/juv4uk/sens/actions/runs/38235487342) |
| D10 finite transducer witness | **PASS** | [run 38235487529](https://github.com/juv4uk/sens/actions/runs/38235487529) |
| Binary executable T5 end-to-end | **PASS** | [run 38235487442](https://github.com/juv4uk/sens/actions/runs/38235487442) |
| Physical binary SENS CLI smoke | **PASS** | [run 38235487498](https://github.com/juv4uk/sens/actions/runs/38235487498) |
| T5 migration inventory (M0) | **PASS** | [run 38235487504](https://github.com/juv4uk/sens/actions/runs/38235487504) |
| T5 program syntax audit | **PASS** | [run 38235487485](https://github.com/juv4uk/sens/actions/runs/38235487485) |
| Hosted CI | **FAIL** | [run 38235487411](https://github.com/juv4uk/sens/actions/runs/38235487411): obsolete COND/ATOM/EQ scanner regression, migrated time-source witnesses and stale Core-logic audit failed. **The new release publication/pre-tag structural regression and release asset verifier controls passed inside this overall red job.** |
| Vertical Day non-cancelling native smoke | **FAIL** | [run 38235487508](https://github.com/juv4uk/sens/actions/runs/38235487508): `native_pair_car_cdr_match_the_interpreter_reference_witness` still reports a non-callable numeric carrier `#q2:110100100000000001000010010/1` at span `8830..8853`. The explicit unadmitted-UD2 rejection test passes; this does not establish positive native parity. |
| Vertical Day immutable L0/native smoke | **FAIL** | [run 38235487599](https://github.com/juv4uk/sens/actions/runs/38235487599): `bounded_eq_cond_native_execution_follows_generated_cmp_jnz_branches` fails at the same non-callable carrier/span. |
| Physical T5 file-authority oracle | **BLOCKED** | [run 38235487525](https://github.com/juv4uk/sens/actions/runs/38235487525): migration reports `UNADMITTED_TEXT7_CONTEXT 'binary'` in quoted data; no T5 oracle verdict. |

**Decision from this snapshot: NO-GO.** These green rows establish only the named narrow properties. The native positive witnesses, source/runtime admission, and whole-corpus independent T5 oracle still block release. The mandatory full Release Preflight workflow also has **no observed run/result** in this audit; do not replace that absence with the green rows above. Re-run every mandatory gate on a newly frozen single SHA, then write that new candidate SHA only after owner review.


## Незалежний контроль GitHub Actions перед публікацією (2026-10-12)

> **Реалізовано контроль, але не сертифіковано GO.** Наявність захисного коду — не результат виконання всіх обов'язкових job.

- `scripts/verify_release_ci.py` звертається до живих GitHub check-runs для **точного 40-символьного Git SHA**. Потрібні актуальні `completed/success` з GitHub Actions; старий зелений rerun не може перекрити новий червоний або очікуваний запуск. Недоступний API та відсутній check — **BLOCK**, не `PASS`.
- `.github/workflows/release.yml` перевіряє ці незалежні результати **перед створенням DRAFT** та повторно **після побайтового replay, безпосередньо перед публікацією**. Обов'язкові назви: `portable critical gates`, `oracle-native-smoke`, `Lisp-owned pair to real CPU, with fail-closed rejection`, `Physical SENS T5 file-admission oracle`, `triple`, `physical T5 to D2 D3 D4 D7 runtime`, `physical-binary-cli`, `d2-grammar-audit`, `focused release preflight`.
- `packaging/tests/test_release_ci_check_runs.py`: 13 локальних тестів (із них 11 сценаріїв позитивних/негативних check-run даних) і окрема перевірка порядку workflow; синтетичні fixtures **не** заміняють реальний Hosted/Native proof.
- `focused release preflight` має бути виконаний на candidate SHA (за потреби через існуючий `workflow_dispatch`, якщо `paths` не запустили workflow автоматично). Обов'язковий full-workspace тест/Clippy на тому самому SHA і незалежні мовні докази залишаються окремими воротами.
- Інтеграційні коміти: [`8aabc6df`](https://github.com/juv4uk/sens/commit/8aabc6df6e12b1f1003aaa266865ea0dac79f958), [`a864dce5`](https://github.com/juv4uk/sens/commit/a864dce59105e4c597773c9851fb09bc8cd73c38), [`5a78cd68`](https://github.com/juv4uk/sens/commit/5a78cd68cabfb769e0556845cd4c3ddb4c5e5825). Реальний `GO` ще не отримано; `l0.42.0` не теговано.

## Exact-head Contract 11.9 / D24+ impact — 2026-10-12

The completed diagnostic batch for `main@9612f4d0f27d479b5779e47f90be896285466b57` records a deeper integration blocker: the current Core math law now requires explicit D24+ qualified numeric values and rejects unqualified Numbers and D1–D10 binary words as arithmetic operands. The new negative witness `crates/sens/tests/math_domain_exclusivity.rs` is an active discovered inventory row. This is a contract boundary; do not “fix” it by implicit promotion or by weakening the negative controls.

| Required gate | Result on `9612f4d0f27d479b5779e47f90be896285466b57` | Evidence |
|---|---|---|
| Hosted runner routing | **PASS** | [run 38253883643](https://github.com/juv4uk/sens/actions/runs/38253883643) |
| Triple projection | **PASS** | [run 38253883126](https://github.com/juv4uk/sens/actions/runs/38253883126) |
| Binary executable T5 | **PASS** | [run 38253883558](https://github.com/juv4uk/sens/actions/runs/38253883558) |
| Binary-only SENS execution | **PASS** | [run 38253883385](https://github.com/juv4uk/sens/actions/runs/38253883385) |
| Physical binary CLI smoke | **PASS** | [run 38253883100](https://github.com/juv4uk/sens/actions/runs/38253883100) |
| T5 program syntax audit | **PASS** | [run 38253883105](https://github.com/juv4uk/sens/actions/runs/38253883105) |
| D10 finite-transducer witness | **PASS** | [run 38253883131](https://github.com/juv4uk/sens/actions/runs/38253883131) |
| Nano-SENS source-closure audit | **PASS** | [run 38253883581](https://github.com/juv4uk/sens/actions/runs/38253883581) |
| EQ/COND Rust oracle migration | **PASS** | [run 38253883751](https://github.com/juv4uk/sens/actions/runs/38253883751) |
| Performance scoreboard | **PASS** | [run 38253882963](https://github.com/juv4uk/sens/actions/runs/38253882963); this is not release correctness evidence |
| Hosted CI | **FAIL** | [run 38253883681](https://github.com/juv4uk/sens/actions/runs/38253883681): clock/time witnesses fail under the explicit D24+ operand law; the strict legacy D3 scanner still reports many live-source findings (799 in this scan), and `test_island_math_evidence_guard_uses_only_d1_cond_tests` finds 60 legacy three-field COND clauses in `scripts/check-island-math-evidence.lisp`. The independent release-preflight registration check reports workflow state `disabled_manually`. |
| Native Vertical Day | **FAIL** | [run 38253883107](https://github.com/juv4uk/sens/actions/runs/38253883107) and [run 38253883687](https://github.com/juv4uk/sens/actions/runs/38253883687): the positive native CONS/CAR and EQ/COND witnesses fail because machine lowering/encoding still performs math with unqualified numbers or D1–D10 bit words, rejected with `math requires explicit D24+ operands`. The unadmitted-UD2 negative witness is separate and passing; it does not establish positive execution parity. |
| Independent physical SENS authority oracle | **BLOCKED** | [run 38253883767](https://github.com/juv4uk/sens/actions/runs/38253883767): quoted `binary` is unadmitted Text7 context; no migration verdict, no whole-corpus T5 oracle PASS. |
| T5 inventory M0 | **PASS** | The discovered-path set and classifications were reconciled in the manifest; [run 38254932249](https://github.com/juv4uk/sens/actions/runs/38254932249) on `main@cd393572fec20a5ebbbb052143887ff9dc39e902` reports `OK: manifest == live registry (451 rows, base_sha=cd393572fec20a5ebbbb052143887ff9dc39e902)`. Earlier drift remains documented as history; this PASS is only for the named SHA, and subsequent source-file changes require another check. |

### Unresolved source-law dependency

The live `lib/time.lisp` calendar transform and machine encoding/lowering still rely on decimal/unqualified numbers. Current numeric policy says decimal-literal lowering is not ratified and forbids implicit D1–D10/unqualified-number arithmetic. The necessary design choice is therefore **not** a Rust cast: an owner-ratified source/reader mechanism must create domain-qualified D24+ constants and typed raw clock observations, or those functions remain blocked. Until that mechanism exists and independent behavior parity passes, the old clock result cannot be certified under Contract 11.9.

The release-preflight workflow is present in source but its GitHub Actions registration check reports `disabled_manually`; no successful run of the mandatory Release Preflight is present in this audit. Re-enabling the workflow requires repository Actions administration/API write access not available in this integration path. Treat this as an external GO blocker, not as permission to remove the check.

**Decision remains NO-GO.** Successful T5 codec/projection/D10 tests are limited proofs and do not override red Hosted CI, native runtime, inventory, or physical-oracle evidence. This SHA is a diagnostic ancestor, not a frozen candidate; all mandatory gates must rerun and be green on one exact candidate SHA after these blockers are resolved.

## Current post-reconciliation release snapshot — `f110f9fa3364ca3444579edc5d77186d5f8ae627`

This is the latest fully observed release-related batch on 2026-10-12. It is a **diagnostic integration SHA**, not a frozen release candidate.

| Exact-SHA gate | Result | Evidence / interpretation |
|---|---|---|
| Hosted runner routing | **PASS** | [run 38255095223](https://github.com/juv4uk/sens/actions/runs/38255095223) |
| T5 migration inventory M0 | **PASS** | [run 38255095019](https://github.com/juv4uk/sens/actions/runs/38255095019); 451 sorted rows and live-registry match at this SHA. |
| Binary executable T5 | **PASS** | [run 38255094961](https://github.com/juv4uk/sens/actions/runs/38255094961) |
| Physical binary CLI smoke | **PASS** | [run 38255095004](https://github.com/juv4uk/sens/actions/runs/38255095004) |
| D10 finite-transducer witness | **PASS** | [run 38255095093](https://github.com/juv4uk/sens/actions/runs/38255095093); this is a bounded witness, not universal executable coverage. |
| Triple projection | **PASS** | [run 38255095074](https://github.com/juv4uk/sens/actions/runs/38255095074) |
| T5 program syntax audit | **PASS** | [run 38255095208](https://github.com/juv4uk/sens/actions/runs/38255095208) |
| Hosted CI | **FAIL** | [run 38255095083](https://github.com/juv4uk/sens/actions/runs/38255095083): migrated user demos, legacy D6 MAP, D9 AVL, filesystem/alist, content-store, time-source, and stale Core audit have red steps; release asset/negative controls and publication structure tests are green inside the same overall red job. GitHub API registration check says Release Preflight is `disabled_manually`. |
| Vertical Day native parity | **FAIL** | [non-cancelling run 38255094957](https://github.com/juv4uk/sens/actions/runs/38255094957) fails `native_pair_car_cdr_match_the_interpreter_reference_witness`; [immutable run 38255094842](https://github.com/juv4uk/sens/actions/runs/38255094842) fails the native CPU step. The current numeric law correctly requires explicit D24+ operands; existing machine encoding/lowering still passes unqualified numbers or D1–D10 words into arithmetic. Invalid machine-form rejection passes independently. |
| Physical SENS file-authority oracle | **BLOCKED** | [run 38255095027](https://github.com/juv4uk/sens/actions/runs/38255095027): assembled Lisp oracle migration fails before complete T5 encode/execute/attestation; no whole-corpus oracle verdict. |

### Exact decision and next dependencies

**NO-GO remains in force.** M0 inventory drift has been repaired and passes on this SHA; this closes the inventory defect only. The semantic/source gap remains: `lib/time.lisp` and machine lowering need a ratified way to obtain explicit D24+ values (including literal/constant and raw clock-observation handling). Do not invent implicit promotions or relax negative witnesses. Separately, repository administration must re-enable the manually disabled Release Preflight workflow so the mandatory full workspace test + Clippy gate can run; repo content edits alone did not change that GitHub Actions setting.

The `l0.42.0` ref and GitHub Release were both absent at last check. This assistant did not set owner GO variables, create a tag, or publish assets. Freeze a future candidate only after the source-law and runtime/oracle blockers are resolved, Release Preflight is enabled, and all required gates are green for one exact SHA.


## Latest exact-head diagnostic — 2026-10-12

This is an immutable **diagnostic snapshot**, not a release candidate. The checks below were run against exact `main@2d642bf43bd88d7502d175b23d1b866e7dbbc775`; any later commit invalidates it as a candidate. `Candidate SHA` remains **UNSET** and verdict remains **NO-GO**.

| Gate on exact SHA | Result | Evidence / boundary |
|---|---|---|
| Physical binary SENS CLI smoke | **PASS** | [run 38262026489](https://github.com/juv4uk/sens/actions/runs/38262026489) — narrow CLI path only |
| Physical T5 to D2/D3/D4/D7 runtime | **PASS** | [run 38262026420](https://github.com/juv4uk/sens/actions/runs/38262026420) — bounded witness, not whole-corpus admission |
| Triple projection gate | **PASS** | [run 38262026521](https://github.com/juv4uk/sens/actions/runs/38262026521) |
| New D3 regression guard | **PASS** | [run 38262026522](https://github.com/juv4uk/sens/actions/runs/38262026522); no new violations in its bounded scope |
| D3 generator regressions | **PASS** | [Hosted CI run 38262026511](https://github.com/juv4uk/sens/actions/runs/38262026511), including exact two-field signature/evaluator generator tests and negative mutations |
| Live-source D3 strict audit | **FAIL** | Same [Hosted CI run 38262026511](https://github.com/juv4uk/sens/actions/runs/38262026511): 144 live Lisp files, 498 findings, **0 scan errors**. This follows the targeted generator repair; it does not certify full D3 migration. |
| Portable critical/runtime gates | **FAIL** | [run 38262026511](https://github.com/juv4uk/sens/actions/runs/38262026511): migrated demos, D6 MAP length, D9 map facade, filesystem/content-store, and time-source witnesses fail with `math requires explicit D24+ operands; D1-D10 bit words and unqualified numbers are not arithmetic values`. Do not add implicit promotions or weaken fail-closed controls. |
| Native CPU positive witness | **FAIL** | [run 38262026526](https://github.com/juv4uk/sens/actions/runs/38262026526): native CPU mechanism witness fails; negative invalid-machine rejection is separate evidence and does not establish positive parity. |
| Physical T5 whole-file authority oracle | **FAIL / NO VERDICT** | [run 38262026507](https://github.com/juv4uk/sens/actions/runs/38262026507): whole assembled oracle migration does not complete; no whole-corpus physical T5 parity claim. |
| Release Preflight workflow registration | **BLOCKED** | The registration guard is fail-closed; workflow is still `disabled_manually`. Requires repository owner/admin to re-enable in GitHub Actions, then run it on a frozen exact SHA. |

A targeted D3 defect found in this batch—an extra closing parenthesis in `scripts/generate-rust-function-signatures.lisp`—was removed in [commit 2d642bf](https://github.com/juv4uk/sens/commit/2d642bf43bd88d7502d175b23d1b866e7dbbc775). Its scanner regression test and new-regression gate are green on that SHA. The strict audit still has 498 findings, so no claim of full migration is made.

**Decision: NO-GO.** Do not create `l0.42.0`, set owner GO variables, or publish assets. The owner/admin action needed to re-enable Release Preflight is an external repository setting; no bypass was used.
