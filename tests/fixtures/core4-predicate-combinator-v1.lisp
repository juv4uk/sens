; #1717 executable witness: variadic predicate combinators after Predicate1 reset.
; Every operand is itself a predicate expression; there are no source predicate literals.
;
; OR: NO, NO, YES -> YES
(01001000
  (10011011
    (00000010 (00000001 (00000000)))
    (00000010 (00000001 (00000000)))
    (00000010 (00000001 ()))))

; AND: YES, YES, YES -> YES
(01001000
  (10011010
    (00000010 (00000001 ()))
    (00000010 (00000001 ()))
    (00000010 (00000001 ()))))

; OR depth matching the active semantic-authority guard: five NO then YES -> YES
(01001000
  (10011011
    (00000010 (00000001 (00000000)))
    (00000010 (00000001 (00000000)))
    (00000010 (00000001 (00000000)))
    (00000010 (00000001 (00000000)))
    (00000010 (00000001 (00000000)))
    (00000010 (00000001 ()))))

; AND depth: six YES operands -> YES
(01001000
  (10011010
    (00000010 (00000001 ()))
    (00000010 (00000001 ()))
    (00000010 (00000001 ()))
    (00000010 (00000001 ()))
    (00000010 (00000001 ()))
    (00000010 (00000001 ()))))

; Composition matching semantic-authority-claim?: six string predicates.
(01001000
  (10011011
    (00111110 "semantic-authority-source" "plain text")
    (00111110 "authority-source" "plain text")
    (00111110 "source-of-truth" "plain text")
    (00111110 "semantic-source" "plain text")
    (00111110 "Authority:" "plain text")
    (00111110 "generated-from-host" "generated-from-host marker")))

; Composition matching host-marker?: eight string predicates.
(01001000
  (10011011
    (00111110 ".rs" "plain text")
    (00111110 "crates/" "plain text")
    (00111110 "Rust" "plain text")
    (00111110 "rust::" "plain text")
    (00111110 "Value::" "plain text")
    (00111110 "ExprKind::" "plain text")
    (00111110 "CanonicalIdentity" "plain text")
    (00111110 "NecessaryFormIdentity" "NecessaryFormIdentity marker")))

; Real guard shape: variadic OR is inside a closure and each predicate consumes
; the lowered lexical local `source`.
(00001001 predicate-local-or-probe
  (00001000 (source)
    (10011011
      (00111110 "semantic-authority-source" source)
      (00111110 "authority-source" source)
      (00111110 "source-of-truth" source)
      (00111110 "semantic-source" source)
      (00111110 "Authority:" source)
      (00111110 "generated-from-host" source))))

(01001000
  (predicate-local-or-probe "generated-from-host marker"))

; Exact nesting shape from the strict semantic-authority guard:
; AND consumes results of two helper functions, each of which uses variadic OR
; over the same lexical source.
(00001001 nested-host-marker?
  (00001000 (source)
    (10011011
      (00111110 ".rs" source)
      (00111110 "crates/" source)
      (00111110 "Rust" source)
      (00111110 "rust::" source)
      (00111110 "Value::" source)
      (00111110 "ExprKind::" source)
      (00111110 "CanonicalIdentity" source)
      (00111110 "NecessaryFormIdentity" source))))

(00001001 nested-authority-claim?
  (00001000 (source)
    (10011011
      (00111110 "semantic-authority-source" source)
      (00111110 "authority-source" source)
      (00111110 "source-of-truth" source)
      (00111110 "semantic-source" source)
      (00111110 "Authority:" source)
      (00111110 "generated-from-host" source))))

(00001001 nested-guard-composition?
  (00001000 (source)
    (10011010
      (nested-host-marker? source)
      (nested-authority-claim? source))))

(01001000
  (nested-guard-composition?
    "Rust generated-from-host semantic-authority-source"))

; Pure semantic core of #1816's strict asymmetric firewall, without filesystem I/O.
(00001001 guard-exact-text?
  (00001000 (left right)
    (00000011 left right)))

(00001001 guard-predicate-yes
  (00001000 ()
    (00000010 (00000001 ()))))

(00001001 guard-language-authority-source?
  (00001000 (path)
    (10011011
      (00111101 "lib/" path)
      (00111101 "contracts/" path)
      (guard-exact-text? path "language-contract.lisp")
      (guard-exact-text? path "my-lisp-constitution.lisp")
      (guard-exact-text? path "tests/semantic-authority-guard-probe.lisp")
      (guard-exact-text? path "tests/semantic-authority-guard-probe.сенс"))))

(00001001 guard-host-marker?
  (00001000 (source)
    (10011011
      (00111110 ".rs" source)
      (00111110 "crates/" source)
      (00111110 "Rust" source)
      (00111110 "rust::" source)
      (00111110 "Value::" source)
      (00111110 "ExprKind::" source)
      (00111110 "CanonicalIdentity" source)
      (00111110 "NecessaryFormIdentity" source))))

(00001001 guard-authority-claim?
  (00001000 (source)
    (10011011
      (00111110 "semantic-authority-source" source)
      (00111110 "authority-source" source)
      (00111110 "source-of-truth" source)
      (00111110 "semantic-source" source)
      (00111110 "Authority:" source)
      (00111110 "generated-from-host" source))))

(00001001 guard-violation-class
  (00001000 (path source)
    (00000111
      ((00100001 (guard-language-authority-source? path))
       (00000001 allowed-local-implementation))
      ((10011010
         (guard-host-marker? source)
         (guard-authority-claim? source))
       (00000001 host-to-language-authority-leak))
      ((guard-predicate-yes)
       (00000001 allowed-language-source)))))

; Unprotected host path -> allowed-local-implementation.
(01001000
  (00000011
    (guard-violation-class
      "README.md"
      "Rust generated-from-host semantic-authority-source")
    (00000001 allowed-local-implementation)))

; Protected path + host marker + authority claim -> leak.
(01001000
  (00000011
    (guard-violation-class
      "language-contract.lisp"
      "Rust generated-from-host semantic-authority-source")
    (00000001 host-to-language-authority-leak)))
