# Zig T5 для SENS · механічний exact-width транспорт

**Стан (14.10.2026):** незалежний Zig-кодек додано в робочу гілку. Користувач повідомив про успішний локальний парний Zig 0.16.0 ↔ Rust T5 прогін зі збігом фізичних байтів, однак первинні samples/environment та SHA ще не долучено до репозиторію для незалежної перевірки. Нативний SENS залишається єдиним джерелом семантичних PASS. Це вузька транспортна реалізація, не production codec.

## Джерело відповідності
- Чинний Rust: `crates/sens/src/ternary_transport.rs`
- Zig: `research/zig-codecs/t5/t5.zig`
- Issue: [#5767](https://github.com/juv4uk/sens/issues/5767), benchmark: [#5771](https://github.com/juv4uk/sens/issues/5771).
- Фізичний T5 (`.sens`) не змінюється; F3C (`.senc`) та F3M — окремі наступні задачі.

`Word { width, bits }` зберігає точну бітність D1–D9; `bits` є лише машинним зберіганням бітів, **не десятковою семантичною ідентичністю**. Немає відображення слова на назви функцій і немає допуску викликів.

Encode: одне слово = його біти 0/1; між словами тільки транспортний роздільник 2, пакування 5 тритів на байт, фізичне EOF без додаткових маркерів, в останньому байті лише 0..4 трити 2. Decode: fail-closed для фізичного байта >=243, порушення ширини, порожніх слів, хвоста/падінгу та невідповідності повторно створеному канонічному носію. Максимальна довжина — 4 MiB як у Rust.

## Перевірка (потрібний Zig 0.16.0)

```bash
zig version            # очікується 0.16.0
zig test research/zig-codecs/t5/t5.zig
```

Тести містять відомі фізичні вектори (передбачувані байти), exhaustive перевірку однословних D1–D9 (1022 значення), багатослівні форми, негативні фізичні байти, недійсні довжини, зламані роздільники, недопустимі слова.

**Важливо:** ці тести перевіряють тільки Zig-механіку. Для статусу DONE потрібна окрема фактично запущена матриця Rust encode→Zig decode та Zig encode→Rust decode на фіксованому корпусі, реальні SHA та нативний SENS execution receipt там, де перевіряється семантика.

## Ручний парний стенд (повідомлений локальний запуск; незалежна перевірка pending)

Потрібні Linux x86_64, Zig 0.16.0, Rust/Cargo та libc. Запускати лише на тому самому фізичному CPU. Скрипт виконує `zig test`, збирає Zig `-O ReleaseFast -lc` і поточний Rust `--locked --release`, перевіряє **повну рівність фізичних байтів** для чотирьох однакових корпусів перед публікацією результатів і зберігає raw-парні samples та SHA.

```bash
python3 research/zig-codecs/t5/run_paired_bench.py \\
  --pairs 3 --out-dir /tmp/sens-zig-rust-t5
cat /tmp/sens-zig-rust-t5/STATUS
cat /tmp/sens-zig-rust-t5/summary.md
```

Порівнюються Zig [`bench.zig`](bench.zig) та чинний Rust [`zig_t5_matched_bench.rs`](../../../crates/sens/examples/zig_t5_matched_bench.rs). На кожному 1, 16, 128, 1024 повтореннях трійки точних слів `10 100 01` збігаються **всі фізичні байти**, не лише FNV-хеш. Отримана таблиця описує тільки прогріту механіку T5. Алокації/peak RSS, F3C, cold startup, confidence intervals та нативний SENS semantic receipts — **NOT_MEASURED**, їх ще слід довести окремо.

## Бенчмарки Zig ↔ Rust (обов'язкова залежність)

Основний proof gate [#5771](https://github.com/juv4uk/sens/issues/5771). Спочатку запустити паритет, потім парні encode/decode на тих самих typed words і фізичних байтах, з однаковими обсягами та CPU, release-конфігураціями, серіями та warmups. Записати `ns/op`, `MiB/s`, `allocs/op`, p50/p95, 95% CI і *реальні* бінарні/корпусні SHA. Якщо паритет не пройшов — `BLOCKED_NO_TIMING`, а не вигаданий speedup.

Ніяких нових автоматичних workflow: єдина автоматична точка — наявна `.github/workflows/ci.yml`. Важкі бенчмарки — тільки ручний режим до окремого дозволу власника.

**Невизначеність:** Zig і Rust недоступні в середовищі цієї сесії; користувач надав результати локального бенчмарку, але raw `samples.jsonl`, `environment.json` і точний SHA ще не звірені незалежно. Не оголошувати production або semantic PASS.

## Ширини: два профілі + статус D11 і D24+ (важливо для споживачів)

Додано 14.10.2026 за фактом перевірки на реальному корпусі (`zig-t5-parity.yml`, run 38559040625, success: 118/118 `.sens` round-trip, 5/5 негативів відхилено).

- **Звичайний шлях:** `t5.encode` / `t5.decode` / `t5.validatePhysical` — максимум **D9** (≤9 біт). Це виконуваний профіль.
- **Координатний шлях:** `t5.encodeCoordinates` / `t5.decodeCoordinates` — максимум **D10** (≤10 біт). D10 — лише механічна координата; вона **не** дає callability.

**Наслідок:** `lib/bridge/prolog-to-datalog.sens` містить D10-координати. Читати його треба **координатним** шляхом, інакше `UnsupportedDomainWidth`. (Саме на цьому спіткнувся `parity_t5.zig` до виправлення — файл при цьому валідний, round-trip OK.)

- **D11 — у мові Є, у T5-кодеку НЕМА.** `publication_cycle.zig` прямо асертить `width = 11 -> UnsupportedDomainWidth`, а «ordinary physical preflight must NOT widen to include D10». **Але D11 — не просто таблиця:** `#d11` працює як справжній носій ширини 11 у мові, і ним користується x86-64 кодувальник, напр. `(0011 x86-encode-jnp-rel8 (0010 (displacement) (x86-encode-jcc-rel8 #d11 displacement)))` у `lib/machine/encoding/x86-64.lisp` (так само `x86-encode-jnp-rel32`, `x86-encode-setnp-r8`, `x86-encode-setpo-r8`, `x86-encode-cmovnp-r64-r64`, `x86-encode-cmovpo-r64-r64`); `language-contract.lisp` тримає `(major . #d11)` (Contract 11.8); є `lib/domains/d11.lisp` — ратифікований власником **тестовий словник** (exact-width 11-bit keys, 2048 ємність: `read-file`, `read-sens`, `decode-t5`, `length`, `count`, `equal?`, `print`, `slice`, `take`, `drop`, `t`, `nil`, `if`…), authority `knowledge/d11-testing-vocabulary-ratified.json`.
  **Наслідок для транспорту:** програми, що вживають `#d11` (x86-кодувальник), **не пройдуть T5-кодек** як є — потрібен або окремий профіль ширини 11, або явне рішення власника. Не розширювати T5 на 11 біт мовчки.
- **D24+ (числові) — окремий канал.** `domain_ladder.zig`: `DomainWord(1..10)` — виконувані координати; `WideDomainWord(24/48/96/192)` — точні числові носії (не арифметика, не допуск викликів). Кодек T5 їх не несе.

Приклад перевірки координатного шляху: `parity_t5.zig` + `tools/parity_corpus.py` (workflow `zig-t5-parity.yml`).
