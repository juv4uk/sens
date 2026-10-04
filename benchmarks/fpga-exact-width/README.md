# FPGA exact-width evidence

Issues: #3045 exact semantic widths, #3046 BRAM packing, #3047 DSP/LUT width sweep.
Parent benchmark gate: #1987. FPGA synthesis comparison: #2004.

This lane records **backend economics only**. Hardware cost never defines SENS
semantic identity.

## Boundary

```text
semantic object
  -> exact (subject, semantic_width, bits)
  -> backend representation / padding / packing
  -> LUT / FF / BSRAM / DSP
```

`semantic_width` and `physical_word_width` are separate fields. A wider
physical carrier must never be reported as a wider semantic domain.

## First measured baseline — 2026-10-04

Target: Gowin `GW5A-LV25MG121NC1/I0` (GW5A-25A)
Tool: Gowin EDA `V1.9.12.03`

The checked-in evidence came from vendor synthesis + place-and-route reports.

| case | semantic | physical | Logic | Register | BSRAM | DSP |
|---|---:|---:|---:|---:|---:|---:|
| D3 decoder exact | 3 | 3 | 4 | 8 | 0 | 0 |
| D3 decoder padded control | 3 | 4 | 9 | 9 | 0 | 0 |
| D3 decoder padded control | 3 | 8 | 11 | 9 | 0 | 0 |
| add/xor width control | 3 | 3 | 7 | 4 | 0 | 0 |
| add/xor width control | 4 | 4 | 9 | 5 | 0 | 0 |
| add/xor width control | 8 | 8 | 17 | 9 | 0 | 0 |
| RAM 1024×3 | 3 | 32* | 0 | 0 | 1 | 0 |
| RAM 1024×4 | 4 | 32* | 0 | 0 | 1 | 0 |
| RAM 1024×8 | 8 | 32* | 0 | 0 | 1 | 0 |

`* physical_word_width=32` is reported from the inferred SP BSRAM primitive's
32-bit `DO` port visible in the vendor netlist/P&R warnings. It is not a
semantic width.

### What this baseline proves

- A D3 decoder carried as exact 3 bits used less logic than otherwise-equivalent
  4-bit and 8-bit carriers that must reject invalid high-bit states.
- Wider arithmetic datapaths cost more logic/registers in this bounded add/xor
  control.
- One isolated 1024×3, 1024×4 or 1024×8 inferred RAM each consumed one BSRAM,
  so exact width alone does **not** prove a BRAM-block saving. #3046 must measure
  dense packing and pack/unpack overhead.

### What it does NOT prove

- The 3/4/8 ALU rows are width controls, not "D3 padded to D4/D8".
- No Fmax claim is made. The first RTL has no useful register→logic→register
  timing path, and Gowin reported no Actual Fmax. `fmax_hz` is therefore
  deliberately null.
- No semantic domain is preferred because hardware likes its width.
- No 24-bit or other arithmetic limb is preferred; #3047 remains open.

## Files

- `schema.json` — hardware evidence contract.
- `validate.py` — fail-closed JSONL validator.
- `evidence/2026-10-04-gw5a25a.jsonl` — first measured rows.
- `repro/bench.v`, `repro/clk.sdc` — exact source used for this first slice.

## Validate

```bash
python3 benchmarks/fpga-exact-width/validate.py \
  benchmarks/fpga-exact-width/evidence/2026-10-04-gw5a25a.jsonl
```

Future local-agent rows should preserve raw vendor reports separately when
practical and include their SHA-256 in `source_rpt_sha256`.

## Admission rule

A hardware result may choose a backend mechanism only after semantic validity is
already established. It may not mint, move, widen or collapse a SENS resident.
