# M0 — реєстр фізичних форматів SENS

**Знімок:** `02500ea33fb7a16fb534b309590fecf4125030c2`
**Git tree:** `02500ea33fb7a16fb534b309590fecf4125030c2`
**Репозиторій:** `juv4uk/sens`
**Статус:** READ-ONLY CENSUS / PARTIAL CONTENT AUDIT — не оголошення міграції завершеною.

## Підсумок

- Повний recursive Git tree на точному SHA: **7927 tracked blobs**, `truncated=false`.
- Знайдено **23 tracked фізичних `.sens` шляхів** та **0 tracked `.senc` шляхів**. У цьому знімку .senc відсутній як tracked file extension; формат живе лише як дослідницький код/контракт.
- Усі 23 файлів .sens мають same-stem .lisp у дереві; 13 також мають same-stem extensionless view, а 10 не мають його у знімку. Для останніх тріадну застосовність слід звірити з fixture policy, не створювати файли автоматично.
- Додано ключові Rust/CLI кодеки й читачі, мігратори/публікатори/аудитори, 69 workflow-кандидатів за назвами та 27 benchmark/physical-format кандидатів.

## Межі доказу

Наявність шляху не доводить активності маршруту; парні шляхи не доводять байтової парності. Вміст ключових джерел прочитано і SHA включено, решта кандидатів із неперевіреною логікою позначені `BLOCKED`.

`crates/sens/src/ternary_transport.rs` — фізичний T5: п'ятитритове пакування, відхилення байтів `>=243`, перевірка кінцевого padding. `crates/sens/src/binary_execution.rs` — декодування T5 → D2 → виконання. `crates/sens-cli/src/bin/sens-trit.rs` — CLI для фізичного `.sens`. Мігратори використовують no-clobber/atomic публікацію, а тріадні аудитори перевіряють source/physical/view hashes.

`crates/sens/src/source_packing.rs` і `crates/sens/src/canonical_reader.rs` відокремлені від фізичного T5 маршруту й залишені `BLOCKED` щодо цієї ролі, доки повний маршрут споживання не доведений.

## Відтворення

1. Перевірити Git tree через `GET /repos/juv4uk/sens/git/trees/02500ea33fb7a16fb534b309590fecf4125030c2?recursive=1` або локально `git ls-tree -r 02500ea33fb7a16fb534b309590fecf4125030c2`.
2. Відтворити фізичний перелік фільтром `path.endswith('.sens')`; для extensionless view перевіряти точний same-stem шлях, не створювати його.
3. Для байтового/семантичного приймання запустити чинні `scripts/audit_t5_file_pairs.py`, `scripts/report_t5_triplet_inventory.py` і `scripts/audit_t5_program_syntax.py` із поточним Rust reader на точному SHA; зберегти raw output та exit code. Цей PR не стверджує, що ці команди запускалися.

## Залежності

- М0 `#5444` → координатор `#5440` → епік `#5438`.
- М1 `#5445` залежить від Rust-оракула `#5439` і CI `#5442`.
- М2 `#5446` залежить від М0 та тріади `#4449`.
- М3 `#5447` — після М1/М2/green CI; downstream: CML `#695`, FPGA `#85`, Futhark `#132`, GraalVM `#301`.

У TSV `T5_REQUIRED` означає контракт T5 за замовчуванням, але не доведений parity. `SENC_RESEARCH` — експериментальний маршрут. `MIGRATION_CANDIDATE` — майбутній кандидат. `BLOCKED` — ще бракує прямої перевірки.

**Рядків маніфесту:** 185. Статуси: {"T5_REQUIRED":61,"BLOCKED":118,"SENC_RESEARCH":6}.

Машинозчитуваний звіт: `m0-inventory-2026-10-10.tsv`.
