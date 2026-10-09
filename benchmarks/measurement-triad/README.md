# SENS: три незалежні крила вимірювань (#5227)

**Це інструменти, а не нове твердження про швидкість SENS.**
Перший вимірюваний об'єкт — справжній публічний API
`DomainCoordinate::owner_residency()` на D3 (7 зайнятих із 8 клітин),
без нових Rust-законів та без англійського виконуваного словника.

## 1. I-refs (Valgrind / iai-callgrind)

```sh
sudo apt-get install valgrind
export SENS_ROOT="$(pwd)"
cargo install --locked --version 0.16.1 iai-callgrind-runner
( cd /tmp && cargo bench --manifest-path "$SENS_ROOT/benchmarks/measurement-triad/Cargo.toml" \\
  --bench instruction_lane )
```

Інструкційний gate — **тільки** при однаковому SHA-відомому workload,
контрактному паритеті, профілі збірки, версіях Callgrind/Valgrind,
компіляторі, CPU/архітектурі, binary hash та pinned baseline.
Поки ці поля не зіставлені, **не робити числовий gate**. I-refs ≠ ns.
Iai порівнює Callgrind інструкції, тоді як наявні SENS Cachegrind
звіти лишаються окремою серією; не можна віднімати їхні лічильники.

## 2. Час (Criterion)

```sh
( cd /tmp && cargo bench --manifest-path "$SENS_ROOT/benchmarks/measurement-triad/Cargo.toml" \\
  --bench wall_time_lane )
```

Criterion виконує прогрів та збирає семпли. Це wall-time для конкретного
in-process D3 механізму, НЕ startup/ingest/lower/execute всієї мови.
Для них є окремі стенди; їхні фази не змішувати. Hosted CI є шумним:
не використовувати цей результат як жорсткий поріг. Для строгих висновків
фіксувати governor, CPU affinity, turbo та шум фонових задач.

## 3. Парний вердикт (K–J-inspired hierarchical bootstrap)

```sh
python3 -m unittest discover -s benchmarks/measurement-triad -p 'test_*.py'
python3 benchmarks/measurement-triad/verdict.py --input paired.json --out verdict.json
```

Формат `sens-paired-wall-time/v1`:

```json
{
  "schema": "sens-paired-wall-time/v1",
  "metric": "wall_time_ns",
  "parity": {"passed": true, "oracle_id": "exact-oracle-SHA"},
  "provenance": {
    "git_sha": "commit",
    "binary_sha256": "sha256",
    "cpu_model": "cpu",
    "rustc": "rustc-version",
    "os": "kernel",
    "affinity": "cpu-ids",
    "governor": "performance-or-recorded-unknown",
    "turbo": "disabled-or-recorded-unknown",
    "timing_source": "monotonic-clock"
  },
  "pairs": [
    {"process_id":"restart-001","order":"AB","baseline_ns":1000,"candidate_ns":920},
    {"process_id":"restart-001","order":"BA","baseline_ns":980,"candidate_ns":918}
  ]
}
```

Вимагається **не менше 8 незалежних process restarts і 4 парних A/B
вимірювань у кожному**, присутність AB та BA у кожному process.
Порядок визначають рандомізованим seed до збору, а не підганяють після.
Застосовано *ієрархічний paired bootstrap за логарифмом відношення*;
це практичний підхід, натхненний Kalibera–Jones, **не дослівна реалізація
їх variance-components методу**. Він не виправляє coordinated omission
у навантажувальних open-loop тестах і не замінює незалежного оракула.

Вердикти: `FASTER`, `SLOWER`, `INCONCLUSIVE`, `BLOCKED`.
Межа практично значущої різниці — 1% за замовчуванням. При `BLOCKED`
відсутні числові оцінки; при недостатній кількості незалежних процесів
— `INCONCLUSIVE`. Тести використовують **лише синтетичні дані**.

## Доказовий шлюз і вихід на пенсію

Порівняння можливе лише після parity на тій самій роботі і тому самому
семантичному поколінні, з однаковим зібраним binary/helper для порівняння
поверхонь. Реальний висновок повинен прикладати raw samples, незалежний
SHA baseline, host provenance та обмеження. Стенд виходить на пенсію
після заміни кращим ratified/measured стендом, із записом старого SHA
та перекриттям свідчень; не стирати минулі вимірювання.

Не запускати CPU-only статистичні гейти на GPU-only локальному ранері.
Цей пакет ізольований від production workspace; core SENS не отримує
ніяких нових runtime dependencies.

У SENS кореневий `.cargo/config.toml` фіксує офлайновий `vendor/`. Для цього
ізольованого стенду запускайте Cargo **з `/tmp` і абсолютним `--manifest-path`**,
щоб Cargo не успадкував цей vendor-override. Production Cargo конфіг не змінюємо.
