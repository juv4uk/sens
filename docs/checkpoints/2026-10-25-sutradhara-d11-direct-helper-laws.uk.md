# Sūtradhāra — D11 direct-helper / контрольний зріз 2026-10-25

## Стан
Базовий HEAD до цього коміту: `a79e30bf29348b1575b8a29bb6450add484db7e4`.
Функція D11 `розділити-суміжні-за-ключем` уже мала публічну
SENS-перевірку `підтвердити-правильний-суфікс`, але не мала
окремого прямого негативного SENS свідка в фізичному гейті.

## Виконано в коді
- У `tests/semantic/d11-clojure-partition-singleton-key-law.lisp` додано два позитивні SENS-закони прямого helper:
  singleton та точне збереження групи й D3-суфікса з D1:ні як елементом.
- `tests/semantic/d11-clojure-partition-direct-helper-bad-tail-negative.lisp` подає неправильний D1:ні як хвіст; замикання навмисно
  видавали б CDR Type, але SENS має відхилити структуру CAR Type спочатку.
- `scripts/prove-lisp-semantic-t5m.sh` підключає негатив до чинних direct, paired, standalone
  SENS/Zig/T5M маршрутів з raw SHA-вхідними квитанціями.

## Межі доказу
Статично перевірені дужки двох SENS-файлів і однозначна підстановка
в гейт. Нативні SENS, Zig, Rust, hosted CI **не запускалися в цьому ході**.
Жодного D11 opcode, хостової бізнес-логіки, ратифікації чи релізного GO.

## Наступному агенту
На повному SHA: `bash -n scripts/prove-lisp-semantic-t5m.sh`;
`cargo test --locked -p sens --test d11_clojure_partition_by`;
`bash scripts/prove-lisp-semantic-t5m.sh target/debug/sens
target/debug/sens-trit /tmp/sens-d11-helper-proof`.
Перевірити прямий/парний/автономний Type і SHA-квитанції. Далі
перемінтити невідповідну D11 фізичну трійку
(`docs/checkpoints/2026-10-25-sutradhara-d11-t5m-source-drift.uk.md`),
а потім дослідити D11 group-by/juxt/alist, D12+ та F6 #5984.
Реліз `l0.42.0`: NO-GO, рішення за власником.

**Deutsch:** SENS-Helfer positive und negative Sprachzeugen, nativer Replay offen.
**English:** Added SENS helper witnesses; native execution remains unverified.
