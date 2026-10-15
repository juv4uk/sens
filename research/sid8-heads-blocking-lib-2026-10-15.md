# Акт: 18 Sens8/Sid8-голів, що блокують `lib/` (для твого рішення)

**Не код.** Кожен 8-бітний код нижче стоїть як **call-head** у програмі — і потребує
**поточного D3–D6-резидента**. Це рішення власника: який резидент кожному.

| head (Sid8) | файлів | статус у таблиці мостів |
|---|---:|---|
| `00000000` | 3 | НЕ в таблиці |
| `00000001` | 2 | НЕ в таблиці |
| `00000010` | 1 | НЕ в таблиці |
| `00001100` | 1 | BRIDGE → D5:01010 (але мігратор не зловив) |
| `00101100` | 1 | НЕ в таблиці |
| `00101110` | 1 | BRIDGE → D8:11111101 (але мігратор не зловив) |
| `01001011` | 1 | BRIDGE → D9:110101001 (але мігратор не зловив) |
| `01011010` | 1 | SEPARATE — потребує власної клітинки |
| `10000100` | 1 | BRIDGE → D9:101101111 (але мігратор не зловив) |
| `10011100` | 1 | BRIDGE → D6:001000 (але мігратор не зловив) |
| `11011011` | 1 | НЕ в таблиці |
| `11100000` | 1 | НЕ в таблиці |
| `11101101` | 2 | НЕ в таблиці |
| `11101110` | 1 | НЕ в таблиці |
| `11110100` | 3 | НЕ в таблиці |
| `11110101` | 1 | НЕ в таблиці |
| `11110110` | 1 | НЕ в таблиці |
| `11110111` | 3 | НЕ в таблиці |

## Файли (перші приклади)

- `00000000`: domains/d8.lisp, generated/function-table.lisp, surface/semantic-registry.lisp
- `00000001`: function-table-mechanisms.lisp, surface/function-signatures.lisp
- `00000010`: machine/intel-core-i5-6400.lisp
- `00001100`: island-math-evidence.lisp
- `00101100`: utf8.lisp
- `00101110`: machine/encoding/admitted-iclass-index.lisp
- `01001011`: machine/dispatch/native-first-execute.lisp
- `01011010`: core.lisp
- `10000100`: machine/cpu/intel-core-i5-6400-inventory.lisp
- `10011100`: surface/semantic-registry-api.lisp
- `11011011`: reason.lisp
- `11100000`: core4.lisp
- `11101101`: clips-import.lisp, world.lisp
- `11101110`: yantra.lisp
- `11110100`: lisp-fs.lisp, machine/admission/x86-64.lisp, machine/effects/u64.lisp
- `11110101`: machine/operands/x86-64.lisp
- `11110110`: si-derived.lisp
- `11110111`: machine/dispatch/native-first-parity.lisp, meta-eval-first-class.lisp, meta-eval.lisp

**Разом:** 18 кодів, 26 файлів. **5** мають ціль у таблиці мостів (не зловились), **1** SEPARATE, решта — без цілі.

**Що потрібно від власника:** для кожного коду — назвати **поточний D3–D6-резидент** (або підтвердити міст).
