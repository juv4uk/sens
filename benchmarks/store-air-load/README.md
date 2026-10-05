# STORE → AIR → LOAD benchmark lane

Цей каталог реалізує спільний machine-readable evidence-контракт для #3580 / #3595.

## Головна межа

Один і той самий канонічний exact-width об'єкт має **три різні фізичні питання**:

```text
STORE
  semantic_payload_bits
  storage_container_bits = physical_container_bytes * 8
  tail_unused_bits = storage_container_bits - semantic_payload_bits

AIR
  carrier_payload_bits
  framing_bits
  integrity_bits
  profile_overhead_bits
  total_wire_bits = carrier_payload_bits + framing_bits + integrity_bits + profile_overhead_bits
  payload_utilization = semantic_payload_bits / total_wire_bits
  ideal_airtime_seconds = total_wire_bits / bitrate_bps

LOAD
  decode / parse / lower / ready / cold / warm I-refs
```

Для `carrier_mode=exact-bitstream`:

```text
carrier_payload_bits = semantic_payload_bits
```

Тобто фінальний slack фізичного byte container **не стає автоматично ефірними
бітами**. Якщо конкретний профіль справді переносить повні байти, він має
явно використовувати `carrier_mode=byte-container`. Це transport/profile
рішення, а не властивість семантики SENS.

`integrity_bits` і `profile_overhead_bits` є окремими фізичними/profile
осями. Вони не ховаються у `framing_bits`. За замовчуванням обидва дорівнюють
нулю, тому чинні exact-bit fixtures зберігають ті самі результати. Це робить
схему напряму сумісною з `juv4uk/radio-log#36/#38`.

## Semantic identity guard

`paired-program` fixture спочатку проходить чинний
`current_en_vs_d1d8_cpu` preflight:

```text
English surface
  -> parse -> lower -> exact-domain trace

canonical exact-width source
  -> decode -> lower -> exact-domain trace
```

Рядки вимірюються лише коли trace/value/output збігаються. Digest рахується
від спільного lowered trace.

`mechanical` fixtures перевіряють тільки exact-width carrier mechanics і
мають `identity_proof=mechanical-exact-word-sequence`; вони не видаються за
доказ семантичної еквівалентності мовних програм.

## Запуск

З кореня репозиторію:

```sh
python3 benchmarks/store-air-load/run.py \
  --out /tmp/store-air-load.jsonl \
  --bitrate-bps 2

python3 benchmarks/store-air-load/validate.py \
  /tmp/store-air-load.jsonl
```

Runner сам збирає два release helpers:

```text
store_air_load_repr
current_en_vs_d1d8_cpu
```

Перший використовує production `parse_binary_source_words`,
`pack_binary_source_tokens` і `packed_transport_accounting`; другий дає
семантичний paired witness.

## LOAD

`load.py` заповнює LOAD-поля через Cachegrind, повторно використовуючи два
чинні helpers, а не створюючи новий loader:

```text
current_en_vs_d1d8_cpu
  baseline
  ingest
  lower
  ready
  full
  repeated N=1,10,100

startup_bench
  session
  bytes
  decode
  parse
  macro
  core
```

Похідні поля:

```text
canonical-packed.decode_i_refs = ingest - baseline
text-surface.parse_i_refs      = ingest - baseline
lower_i_refs                   = lower - ingest
ready_i_refs                   = ready - baseline
cold_total_i_refs              = full - baseline
warm_incremental_i_refs        = OLS slope repeated(N=1,10,100)
```

Тому whole-process cold-start не видається за parser/decode cost. Сирі totals,
repeat ladder і Core-bootstrap breakdown зберігаються в `provenance`.

Приклад після базового `run.py`:

```sh
python3 benchmarks/store-air-load/load.py \
  --in /tmp/store-air-load.jsonl \
  --out /tmp/store-air-load.load.jsonl \
  --helper target/release/examples/current_en_vs_d1d8_cpu \
  --startup-helper target/release/examples/startup_bench \
  --fasl lib/core.lisp.fasl \
  --only d3-quote-empty \
  --reps 1
```

#3513 лишається власником оптимізації Core bootstrap; цей каталог лише приєднує
його фазові виміри до спільного STORE → AIR → LOAD evidence-контракту.

## Поточні fixtures

Ratchet покриває всі критичні довжини:
- `zero-suffix-mechanical` — 6 біт, semantic zero suffix;
- `seven-bit-mechanical` — 7 біт, нижче байта;
- `seven-bit-overhead-mechanical` — ті самі 7 semantic bits плюс 5 framing, 3 integrity і 2 profile-overhead bits;
- `eight-bit-mechanical` — рівно 8 біт;
- `twelve-bit-mechanical` — 9..15-бітний клас;
- `mixed-28-bit-mechanical` — довга mixed-width послідовність D1..D7;
- `d3-quote-empty` — English/canonical paired semantic witness;
- `d3-car-empty` — другий English/canonical paired witness.

Для кожної canonical fixture runner незалежно рахує
`expected_semantic_bits = sum(word_widths)`, звіряє його з production helper,
перевіряє `artifact_bytes = ceil(bits/8)` і вимагає exact-width round-trip
через `unpack_binary_source_words`. CI також містить навмисно неправильний
reference encoder «один байт на слово» й перевіряє, що validator його відкидає.

Фактичні розміри, ratios і airtime генеруються runner-ом; у README немає
ручних benchmark-констант.
