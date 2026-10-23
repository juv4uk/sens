; #4057 — машинно-читане походження доказів обмежених машинних можливостей.
; Рядки описують лише докази реалізації, не визначаючи значення СЕНС.
; Джерело семантики — Контракт 11.8 і ратифіковані закони точних доменів.
; Автоматична перевірка звіряє рядки з відмовою за замовчуванням
; у scripts/machine-authority-guard.lisp.
;
; Поле independent-semantic-witness містить повні українські назви
; ратифікованих резидентів як людську проєкцію, а не машинний ключ.
; Точні DomainIdentity й ширини визначають lib/domains/d3.lisp та d5.lisp;
; історичні байти сід8 не використовуються для зіставлення.

(capability-provenance
  (name add-u64)
  (semantic-authority language-contract.lisp+ratified-domain-laws)
  (admitted-form add-r64-r64)
  (lowering-owner lib/machine/lowering/semantic-x86-64.lisp)
  (machine-witness crates/my-lisp-host/tests/native_lisp_bytes.rs)
  (reverse-edge forbidden)
  (independent-semantic-witness (exact-domain-expression додати))
  (representation-witness tests/fixtures/machine-representation-independence-witness.lisp))

(capability-provenance
  (name eq-cond-u64)
  (semantic-authority language-contract.lisp+ratified-domain-laws)
  (admitted-form cmp-r64-r64+jnz-rel8)
  (lowering-owner lib/machine/lowering/semantic-x86-64.lisp)
  (machine-witness crates/my-lisp-host/tests/native_cond_profile.rs)
  (reverse-edge forbidden)
  (independent-semantic-witness (exact-domain-expression тотожне? за-умовою))
  (representation-witness not-yet-required))

(capability-provenance
  (name car-cons-u64)
  (semantic-authority language-contract.lisp+ratified-domain-laws)
  (admitted-form store-pair+load-pair-head)
  (lowering-owner lib/machine/lowering/semantic-x86-64.lisp)
  (machine-witness crates/my-lisp-host/tests/native_lisp_bytes.rs)
  (reverse-edge forbidden)
  (independent-semantic-witness (exact-domain-expression сполучити перше))
  (representation-witness crates/my-lisp-host/tests/native_guest_abi.rs))
