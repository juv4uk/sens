; #749 — Lisp-owned language-facing island compatibility contract.
;
; This document defines what my-lisp promises at the border with autonomous
; execution islands. It does NOT define Common Lisp, Prolog, CLIPS or Datalog
; semantics and does not invent a universal result ontology.
;
; Mechanical C/Rust boundaries may transport these identities and observations.
; They do not own the meaning of the fields below.
;
; Outer form:
;   (island-compat-contract/1 ENTRY ...)
;
; Key distinction:
;   literal () is Canon 0 in the language.
;   protocol zero-results is an observation about one completed island call.
;   The protocol must not silently make those two things identical.

(island-compat-contract/1
  ((identity . semantic-id)
   (owner . my-lisp)
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
