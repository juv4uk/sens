# Архів першоджерел GitHub PR #5457

Оригінал: https://github.com/juv4uk/sens/pull/5457
Заголовок: дослід(T5): незалежний Rust-паритет D2 для 1022 слів і негативні F3/F4 (#5439)
Точний head джерела: `4b0918a1ab0c7fdee7ba6351abc6c35c391bbd1e`
Стан на перевірці: `open`, base: `main`, files: 10.
Приймальний head main: `a7dd9cc18ad8d4c9ab057d4d29de8358b3625aea`.

Статус: НЕАКТИВНИЙ АРХІВ. Оригінальні Git blobs перенесено побайтно,
без зміни активних шляхів чи ратифікації D1–D10. Це НЕ повне git merge PR.
Потрібна окрема перевірка тестів, чинного контракту й dedup перед використанням як коду.

## Збережені об'єкти
- `.github/workflows/lisp-paren-balance.yml` — `8fded5f434b90debf8554095a3520917ddbe2017`, modified, +22/-5
- `.github/workflows/machine-golden-corpus.yml` — `4da5de90dc3efdba54874ac0d9234ea05abcbe96`, added, +36/-0
- `.github/workflows/physical-binary-sens-cli.yml` — `b8f1e4d95fdc037fa4b1862936fce078e005db05`, modified, +3/-0
- `crates/sens/tests/fixtures/machine-asm-corpus.json` — `07cd4714369dcdf01dd77a705deeff5f3791b5d8`, added, +91/-0
- `crates/sens/tests/t5_exact_word_d2_admission.rs` — `bcb269c3fe6adaaa739de78dc7783e9565f488af`, added, +147/-0
- `lib/machine/admission/x86-64.lisp` — `b6f3bb0aa136860fb343aa89c13e1ce63914bbda`, modified, +1/-1
- `scripts/check-lisp-paren-balance.py` — `4e4457503277170bb401fdd320b0b697f08f40f0`, modified, +98/-56
- `scripts/gen-machine-asm-fixtures.py` — `5fdf18868c130769be323b820016eb56f287db91`, added, +163/-0
- `scripts/test-machine-asm-corpus.py` — `127f89ab9a65f20ce16e254b3e33fc43436a9c8a`, added, +70/-0
- `scripts/test-machine-source-integrity.py` — `04e1cee2381087a3fcb645594dbc0f11ce22f117`, added, +101/-0
