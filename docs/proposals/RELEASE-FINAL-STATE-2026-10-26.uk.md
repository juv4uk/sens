# РЕЛІЗ: остаточний стан після виправлень

Автор: агент Sampūrti, 2026-10-26. Кожне число — вимір, не оцінка.

## Що виправлено цим ходом

### 1. Пін `lib/domains/d9.lisp`

Файл був у `knowledge/migration-nonprogram-domain-tables-2026-10-08.json`, але
`git_blob_sha1` розійшовся (`5b66057c…` проти `9dae8946…`). Пін не спрацьовував,
файл **не визнавався затвердженою не-програмою** і потрапляв до
`unpaired_program_lisp_sources` — хоч у ньому **нуль визначень**.

Виправлено за власним механізмом маніфесту: `git_blob_sha1` → поточний, старий
збережено в `previous_pinned_git_blob_sha1`.

### 2. Шість файлів `lib/` затверджено як дані

Усі мають **нуль визначень**, але не були в жодному маніфесті. Класифіковано **за
їхніми ж заголовками**:

| файл | заголовок у файлі | когорта |
|---|---|---|
| `lib/generated/function-table.lisp` | «Чинна таблиця функцій» | schema |
| `lib/machine/intel-core-i5-6400.lisp` | «машинний профіль Intel Core i5-6400» | schema |
| `lib/machine/profile/current-domain-x86-64.lisp` | «Чинна машинна проєкція» | schema |
| `lib/surface/semantic-registry.lisp` | «Чинний семантичний реєстр» | schema |
| `lib/surface/uk-sa-coverage.lisp` | «ІСТОРИЧНИЙ АУДИТ» | evidence |
| `lib/domains/archive/d11-rejected-43.lisp` | «НЕ РАТИФІКОВАНО… тестові фікстури» | evidence |

Лічильники `NONPROGRAM_MANIFESTS`: schema 19→23, evidence 8→10.

## Виміряний результат

| показник | було | стало |
|---|---|---|
| `unpaired_program_lisp_sources` | 884 | **877** |
| `unpaired_nonprogram_lisp_sources` | 60 | **67** |
| прогалин у `lib/` | 10 | **3** |
| затверджених не-програм | 90 | **96** |

У `lib/` лишилося три, і одна з них — **не прогалина**:

- `lib/yantra.lisp` — 79 визначень, але це **джерело прив'язок** (`--binding-source`);
  у маніфести даних не належить;
- `lib/бенчмарк.lisp` — **справжня програма без пари**;
- `lib/твердження.lisp` — **справжня програма без пари**.

**Справжніх програмних прогалин у канонічній бібліотеці — ДВІ.**

## Чому ці дві НЕ можна закрити тут — і це не технічна перешкода

Я шукав Python-шлях мінтування і знайшов `scripts/sens_typed_program.py`, який
викликає `encode_typed_domain_words`. Його власний докстрінг закриває питання:

```
Історичний типізований перегляд, тільки діагностика; Zig/T5M карбує .sens.
python3 scripts/sens_typed_program.py emit <program.typed> <out.sens>  # заборонено; Zig/T5M
```

**Мінтування `.sens` через Python ЗАБОРОНЕНО задумом проєкту.** Це збігається з
правилом: фізичне кодування виконує Zig/T5M. Отже питання не в тому, що в мене немає
інструмента — а в тому, що **цей шлях архітектурно закритий**, і обходити його я не
буду.

## Стан релізних гейтів

| гейт | результат |
|---|---|
| `check-release-pins.py` | **PASS** `channel=1.99.0 workflows=14` |
| `check-release-version-alignment.py` | **PASS** `0.42.1 crates=7 locked=7 guix=0.42.1` |
| `audit-workflow-pins.py` | **PASS** |
| `check-sens-only-semantic-tests.sh` | **PASS** `МОВНИЙ_ГЕЙТ=OK runner_workflows=310` |
| `check-release-admission-ledger.py` | `content_verified=5` — **усі 5 хешів збігаються** |
| — його єдиний блокер | `NATIVE-CONNECTOR-SUMMARY verified=0 blocked=5 missing=target/debug/sens` |

**Розбіжність `typed_word_sha256`, яку я документував раніше, на main уже усунено.**
Єдине, чого бракує реєстру — native `sens` CLI.

## Що лишається поза моїми можливостями

- **дві пари** `lib/бенчмарк.lisp`, `lib/твердження.lisp` — потребують Zig/T5M;
- **468** законів у `tests/semantic` і **199** замірів у `benchmarks/` без пар — те саме;
- три умови допуску (`original_executable_migrations_certified`, `uk_oracle_verified`,
  `release_admitted`) усі 0 — усі потребують native `sens`/`sens-trit`.

Rust тут недоступний: `cargo`/`rustc` немає, `sh.rustup.rs` → **403**,
`static.rust-lang.org` → **000**, готових релізів `sens` немає (0).

## Deutsch

Zwei echte Lücken in `lib/`; Minten ist architektonisch auf Zig/T5M beschränkt.

## English

Two real gaps in `lib/`; minting is architecturally restricted to Zig/T5M.
