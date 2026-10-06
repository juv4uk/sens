# Аудит: GPU на self-hosted runner — стан у `sens` (2026-10-06)

**Статус:** research / аудит, не авторитет. Не змінює контракт чи рішення.
**Дата:** 2026-10-06. **Джерело даних:** `origin/main` @ `450336271` (робоче дерево `main-sync` — лише де зазначено).

## Походження і межі довіри

Звіт склав агент-дослідник (ephemeral subagent, лише читання, модель не експонується середовищем) на завдання координатора. Координатор незалежно **не** перевіряв кожне твердження. Мітки: `source-confirmed` (прочитано в коді/конфігу), `empirically-confirmed` (виконано read-only команду або побачено CI-результат), `not-verified`.

Це перший прохід по **типовій гілці** (`origin/main`). Гілки та відкриті PR охоплюються окремим другим проходом.

## Мета

Щоб self-hosted runner (GTX 1050 Ti 4 ГіБ, CUDA 12.6, WSL2) справді використовував GPU у CI, а не лише мав мітку `gpu`.

## A. Що вже є

- Єдиний реальний запуск CUDA: `.github/workflows/gpu-worker-smoke.yml` (лише `workflow_dispatch`), `runs-on [self-hosted,Linux,X64,gpu,gtx-1050-ti,cuda-12.6]`. Викликає `cml-gpu-worker ping`, `probe`, `add-i32 7 1 2 3 4` і очікує `8 9 10 11` (source-confirmed). Прогін 37379684633 на `main` — success (empirically-confirmed через `gh run list`).
- Пакет `SGP\x01`: `crates/sens/src/gpu_execution_packet.rs` (428 рядків) і `contracts/compiler-gpu-execution-packet-v1.lisp`. Є encode/decode, канонічний varint, fail-closed на unknown opcode, trailing bytes та ліміт 1024 входів; юніт-тести є. Злито в #3845 (source-confirmed).
- Admission опкодів: `compiler_role.rs` допускає лише SelectorHead, SelectorTail, PairConstruct (D3). ATOM, EQ, D4+ повертають `None`, тобто fail-closed (source-confirmed).
- Реальна сторона GPU у PR #3745 (OPEN, не злитий): `benchmarks/sens-surface/gpu_numeric_buffer_map.py` викликає `cml-gpu-worker chain-file-i32` на i32, `x→x+1`. Перевірка — «вхід усі нулі → результат усі одиниці», без оракула SENS. Job `gpu-worker` у CI #3745 = SUCCESS (empirically-confirmed через `gh pr checks`).
- Runner: `gh api` показує один runner `wsm-i5-6400`, online, з мітками `author,guix,gpu,gtx-1050-ti,cuda-12.6`. Усі self-hosted job-и (і `guix`, і `gpu`) ідуть на нього одного (empirically-confirmed).

## B. Заглушка або лише специфікація

