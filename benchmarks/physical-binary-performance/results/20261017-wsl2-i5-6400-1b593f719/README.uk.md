# Походження та межі вимірювання

- Виміряний вихідний `main`: `1b593f719ad9d64a46363b22d918afac0ca0e94f`.
- Середовище: WSL2 x86_64, Intel Core i5-6400 @ 2.70 GHz; запуск через `./guix/run bench`.
- Guix channel pin із `channels.scm`: `5375f33fd48ffc3b39ecc1c5993e299258a043d8`.
- Інструменти з Guix bench-профілю: Cargo 1.93.0, Rust 1.93.0, Python 3.12.12, Valgrind 3.27.0. Пінований Zig 0.16.0 передано як `ZIG`; Cachegrind у цьому вимірюванні вимкнений.
- Параметри: 8 наявних фізичних T5-фікстур, 4 прогріви й 21 вимір на кожну з трьох CLI-доріжок; кодування — 1 прогрів і 5 вимірів на фікстуру.

`results.json` містить точні SHA коміту, виконуваних файлів, кодека й вимірювача. `raw.tsv` і `compile-raw.tsv` зберігають сирі вибірки; `report.md` — зведення.

## Інтерпретація

Це вимірювання фізичного T5-кодування, розміру артефакту та часу окремого процесу разом зі стартом, I/O, виконанням і stdout. До часу допускаються лише побайтно тотожні T5 roundtrip та узгоджений stdout виконавчих доріжок. Це не доводить семантичну правильність довільних програм, hot-loop throughput, час холодного OS-кешу або перевагу над іншою мовою. Числа не слід порівнювати між різними машинами.

## Відтворення

Із кореня репозиторію, маючи локальний pinned Zig 0.16.0:

```sh
./guix/run bench -- bash -c 'export ZIG=/шлях/до/zig-0.16.0/zig CARGO_HOME=/home/agents/.cargo CARGO_TARGET_DIR=/tmp/sens-t5-bench-target CARGO_BUILD_JOBS=2 CARGO_NET_OFFLINE=true; python3 -m unittest discover -s benchmarks/physical-binary-performance -p "test_*.py" -v; cargo build --locked --release -p sens-cli --bin sens --bin sens-trit; python3 benchmarks/physical-binary-performance/run.py --sens "$CARGO_TARGET_DIR/release/sens" --sens-trit "$CARGO_TARGET_DIR/release/sens-trit" --reps 21 --warmup 4 --out /tmp/sens-physical-binary-performance'
```
