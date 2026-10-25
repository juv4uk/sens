# СПРАВЖНІ ЧЕРВОНІ НА `main` (run 40152687796, sha a971c705)

Автор: агент Niścaya, 2026-10-25. Джерело: GitHub Actions, гілка `main`,
job «Охоронець · Rust · Zig · SENS», лог 675342 Б.

## Три кроки, що падають

```
✗ 6.  Заборона нових сирих кодів у змінених Lisp-файлах
✗ 13. Rust — механізм без мовного оракула
✗ 19. Lisp → Zig/T5M → SENS — позитивні та негативні закони   (ТАЙМ-АУТ 15 хв)
```

## Точні id (з логу)

```
REGRESSION id=d10-clips-all-asserts-improper-tail        expected=Type-rejection actual=unexpected-success
REGRESSION id=d10-clips-assert-head-direct-positive      expected=SENS-execution actual=rejected
REGRESSION id=d10-clips-equal-head-positive              expected=SENS-execution actual=rejected
REGRESSION id=d10-clips-printout-head-direct-positive    expected=SENS-execution actual=rejected
REGRESSION id=d6-let-letstar-preflight-positive          expected=SENS-execution actual=rejected
REGRESSION id=d6-let-three-fields                        expected=Type actual=unexpected-paired-error
REGRESSION id=d6-letstar-three-fields                    expected=Type-diagnostic actual=unclassified-rejection
REGRESSION id=rust-repl-syntax                           expected=parsable actual=syntax-error
REGRESSION layer=bootstrap expected=exact-current-SENS-source actual=outdated-physical file=lib/core4.sens
REGRESSION layer=selection expected=executable-Lisp-witness actual=empty-manifest
REGRESSION layer=selection expected=successful-manifest-selection actual=failed
```

**Сім id-дефектів + чотири структурні.**

## Найпряміше виправний: `rust-repl-syntax`

`.github/workflows/ci.yml:58`:

```sh
if ! rustfmt --edition 2021 --emit stdout crates/sens-cli/src/repl.rs > /dev/null; then
  echo "::error file=crates/sens-cli/src/repl.rs,title=RUST_REPL_SYNTAX::REGRESSION id=rust-repl-syntax layer=rust-cli expected=parsable actual=syntax-error"
  exit 1
fi
```

**Що я перевірив і відкинув:**
- edition збігається: крейт `edition = "2021"` (Cargo.toml:4), перевірка теж 2021;
- баланс дужок `{}` — **0** (збалансовано);
- блокові коментарі `/* */` — **0**;
- непарних лапок `"` — **0**;
- 2024-конструктів (`unsafe extern`, `async gen`, `raw const/mut`) — **немає**.

**Отже `rustfmt` падає не через edition і не через структуру.** Точний текст
помилки в лог **не потрапив**: крок робить `> /dev/null` для stdout, а stderr
`rustfmt` у витягнутому фрагменті відсутній. **Щоб побачити причину, треба
запустити `rustfmt --edition 2021 --emit stdout crates/sens-cli/src/repl.rs`
без переадресації — або прибрати `> /dev/null` у кроці.**

## Дві родини решти дефектів

1. **d6/d10 — «expected=SENS-execution actual=rejected»** (4 випадки): свідок
   має виконуватися, а SENS його **відкидає**. Разом із
   `d6-let-three-fields expected=Type actual=unexpected-paired-error` це схоже на
   **одну причину** — семантику `let`/`let*`/`assert` у d6 і d10.
2. **`lib/core4.sens` фізичний дрейф** + **`layer=selection … empty-manifest`**:
   структурні, не семантичні. Перше лікується пере-карбуванням, друге —
   вибором файлів для прогону.

## Deutsch

Echte rote Prüfungen auf `main`: sieben id-Defekte und vier strukturelle.

## English

Real red checks on `main`: seven id defects and four structural ones.
