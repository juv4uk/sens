# SENS Silicon — bounded hardware D1/D2/D3 research pilot

**Not an independent ISA or ratification.** This isolated HDL experiment
implements only **physical T5 → exact-width words → D2 stack structure →
restricted D3 operations**. It reads no host-language names and imports no
retired `t`/`NIL` truthiness. The language authority remains
`language-contract.lisp` and ratified domain tables.

The synthesizable modules are `rtl/sens_t5_decoder.sv`,
`rtl/sens_d3_microcore.sv`, and `rtl/sens_silicon_d3.sv` (top-level byte-stream
interface). `byte_valid` is accepted on the rising edge when `byte_ready`
is high. `byte_last` means the final physical byte. The output is `done`,
`valid`, `error`, `result_is_predicate`, and `result_bit`. Each run must begin
with reset. There is no CPU, operating system, host Lisp interpreter or UART
in the datapath.

The prototype is deliberately **bounded**: up to 48 structural stack cells,
16 nested D2 frames and 16 CONS cells. The only evaluable D3 heads are:

| Domain word | Behavior / bound |
| --- | --- |
| `001` | QUOTE of D1 PredicateBit or structural EMPTY only |
| `010` | ATOM returns exact D1 bit |
| `011`, `100` | CDR and CAR of a bounded CONS |
| `101` | EQ of atomic typed values; refuses pairs rather than guessing |
| `111` | CONS into the bounded pair arena |

D3 `000` denotes the **structural empty object**, distinct from D1 `0`.
D3 `110` (COND), D2 dotted pairs, D4+ evaluation and non-atomic quotation
are **intentionally unsupported**; encountering them fails closed.
The T5 transport layer can retain widths D1 through D9, but the evaluator
admits only D1/D2/D3. This pilot must **not** be advertised as a general
SENS CPU, complete COND semantics, production synthesis, timing closure or
real FPGA execution.

## Reproduce on GitHub-hosted Ubuntu

```sh
python3 hardware/sens-silicon/tests/check_silicon_d3_vectors.py
iverilog -g2012 -s tb_sens_silicon_d3 -o /tmp/sens-silicon.vvp \
  hardware/sens-silicon/rtl/sens_t5_decoder.sv \
  hardware/sens-silicon/rtl/sens_d3_microcore.sv \
  hardware/sens-silicon/rtl/sens_silicon_d3.sv \
  hardware/sens-silicon/tb/tb_sens_silicon_d3.sv
vvp /tmp/sens-silicon.vvp
```

`tb/d3-primitives.t5.hex` is **only a testbench memory image of physical
T5 bytes**, not a new SENS executable format. The independent Python ROM
check rebuilds all six byte slices from the original
`examples/binary/d3-primitives-program.bits`, including the explicitly
normalized `ATOM(())` D2 empty frame → D3 `000`. Five original slices keep
identical physical bits; one is canonically normalized. The testbench streams
all 38 exact bytes into the RTL and checks outcomes `1, 1, 0, 1, 1, 0`.
Two malformed transports must fail closed. An additional physical EQ witness
proves D1:0 and D3:000 are distinct, and a D3:110 COND specimen must be
rejected until that law is admitted. The bench prints **total simulation clock
counts per reset+stream run** (including byte ingress), not nanoseconds,
wall time, FPGA frequency or throughput.

## Next research gate

Run synthesis with published LUT/register/BRAM results, expand the independent
Lisp-owned oracle, then admit two-part D3 COND in a separately ratified slice.
Until then: no hardware speedup claims, no `main` mutation outside the
single-writer merger, and no reuse of `fpga-lisp`'s historical NIL tagged ISA.
