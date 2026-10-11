# Архів PR #650 — перенесення surface coverage gate на старий my-lisp шлях

**Статус: ARCHIVE-ONLY / НЕ ЗЛИВАТИ НАСЛІПО.**

Збережено всі шість змінених шляхів PR #650 із гілки `replay/643-surface-coverage-current-main` (head `bbd1cdcae0850a6ff7c3835bac6134177c2e8b0f`). Вона спирається на застарілі назви `crates/my-lisp` і `lib/core.my`, тоді як чинний main використовує `crates/sens` та `lib/core.lisp`. Її workflow не є безпечною заміною поточного `.github/workflows/surface-drift-check.yml`; окремо, старий PR видаляв `scripts/check_surface_coverage.py`, але його видалення не можна переносити до main без доведеного current-SENS parity.

Для повноти provenance файл `scripts/check_surface_coverage.py`, який PR видаляв, збережено зі сторони base commit `42e3945c5e8f27902ade6fedf52f54786c56f914` (blob `8948924c52e9d90f98012cfda1f6bd3e82eaecf1`); інші п'ять файлів збережені зі сторони PR head. `manifest.json` точно розрізняє ці джерела.

Унікальний намір — власницька coverage-check логіка на Lisp, що читає semantic registry, — збережений, але потребує портованої реалізації проти поточних SENS APIs і перевірки еквівалентності. Продовжувати тільки в наявному #76/#5041, без нової гілки.
