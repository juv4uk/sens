# D10 — апаратна карта → перевірювані універсальні закони (2026-10-09)

**Статус: RESEARCH ONLY / UNRATIFIED.** Це не список нових ратифікованих резидентів. **Зміна лічильника selected: 0; координат: 0; ратифікацій: 0.** Завдання: [sens#4012](https://github.com/juv4uk/sens/issues/4012), [sens#4463](https://github.com/juv4uk/sens/issues/4463), [wsm-os-lisp#74](https://github.com/juv4uk/wsm-os-lisp/issues/74), [sens#4896](https://github.com/juv4uk/sens/issues/4896). D2 залишається єдиною владою структури/керування мовою.

## 1. Verified hardware evidence (snapshot, NOT live reprobe)

Першоджерела станом на цей зріз:
- `juv4uk/wsm-os` `docs/OWNER-HARDWARE-PROFILE.md`, Git blob `cb0fa1af003b3a0a6ed61a94ce3ebb065a0fe32b`; `README.md` blob `08a6a03ec089893848ab66dbea4e95fb0514fc18`.
- `juv4uk/wsm-os-lisp` `docs/OWNER-HARDWARE-PROFILE.md` (snapshot 2026-08-29; фізичний boot witness 2026-09-03).
- `juv4uk/sens`: D9 ratified `knowledge/d9-ratified.json` blob `<read from live Git before admission>`; D10 selected inventory blob `292ef3086114ad0dfe71776c831c2a31b39352a8`, **636/1024 selected, 256 selector-law coordinates, 380 unplaced, 388 missing, 0 ratified** on this read.

Фізичний хост: Gigabyte H170-Gaming 3 / AMI UEFI F22e; Intel i5-6400 Skylake, 4 ядра без SMT, little-endian x86-64, 16 GiB DDR4-2133; L1d/L1i по 32 KiB на ядро, L2 по 256 KiB, L3 6 MiB; Intel HD 530; NVIDIA GTX 1050 Ti 4 GiB `sm_61`; Kingston SNV2S1000G NVMe 1 TB, Samsung 850 EVO SATA 120 GB, Samsung HD321KJ SATA 320 GB; Killer E2200 1 Gbit/s. Тестовий WSL2 на час профілю мав ~7.7 GiB RAM / 4 vCPU і **віртуальні**, не справжні PCI-пристрої.

Справжній UEFI probe засвідчив CPUID `0x000506E3`, GOP 1024×768, змінну карту пам'яті, TSC близько 2.7 GHz. TSC не є абстрактним незмінним годинником, а адреси GOP/CR3/ACPI/SMBIOS із boot session **заборонено** вбудовувати константами. Інструкції AVX2/BMI2/FMA/RDRAND/RDSEED — факультативні target capabilities, не зміст нових кодів D10. BIOS/CSME/HECI є окремим предметом спостереження, не Core.

Додаткові дослідницькі пристрої, відомі з ширшого проєкту, **не підтверджені цим hardware-profile snapshot**: FPGA (GW5A-25 у `fpga-lisp`), ESP32-S3 N16R8, RTL-SDR/MSI.SDR, ADS1115, AS5600. Для них потрібен окремий live manifest `device ID + firmware + driver/toolchain + witness`; не видавати їх за автоматично доступні у WSL або bare metal.

## 2. Строга межа володіння

```text
SENS D1–D10    : математичне/мовне meaning, незалежне від CPU/GPU/FPGA
D2             : структура й контроль мови, не периферія
CML            : зниження/емісія з точним збереженням meaning
wsm-target-contract: target ABI, числові теги/вирівнювання
wsm-os-lisp    : GC, scheduler, image, capability/effect gateway, I/O
wsm-os         : фізичні та QEMU witness, а не фабрика Core meanings
CPU/GPU/FPGA   : mechanisms, не автоматичні D10 residents
```

Already accounted in `wsm-os-lisp#74`: MMIO-CAPABILITY, MMIO-READ/WRITE, PCI-CONFIG-READ, BLOCK-READ/WRITE/FLUSH, GC-COLLECT, ROOT-ENUMERATION, TASK-STATE/SUSPEND/RESUME/ABORT, SAVE/RESTORE-LIVE-IMAGE, REBIND-CAPABILITIES. **Не дублювати їх у D10 з причини наявності заліза.** Existing D10 `SWAP-REF!` needs independent atomicity review; `MISSING-CAPABILITY`, `NATIVE-OBSERVATION`, `MAKE-OBSERVATION`, `UNIX-TIME-NOW` already appear in research inventory. D9 already contains `MONO-MS`, `UTC-NOW`, `ROTATE`, `ARITHMETIC-SHIFT`, `LOGBITP`, `NUMERIC-BUFFER-REF`, `NUMERIC-BUFFER-MAP`. D10 already has `DPB`, `GF2-MINIMAL-RECURRENCE` and Gray encode/decode research, so no new aliases.

## 3. Семантичні root claims для review — ще НЕ SELECTED

Правило кожного рядка: `width = D10`, `coordinate = null`, `ratified = 0`, `blocked_source = NONE (hardware-motivated, not a proven migration blocker)`; `surface_uk/surface_ukr` — пропозиція, не чинний словник. Наведені очікувані відповіді — **reference vectors**, не виконані SENS/Chez/SWI/Z3 oracle runs. Спочатку довести відмінність від D1–D9 і 636 D10 рядків за поведінкою, потім мінімальний незалежний root, тільки тоді proposal ledger і власникове рішення. Похідність сама по собі не забороняє кандидата; псевдонезалежність забороняє.

### HW-01 — unsigned saturating addition

- **Запропоновані поверхні:** `нас-дод` / `насичене-додавання`; donor motivation: i5 scalar/AVX2, GPU SIMD, fixed-width FPGA arithmetic; independent semantic donor/oracle **pending**.
- **Law:** `sat_add_u(w,a,b)=min(a+b, 2^w-1)`, `w>=1`, `0<=a,b<2^w`; invalid domain => explicit typed rejection, no silent wrap.
- Positive: `(3,6,1)->7`; `(3,2,3)->5`. Negative: `(3,7,1)->0` is **false** (wrap is wrong); negative/oversized input must reject.
- **Dedup attack:** explicit `MIN` + `+` + `EXPT` derivation, exact arithmetic/overflow functions; review whether root merits its own resident as algebraic fixed-width law.

### HW-02 — unsigned saturating subtraction

- **Поверхні:** `нас-від` / `насичене-віднімання`.
- **Law:** `sat_sub_u(w,a,b)=max(a-b,0)`, same domain.
- Positive: `(3,4,2)->2`; `(3,0,1)->0`. Negative: `(3,0,1)->7` is **false**.
- **Dedup:** test whether HW-01 and HW-02 are one justified dual family or two necessary names, and whether lower Core arithmetic already supplies the same law.

### HW-03 — GF(2) polynomial remainder

- **Поверхні:** `ост-гф2` / `залишок-полінома-гф2`; useful for radio bitstreams, CRC and FPGA checks, not a CRC-32 device primitive.
- **Law:** nonnegative integers encode polynomial coefficients over GF(2); `gf2_rem(a,p)` is the unique remainder with `deg(r)<deg(p)`, using XOR elimination; `p>0`.
- Positive: `gf2_rem(0b1011,0b11)=0b1`; `gf2_rem(0b110,0b11)=0`. Negative: integer remainder `11 % 3 = 2` **must not substitute** polynomial remainder; `p=0` rejects.
- **Dedup:** generic `DIVMOD` is different ring; existing GF2 minimal recurrence is a distinct algorithm. Prove with two independent GF2 implementations, then classify polynomial division versus mere wrapper.

### HW-04 — finite linear convolution over an explicit semiring

- **Поверхні:** `лін-згорт` / `лінійна-згортка`. Mathematical use from audio, SDR and DSP; algorithm (CPU/GPU/FPGA) is not meaning.
- **Law:** for finite `a,b`, `c[k]=Σ_(i+j=k) a[i]*b[j]` using explicitly supplied exact semiring operations; empty input yields empty sequence.
- Positive: `[1,2] * [3,4] -> [3,10,8]`; `[1] * [0,2] -> [0,2]`. Negative: cyclic convolution `[11,10]` for the first input is **false**. Reject operation without defined additive/multiplicative identities.
- **Dedup:** generic nested MAP/FOLD or polynomial multiplication might define the same law. Clarify whether this is one admitted universal mathematical meaning or merely library composition.

### HW-05 — canonical exact-width wordstream interpretation

- **Поверхні:** `біт-спл` / `сполучити-точні-слова`; candidate is *pure value meaning*, not wire transport, file layout, D2 reader/framing or byte alignment.
- **Law:** for `w>=1`, `concat_w([x_1,...,x_n])` is the ordered concatenation of **exactly w** high-to-low bits per validated word; resulting length `n*w`; inverse rejects length not divisible by w. Never insert silent byte padding.
- Positive: `w=3,[5,1] -> 101001`; `w=10,[1,1023]` has exactly 20 bits. Negative: `w=10,[1]` silently becoming a 16-bit *semantic* word is **false**.
- **Dedup:** D2 owns framing; D10 already includes bitfield/Gray/word roots; BIT/VECTOR/APPEND may derive this operation entirely. HOLD as semantic candidate if only a codec mechanism remains.

### HW-06 — atomic compare-and-exchange (state-transition law)

- **Поверхні:** `звір-змін` / `атомарно-порівняти-та-замінити`; memory model and state semantics **not yet ratified**; **HOLD** until explicit concurrency model.
- **Claim:** on an abstract mutable cell, CAS(expected,new) returns old value and success flag, changes cell iff old=expected, and is linearizable: each concurrent call has one legal atomic point. `EQ` identity and state value equality must be specified.
- Positive: cell 5, CAS(5,7) -> (5,true), cell 7; then CAS(5,9) -> (7,false), cell 7. Falsifier: with two simultaneous CAS(5,6) and CAS(5,7), both reporting success from initial cell 5 is **invalid**.
- **Dedup:** D10 `SWAP-REF!` research and D1–D9 mutation must be checked. Do **not** claim linearizability from sequential `DEREF; RESET`. No CPU `LOCK CMPXCHG` instruction or memory barrier becomes Core identity by itself.

### HW-07 — fixed-point rounding at explicit precision

- **Поверхні:** `квант-точ` / `точне-квантування`; motivation: ADS1115/AS5600, audio, GPU/FPGA fixed-point; sensor register widths are not Core law.
- **Claim:** `quantize(x,step,mode)` accepts exact rational `x`, positive rational `step`, and explicit tie rule (e.g. nearest-even), returns integer index `q` with `q*step` as decoded value; distinguish rounding rule at halfway.
- Positive nearest-even: `x=5/2, step=1 -> q=2`; `x=7/2 -> q=4`. Negative: `x=5/2 -> 3` under nearest-even is **false**. Invalid nonpositive step rejects.
- **Dedup:** `ROUND` + rational division may fully supply meaning; absent independent law mark DERIVED not new resident.

## 4. Device and OS mechanisms — NO NEW D10 ID solely for these

| Hardware / observation | Correct owner | Safe first witness |
|---|---|---|
| UEFI F22e, GOP, ACPI, CPUID, MSRs, HECI/CSME | `wsm-os` physical/firmware probe | read-only, no firmware writes, dynamic discovery |
| Heap/GC/roots, page tables, OOM | `wsm-os-lisp` runtime + `wsm-target-contract` | bounded QEMU allocations, roots, stack, deterministic OOM |
| 4-core scheduling, IRQ, timers, TSC | `wsm-os-lisp` package/effect gateway | monotonic nondecreasing observation; no constant TSC GHz |
| NVMe/SATA disk, VirtIO block | `wsm-os-lisp` driver package | QEMU image only; failures/flush order; NEVER real partitions |
| NIC Killer E2200, TCP, serial/console | `wsm-os-lisp` package | mocked/virtual interface; capability-denied behavior |
| GTX 1050 Ti `sm_61` CUDA | `wsm-cuda` hosted compute | compare exact input-output to scalar oracle; no assumed native bare-metal NVIDIA driver |
| Intel HD 530 | `wsm-os` UEFI GOP | boot text/serial then observed framebuffer |
| GW5A-25 FPGA | `fpga-lisp` substrate | width-exact test vectors and equivalence to SENS oracle |
| ESP32, SDR, ADC, angle encoder | peripheral owners, manifest TBD | detachable capability, sampled-value provenance, no fabricated live access |

## 5. Clockwork acceptance gates (do not claim tested without logs)

1. **Semantic gate:** same pure input -> exact same SENS outcome under interpreter, CML-hosted, QEMU, FPGA oracle / GPU reference if applicable; include overflow, error and empty cases.
2. **Memory gate:** 16 GiB host is not a default heap promise; bound RAM in QEMU; 100k tail calls + GC root preservation + explicit OOM outcome; no host raw pointer as portable identity.
3. **Clock gate:** monotonic duration never confused with UTC wall time or FS revision; hardware timing/precision is observation, not SENS meaning; no hardcoded RDTSC rate.
4. **Boot gate:** QEMU UEFI/serial first, then owner-authorized read-only real-hardware witness; never auto-write physical NVMe/SATA/ESP flash or BIOS.
5. **Device gate:** absent/disconnected capability returns typed failure, no silent fallback; no assumption that WSL virtual PCI == physical topology.
6. **Repro gate:** log oracle name/revision, command, exact output, seed, architecture, build flags and result; no unsupported 100% parity claim.
7. **D10 gate:** run exact D1–D9 and current D10 **behavioral** dedup and intra-family minimization; D2-control attack; only independent roots can enter proposal ledger. `coordinate=null`, `ratified=0` until owner decision. The owner-approved selection→ledger CI (#4894 lineage) must be green before new selected rows.
8. **Swarm gate:** research branch only; **one merger-agent** writes main; do not merge or force-push from this work; avoid another competing D10 ledger authority.

## 6. Immediate coordination

- To `sens#4012` / `sens#4463`: review HW-01..HW-07 for minimal semantics and rank by actual migration blockers (unknown != zero). State owner decision per root: SELECT-RESEARCH / DERIVED / HOLD / REJECT, with oracle attachments.
- To `wsm-os-lisp#74`: map the hardware matrix to existing device/runtime milestones, do not spawn a shadow D10 registry.
- To `sens#4896`: GF(2), exact words and fixed-point formulas need mathematical oracle; mutable CAS needs concurrency oracle; no unrelated CLHS/CLOS reseeding.
- Owner ratifies *after* independent evidence and growth-gate, not after naming these proposals.

**Result of this document:** seven explicit HW research claims, a dedup/ownership roadmap, zero new D10 selected IDs, no edits to ratified core or main.
## 7. Executable reference witnesses (not SENS parity)

A separate **pure Python / stdlib** mathematical reference is committed on the same research branch at `tests/test_d10_hardware_reference_20261009.py`. It contains 11 `unittest` cases for the seven claims above: expected values, counterexamples, invalid-domain rejections, a bounded GF(2) degree invariant, and a **sequential-only** two-CAS-contenders consistency check.

Reproduction:

```sh
python3 -m unittest discover -s tests -p 'test_d10_hardware_reference_20261009.py' -v
```

This reference was locally run with 11/11 tests passing on 2026-10-09; it is **not** a Chez/SWI/Z3 oracle, **not** a concurrent CAS linearizability proof, **not** an actual SENS implementation, and **not** proof of QEMU/GPU/FPGA parity. Those are the independent next evidence gates. No other D10 state or ledger files are changed by this package.
