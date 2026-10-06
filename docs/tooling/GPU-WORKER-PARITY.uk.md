# GPU worker parity: справжня GPU-перевірка в CI

Статус: робочий інструмент перевірки механізму, **не авторитет** над семантикою
SENS. Авторитет лишається в `language-contract.lisp` та оракулі; GPU-оракул
залишається `BLOCKED-MECHANISM` (sens#3889), доки не ратифіковано закон
exact-domain batched/buffer map (sens#3766).

## Навіщо

Мітка `gpu` на job-і ще не означає, що карта використана. Ця перевірка доводить,
що runner **справді виконав ядро CUDA** на GTX 1050 Ti через спільний воркер
`cml-gpu-worker` і що результат збігається з CPU-референсом.

## Що робить `scripts/gpu-worker-parity.py`

1. `ping` воркера, `probe` пристрою (ім'я, compute capability, VRAM) і
   `add-i32` як швидкий димовий тест.
2. Ланцюг `x -> x + 1 + 2 + 3` над 1 048 576 елементів i32 через
   `chain-file-i32-provenance` (з `GITHUB_REPOSITORY`, `GITHUB_RUN_ID`,
   `GITHUB_JOB` у provenance), порівняння з референсом на CPU **побайтово для
   всіх елементів**; `cuda_ns > 0` доводить, що ядро виконувалось.
3. Негативний контроль: переповнення i32 мусить бути відхилене воркером
   (`UnsupportedInput`), а не обернуте мовчки.
4. JSON-свідчення (пристрій, `admission_wait_ns`, `cuda_ns`) іде в підсумок job-а.

Будь-яка відсутність воркера, CUDA чи розбіжність результату дає іменований
стан `GPU_WORKER_PARITY_RED <ПРИЧИНА>` (`WORKER_UNREACHABLE`, `CUDA_DEVICE_ABSENT`,
`GPU_NOT_USED`, `PARITY_MISMATCH`, `OVERFLOW_NOT_REJECTED` тощо) і код виходу 1.
Тихого зеленого немає.

## Обмеження

- Не викликати скрипт під зовнішнім `flock`: замок допуску
  `/run/cml-gpu-worker/gpu-admission.lock` бере сам воркер, і обгортка
  заблокувала б сама себе.
- Референс лише арифметичний (`+` на i32 без переповнення). Паритет з оракулом
  SENS (CPU-значення з `gpu_oracle_conformance`) додається окремо, коли буде
  закон для #3766.
- Перевірка йде лише на змінах GPU-шляху (`crates/sens/src/gpu_*.rs`,
  `compiler_role.rs`, пакет `SGP`, сам скрипт і workflow), щоб не займати єдину
  карту всім PR.
- Потрібен воркер `cml`, зібраний з `--features gpu-cuda` (виправлення збірки: cml#643).

## Запуск вручну

```bash
python3 scripts/gpu-worker-parity.py --evidence gpu-worker-parity.json
```

---

## English mirror (short)

`scripts/gpu-worker-parity.py` proves the self-hosted runner actually executes a
CUDA kernel: it chains i32 adds over 1,048,576 elements through the shared
`cml-gpu-worker`, compares every element with a CPU reference, and checks that
i32 overflow is rejected rather than wrapped. Failures are named
(`GPU_WORKER_PARITY_RED <REASON>`), never a silent green. It is a mechanism
check, not SENS-oracle parity (still blocked by sens#3766). Do not wrap it in an
external `flock`; the worker takes the admission lease itself.
