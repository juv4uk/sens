# PR #5229: дослід парної статистики

Оригінали коду з PR #5229 (head `782312157cb746d03b001b97cffbb586630a8c93`) перенесено у `main` за початковими шляхами:

- `benchmarks/packed-vs-visible/paired_effect_ci.py`
- `docs/benchmark-measurement-standard.uk.md`
- `tests/test_paired_effect_ci.py`

Оригінальний PR-only staging workflow збережено у цьому архіві незмінним Git-блобом, бо робочі тести підключені в існуючий `.github/workflows/benchmark-registry.yml`, і дублювати workflow не потрібно. Це НЕ результат вимірювання продуктивності реального кодека.
