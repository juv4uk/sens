; #749 — Мовний контракт сумісності СЕНС із незалежними виконавчими островами.
;
; Цей контракт визначає зобов'язання СЕНС на межі з автономними
; виконавчими островами. Він НЕ встановлює семантику Common Lisp, Prolog,
; CLIPS чи Datalog і не вигадує спільної для всіх онтології результатів.
;
; Механічна межа C/Rust може передавати ці тотожності та спостереження,
; але не визначає значення полів, наведених нижче.
;
; Зовнішня форма:
;   (island-compat-contract-1 ENTRY ...)
;
; Принципова відмінність:
;   літерал () — це Канон 0 у самій мові;
;   протокольний zero-results — спостереження одного завершеного
;   виклику острова, що повернув нуль результатів.
;   Протокол не має права неявно ототожнювати ці дві сутності.

(island-compat-contract-1
  ((identity . semantic-id)
   (owner . sens)
   (representation . opaque-u8)
   (meaning-source . semantic-registry-and-laws)
   (kernel-interpretation . forbidden)
   (renumber-on-kernel-change . forbidden))

  ((identity . execution-witness)
   (cardinality . zero-or-more)
   (kernel-required . no)
   (multiple-kernels-per-sid . allowed)
   (semantic-authority . forbidden)
   (replacement-preserves-sid . yes))

  ((identity . island-call)
   (input . (semantic-id native-payload))
   (output . native-observation)
   (producer-required . yes)
   (provenance-preserved . yes)
   (native-payload-preserved . yes)
   (universal-result-coercion . forbidden)
   (truth-coercion . forbidden))

  ((identity . zero-results)
   (kind . protocol-observation)
   (result-count . 0)
   (literal-empty-list-alias . forbidden)
   (may-become-lisp-data . explicit-projection-only))

  ((identity . one-result)
   (kind . protocol-observation)
   (result-count . 1)
   (native-result-preserved . yes)
   (may-become-lisp-data . explicit-projection-only))

  ((identity . many-results)
   (kind . protocol-observation)
   (result-count . many)
   (native-result-preserved . yes)
   (multiplicity-preserved . yes)
   (may-become-lisp-data . explicit-projection-only))

  ((identity . bridge)
   (availability . partial)
   (missing-bridge . legal)
   (source-result-preserved . yes)
   (target-conversion . explicit)
   (semantic-equivalence-assumed . no))

  ((identity . missing-kernel)
   (kind . execution-availability)
   (legal . yes)
   (changes-sid-meaning . no)
   (changes-registry-numbering . no))
)
