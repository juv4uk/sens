# М1 #5445 — межа CLI/читача: T5 (`.sens`) за замовчуванням

- **Задача:** #5445 (М1, «ефективний кодек») · батько #5440 · епік #5438
- **Репозиторій:** `juv4uk/sens`
- **База:** `main` = `33bd5a32877f63de78eee28b0f97ea629e83a4fa`
- **Дата:** 2026-10-10
- **Статус:** CHANGED (read-only відтворення + fail-closed свідок). Canonical
  loader **НЕ змінювався** — вимога М1 до проходження обох оракулів.

## Призначення

Зафіксувати наявний інваріант: канонічний фізичний носій — **T5 (`.sens`)**;
дослідний кодек `.senc` (профілі F3/F4, adaptive/framed) **не автовиявляється**,
не відкривається як програма і не підміняє типовий маршрут. Межа лишається
**fail-closed**: усе не-`.sens` відхиляється, а не декодується «найкращим
зусиллям».

## Матриця маршрутів CLI (HEAD)

Джерело: `crates/sens-cli/src/bin/sens-trit.rs` (307 рядків).

| Маршрут | Рядок | Поведінка | Фізичний носій |
|---|---|---|---|
| `sens-trit <path>` (1 арг, `.sens`) | 140 | → `open` (лише відкриття, **ніколи** неявне виконання) | `.sens` |
| `encode path.lisp` | 147 | `.lisp` → новий `.sens` (create_new, без перезапису) | вхід `.lisp` |
| `open`/`view path.sens` | 158 | `read_sens` → `open_ternary_program` | `.sens` |
| `decode path.sens` | 166 | вертикальний дамп слів | `.sens` |
| `explain path.sens` | 174 | точна діагностика граматики, без виконання | `.sens` |
| `eval`/`eval-core4 path.sens` | 182 | явне виконання (Core4 лише на запит) | `.sens` |
| `verify path.lisp` | 198 | звірка `.lisp` з парним `.sens` | `.lisp`+`.sens` |
| невідома команда / 1 арг не-`.sens` | 204 | `USAGE`, exit 1 | — |

**Межа розширення** (`read_sens`, `sens-trit.rs:24-29`):

```rust
if path.extension().and_then(|e| e.to_str()) != Some("sens") {
    return Err("expected a physical .sens file".into());
}
```

**Незвний маршрут** (`sens-trit.rs:140`): однопараметрична форма активується
**лише** для шляху, що закінчується `.sens`. `.senc` цій умові не відповідає →
потрапляє у гілку помилки `USAGE`, ніколи не відкривається і не виконується.

## Доказ відсутності `.senc`-кодека на HEAD

```
$ git ls-tree -r --name-only origin/main | grep -cE '\.senc$'   # → 0
```

У `crates/sens` і `crates/sens-cli` немає ні `.senc`, ні `framed3/4`, ні `tb33`,
ні `adaptive_encoder`. Межа «T5 за замовчуванням» тримається **за відсутністю**.
Дослідний адаптивний кодек існує лише як чернетка PR #5429 (не в `main`).

## Що додано (заморожування інваріанта)

1. `crates/sens-cli/tests/codec_boundary_t5_default.rs` — негативні CLI-свідки:
   - `canonical_t5_is_the_default_and_roundtrips_byte_for_byte` — T5 відкривається,
     `encode(open(b)) == b` байт-у-байт;
   - `senc_extension_is_never_autodetected_even_with_valid_t5_bytes` — навіть
     канонічні T5-байти під `.senc` відхиляються (і неявно, і через `open`);
   - `non_sens_extension_is_refused_on_open` — `.lisp` як `.sens` відхилено;
   - `out_of_domain_bytes_are_refused_without_fallback` — байти `>= 243` → відмова;
   - `unknown_subcommand_is_refused` — `USAGE`, stdout порожній.
2. `scripts/check-t5-default-boundary.py` — статичний fail-closed страж із
   self-test: сканує канонічні крейти на заборонені токени дослідного кодека й
   вимагає наявності межі розширення в `sens-trit.rs`.
3. `.github/workflows/t5-codec-boundary.yml` — `--self-test`, статичний скан,
   і hosted `cargo test -p sens-cli --test codec_boundary_t5_default`.

## Обмеження (чесно)

- Canonical loader (`crates/sens/src/{canonical_reader,source_packing,binary_execution}.rs`)
  **не змінювався** — М1 прямо забороняє це до проходження **двох незалежних
  оракулів** (#5439 / PR #5457).
- Rust-тест верифікується **hosted CI на точному SHA**; локальна збірка не
  запускалася (resource policy роя). Статичний страж перевірено локально.
- Профіль F3 «до 128 тритів» і `UNSUPPORTED` для out-of-domain на рівні
  явного `.senc`-режиму — поза цим PR (немає кодека в `main`; залежить #5439).

## Наступний атомарний крок

Після злиття #5439/#5442 — розширити свідок до явно-режимної матриці `.senc`
(F3/F4, opt-in, без autodetect) і додати byte fixtures; canonical loader
чіпати лише після двох оракулів.