- `gpu_oracle.rs` на `origin/main` **не** placeholder: fail-closed схема v2 (#3889 злито). Позитивних рядків 0, статус `BLOCKED-MECHANISM`, contract sha256 справжній (source-confirmed).
- `gpu_admission.rs`: хардкод. D3 (7 операцій) і лише 2 з 16 D4; `created_at` зашито; `coverage_percent: 100` захардкоджено попри неповноту. Тести тривіальні: створюють `GpuAdmission` вручну, а не викликають `classify` (source-confirmed).
- `gpu_oracle_conformance.rs` (лише `main-sync` / PR #3907; у `origin/main` його немає): плейсхолдери `"quote-result-sha256"`, `"contract-11-6-sha256"`, 12 фікстур. Тест `all_fixtures_gpu_executable` стверджує GPU-виконуваність, що суперечить `BLOCKED` у #3889 (source-confirmed).
- `benchmarks/gpu-oracle-current/blocked-gpu-admission.json` — лише дані (BLOCKED).
- `experiments/gpu2-e1e3/witness.py` — протокол-адаптер; CUDA-ноги чекають `cml`.
- Документи `HETEROGENEOUS-EXECUTION-FABRIC`, `gpu2-bitwise-contract`, `PROPOSAL-TYPED-NUMERIC-BUFFERS` — специфікація.
- `compilation_artifact.rs` містить лише рядки `"gpu-cuda"`; `compiler_language.rs` і xtask навмисно **забороняють** слова cuda/ptx в експорті (мова не знає механізмів).
- Жоден код `sens` не викликає воркер і не споживає `SGP` (grep по локальних `cml` і `sens-futhark` теж порожній; для інших гілок не перевірялось).

### Workflow-и на `origin/main`: чи виконують CUDA-ядро

| workflow | runs-on | CUDA? |
|---|---|---|
| `gpu-worker-smoke` | gpu-мітки | ТАК (`add-i32`) |
| `d3-l1-l5-structure-projection`, `d8-fill-v2-seed`, `domain-tables-d1-d6`, `sens-code-migration`, `publish-binary-master` | gpu-мітки | НІ (python/cargo/git) |
| `d8-v2-semantic-inventory` | gpu-мітки | НІ (лише `nvidia-smi \|\| true`, потім python) |
| `gpu-oracle-current`, `compiler-role-cutover` | `[self-hosted, guix]` | НІ (свідомо; #3875 «free the GPU lane») |
| `ci.yml` та інші | guix | НІ |

## C. Що треба доробити (за порядком)

1. Закон `sens`: exact-domain batched/buffer map (D1–D7), якого ще немає. Блокує #3766 (відкритий, власник каже тримати відкритим). Без нього позитивний рядок оракула заборонений.
2. Довести #3801 (повна класифікація замість 9 хардкод-рядків); блокує споживача #3802.
3. Споживач пакета: `SGP` → воркер `cml`. Такого Rust-коду чи CLI у `sens`/`cml` зараз немає. Залежить від `cml#472` і `sens-futhark#85/#88`.
4. CI-ланка: обчислити CPU-дайджест через оракул `sens`, виконати на воркері, порівняти. Вимога #1566, #3700: розбіжність = RED, відмова CUDA = іменований стан. Зараз #3745 порівнює з «усі одиниці», а не з `sens`.
5. Виправити або прибрати плейсхолдер `gpu_oracle_conformance` (#3907), бо він суперечить #3889.
6. Не плутати з #3948: жоден job не має резервувати GPU без виконання на ній.

## D. Ризики та суперечності

- `#3948` містить 3 файли (не 2): окрім двох змін міток — новий `d8-recovery-gpu.yml`. Його job `recovery-witness` **падає**: `nvidia-smi: command not found` (код 127, CI run 37505890964); потрібен повний шлях `/usr/lib/wsl/lib/nvidia-smi`, як у smoke. Тіло PR саме визнає, що тести лишаються CPU.
- 5 workflow на `origin/main` уже мають gpu-мітки без CUDA (див. таблицю).
- Усі job-и на одному runner-і: мітка `gpu` без використання карти блокує всю чергу; саме тому #3875 зняв її. PR #3745 теж ставить smoke на `[self-hosted, guix]`: воркер — systemd-служба із сокетом `/run/cml-gpu-worker/worker.sock`, і мітка для доступу до GPU не потрібна.
- `compiler_nucleus_request_diff`: на `origin/main` виправлено (#3925, рядок 267 має `'\t'`). У локальному `main-sync` там літеральний TAB, і `cargo check -p sens --test compiler_nucleus_request_diff` падає: «character constant must be escaped» (empirically-confirmed, 1 помилка). Зламана лише локальна гілка.
- PR #3745: «focused PR verification» = FAILURE (причину не читали).
- `gpu_admission` каже, що D3-операції «мають іти через CUDA, CPU заборонено», тоді як оракул каже `BLOCKED`. Семантична суперечність між #3801 і #3766.

## E. Не перевірено / питання власнику

- Причина FAILURE у #3745; чи компілюється `origin/main` повністю.
- Чи читає воркер `cml` формат `SGP\x01` (дивились лише локальні клони).
- Чи потрібна мітка `gpu` взагалі, якщо воркер доступний через сокет із `guix`-runner-а; чи ставити ще один runner.
- Який закон (D3 batched? D5 арифметика?) власник готовий ратифікувати для #3766.

---

## Другий прохід: усі гілки та відкриті PR (2026-10-06)

Джерело: агент-дослідник (лише читання, модель не експонується), після `git fetch origin`. `origin/main` зсунувся з `450336271` на `d54ac156a` (#3957); числа нижче відносно `d54ac156a`. Мітки як у першому проході; координатор окремо не перевіряв.

**Масштаб** (empirically-confirmed): 2437 віддалених гілок не злиті в `origin/main`, 202 відкриті PR. Частина «незлитих» — це вже squash-злиті гілки (їхні GPU-файли за blob-хешем ідентичні `main`).

### GPU-дотичні гілки та PR

| № / гілка | відст./випер. | стан | що змінює на GPU-шляху | вердикт |
|---|---|---|---|---|
| #3745 `perf/gpu-offload-live-20261005` | 171/5 | CONFLICTING; `gpu-worker` pass, «focused PR verification» FAIL (причину не читали) | єдиний реальний CUDA у польоті: `gpu_numeric_buffer_map.py` → `cml-gpu-worker` (i32 `x→x+1`, перевірка «усі одиниці», без оракула SENS); smoke → `[self-hosted, guix]` + concurrency `gpu-gtx-1050-ti` | needs-fix (rebase; взяти concurrency і guix-мітку; з'ясувати FAIL; порівнювати з дайджестом SENS) |
| #3948 `ci/d8-recovery-gpu-runner` | 7/3 | MERGEABLE; `recovery-witness` FAIL (run 37505890964) | label-only: два workflow `ubuntu-latest` → gpu-мітки та новий `d8-recovery-gpu.yml` (`nvidia-smi` без повного шляху, далі `cargo test` на CPU) | needs-fix (`/usr/lib/wsl/lib/nvidia-smi`) або needs-owner-decision (чи резервувати GPU без CUDA) |
| #3907 `main-sync` | 47/1 | `cutover` pass; MERGEABLE | `gpu_oracle_conformance.rs`: заглушки `"quote-result-sha256"`, `"contract-11-6-sha256"`, тест `all_fixtures_gpu_executable` — суперечать `BLOCKED` на `main` | needs-fix (прибрати заглушки); не зливати як є |
| #3863 `fix/core-artifact-json-feature` | 59/2 | `cutover` FAIL, MERGEABLE | прибирає `serde`/`serde_json` з `crates/sens/Cargo.toml`, а на `main` їх використовують `compilation_artifact.rs`, `gpu_oracle.rs`, `gpu_admission.rs` | superseded-by #3864 або needs-fix |
| #3864 `fix/remove-rust-owned-artifact-duplicates` | 61/9 | CONFLICTING | видаляє `compilation_artifact*.rs`, `selfhost_lineage.rs` (−696 рядків); CUDA не чіпає; суперечить #3835 | needs-owner-decision + rebase |
| #3737 `infra/self-hosted-critical-gates-r2` | 172/12 | CONFLICTING; кілька FAIL | 15 `runs-on` з `ubuntu-latest` на `[self-hosted, linux, x64]` у 12 workflow; без CUDA, вся CPU-робота на один runner | needs-owner-decision (черга одного runner-а) + rebase |
| `agent/3766-gpu-oracle-blocked-handoff` (+v2…v5), `agent/chatgpt-sol/3802-gpu-execution-packet`, `agent/3801-gpu-admission`, `chatgpt/3784`, `3799`, `fix/gpu-packet-*`, `fix/3874-*`, `agent/3840-*` | — | без PR | GPU-файли ідентичні `main` або застарілі версії #3845/#3871/#3888/#3889 | stale (superseded-by `main`) |
| `gpu/1565-sens-cml-numeric-fasl`, `docs/1585-*`, `exp/1585-e1e3-witness` | ~1060 позаду | без PR | FASL typed numeric buffers без CUDA-виконання; документи/протокол | stale / needs-owner-decision |
| `master` | 30/5 | — | «reset to binary-only root»: видаляє `gpu-smoke` і GPU-файли `main` | **не зливати в `main`** (інша роль гілки) |

### Гілки, що змінюють runner-мітки (source-confirmed)

- `compiler-role-cutover.yml`: на `main` зараз `[self-hosted, guix]`; гілки перемикають його по колу — `fix/3874-selfhost-cond-shape-gpu` і `-current`, `agent/3840-bootstrap-bundle(-v2,-v3)` → gpu-мітки; `ci/compiler-cutover-hosted-cpu`, `ci/compiler-cutover-ubuntu-hosted` → ubuntu. Ризик відкату на gpu-мітку.
- ~14 `research/d8-*` додають `[self-hosted, linux, x64]`; `research/d8-fill-v2-seed`, `-inventory-256`, `d8-v2-gauge-s4`, `-geometry-s2`, `ratify/d8-3960`, `codex/sens-code-migration-tools`, `domain-sanskrit-names-d1-d6` додають gpu-мітки з `nvidia-smi || true` без CUDA.
- PR #3793 і #3794 та кілька `ci/*`/`fix/local-runner-routing-*` додають `[self-hosted, guix]`. Скан показав 41 гілку зі зміною self-hosted/gpu-міток (не вичерпно).
- Стан `main` (empirically-confirmed): 9 workflow з gpu-мітками, лише `gpu-worker-smoke` виконує CUDA; 13 на `guix`; 2 на `linux/x64` у нижньому регістрі.

### Оновлений список робіт

- **Вже в польоті (завершити, не будувати):** реальний CUDA-виклик воркера та concurrency-група — #3745; виправлення заглушок — #3907; GPU-recovery workflow — #3948 (лише label-only); відновлення збірки — #3863/#3864.
- **Не розпочато ніде** (пошук за назвами файлів/комітів, вмістом усіх гілок не grep-ано → not-verified): закон exact-domain batched/buffer map (#3766); повна класифікація #3801 (є лише злитий #3871); споживач `SGP` → воркер `cml`; CI-ланка «дайджест оракула SENS = дайджест GPU» (#3745 порівнює лише з «усі одиниці»).

### Рекомендований порядок (лише рекомендація)

1. Власник вирішує долю #3864 проти #3863 (і #3835). 2. #3745: rebase, guix-мітка, concurrency, з'ясувати FAIL, лише тоді merge. 3. #3948: виправити шлях `nvidia-smi` або закрити. 4. #3907: прибрати заглушки. 5. #3737 — після рішення про чергу одного runner-а. Застарілі кандидати на закриття: рядки про `agent/3766-*`, `3802`, `3801`, `fix/gpu-packet-*` та `gpu/1565`; `master` не чіпати.

### Не перевірено

- Причина FAIL у #3745 і #3863 (лог порожній); вміст кожного з 202 PR; чи лишиться `compiler-role-cutover` на guix (є 5 конкуруючих гілок).
- Питання власнику: чи резервувати мітку `gpu` для job-ів без CUDA (D8, #3948); чи лишити smoke на guix із concurrency; чи видаляти Rust-дублікати (#3864).

### Живий стан, перевірений координатором (локальний запуск, найнижчий щабель доказів)

- Воркер із `CML_GPU_WORKER_SOCKET=/run/cml-gpu-worker/worker.sock`: `ping` → `pong`; `probe` → GTX 1050 Ti, compute capability 6.1, 4294705152 байт; `add-i32 7 1 2 3 4` → `8 9 10 11`.
- Те саме відповідає user-воркер (`/run/user/1008/cml-gpu-worker.sock`). `nvidia-smi --query-compute-apps` показує обидва процеси воркерів (PID 547 і 964), тобто два CUDA-контексти займають VRAM.
- Службовий юніт `actions-runner@sens.service` виставляє `CML_GPU_WORKER_SOCKET=/run/user/1008/cml-gpu-worker.sock` (user-воркер), а `gpu-worker-smoke.yml` перекриває його на системний сокет; без явної змінної CLI шукає `/tmp/cml-gpu-worker.sock`, якого немає.

---

## Стан після виконаних змін (2026-10-06, вечір)

Розділи вище — знімок на момент аудиту. Далі зафіксовано, що змінилось відтоді (кожне — з посиланням на докази):

- **GPU-перевірка в CI додана й злита:** `scripts/gpu-worker-parity.py` і `.github/workflows/gpu-worker-parity.yml` (#3973). Перший прогін на runner-і `wsm-i5-6400`: `GPU_WORKER_PARITY_GREEN`, GTX 1050 Ti, CC 6.1, 1 048 576 елементів, `cuda_ns ≈ 10 мс`, негативний контроль (переповнення i32 → `UnsupportedInput`) пройдено. Це перевірка механізму, не паритет з оракулом SENS. Опис: `docs/tooling/GPU-WORKER-PARITY.uk.md`.
- **#3907 виправлено** (коміт `d2c84af19`): заглушки замінено виміряними результатами CPU-оракула, тест `every_fixture_matches_the_cpu_oracle` (4/4) проходить; зайву зміну імпортів у `gpu_execution_packet.rs` скасовано; опис PR виправлено. На момент запису PR ще відкритий.
- **Воркер `cml` виправлено:** на `master` він не збирався з `--features gpu-cuda` (cml#643, злито). На хості тепер працює нова збірка із резервом VRAM 1 ГіБ і замком допуску; дубль user-воркера й user-listener `cml` вимкнено.
- **Не змінилось:** закон batched/buffer map для #3766, повна класифікація #3801, споживач `SGP` → воркер, паритет з оракулом SENS, рішення про #3863/#3864 і #3737, зайві gpu-мітки на workflow-ах без CUDA (#3948 та інші).
- Рядок про `compiler_nucleus_request_diff` стосується лише локальної `main-sync`; на `main` це виправлено (#3925).

---

## English mirror (short)

First-pass audit of GPU execution in `sens` at `origin/main` @ `450336271`, by a read-only subagent; not independently re-verified by the coordinator. Only one workflow (`gpu-worker-smoke`, manual) actually runs a CUDA kernel; five others carry `gpu` labels without CUDA, which blocks the single shared runner. The `SGP\x01` packet exists and is tested but nothing consumes it. On `origin/main` the oracle is fail-closed (`BLOCKED-MECHANISM`); placeholder digests exist only in `gpu_oracle_conformance.rs` (PR #3907, `main-sync`). Blocking decision for the owner: which law to ratify for #3766 (exact-domain batched/buffer map).
