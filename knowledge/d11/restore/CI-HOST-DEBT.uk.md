# CI: host_debt перед language-stays-in-sens

```bash
python3 knowledge/d11/restore/apply-debt0-all.py
# або напряму:
python3 knowledge/d11/restore/patch-host-debt-live.py
python3 -m unittest tests.test_language_stays_in_sens.LanguageStaysInSens.test_frozen_host_debt_only_shrinks -q
```

D1–D10 = `lib/domains/d1.lisp`…`d10.lisp` (ратифіковані, не заглушки).
