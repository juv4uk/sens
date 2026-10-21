; Контракт незалежності від субстрату LIFE (#809).
;
; Це контракт допуску паритету, що належить Lisp. Він не реалізує GraalVM
; чи виконання Rust. Обидва субстрати — свідки; жоден не володіє очікуваною істиною.
;
; Рядок паритету може стати GREEN лише коли присутнє все потрібне свідчення:
; точне закріплення upstream, очікуваний датум, що належить Lisp, спостереження Rust, Graal
; спостереження і походження субстрату. Відсутній механізм Graal — це обмеження
; виконання, ніколи не семантична мутація.

(life-substrate-parity-1
  ((owner . my-lisp)
   (life-contract-source . "contracts/life-1-contract.lisp")
   (expected-evidence-owner . lisp)
   (rust-role . witness)
   (graal-role . witness)
   (substrate-oracle . forbidden)
   (exact-upstream-pin . required)
   (same-life-contract-set . required)
   (contract-observables-only . required)
   (java-rust-internals-comparison . forbidden)
   (silent-graal-fallback . forbidden)
   (missing-substrate-mechanism . execution-limitation)
   (semantic-mutation-on-missing-mechanism . forbidden)
   (parity-admission . all-required-evidence))

  ; #93 ще не надав справжнього свідка диференційного виконання Graal.
  ; Тримайте це порожнім замість виготовлення паритету зі свідчень лише Rust.
  (rows
  ))
