# Відновлення test_domain_function_reuse_rule.py

```bash
python3 knowledge/d11/restore/apply-fulltest.py
python3 -m unittest tests.test_domain_function_reuse_rule tests.test_language_stays_in_sens -q
```

Першопричина host_debt: суцільні `(визначити` у probe-рядках.
Фікстури: `tests/_guard_probe_fixtures.py`.
