# Guix як execution substrate SENS

Цей каталог визначає відтворюване **середовище виконання**, а не семантику SENS.
Семантична влада лишається у Lisp/контрактах; Guix фіксує лише інструменти,
залежності та походження виконуваних артефактів.

## Влада і відтворюваність

1. `channels.scm` — точна ревізія Guix; це lock-файл рівня середовища.
2. `manifest.scm` — мінімальний базовий dev-layer.
3. `guix/manifests/*.scm` — додаткові capability layers.
4. `guix.scm` — package definition для SENS і `swarm-node`.
5. `./guix/run` — єдиний короткий вхід у pinned `time-machine -- shell --pure`.

Shared profile та звичайний `$PATH` — лише інтерактивна зручність. Результат,
який називається evidence-grade, не повинен залежати від них.

## Ролі

- `dev` — Rust/Cargo + GCC + certs + git + Racket.
- `bench` — `dev` + Python + Valgrind + taskset/coreutils.
- `native` — `dev` + GCC/binutils/LLVM/LLD/GDB/strace/NASM.
- `islands` — `dev` + SWI-Prolog + CLIPS + SBCL.
- `fpga` — `dev` + Yosys + Icarus Verilog + Verilator.
- `all` — композиція всіх попередніх capability layers.
## Запуск

```sh
./guix/run dev -- cargo test -p sens
./guix/run bench -- python3 benchmarks/sens-surface/run.py --help
./guix/run islands -- swipl --version
./guix/run --container fpga -- yosys -V
./guix/run --container --network dev -- cargo fetch
./guix/run --gc-root .guix-env bench -- cargo bench
```

`--container` ділиться лише поточним checkout як `/workspace`; мережа вимкнена,
доки її явно не додати через `--network`. `--gc-root` утримує closure від GC.

### Локальний Skylake fast path

Для Intel Core i5-6400 можна явно увімкнути локальний режим:

```sh
./guix/run --local-skylake native -- cargo build --profile ci-meta -p sens-cli --bin sens
```

Runner fail-closed звіряє модель CPU, живі `/proc/cpuinfo` flags та Lisp-owned
`intel-core-i5-6400` inventory. Лише після цього він задає Rust
`target-cpu=skylake` і C/C++ `-march=skylake -mtune=skylake`. Цей режим
призначений для локальної швидкодії, **не** для portable/evidence артефактів.

### Лагідний профіль WSL для цієї машини

Операційний baseline: 4 vCPU, 12 GB RAM, 4 GB swap, `vm.swappiness=20` і
`autoMemoryReclaim=gradual`. Репозиторії та build targets тримати на ext4 під
`/home/agents`, а не на DrvFS `/mnt/c`. Жодних custom-kernel, hugepage або
spectre-mitigation hacks цей профіль не вимагає.

## Swarm-node

Постійний сервіс не запускає бінарник із `target/release`. Кожна identity має
явний `GUIX_PROFILE`; `/proc/<PID>/exe` після старту має вести в `/gnu/store`.
`node-id` і `data-dir` залишаються даними identity, а executable є змінним
відтворюваним substrate.

## Перевірка

```sh
./guix/check
```

Self-check перевіряє shell syntax, package identity, відсутність repo-built
`swarm-node` у systemd template, dry-run повного role closure та dry-run пакета.
