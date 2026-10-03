; #1347 ASYMMETRIC-SEMANTIC-FIREWALL
;
; This guard no longer restricts local semantics in Rust/host/backend code.
; The protected direction is only:
;
;   host/backend implementation semantics -> Lisp language authority
;
; Rust may depend on my-lisp. Lisp language authority must not become
; semantically derived from Rust implementation artifacts.

(00001001 changed
  (01001011 (10100110 "tests/semantic-authority-changes.lisp")))

(00001001 exact-text?
  (00001000 (left right)
    (00000011 left right)))

; Exact PredicateBit YES without a source literal.
(00001001 predicate-yes
  (00001000 ()
    (00000010 (00000001 ()))))

(00001001 language-authority-source?
  (00001000 (path)
    (10011011
      (00111101 "lib/" path)
      (00111101 "contracts/" path)
      (exact-text? path "language-contract.lisp")
      (exact-text? path "my-lisp-constitution.lisp")
      ; Synthetic protected paths used only by the guard self-test.
      (exact-text? path "tests/semantic-authority-guard-probe.lisp")
      (exact-text? path "tests/semantic-authority-guard-probe.сенс"))))

(00001001 host-marker?
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

(00001001 semantic-authority-claim?
  (00001000 (source)
    (10011011
      (00111110 "semantic-authority-source" source)
      (00111110 "authority-source" source)
      (00111110 "source-of-truth" source)
      (00111110 "semantic-source" source)
      (00111110 "Authority:" source)
      (00111110 "generated-from-host" source))))

(00001001 violation-class
  (00001000 (path source)
    (00000111
      ; Host/runtime/compiler/backend files are intentionally unrestricted.
      ((00100001 (language-authority-source? path))
       (00000001 allowed-local-implementation))
      ; Protected Lisp source is a violation only when host implementation is
      ; explicitly claimed as semantic authority/source of truth.
      ((10011010
         (host-marker? source)
         (semantic-authority-claim? source))
       (00000001 host-to-language-authority-leak))
      ((predicate-yes)
       (00000001 allowed-language-source)))))

(00001001 scan
  (00001000 (rows)
    (00000111
      ((00000010 rows)
       (00000001 (semantic-authority-ok)))
      ((predicate-yes)
       (10011101 ((row (00000101 rows))
              (path (00101111 row)))
         (00000111
           ; Crucial asymmetry: do not inspect host implementation text.
           ((00100001 (language-authority-source? path))
            (scan (00000110 rows)))
           ((predicate-yes)
            (10011100 ((raw-source (10100110 path)))
              (00000111
                ((00100001 (00100100 raw-source))
                 (00100111
                   (00000001 semantic-authority-violation)
                   path
                   (00000001 unreadable-language-authority-source)
                   "protected Lisp language source must be readable text"))
                ((predicate-yes)
                 (10011100 ((class (violation-class path raw-source)))
                   (00000111
                     ((00000011 class (00000001 host-to-language-authority-leak))
                      (00100111
                        (00000001 semantic-authority-violation)
                        path
                        class
                        "Lisp language authority must not derive semantic truth from host/Rust implementation artifacts"))
                     ((predicate-yes)
                      (scan (00000110 rows)))))))))))))))

(01001000 (scan changed))
