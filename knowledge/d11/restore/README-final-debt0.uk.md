# Final host_debt до релізу (अनन्त)

## Залишок на main до apply
- `scripts/guard-domain-function-reuse.py` (2→19)
- `tests/test_audit_all_lisp_triplets.py` (15→16)
- `knowledge/d1-d11-surface-verdicts-20261024.json` (новий у scan path)

## Застосувати
```bash
python3 knowledge/d11/restore/apply-final-debt0.py
python3 -m unittest tests.test_language_stays_in_sens.LanguageStaysInSens.test_frozen_host_debt_only_shrinks -q
```
Потрібні payload: `audit-debt0.zlib.b64` (або part1..3) та `guard-debt0.part1..3.b64`.

## D1–D10
Ратифіковані. Не переписувати.
