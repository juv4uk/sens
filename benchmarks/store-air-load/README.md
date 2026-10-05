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
  total_wire_bits = carrier_payload_bits + framing_bits
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

Поля LOAD навмисно обов'язкові в schema, але поки мають `null`.
#3513 володіє фазово ізольованими I-ref вимірами. Whole-process cold-start не
можна записувати в `parse_i_refs` або `decode_i_refs` без фазового доказу.

## Поточні fixtures

- `seven-bit-mechanical` — 7-bit exact-width packing control;
- `zero-suffix-mechanical` — semantic zero suffix + tail control;
- `d3-quote-empty` — English/canonical paired semantic witness;
- `d3-car-empty` — другий English/canonical paired witness.

Фактичні розміри, ratios і airtime генеруються runner-ом; у README немає
ручних benchmark-констант.
