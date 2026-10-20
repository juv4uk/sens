# T5M-3 на асемблері — і бенчмарк проти Zig / Rust / C

Асемблерна реалізація ядра кодека **T5M-3** (фізичний носій SENS) на x86-64 і
порівняння швидкості з референсними реалізаціями.

## Що таке T5M-3

Потік тритів (0/1, роздільник `2`) пакується по **15 тритів у 3 байти
little-endian**: `3^15 = 14348907 < 2^24`, тож 15 тритів точно вміщаються в
24 біти. Значення групи — `value = value*3 + trit`. Дзеркалить
`research/zig-codecs/t5m3.zig` і SENS-функції `т5м-у-байти` / `т5м-з-байтів`
у `lib/core4.lisp`.

Це **механізм транспорту**, а не джерело семантики SENS.

## Файли

| файл | що це |
|---|---|
| `t5m_pack.S` | асемблерний pack/unpack (x86-64 SysV, без libc) |
| `t5m_ref.zig` | Zig-реалізація з C-ABI |
| `t5m_ref.rs` | Rust-реалізація з C-ABI |
| `bench.c` | спільний харнес: міряє asm, Zig, C (і Rust за `-DHAVE_RUST`) |
| `check_asm.py` | локальна перевірка: mmap `.text`, звірка з `scripts/sens_t5_codec.py` |

## Збірка й запуск

```sh
# асемблер
as --64 -o t5m_pack.o t5m_pack.S

# Zig
zig build-obj t5m_ref.zig -O ReleaseFast -femit-bin=t5m_ref.o

# Rust
rustc -O --edition 2021 --crate-type staticlib t5m_ref.rs -o librust_t5m_ref.a

# харнес
zig cc -O2 bench.c t5m_pack.o t5m_ref.o -o bench            # asm + Zig + C
zig cc -O2 -DHAVE_RUST bench.c t5m_pack.o t5m_ref.o librust_t5m_ref.a -o bench
./bench
```

## Результати (локально, x86-64, 3 млн тритів, 200 повторів)

Коректність: asm, Zig і C дають **байт-у-байт ідентичний** результат, і всі
три unpack повертають вихідні трити.

| реалізація | M трит/с |
|---|---|
| pack asm | ~1410 |
| pack zig | ~1500 |
| pack c | ~2650 |
| unpack asm | ~600 |
| unpack zig | ~800 |
| unpack c | ~750 |

Спостереження: ручний асемблер **на рівні Zig** на pack, але C виграє (компілятор
розгортає/векторизує). На unpack асемблер поступається: ділення на 3 замінено
магічним множенням `(x*0xAAAAAAAB)>>33`, що пришвидшило unpack у 4.4 раза
(133 → 600 M трит/с) проти найпростішого варіанта з `div`, але Zig-компілятор
усе одно тримає перевагу. Rust-стовпець додається в CI (див. workflow).

## CI

`.github/workflows/t5m-asm-bench.yml` (ручний запуск) збирає все разом із Rust і
друкує таблицю.
