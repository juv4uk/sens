# host_debt → 0 (निर्वाह)

## На чистому main
```bash
python3 knowledge/d11/restore/patch-host-debt-live.py
# або після повних part*.b64:
python3 knowledge/d11/restore/apply-debt0-all.py
python3 -m unittest tests.test_language_stays_in_sens.LanguageStaysInSens.test_frozen_host_debt_only_shrinks -q
```

`patch-host-debt-live.py` — канонічний шлях (не залежить від zlib payload).
D1–D10 ратифіковані в `lib/domains/` — не заглушки.
