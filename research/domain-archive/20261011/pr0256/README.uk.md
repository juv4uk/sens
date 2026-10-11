# Архів історичної гілки #256 — активація exact-Q

**Статус: ARCHIVE-ONLY для старої реалізації; валідні свідки перенесені окремо.**

Цей PR змінював старий файл `crates/my-lisp/src/eval/arithmetic.rs` та observer старого crate. Поточний main використовує `crates/sens` і чинний контракт `contracts/exact-q-binary-contract.lisp` із PredicateBit, де семантичний результат порівняння — YES/NO, а не rational payload. Стару реалізацію та identity-tagged schema не можна переносити wholesale.

Повний diff чотирьох PR paths збережено у `exact-q-branch-review.patch`; `manifest.json` містить origin head та доступні blob SHA. Дві незалежно сумісні точні-Q перевірки були виділені з наступної гілки #258 та додані до чинного `tests/fixtures/exact-q-binary-v1.lisp` в коміті `309813e3ead48b616dd41ba776deb2c68fbd38e6`:
- `(= 3 3) → 1`;
- `(< 1 2 3 4) → 1`.

Очікування старого PR щодо inexact JSON inputs та відсутності відповіді не були автоматично перенесені: вони мають бути перевірені проти поточного runtime і exact-Q authority окремо. Архів зберігає ці твердження як історичний evidence, не як активну семантику. Нових гілок не створено.
