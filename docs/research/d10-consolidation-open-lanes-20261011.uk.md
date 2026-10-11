# Інвентар D10 для консолідації — 11.10.2026

> Це **знімок за назвою** відкритих issue, відкритих PR та наявних Git-гілок з `D10` у назві. Це **не** твердження, що кожна гілка містить новий закон, є незлитою або має чинні докази. Історичні закриті PR / гілки без D10 в імені ще потребують наскрізного audit. Не використовувати для автоматичного видалення чи ратифікації.

**База перевірки:** `main` після директиви `1a10086d234cfa47d1f693a4a20d28074048a9bf`. Джерела: GitHub REST Search Issues (`in:title D10 is:issue is:open`), paginated open Pull Requests, GitHub Branch Search (`d10`).

## Підсумок

- D10 у назві відкритого issue: **48**.
- Git branches із `d10` у назві: **272** (пошук вичерпано).
- Відкриті PR з `d10` у назві PR або source branch: **3** (перевірено 233 відкритих PR за всіма доступними сторінками).
- Гілки цього пошуку без відповідного відкритого D10-PR: **269** (не обов'язково unmerged).
- `knowledge/d10-proposal-ledger.tsv`: **130** pending-review пропозицій на snapshot 11.10.2026. `main` D10 inventory: **653/1024 selected, 0 ratified** перед #5600.
- Групи гілок: `research` 188, `fix` 36, `replay` 19, `integration` 12, `integrate` 8, `archive` 2, `audit` 2, `coord` 1, `виправлення` 1, `proposal` 1, `repair` 1, `test` 1.

## Відкриті D10-PR і первинний вердикт

| PR | Base | Попередній статус |
|---|---|---|
| [#5600](https://github.com/juv4uk/sens/pull/5600) — D10: integrate 45 existing research laws 653→698 in one main-targeted intake | `main` | BLOCKED: GitHub `dirty`, red CI; 653→698 лише пропозиція |
| [#5310](https://github.com/juv4uk/sens/pull/5310) — виправлення: розділити історичне та чинне походження D10 Yantra | `main` | BLOCKED: `mergeable=false`; необхідне порівняння із чинним main |
| [#5306](https://github.com/juv4uk/sens/pull/5306) — Виправити джерельний хеш D10 для гілки стабілізації | `fix/quarantine-legacy-quantity-gate-20261010` | НЕ ДО MAIN: допоміжний base; потрібна перевірка переносу |

> PR статуси нижче — audit-черга, не санкція на merge. Для спірної D10 семантики потрібен власницький вердикт `ЗЛИТИ / ДУБЛЬ / ВІДХИЛИТИ`. Уся вибрана без ратифікації D10 семантика лишається research, а не Core.

## Відкриті issue з D10 у назві (всього 48)

| Issue | Назва | Облік |
|---|---|---|
| [#4012](https://github.com/juv4uk/sens/issues/4012) | [P0][D10-FILL-V1] Start dense 10-bit Core research after full D9 inventory | Потрібна змістова перевірка проти ledger/main |
| [#4013](https://github.com/juv4uk/sens/issues/4013) | [P0][D10-INVENTORY-1] Fill remaining 768 D10 meanings after selector seed | Потрібна змістова перевірка проти ledger/main |
| [#4016](https://github.com/juv4uk/sens/issues/4016) | [P0][D10-RECOVERY-1] Re-review surviving D9 HOLD rows against ratified D1-D9 | Потрібна змістова перевірка проти ledger/main |
| [#4026](https://github.com/juv4uk/sens/issues/4026) | [P0][D10-LIBRARY-HARVEST-1] Add 39 language-owned protocol/data laws from canonical Lisp libraries | Потрібна змістова перевірка проти ledger/main |
| [#4028](https://github.com/juv4uk/sens/issues/4028) | [P0][D10-FORWARD-HARVEST-1] Add 26 rule-matching and JTMS semantics | Потрібна змістова перевірка проти ledger/main |
| [#4030](https://github.com/juv4uk/sens/issues/4030) | [P0][D10-KNOWLEDGE-HARVEST-1] Add 37 epistemic/knowledge/result protocol semantics | Потрібна змістова перевірка проти ledger/main |
| [#4033](https://github.com/juv4uk/sens/issues/4033) | [P0][ISLAND-OWNERSHIP-GATE-1] Reconcile D9/D10 Core residency with execution-island ownership | Потрібна змістова перевірка проти ledger/main |
| [#4039](https://github.com/juv4uk/sens/issues/4039) | [P0][D10-HISTORICAL-MACLISP-1] Recover 21 Core-owned MacLisp capabilities from the 1975 reference manual | Потрібна змістова перевірка проти ledger/main |
| [#4042](https://github.com/juv4uk/sens/issues/4042) | [P0][D10-HISTORICAL-MACLISP-2] Recover 12 reader/symbol/array semantics and classify modern projections | Потрібна змістова перевірка проти ledger/main |
| [#4045](https://github.com/juv4uk/sens/issues/4045) | [P0][D10-WSM-OS-LISP-OWNERSHIP-1] Split Core Lisp-machine laws from WSM OS-owned semantics | Потрібна змістова перевірка проти ledger/main |
| [#4047](https://github.com/juv4uk/sens/issues/4047) | [P0][D10-OWNERSHIP-CLEANUP-1] Remove 55 definite non-Core rows from unratified D10 | Потрібна змістова перевірка проти ledger/main |
| [#4061](https://github.com/juv4uk/sens/issues/4061) | [P0][D10-CROSSREPO-CONTROL-1] Harvest continuations, channels, type and sequence laws from Lisp donors | Потрібна змістова перевірка проти ledger/main |
| [#4071](https://github.com/juv4uk/sens/issues/4071) | [P0][D10-CROSSREPO-EARLY-LISP-1] Recover six missing Core semantics from early Lisp-family donors | Потрібна змістова перевірка проти ledger/main |
| [#4074](https://github.com/juv4uk/sens/issues/4074) | [P0][D10-CROSSREPO-LISP-KOANS-1] Recover 36 general Common Lisp semantics | Потрібна змістова перевірка проти ledger/main |
| [#4077](https://github.com/juv4uk/sens/issues/4077) | [P0][D10-CROSSREPO-GOLISP-PASCAL-1] Recover 22 portable language semantics | Потрібна змістова перевірка проти ledger/main |
| [#4085](https://github.com/juv4uk/sens/issues/4085) | [P0][D10-CROSSREPO-REMAINDER-1] Exhaust paip-lisp, Clojure-code and clojure-cookbook | Потрібна змістова перевірка проти ledger/main |
| [#4089](https://github.com/juv4uk/sens/issues/4089) | [P0][D10-CROSSREPO-PAIP-1] Recover 23 general language semantics from PAIP | Потрібна змістова перевірка проти ledger/main |
| [#4092](https://github.com/juv4uk/sens/issues/4092) | [P0][D10-OWNERSHIP-CLEANUP-2] Reclassify final 15 review-required rows outside Core | Потрібна змістова перевірка проти ledger/main |
| [#4162](https://github.com/juv4uk/sens/issues/4162) | [OWNER-CORRECTION][D10-SINGLE-STREAM] One 10-bit domain; all owner repos are semantic donors | Потрібна змістова перевірка проти ledger/main |
| [#4182](https://github.com/juv4uk/sens/issues/4182) | [P0][D10-ALL-REPO-DONOR-SWEEP-1] Exhaust all 87 owner repositories under single-stream rule | Потрібна змістова перевірка проти ledger/main |
| [#4299](https://github.com/juv4uk/sens/issues/4299) | [P0][D10-ALLREPO-CHESS-1] Review six owner chess/search donors for language-visible laws | Потрібна змістова перевірка проти ledger/main |
| [#4300](https://github.com/juv4uk/sens/issues/4300) | [P0][D10-ALLREPO-LINGUISTIC-1] Review remaining Ukrainian/Sanskrit/text donors | Потрібна змістова перевірка проти ledger/main |
| [#4301](https://github.com/juv4uk/sens/issues/4301) | [P0][D10-ALLREPO-DOMAIN-1] Review physical/science/application owner donors | Потрібна змістова перевірка проти ledger/main |
| [#4302](https://github.com/juv4uk/sens/issues/4302) | [P0][D10-ALLREPO-KNOWLEDGE-TOOLING-1] Review remaining knowledge/search/tooling donors | Потрібна змістова перевірка проти ledger/main |
| [#4463](https://github.com/juv4uk/sens/issues/4463) | [P0][D10-PROPOSAL-RULE] Необхідні функції пропонувати в D10 з provenance, не вигадувати локально | Потрібна змістова перевірка проти ledger/main |
| [#4840](https://github.com/juv4uk/sens/issues/4840) | [D10][HISTORICAL-RESIDUAL] Re-examine six D9 overflow laws absent by exact name from D1–D10 | Потрібна змістова перевірка проти ledger/main |
| [#4867](https://github.com/juv4uk/sens/issues/4867) | [P0][D10-GROWTH-GATE] Розв'язати історичні 625-only CI бар'єри для перевірюваного наповнення D10 | Потрібна змістова перевірка проти ledger/main |
| [#4872](https://github.com/juv4uk/sens/issues/4872) | [D10][ORACLE][629] Independent ANSI CL / R6RS witnesses for four selected research laws | Потрібна змістова перевірка проти ledger/main |
| [#4896](https://github.com/juv4uk/sens/issues/4896) | [D10][SYSTEMATIC-HARVEST] CLHS → CLOS MOP → SRFI: section-by-section evidence pipeline | Потрібна змістова перевірка проти ledger/main |
| [#4897](https://github.com/juv4uk/sens/issues/4897) | [D10][DONOR][CLHS] Systematic semantic audit: Conditions → Streams → Pathnames → Format | Потрібна змістова перевірка проти ledger/main |
| [#4898](https://github.com/juv4uk/sens/issues/4898) | [D10][DONOR][CLOS-MOP] Source-grade metaobject protocol family and executable oracle | Потрібна змістова перевірка проти ledger/main |
| [#4899](https://github.com/juv4uk/sens/issues/4899) | [D10][DONOR][SRFI] Enumerate finalized Scheme SRFIs with semantic tests | Потрібна змістова перевірка проти ledger/main |
| [#4900](https://github.com/juv4uk/sens/issues/4900) | [D10][LEDGER-BACKFILL] Reconcile five 625→630 historical selections without invented evidence | Потрібна змістова перевірка проти ledger/main |
| [#4908](https://github.com/juv4uk/sens/issues/4908) | [D10][SOURCE CLAIM] Universal roots from chess, epistemic proofs, live Lisp and Lisp-machine evidence | Потрібна змістова перевірка проти ledger/main |
| [#4913](https://github.com/juv4uk/sens/issues/4913) | D10 donor oracle tests for NIST and GNU Radio candidates | Потрібна змістова перевірка проти ledger/main |
| [#4936](https://github.com/juv4uk/sens/issues/4936) | [D10][GRAY][OWNER-REVIEW] Core vs derived bit-word bijection for FPGA and SDR | Потрібна змістова перевірка проти ledger/main |
| [#4959](https://github.com/juv4uk/sens/issues/4959) | [D10][DONOR][FORTH-2012] Systematic word-law harvest with native Gforth oracle and hobby borders | Потрібна змістова перевірка проти ledger/main |
| [#4977](https://github.com/juv4uk/sens/issues/4977) | [D10][SYMBOLIC-AI] Historical law harvest: CLP, congruence closure, rewriting and Advice Taker | Потрібна змістова перевірка проти ledger/main |
| [#4980](https://github.com/juv4uk/sens/issues/4980) | [CI][P0] Current semantic slice #229 canon-empty-list fails on unrelated source-only D10 research PRs | Потрібна змістова перевірка проти ledger/main |
| [#4988](https://github.com/juv4uk/sens/issues/4988) | [D10][HISTORY][IPL] Відновити закони Logic Theorist 1956: підцілі, евристики, provenance без дублювання D9 | Потрібна змістова перевірка проти ledger/main |
| [#4991](https://github.com/juv4uk/sens/issues/4991) | [D10][SYMBOLIC-AI][CSP] Source-grade finite arc-consistency fixed point (Mackworth 1977) | Потрібна змістова перевірка проти ledger/main |
| [#4995](https://github.com/juv4uk/sens/issues/4995) | [D10][SYMBOLIC AI] McCarthy 1980 finite circumscription: independent ASP/SAT oracle and Core-vs-library review | Потрібна змістова перевірка проти ledger/main |
| [#4996](https://github.com/juv4uk/sens/issues/4996) | [D10][SYMBOLIC-AI][REWRITING] Knuth–Bendix finite ground critical-peak witnesses | Потрібна змістова перевірка проти ledger/main |
| [#5331](https://github.com/juv4uk/sens/issues/5331) | D10: відмова при підміненому Git-донорі та перевірка справжніх blob-ідентичностей | Потрібна змістова перевірка проти ledger/main |
| [#5411](https://github.com/juv4uk/sens/issues/5411) | [P0][D10][ПОХОДЖЕННЯ] Три червоні свідки Git blob: quantity, time та meta-eval — відновити без сліпого repin | Потрібна змістова перевірка проти ledger/main |
| [#5417](https://github.com/juv4uk/sens/issues/5417) | [P0][D10][CI] Відділити історичні SHA донорів від current Lisp без підміни доказу | Потрібна змістова перевірка проти ledger/main |
| [#5539](https://github.com/juv4uk/sens/issues/5539) | D10: відсіяти дублікати й опрацювати 44 готові донорні назви | Потрібна змістова перевірка проти ledger/main |
| [#5540](https://github.com/juv4uk/sens/issues/5540) | D10→1024: пошук відсутніх незалежних законів у 87 репозиторіях | Потрібна змістова перевірка проти ledger/main |

## Наявні D10-гілки (всього 272)

Кожна гілка нижче — **джерело для dedup/provenance**, не дозвіл зливати ціле дерево. `PR` означає наявний відкритий PR зі збігом назви; `БЕЗ ВІДКРИТОГО D10 PR` не означає, що гілка не злита.

| Гілка | Зв'язок |
|---|---|
| [`archive/d10-canonical-topological-order-proof-20261011`](https://github.com/juv4uk/sens/tree/archive/d10-canonical-topological-order-proof-20261011) | без відкритого D10 PR |
| [`archive/domain-research-d3-d10-supplement-20261011`](https://github.com/juv4uk/sens/tree/archive/domain-research-d3-d10-supplement-20261011) | без відкритого D10 PR |
| [`audit/d10-source-grounded-dedup-ratchet-20261009`](https://github.com/juv4uk/sens/tree/audit/d10-source-grounded-dedup-ratchet-20261009) | без відкритого D10 PR |
| [`audit/d10-vault-semantic-scope`](https://github.com/juv4uk/sens/tree/audit/d10-vault-semantic-scope) | без відкритого D10 PR |
| [`coord/d10-proposal-intake-4463`](https://github.com/juv4uk/sens/tree/coord/d10-proposal-intake-4463) | без відкритого D10 PR |
| [`fix/4013-d10-source-harvest-validator`](https://github.com/juv4uk/sens/tree/fix/4013-d10-source-harvest-validator) | без відкритого D10 PR |
| [`fix/4463-d10-archipelago-inventory-doc-guard-20261009`](https://github.com/juv4uk/sens/tree/fix/4463-d10-archipelago-inventory-doc-guard-20261009) | без відкритого D10 PR |
| [`fix/4463-d10-selection-ledger-gate-20261009`](https://github.com/juv4uk/sens/tree/fix/4463-d10-selection-ledger-gate-20261009) | без відкритого D10 PR |
| [`fix/d10-allow-unknown-dedup-pending-20261009`](https://github.com/juv4uk/sens/tree/fix/d10-allow-unknown-dedup-pending-20261009) | без відкритого D10 PR |
| [`fix/d10-clos-historical-transition-ci-20261009`](https://github.com/juv4uk/sens/tree/fix/d10-clos-historical-transition-ci-20261009) | без відкритого D10 PR |
| [`fix/d10-clos-root-negative-tests-stable-id-20261009`](https://github.com/juv4uk/sens/tree/fix/d10-clos-root-negative-tests-stable-id-20261009) | без відкритого D10 PR |
| [`fix/d10-common-lisp-donor-oracle-evidence-class-20261009`](https://github.com/juv4uk/sens/tree/fix/d10-common-lisp-donor-oracle-evidence-class-20261009) | без відкритого D10 PR |
| [`fix/d10-current-single-stream-doc-20261009`](https://github.com/juv4uk/sens/tree/fix/d10-current-single-stream-doc-20261009) | без відкритого D10 PR |
| [`fix/d10-finite-bayes-snapshot-append-history-20261009`](https://github.com/juv4uk/sens/tree/fix/d10-finite-bayes-snapshot-append-history-20261009) | без відкритого D10 PR |
| [`fix/d10-gf2-selection-snapshot-append-history-20261009`](https://github.com/juv4uk/sens/tree/fix/d10-gf2-selection-snapshot-append-history-20261009) | без відкритого D10 PR |
| [`fix/d10-gray-historical-growth-guard-20261009`](https://github.com/juv4uk/sens/tree/fix/d10-gray-historical-growth-guard-20261009) | без відкритого D10 PR |
| [`fix/d10-gray-historical-snapshot-append-chain-20261009`](https://github.com/juv4uk/sens/tree/fix/d10-gray-historical-snapshot-append-chain-20261009) | без відкритого D10 PR |
| [`fix/d10-gray-history-prefix-growth-20261009`](https://github.com/juv4uk/sens/tree/fix/d10-gray-history-prefix-growth-20261009) | без відкритого D10 PR |
| [`fix/d10-gray-ledger-append-id-20261009`](https://github.com/juv4uk/sens/tree/fix/d10-gray-ledger-append-id-20261009) | без відкритого D10 PR |
| [`fix/d10-historical-donor-pins-20261011`](https://github.com/juv4uk/sens/tree/fix/d10-historical-donor-pins-20261011) | без відкритого D10 PR |
| [`fix/d10-historical-gap-traced-promotion-20261009`](https://github.com/juv4uk/sens/tree/fix/d10-historical-gap-traced-promotion-20261009) | без відкритого D10 PR |
| [`fix/d10-historical-gap-transition-20261009`](https://github.com/juv4uk/sens/tree/fix/d10-historical-gap-transition-20261009) | без відкритого D10 PR |
| [`fix/d10-historical-lisp15-snapshot-compat-20261009`](https://github.com/juv4uk/sens/tree/fix/d10-historical-lisp15-snapshot-compat-20261009) | без відкритого D10 PR |
| [`fix/d10-historical-source-snapshots-20261011`](https://github.com/juv4uk/sens/tree/fix/d10-historical-source-snapshots-20261011) | без відкритого D10 PR |
| [`fix/d10-historical-sources-sha-ledger-20261011`](https://github.com/juv4uk/sens/tree/fix/d10-historical-sources-sha-ledger-20261011) | без відкритого D10 PR |
| [`fix/d10-ledger-selection-growth-gate-20261009`](https://github.com/juv4uk/sens/tree/fix/d10-ledger-selection-growth-gate-20261009) | без відкритого D10 PR |
| [`fix/d10-ledger-selection-trace-gate`](https://github.com/juv4uk/sens/tree/fix/d10-ledger-selection-trace-gate) | без відкритого D10 PR |
| [`fix/d10-library-selected-vs-source-symbols-20261009`](https://github.com/juv4uk/sens/tree/fix/d10-library-selected-vs-source-symbols-20261009) | без відкритого D10 PR |
| [`fix/d10-lisp-machine-historical-source-snapshot-20261009`](https://github.com/juv4uk/sens/tree/fix/d10-lisp-machine-historical-source-snapshot-20261009) | без відкритого D10 PR |
| [`fix/d10-maling-selection-snapshot-growth-20261009`](https://github.com/juv4uk/sens/tree/fix/d10-maling-selection-snapshot-growth-20261009) | без відкритого D10 PR |
| [`fix/d10-pending-dedup-plus-forth-intake-20261009`](https://github.com/juv4uk/sens/tree/fix/d10-pending-dedup-plus-forth-intake-20261009) | без відкритого D10 PR |
| [`fix/d10-pending-intake-bayes-20261009`](https://github.com/juv4uk/sens/tree/fix/d10-pending-intake-bayes-20261009) | без відкритого D10 PR |
| [`fix/d10-pending-source-intake-after-4902-20261009`](https://github.com/juv4uk/sens/tree/fix/d10-pending-source-intake-after-4902-20261009) | без відкритого D10 PR |
| [`fix/d10-science-ledger-monotonic-20261009`](https://github.com/juv4uk/sens/tree/fix/d10-science-ledger-monotonic-20261009) | без відкритого D10 PR |
| [`fix/d10-selection-ledger-gate-reconciled-20261009`](https://github.com/juv4uk/sens/tree/fix/d10-selection-ledger-gate-reconciled-20261009) | без відкритого D10 PR |
| [`fix/d10-selection-ledger-gate-reconciled-v2-20261009`](https://github.com/juv4uk/sens/tree/fix/d10-selection-ledger-gate-reconciled-v2-20261009) | без відкритого D10 PR |
| [`fix/d10-strips-checker-api-preserve-20261009`](https://github.com/juv4uk/sens/tree/fix/d10-strips-checker-api-preserve-20261009) | без відкритого D10 PR |
| [`fix/d10-symbolic-ai-pending-intake-635-20261009`](https://github.com/juv4uk/sens/tree/fix/d10-symbolic-ai-pending-intake-635-20261009) | без відкритого D10 PR |
| [`fix/d10-tochna-pryviazka-kilkosti-20261010`](https://github.com/juv4uk/sens/tree/fix/d10-tochna-pryviazka-kilkosti-20261010) | відкритий PR #5306 |
| [`fix/d10-yantra-dual-provenance-20261010`](https://github.com/juv4uk/sens/tree/fix/d10-yantra-dual-provenance-20261010) | відкритий PR #5310 |
| [`fix/time-twofield-cond-d10-ledger-20261009`](https://github.com/juv4uk/sens/tree/fix/time-twofield-cond-d10-ledger-20261009) | без відкритого D10 PR |
| [`integrate/d10-four-archive-on-main-20261011`](https://github.com/juv4uk/sens/tree/integrate/d10-four-archive-on-main-20261011) | без відкритого D10 PR |
| [`integrate/d10-four-proof-selected-20261011`](https://github.com/juv4uk/sens/tree/integrate/d10-four-proof-selected-20261011) | без відкритого D10 PR |
| [`integrate/d10-island-bridge-current`](https://github.com/juv4uk/sens/tree/integrate/d10-island-bridge-current) | без відкритого D10 PR |
| [`integrate/d10-island-seam-current`](https://github.com/juv4uk/sens/tree/integrate/d10-island-seam-current) | без відкритого D10 PR |
| [`integrate/d10-kraft-isolated-20261011-gpt6`](https://github.com/juv4uk/sens/tree/integrate/d10-kraft-isolated-20261011-gpt6) | без відкритого D10 PR |
| [`integrate/d10-modular-lift-652-oracle-20261011-gpt6`](https://github.com/juv4uk/sens/tree/integrate/d10-modular-lift-652-oracle-20261011-gpt6) | без відкритого D10 PR |
| [`integrate/d10-proposal-intake-main-20261009`](https://github.com/juv4uk/sens/tree/integrate/d10-proposal-intake-main-20261009) | без відкритого D10 PR |
| [`integrate/d10-proposal-intake-main-v2-20261009`](https://github.com/juv4uk/sens/tree/integrate/d10-proposal-intake-main-v2-20261009) | без відкритого D10 PR |
| [`integration/d10-bit-hash-after-636-20261009`](https://github.com/juv4uk/sens/tree/integration/d10-bit-hash-after-636-20261009) | без відкритого D10 PR |
| [`integration/d10-bit-hash-on-630-20261009`](https://github.com/juv4uk/sens/tree/integration/d10-bit-hash-on-630-20261009) | без відкритого D10 PR |
| [`integration/d10-bit-hash-second-tranche-20261009`](https://github.com/juv4uk/sens/tree/integration/d10-bit-hash-second-tranche-20261009) | без відкритого D10 PR |
| [`integration/d10-clock-signal-ledger-20261009`](https://github.com/juv4uk/sens/tree/integration/d10-clock-signal-ledger-20261009) | без відкритого D10 PR |
| [`integration/d10-four-historical-roots-current-main-20261009`](https://github.com/juv4uk/sens/tree/integration/d10-four-historical-roots-current-main-20261009) | без відкритого D10 PR |
| [`integration/d10-gf2-minimal-recurrence-current-main-20261009`](https://github.com/juv4uk/sens/tree/integration/d10-gf2-minimal-recurrence-current-main-20261009) | без відкритого D10 PR |
| [`integration/d10-gray-word-on-632-20261009`](https://github.com/juv4uk/sens/tree/integration/d10-gray-word-on-632-20261009) | без відкритого D10 PR |
| [`integration/d10-hysteresis-634-to-635-20261009`](https://github.com/juv4uk/sens/tree/integration/d10-hysteresis-634-to-635-20261009) | без відкритого D10 PR |
| [`integration/d10-hysteretic-646-to-647-20261010`](https://github.com/juv4uk/sens/tree/integration/d10-hysteretic-646-to-647-20261010) | без відкритого D10 PR |
| [`integration/d10-hysteretic-main-ledger-20261009`](https://github.com/juv4uk/sens/tree/integration/d10-hysteretic-main-ledger-20261009) | без відкритого D10 PR |
| [`integration/d10-hysteretic-on-632-20261009`](https://github.com/juv4uk/sens/tree/integration/d10-hysteretic-on-632-20261009) | без відкритого D10 PR |
| [`integration/d10-mechanical-word-replay-on-ledger-main`](https://github.com/juv4uk/sens/tree/integration/d10-mechanical-word-replay-on-ledger-main) | без відкритого D10 PR |
| [`proposal/d10-class-of-ledger-20261009`](https://github.com/juv4uk/sens/tree/proposal/d10-class-of-ledger-20261009) | без відкритого D10 PR |
| [`repair/uk-d10-yantra-provenance-20261010`](https://github.com/juv4uk/sens/tree/repair/uk-d10-yantra-provenance-20261010) | без відкритого D10 PR |
| [`replay/4013-d10-binary-lyndon-original-hobbies-20261009`](https://github.com/juv4uk/sens/tree/replay/4013-d10-binary-lyndon-original-hobbies-20261009) | без відкритого D10 PR |
| [`replay/4912-d10-finite-transducer-fresh-main-20261009`](https://github.com/juv4uk/sens/tree/replay/4912-d10-finite-transducer-fresh-main-20261009) | без відкритого D10 PR |
| [`replay/d10-archive-donor-evidence-20261009`](https://github.com/juv4uk/sens/tree/replay/d10-archive-donor-evidence-20261009) | без відкритого D10 PR |
| [`replay/d10-clos-slot-state-current-main-20261009`](https://github.com/juv4uk/sens/tree/replay/d10-clos-slot-state-current-main-20261009) | без відкритого D10 PR |
| [`replay/d10-critical-pair-confluence-evidence-20261009`](https://github.com/juv4uk/sens/tree/replay/d10-critical-pair-confluence-evidence-20261009) | без відкритого D10 PR |
| [`replay/d10-crossdomain-exact-math-signal-hobby-20261009`](https://github.com/juv4uk/sens/tree/replay/d10-crossdomain-exact-math-signal-hobby-20261009) | без відкритого D10 PR |
| [`replay/d10-dll1962-unit-propagation-20261009`](https://github.com/juv4uk/sens/tree/replay/d10-dll1962-unit-propagation-20261009) | без відкритого D10 PR |
| [`replay/d10-flavors-restarts-evidence-20261009`](https://github.com/juv4uk/sens/tree/replay/d10-flavors-restarts-evidence-20261009) | без відкритого D10 PR |
| [`replay/d10-forth-within-circular-arc-20261009`](https://github.com/juv4uk/sens/tree/replay/d10-forth-within-circular-arc-20261009) | без відкритого D10 PR |
| [`replay/d10-ground-congruence-ai-currentmain-20261009`](https://github.com/juv4uk/sens/tree/replay/d10-ground-congruence-ai-currentmain-20261009) | без відкритого D10 PR |
| [`replay/d10-historical-hysteresis-babbage-reiter-gpt6-20261009`](https://github.com/juv4uk/sens/tree/replay/d10-historical-hysteresis-babbage-reiter-gpt6-20261009) | без відкритого D10 PR |
| [`replay/d10-interdisciplinary-science-main-20261009`](https://github.com/juv4uk/sens/tree/replay/d10-interdisciplinary-science-main-20261009) | без відкритого D10 PR |
| [`replay/d10-quine-implicants-archive-20261009`](https://github.com/juv4uk/sens/tree/replay/d10-quine-implicants-archive-20261009) | без відкритого D10 PR |
| [`replay/d10-reiter-minimal-diagnoses-current-20261009`](https://github.com/juv4uk/sens/tree/replay/d10-reiter-minimal-diagnoses-current-20261009) | без відкритого D10 PR |
| [`replay/d10-strips-clean-main-20261009`](https://github.com/juv4uk/sens/tree/replay/d10-strips-clean-main-20261009) | без відкритого D10 PR |
| [`replay/research-d10-clock-radio-current-main-20261009`](https://github.com/juv4uk/sens/tree/replay/research-d10-clock-radio-current-main-20261009) | без відкритого D10 PR |
| [`replay/research-d10-hardware-law-triage-20261009`](https://github.com/juv4uk/sens/tree/replay/research-d10-hardware-law-triage-20261009) | без відкритого D10 PR |
| [`replay/research-d10-hobbies-source-laws-current-main-20261009`](https://github.com/juv4uk/sens/tree/replay/research-d10-hobbies-source-laws-current-main-20261009) | без відкритого D10 PR |
| [`replay/research-d10-stern-brocot-current-main-20261009`](https://github.com/juv4uk/sens/tree/replay/research-d10-stern-brocot-current-main-20261009) | без відкритого D10 PR |
| [`research/4013-d10-first-order-anti-unification-20261009`](https://github.com/juv4uk/sens/tree/research/4013-d10-first-order-anti-unification-20261009) | без відкритого D10 PR |
| [`research/4904-d10-finite-transducer-cross-hobby-20261009`](https://github.com/juv4uk/sens/tree/research/4904-d10-finite-transducer-cross-hobby-20261009) | без відкритого D10 PR |
| [`research/d10-1024-evidence-readiness-20261011`](https://github.com/juv4uk/sens/tree/research/d10-1024-evidence-readiness-20261011) | без відкритого D10 PR |
| [`research/d10-1971-strips-goal-regression-20261009`](https://github.com/juv4uk/sens/tree/research/d10-1971-strips-goal-regression-20261009) | без відкритого D10 PR |
| [`research/d10-4301-physical-donor-scan`](https://github.com/juv4uk/sens/tree/research/d10-4301-physical-donor-scan) | без відкритого D10 PR |
| [`research/d10-648-bounded-modular-lift-20261011`](https://github.com/juv4uk/sens/tree/research/d10-648-bounded-modular-lift-20261011) | без відкритого D10 PR |
| [`research/d10-abductive-minimal-explanations-20261009`](https://github.com/juv4uk/sens/tree/research/d10-abductive-minimal-explanations-20261009) | без відкритого D10 PR |
| [`research/d10-adjust-array-rearray-differential-20261009`](https://github.com/juv4uk/sens/tree/research/d10-adjust-array-rearray-differential-20261009) | без відкритого D10 PR |
| [`research/d10-affine-correlated-uncertainty-20261009`](https://github.com/juv4uk/sens/tree/research/d10-affine-correlated-uncertainty-20261009) | без відкритого D10 PR |
| [`research/d10-affine-quantity-current-main-20261009`](https://github.com/juv4uk/sens/tree/research/d10-affine-quantity-current-main-20261009) | без відкритого D10 PR |
| [`research/d10-affine-quantity-point-delta-20261009`](https://github.com/juv4uk/sens/tree/research/d10-affine-quantity-point-delta-20261009) | без відкритого D10 PR |
| [`research/d10-all-repo-audit-1`](https://github.com/juv4uk/sens/tree/research/d10-all-repo-audit-1) | без відкритого D10 PR |
| [`research/d10-all-repo-audit-1-v2`](https://github.com/juv4uk/sens/tree/research/d10-all-repo-audit-1-v2) | без відкритого D10 PR |
| [`research/d10-allen-atms-hobby-history-20261009`](https://github.com/juv4uk/sens/tree/research/d10-allen-atms-hobby-history-20261009) | без відкритого D10 PR |
| [`research/d10-alltime-archive-batch14-20261011`](https://github.com/juv4uk/sens/tree/research/d10-alltime-archive-batch14-20261011) | без відкритого D10 PR |
| [`research/d10-astrophoto-pinhole-exact-rays-20261009`](https://github.com/juv4uk/sens/tree/research/d10-astrophoto-pinhole-exact-rays-20261009) | без відкритого D10 PR |
| [`research/d10-atms-strips-symbolic-foundations-20261009`](https://github.com/juv4uk/sens/tree/research/d10-atms-strips-symbolic-foundations-20261009) | без відкритого D10 PR |
| [`research/d10-babbage-reiter-symbolic-hobby-20261009`](https://github.com/juv4uk/sens/tree/research/d10-babbage-reiter-symbolic-hobby-20261009) | без відкритого D10 PR |
| [`research/d10-binary-lyndon-factorization`](https://github.com/juv4uk/sens/tree/research/d10-binary-lyndon-factorization) | без відкритого D10 PR |
| [`research/d10-binary-state-shortest-witness-20261009`](https://github.com/juv4uk/sens/tree/research/d10-binary-state-shortest-witness-20261009) | без відкритого D10 PR |
| [`research/d10-brzozowski-1964-symbolic-ai-derivative`](https://github.com/juv4uk/sens/tree/research/d10-brzozowski-1964-symbolic-ai-derivative) | без відкритого D10 PR |
| [`research/d10-canonical-cycle-witness-owner-hobbies-20261009`](https://github.com/juv4uk/sens/tree/research/d10-canonical-cycle-witness-owner-hobbies-20261009) | без відкритого D10 PR |
| [`research/d10-canonical-ledger-evidence-batch23-20261011`](https://github.com/juv4uk/sens/tree/research/d10-canonical-ledger-evidence-batch23-20261011) | відкритий PR #5600 |
| [`research/d10-canonical-topological-order-20261011`](https://github.com/juv4uk/sens/tree/research/d10-canonical-topological-order-20261011) | без відкритого D10 PR |
| [`research/d10-change-class-selected-current-main-20261011`](https://github.com/juv4uk/sens/tree/research/d10-change-class-selected-current-main-20261011) | без відкритого D10 PR |
| [`research/d10-chess-zero-sum-castling-roots-20261009`](https://github.com/juv4uk/sens/tree/research/d10-chess-zero-sum-castling-roots-20261009) | без відкритого D10 PR |
| [`research/d10-class-of-current-main-20261011`](https://github.com/juv4uk/sens/tree/research/d10-class-of-current-main-20261011) | без відкритого D10 PR |
| [`research/d10-clhs-pathnames-dictionary-20261009`](https://github.com/juv4uk/sens/tree/research/d10-clhs-pathnames-dictionary-20261009) | без відкритого D10 PR |
| [`research/d10-clhs-streams-census-20261009`](https://github.com/juv4uk/sens/tree/research/d10-clhs-streams-census-20261009) | без відкритого D10 PR |
| [`research/d10-clips-library-harvest-20261009`](https://github.com/juv4uk/sens/tree/research/d10-clips-library-harvest-20261009) | без відкритого D10 PR |
| [`research/d10-clojure-reference-reclassification`](https://github.com/juv4uk/sens/tree/research/d10-clojure-reference-reclassification) | без відкритого D10 PR |
| [`research/d10-clos-interlisp-residual-proof-20261009`](https://github.com/juv4uk/sens/tree/research/d10-clos-interlisp-residual-proof-20261009) | без відкритого D10 PR |
| [`research/d10-clos-method-class-independent-oracle-20261009`](https://github.com/juv4uk/sens/tree/research/d10-clos-method-class-independent-oracle-20261009) | без відкритого D10 PR |
| [`research/d10-clos-slot-sbcl-oracle-20261009`](https://github.com/juv4uk/sens/tree/research/d10-clos-slot-sbcl-oracle-20261009) | без відкритого D10 PR |
| [`research/d10-clos-three-roots-selection-20261009`](https://github.com/juv4uk/sens/tree/research/d10-clos-three-roots-selection-20261009) | без відкритого D10 PR |
| [`research/d10-clos-three-roots-stacked-627-to-630-20261009`](https://github.com/juv4uk/sens/tree/research/d10-clos-three-roots-stacked-627-to-630-20261009) | без відкритого D10 PR |
| [`research/d10-closhistory-627-to630-current-main-20261009`](https://github.com/juv4uk/sens/tree/research/d10-closhistory-627-to630-current-main-20261009) | без відкритого D10 PR |
| [`research/d10-cnf-unit-fixpoint-648-20261011`](https://github.com/juv4uk/sens/tree/research/d10-cnf-unit-fixpoint-648-20261011) | без відкритого D10 PR |
| [`research/d10-conditions-final-main-replay-20261009`](https://github.com/juv4uk/sens/tree/research/d10-conditions-final-main-replay-20261009) | без відкритого D10 PR |
| [`research/d10-conditions-finish-20261009`](https://github.com/juv4uk/sens/tree/research/d10-conditions-finish-20261009) | без відкритого D10 PR |
| [`research/d10-conditions-finish-rebase-20261009`](https://github.com/juv4uk/sens/tree/research/d10-conditions-finish-rebase-20261009) | без відкритого D10 PR |
| [`research/d10-correct-method-precedence-and-dynamic-restart-20261009`](https://github.com/juv4uk/sens/tree/research/d10-correct-method-precedence-and-dynamic-restart-20261009) | без відкритого D10 PR |
| [`research/d10-cross-hobby-law-donors-20261009`](https://github.com/juv4uk/sens/tree/research/d10-cross-hobby-law-donors-20261009) | без відкритого D10 PR |
| [`research/d10-crossrepo-control-1`](https://github.com/juv4uk/sens/tree/research/d10-crossrepo-control-1) | без відкритого D10 PR |
| [`research/d10-crossrepo-early-lisp-1`](https://github.com/juv4uk/sens/tree/research/d10-crossrepo-early-lisp-1) | без відкритого D10 PR |
| [`research/d10-crossrepo-golisp-pascal-1`](https://github.com/juv4uk/sens/tree/research/d10-crossrepo-golisp-pascal-1) | без відкритого D10 PR |
| [`research/d10-crossrepo-lisp-koans-1`](https://github.com/juv4uk/sens/tree/research/d10-crossrepo-lisp-koans-1) | без відкритого D10 PR |
| [`research/d10-crossrepo-mal-1`](https://github.com/juv4uk/sens/tree/research/d10-crossrepo-mal-1) | без відкритого D10 PR |
| [`research/d10-crossrepo-paip-v1`](https://github.com/juv4uk/sens/tree/research/d10-crossrepo-paip-v1) | без відкритого D10 PR |
| [`research/d10-cyclic-binary-word-canon-20261009`](https://github.com/juv4uk/sens/tree/research/d10-cyclic-binary-word-canon-20261009) | без відкритого D10 PR |
| [`research/d10-cyclic-canonical-word-20261009`](https://github.com/juv4uk/sens/tree/research/d10-cyclic-canonical-word-20261009) | без відкритого D10 PR |
| [`research/d10-cyclic-word-canon-fresh-main-20261009`](https://github.com/juv4uk/sens/tree/research/d10-cyclic-word-canon-fresh-main-20261009) | без відкритого D10 PR |
| [`research/d10-d9-dedup-guard-20261009`](https://github.com/juv4uk/sens/tree/research/d10-d9-dedup-guard-20261009) | без відкритого D10 PR |
| [`research/d10-debruijn-binary-cycle-witness`](https://github.com/juv4uk/sens/tree/research/d10-debruijn-binary-cycle-witness) | без відкритого D10 PR |
| [`research/d10-dll1962-unit-closure-20261009`](https://github.com/juv4uk/sens/tree/research/d10-dll1962-unit-closure-20261009) | без відкритого D10 PR |
| [`research/d10-dung-grounded-argumentation-20261009`](https://github.com/juv4uk/sens/tree/research/d10-dung-grounded-argumentation-20261009) | без відкритого D10 PR |
| [`research/d10-early-ai-strips-regression-oracle-20261009`](https://github.com/juv4uk/sens/tree/research/d10-early-ai-strips-regression-oracle-20261009) | без відкритого D10 PR |
| [`research/d10-early-programming-treasures-20261009`](https://github.com/juv4uk/sens/tree/research/d10-early-programming-treasures-20261009) | без відкритого D10 PR |
| [`research/d10-ebg-operational-horn-proof-20261009`](https://github.com/juv4uk/sens/tree/research/d10-ebg-operational-horn-proof-20261009) | без відкритого D10 PR |
| [`research/d10-evidence-archive-20261011`](https://github.com/juv4uk/sens/tree/research/d10-evidence-archive-20261011) | без відкритого D10 PR |
| [`research/d10-exact-barycentric-interpolation-20261009`](https://github.com/juv4uk/sens/tree/research/d10-exact-barycentric-interpolation-20261009) | без відкритого D10 PR |
| [`research/d10-exact-interval-conflict-clean-main-20261009`](https://github.com/juv4uk/sens/tree/research/d10-exact-interval-conflict-clean-main-20261009) | без відкритого D10 PR |
| [`research/d10-exact-radix-normalization-20261009`](https://github.com/juv4uk/sens/tree/research/d10-exact-radix-normalization-20261009) | без відкритого D10 PR |
| [`research/d10-exact-rational-interval-conflict-20261009`](https://github.com/juv4uk/sens/tree/research/d10-exact-rational-interval-conflict-20261009) | без відкритого D10 PR |
| [`research/d10-existing-combinatorics-batch-20261011`](https://github.com/juv4uk/sens/tree/research/d10-existing-combinatorics-batch-20261011) | без відкритого D10 PR |
| [`research/d10-existing-math-signal-batch-20261011`](https://github.com/juv4uk/sens/tree/research/d10-existing-math-signal-batch-20261011) | без відкритого D10 PR |
| [`research/d10-fill-v1-seed`](https://github.com/juv4uk/sens/tree/research/d10-fill-v1-seed) | без відкритого D10 PR |
| [`research/d10-find-method-selected-proof-20261009`](https://github.com/juv4uk/sens/tree/research/d10-find-method-selected-proof-20261009) | без відкритого D10 PR |
| [`research/d10-finite-bayes-update-selected-634-to-635-20261009`](https://github.com/juv4uk/sens/tree/research/d10-finite-bayes-update-selected-634-to-635-20261009) | без відкритого D10 PR |
| [`research/d10-finite-update-20261009`](https://github.com/juv4uk/sens/tree/research/d10-finite-update-20261009) | без відкритого D10 PR |
| [`research/d10-first-semantic-growth-627-current-main-20261009`](https://github.com/juv4uk/sens/tree/research/d10-first-semantic-growth-627-current-main-20261009) | без відкритого D10 PR |
| [`research/d10-flavors-restarts-law-proposals-20261009`](https://github.com/juv4uk/sens/tree/research/d10-flavors-restarts-law-proposals-20261009) | без відкритого D10 PR |
| [`research/d10-floyd-hoare-inductive-safety-witness-20261009`](https://github.com/juv4uk/sens/tree/research/d10-floyd-hoare-inductive-safety-witness-20261009) | без відкритого D10 PR |
| [`research/d10-forth-circular-arc-20261009`](https://github.com/juv4uk/sens/tree/research/d10-forth-circular-arc-20261009) | без відкритого D10 PR |
| [`research/d10-forth-preselection-ledger-20261009`](https://github.com/juv4uk/sens/tree/research/d10-forth-preselection-ledger-20261009) | без відкритого D10 PR |
| [`research/d10-forward-harvest-1`](https://github.com/juv4uk/sens/tree/research/d10-forward-harvest-1) | без відкритого D10 PR |
| [`research/d10-four-archive-selections-20261011`](https://github.com/juv4uk/sens/tree/research/d10-four-archive-selections-20261011) | без відкритого D10 PR |
| [`research/d10-general-crt-merge-cross-hobbies-20261009`](https://github.com/juv4uk/sens/tree/research/d10-general-crt-merge-cross-hobbies-20261009) | без відкритого D10 PR |
| [`research/d10-generalized-crt-after-unique-20261011`](https://github.com/juv4uk/sens/tree/research/d10-generalized-crt-after-unique-20261011) | без відкритого D10 PR |
| [`research/d10-generalized-crt-periods-20261009`](https://github.com/juv4uk/sens/tree/research/d10-generalized-crt-periods-20261009) | без відкритого D10 PR |
| [`research/d10-gf2-linear-complexity-20261009`](https://github.com/juv4uk/sens/tree/research/d10-gf2-linear-complexity-20261009) | без відкритого D10 PR |
| [`research/d10-gf2-minimal-recurrence-635-to-636-20261009`](https://github.com/juv4uk/sens/tree/research/d10-gf2-minimal-recurrence-635-to-636-20261009) | без відкритого D10 PR |
| [`research/d10-gf2-minimal-recurrence-635-to-636-mainline-20261009`](https://github.com/juv4uk/sens/tree/research/d10-gf2-minimal-recurrence-635-to-636-mainline-20261009) | без відкритого D10 PR |
| [`research/d10-gf2-minimal-recurrence-635-to-636-mainline-v2-20261009`](https://github.com/juv4uk/sens/tree/research/d10-gf2-minimal-recurrence-635-to-636-mainline-v2-20261009) | без відкритого D10 PR |
| [`research/d10-gf2-minimal-recurrence-cross-hobbies-20261009`](https://github.com/juv4uk/sens/tree/research/d10-gf2-minimal-recurrence-cross-hobbies-20261009) | без відкритого D10 PR |
| [`research/d10-gf2-minimal-recurrence-selected-635-to-636-20261009`](https://github.com/juv4uk/sens/tree/research/d10-gf2-minimal-recurrence-selected-635-to-636-20261009) | без відкритого D10 PR |
| [`research/d10-gps-means-ends-oplink-1958-20261009`](https://github.com/juv4uk/sens/tree/research/d10-gps-means-ends-oplink-1958-20261009) | без відкритого D10 PR |
| [`research/d10-gray-word-hobby-root-20261009`](https://github.com/juv4uk/sens/tree/research/d10-gray-word-hobby-root-20261009) | без відкритого D10 PR |
| [`research/d10-ground-congruence-ai-20261009`](https://github.com/juv4uk/sens/tree/research/d10-ground-congruence-ai-20261009) | без відкритого D10 PR |
| [`research/d10-hadamard-donor-ledger-20261009`](https://github.com/juv4uk/sens/tree/research/d10-hadamard-donor-ledger-20261009) | без відкритого D10 PR |
| [`research/d10-hadamard-preselection-0008-after-632-20261009`](https://github.com/juv4uk/sens/tree/research/d10-hadamard-preselection-0008-after-632-20261009) | без відкритого D10 PR |
| [`research/d10-hardware-law-triage-20261009`](https://github.com/juv4uk/sens/tree/research/d10-hardware-law-triage-20261009) | без відкритого D10 PR |
| [`research/d10-harvest-admission-20261011`](https://github.com/juv4uk/sens/tree/research/d10-harvest-admission-20261011) | без відкритого D10 PR |
| [`research/d10-historical-admission-batch1-20261009`](https://github.com/juv4uk/sens/tree/research/d10-historical-admission-batch1-20261009) | без відкритого D10 PR |
| [`research/d10-historical-clos-instance-lifecycle-residual-20261009`](https://github.com/juv4uk/sens/tree/research/d10-historical-clos-instance-lifecycle-residual-20261009) | без відкритого D10 PR |
| [`research/d10-historical-clos-slot-state-20261009`](https://github.com/juv4uk/sens/tree/research/d10-historical-clos-slot-state-20261009) | без відкритого D10 PR |
| [`research/d10-historical-coverage-gaps-20261009`](https://github.com/juv4uk/sens/tree/research/d10-historical-coverage-gaps-20261009) | без відкритого D10 PR |
| [`research/d10-historical-maclisp-1`](https://github.com/juv4uk/sens/tree/research/d10-historical-maclisp-1) | без відкритого D10 PR |
| [`research/d10-historical-maclisp-2`](https://github.com/juv4uk/sens/tree/research/d10-historical-maclisp-2) | без відкритого D10 PR |
| [`research/d10-historical-primary-manual-reconcile-20261009`](https://github.com/juv4uk/sens/tree/research/d10-historical-primary-manual-reconcile-20261009) | без відкритого D10 PR |
| [`research/d10-historical-selection-4-20261009`](https://github.com/juv4uk/sens/tree/research/d10-historical-selection-4-20261009) | без відкритого D10 PR |
| [`research/d10-hobbies-clock-sdr-exact-630to634-20261009`](https://github.com/juv4uk/sens/tree/research/d10-hobbies-clock-sdr-exact-630to634-20261009) | без відкритого D10 PR |
| [`research/d10-hobbies-source-laws-20261009`](https://github.com/juv4uk/sens/tree/research/d10-hobbies-source-laws-20261009) | без відкритого D10 PR |
| [`research/d10-hysteretic-selected-631-20261009`](https://github.com/juv4uk/sens/tree/research/d10-hysteretic-selected-631-20261009) | без відкритого D10 PR |
| [`research/d10-hysteretic-state-universal-20261009`](https://github.com/juv4uk/sens/tree/research/d10-hysteretic-state-universal-20261009) | без відкритого D10 PR |
| [`research/d10-interdisciplinary-science-first-20261009`](https://github.com/juv4uk/sens/tree/research/d10-interdisciplinary-science-first-20261009) | без відкритого D10 PR |
| [`research/d10-interlisp-dwim-safe-suggestion-20261009`](https://github.com/juv4uk/sens/tree/research/d10-interlisp-dwim-safe-suggestion-20261009) | без відкритого D10 PR |
| [`research/d10-island-bridge-v1`](https://github.com/juv4uk/sens/tree/research/d10-island-bridge-v1) | без відкритого D10 PR |
| [`research/d10-island-bridge-v1-clean`](https://github.com/juv4uk/sens/tree/research/d10-island-bridge-v1-clean) | без відкритого D10 PR |
| [`research/d10-island-bridge-v1-rebased`](https://github.com/juv4uk/sens/tree/research/d10-island-bridge-v1-rebased) | без відкритого D10 PR |
| [`research/d10-knowledge-harvest-1`](https://github.com/juv4uk/sens/tree/research/d10-knowledge-harvest-1) | без відкритого D10 PR |
| [`research/d10-knowledge-tooling-v1`](https://github.com/juv4uk/sens/tree/research/d10-knowledge-tooling-v1) | без відкритого D10 PR |
| [`research/d10-kraft-certificate-20261011`](https://github.com/juv4uk/sens/tree/research/d10-kraft-certificate-20261011) | без відкритого D10 PR |
| [`research/d10-library-harvest-1`](https://github.com/juv4uk/sens/tree/research/d10-library-harvest-1) | без відкритого D10 PR |
| [`research/d10-linguistic-v1`](https://github.com/juv4uk/sens/tree/research/d10-linguistic-v1) | без відкритого D10 PR |
| [`research/d10-lisp-machine-evaluator-harvest-20261009`](https://github.com/juv4uk/sens/tree/research/d10-lisp-machine-evaluator-harvest-20261009) | без відкритого D10 PR |
| [`research/d10-lisp15-appendix-reconcile-20261009`](https://github.com/juv4uk/sens/tree/research/d10-lisp15-appendix-reconcile-20261009) | без відкритого D10 PR |
| [`research/d10-loops-active-values-current-main-630-to-632-20261009`](https://github.com/juv4uk/sens/tree/research/d10-loops-active-values-current-main-630-to-632-20261009) | без відкритого D10 PR |
| [`research/d10-loops-active-values-intake-20261009`](https://github.com/juv4uk/sens/tree/research/d10-loops-active-values-intake-20261009) | без відкритого D10 PR |
| [`research/d10-loops-active-values-stacked-630-to-632-20261009`](https://github.com/juv4uk/sens/tree/research/d10-loops-active-values-stacked-630-to-632-20261009) | без відкритого D10 PR |
| [`research/d10-maling-differentiation-1959-20261009`](https://github.com/juv4uk/sens/tree/research/d10-maling-differentiation-1959-20261009) | без відкритого D10 PR |
| [`research/d10-maling-differentiation-1959-current-main-20261009`](https://github.com/juv4uk/sens/tree/research/d10-maling-differentiation-1959-current-main-20261009) | без відкритого D10 PR |
| [`research/d10-maling-differentiation-main636-20261009`](https://github.com/juv4uk/sens/tree/research/d10-maling-differentiation-main636-20261009) | без відкритого D10 PR |
| [`research/d10-math-signal-law-evidence`](https://github.com/juv4uk/sens/tree/research/d10-math-signal-law-evidence) | без відкритого D10 PR |
| [`research/d10-mealy-distinguishing-20261011`](https://github.com/juv4uk/sens/tree/research/d10-mealy-distinguishing-20261011) | без відкритого D10 PR |
| [`research/d10-mechanical-binary-words`](https://github.com/juv4uk/sens/tree/research/d10-mechanical-binary-words) | без відкритого D10 PR |
| [`research/d10-mechanical-word-clean-main-20261009`](https://github.com/juv4uk/sens/tree/research/d10-mechanical-word-clean-main-20261009) | без відкритого D10 PR |
| [`research/d10-mitchell-version-space-1977-20261009`](https://github.com/juv4uk/sens/tree/research/d10-mitchell-version-space-1977-20261009) | без відкритого D10 PR |
| [`research/d10-mop-17-readers-source-oracle-20261009`](https://github.com/juv4uk/sens/tree/research/d10-mop-17-readers-source-oracle-20261009) | без відкритого D10 PR |
| [`research/d10-my-idea-harvest-1`](https://github.com/juv4uk/sens/tree/research/d10-my-idea-harvest-1) | без відкритого D10 PR |
| [`research/d10-newman-knuth-bendix-critical-pairs-20261009`](https://github.com/juv4uk/sens/tree/research/d10-newman-knuth-bendix-critical-pairs-20261009) | без відкритого D10 PR |
| [`research/d10-next-tranche-pending-20261011`](https://github.com/juv4uk/sens/tree/research/d10-next-tranche-pending-20261011) | без відкритого D10 PR |
| [`research/d10-ownership-cleanup-1`](https://github.com/juv4uk/sens/tree/research/d10-ownership-cleanup-1) | без відкритого D10 PR |
| [`research/d10-ownership-cleanup-v2`](https://github.com/juv4uk/sens/tree/research/d10-ownership-cleanup-v2) | без відкритого D10 PR |
| [`research/d10-panini-harvest-1`](https://github.com/juv4uk/sens/tree/research/d10-panini-harvest-1) | без відкритого D10 PR |
| [`research/d10-placement-proof-crosswalk-20261011`](https://github.com/juv4uk/sens/tree/research/d10-placement-proof-crosswalk-20261011) | без відкритого D10 PR |
| [`research/d10-portable-control-residual-v1`](https://github.com/juv4uk/sens/tree/research/d10-portable-control-residual-v1) | без відкритого D10 PR |
| [`research/d10-primitive-binary-word-root-631`](https://github.com/juv4uk/sens/tree/research/d10-primitive-binary-word-root-631) | без відкритого D10 PR |
| [`research/d10-primitive-binary-word-root-632-current-main-20261009`](https://github.com/juv4uk/sens/tree/research/d10-primitive-binary-word-root-632-current-main-20261009) | без відкритого D10 PR |
| [`research/d10-prolog-constraint-hobbies-20261009`](https://github.com/juv4uk/sens/tree/research/d10-prolog-constraint-hobbies-20261009) | без відкритого D10 PR |
| [`research/d10-psl-interlisp-historical-20261009`](https://github.com/juv4uk/sens/tree/research/d10-psl-interlisp-historical-20261009) | без відкритого D10 PR |
| [`research/d10-psl-interlisp-lispm-residual-20261009`](https://github.com/juv4uk/sens/tree/research/d10-psl-interlisp-lispm-residual-20261009) | без відкритого D10 PR |
| [`research/d10-quantity-derived-dedup-20261009`](https://github.com/juv4uk/sens/tree/research/d10-quantity-derived-dedup-20261009) | без відкритого D10 PR |
| [`research/d10-quine-prime-implicants-20261009`](https://github.com/juv4uk/sens/tree/research/d10-quine-prime-implicants-20261009) | без відкритого D10 PR |
| [`research/d10-r6rs-hashtable-copy-mutable-oracle-20261009`](https://github.com/juv4uk/sens/tree/research/d10-r6rs-hashtable-copy-mutable-oracle-20261009) | без відкритого D10 PR |
| [`research/d10-r6rs-hashtable-hygiene-audit-20261009`](https://github.com/juv4uk/sens/tree/research/d10-r6rs-hashtable-hygiene-audit-20261009) | без відкритого D10 PR |
| [`research/d10-r7rs-primary-manual-slice-20261009`](https://github.com/juv4uk/sens/tree/research/d10-r7rs-primary-manual-slice-20261009) | без відкритого D10 PR |
| [`research/d10-reason-alternate-define-source-witness-20261009`](https://github.com/juv4uk/sens/tree/research/d10-reason-alternate-define-source-witness-20261009) | без відкритого D10 PR |
| [`research/d10-reason-d9-collision-guard-20261009`](https://github.com/juv4uk/sens/tree/research/d10-reason-d9-collision-guard-20261009) | без відкритого D10 PR |
| [`research/d10-reason-historical-define-census-20261009`](https://github.com/juv4uk/sens/tree/research/d10-reason-historical-define-census-20261009) | без відкритого D10 PR |
| [`research/d10-recovery-1`](https://github.com/juv4uk/sens/tree/research/d10-recovery-1) | без відкритого D10 PR |
| [`research/d10-recovery-v2`](https://github.com/juv4uk/sens/tree/research/d10-recovery-v2) | без відкритого D10 PR |
| [`research/d10-reiter-diagnoses-after-ledger68-20261009`](https://github.com/juv4uk/sens/tree/research/d10-reiter-diagnoses-after-ledger68-20261009) | без відкритого D10 PR |
| [`research/d10-reiter-diagnoses-clean-main-20261009`](https://github.com/juv4uk/sens/tree/research/d10-reiter-diagnoses-clean-main-20261009) | без відкритого D10 PR |
| [`research/d10-reiter-finite-minimal-diagnoses-20261009`](https://github.com/juv4uk/sens/tree/research/d10-reiter-finite-minimal-diagnoses-20261009) | без відкритого D10 PR |
| [`research/d10-rosenblatt-novikoff-exact-perceptron-20261009`](https://github.com/juv4uk/sens/tree/research/d10-rosenblatt-novikoff-exact-perceptron-20261009) | без відкритого D10 PR |
| [`research/d10-sardinas-patterson-historical-20261009`](https://github.com/juv4uk/sens/tree/research/d10-sardinas-patterson-historical-20261009) | без відкритого D10 PR |
| [`research/d10-selfhost-reasoning-harvest-20261009`](https://github.com/juv4uk/sens/tree/research/d10-selfhost-reasoning-harvest-20261009) | без відкритого D10 PR |
| [`research/d10-shiva-c1p-canonical-order-20261009`](https://github.com/juv4uk/sens/tree/research/d10-shiva-c1p-canonical-order-20261009) | без відкритого D10 PR |
| [`research/d10-single-stream-restoration`](https://github.com/juv4uk/sens/tree/research/d10-single-stream-restoration) | без відкритого D10 PR |
| [`research/d10-single-stream-restoration-rebased`](https://github.com/juv4uk/sens/tree/research/d10-single-stream-restoration-rebased) | без відкритого D10 PR |
| [`research/d10-spanda-631-ledger-current-main-clean-20261009`](https://github.com/juv4uk/sens/tree/research/d10-spanda-631-ledger-current-main-clean-20261009) | без відкритого D10 PR |
| [`research/d10-spanda-after-ledger-631-20261009`](https://github.com/juv4uk/sens/tree/research/d10-spanda-after-ledger-631-20261009) | без відкритого D10 PR |
| [`research/d10-spanda-bounded-rational-631-20261009`](https://github.com/juv4uk/sens/tree/research/d10-spanda-bounded-rational-631-20261009) | без відкритого D10 PR |
| [`research/d10-spanda-bounded-rational-exact-20261009`](https://github.com/juv4uk/sens/tree/research/d10-spanda-bounded-rational-exact-20261009) | без відкритого D10 PR |
| [`research/d10-stern-brocot-runs-20261009`](https://github.com/juv4uk/sens/tree/research/d10-stern-brocot-runs-20261009) | без відкритого D10 PR |
| [`research/d10-stern-brocot-runs-current-main-20261009`](https://github.com/juv4uk/sens/tree/research/d10-stern-brocot-runs-current-main-20261009) | без відкритого D10 PR |
| [`research/d10-symbolic-ai-anti-unification-20261009`](https://github.com/juv4uk/sens/tree/research/d10-symbolic-ai-anti-unification-20261009) | без відкритого D10 PR |
| [`research/d10-symbolic-ai-antiunification-20261009`](https://github.com/juv4uk/sens/tree/research/d10-symbolic-ai-antiunification-20261009) | без відкритого D10 PR |
| [`research/d10-symbolic-ai-arc-support-20261009`](https://github.com/juv4uk/sens/tree/research/d10-symbolic-ai-arc-support-20261009) | без відкритого D10 PR |
| [`research/d10-symbolic-ai-audit-20261009`](https://github.com/juv4uk/sens/tree/research/d10-symbolic-ai-audit-20261009) | без відкритого D10 PR |
| [`research/d10-symbolic-ai-finite-antiunification`](https://github.com/juv4uk/sens/tree/research/d10-symbolic-ai-finite-antiunification) | без відкритого D10 PR |
| [`research/d10-symbolic-ai-ground-antiunification-20261009`](https://github.com/juv4uk/sens/tree/research/d10-symbolic-ai-ground-antiunification-20261009) | без відкритого D10 PR |
| [`research/d10-symbolic-ai-one-sided-subsumption`](https://github.com/juv4uk/sens/tree/research/d10-symbolic-ai-one-sided-subsumption) | без відкритого D10 PR |
| [`research/d10-symbolic-ai-pending-ledger-20261009`](https://github.com/juv4uk/sens/tree/research/d10-symbolic-ai-pending-ledger-20261009) | без відкритого D10 PR |
| [`research/d10-symbolic-ai-swi-oracle-current-main-20261009`](https://github.com/juv4uk/sens/tree/research/d10-symbolic-ai-swi-oracle-current-main-20261009) | без відкритого D10 PR |
| [`research/d10-temporal-stp-20261009`](https://github.com/juv4uk/sens/tree/research/d10-temporal-stp-20261009) | без відкритого D10 PR |
| [`research/d10-three-donor-replay-20261009`](https://github.com/juv4uk/sens/tree/research/d10-three-donor-replay-20261009) | без відкритого D10 PR |
| [`research/d10-time-source-pinned-review-20261009`](https://github.com/juv4uk/sens/tree/research/d10-time-source-pinned-review-20261009) | без відкритого D10 PR |
| [`research/d10-uk-sanskrit-stress-context-rewrite-20261009`](https://github.com/juv4uk/sens/tree/research/d10-uk-sanskrit-stress-context-rewrite-20261009) | без відкритого D10 PR |
| [`research/d10-unification-lexical-harvest-20261009`](https://github.com/juv4uk/sens/tree/research/d10-unification-lexical-harvest-20261009) | без відкритого D10 PR |
| [`research/d10-unify-lexical-proposals-only-20261009`](https://github.com/juv4uk/sens/tree/research/d10-unify-lexical-proposals-only-20261009) | без відкритого D10 PR |
| [`research/d10-unique-bounded-modular-lift-20261009`](https://github.com/juv4uk/sens/tree/research/d10-unique-bounded-modular-lift-20261009) | без відкритого D10 PR |
| [`research/d10-unique-decodability-20261011-a`](https://github.com/juv4uk/sens/tree/research/d10-unique-decodability-20261011-a) | без відкритого D10 PR |
| [`research/d10-wsm-os-lisp-ownership`](https://github.com/juv4uk/sens/tree/research/d10-wsm-os-lisp-ownership) | без відкритого D10 PR |
| [`research/d10-wsm24-chamfer-law-20261009`](https://github.com/juv4uk/sens/tree/research/d10-wsm24-chamfer-law-20261009) | без відкритого D10 PR |
| [`research/d10-yantra-library-harvest-20261009`](https://github.com/juv4uk/sens/tree/research/d10-yantra-library-harvest-20261009) | без відкритого D10 PR |
| [`research/d10-younger-1967-exact-grammar-ambiguity-20261009`](https://github.com/juv4uk/sens/tree/research/d10-younger-1967-exact-grammar-ambiguity-20261009) | без відкритого D10 PR |
| [`test/4013-d10-canonical-lgg-529-native-prolog-20261009`](https://github.com/juv4uk/sens/tree/test/4013-d10-canonical-lgg-529-native-prolog-20261009) | без відкритого D10 PR |
| [`виправлення/d10-незмінний-донор-20261010`](https://github.com/juv4uk/sens/tree/%D0%B2%D0%B8%D0%BF%D1%80%D0%B0%D0%B2%D0%BB%D0%B5%D0%BD%D0%BD%D1%8F/d10-%D0%BD%D0%B5%D0%B7%D0%BC%D1%96%D0%BD%D0%BD%D0%B8%D0%B9-%D0%B4%D0%BE%D0%BD%D0%BE%D1%80-20261010) | без відкритого D10 PR |

## Завершення кожної ланки

1. Порівняти `main` та git head за semantic law, а не лише назвою; знайти donor SHA, негативний свідок і незалежний оракул.
2. Якщо вже у `main` — документувати main SHA/ledger ID і закрити дубль. Якщо унікальне та прийняте — доказовий append ledger + transition history, short-lived PR прямо до `main`, exact-head CI, single-writer #5041. Якщо не підтверджено — рішення власника в існуючій нитці.
3. 72 години від включення до черги без merge-or-close → власникова ескалація без нової issue.
4. Щоденне звітування в #5549: скільки підтверджено злитих, закритих як дубль, обґрунтовано відхилених, заблокованих, відкритих нових (ціль 0).

Пов'язані чинні нитки: [#5549](https://github.com/juv4uk/sens/issues/5549), [#5041](https://github.com/juv4uk/sens/issues/5041), [#4012](https://github.com/juv4uk/sens/issues/4012), [#4463](https://github.com/juv4uk/sens/issues/4463), [директива D10](https://github.com/juv4uk/sens/issues/5549#issuecomment-6104447540).
