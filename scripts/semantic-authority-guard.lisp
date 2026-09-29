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
    (00000111
      ((00100010 left right) (1) t)
      (t t ()))))

(00001001 contains-any?
  (00001000 (source needles)
    (00000111
      ((00000010 needles) () ())
      ((00111110 (00000101 needles) source) t)
      (t (contains-any? source (00000110 needles))))))

(00001001 language-authority-source?
  (00001000 (path)
    (10011011
      (00111101 "lib/" path)
      (00111101 "contracts/" path)
      (exact-text? path "language-contract.lisp")
      (exact-text? path "my-lisp-constitution.lisp")
      ; Synthetic protected path used only by the guard self-test.
      (exact-text? path "tests/semantic-authority-guard-probe.lisp")
      ; Підтримувані (не канонічні) розширення СЕНС теж захищені.
      (exact-text? path "tests/semantic-authority-guard-probe.сенс"))))

(00001001 host-marker?
  (00001000 (source)
    (contains-any?
      source
      (00000001
        (".rs"
         "crates/"
         "Rust"
         "rust::"
         "Value::"
         "ExprKind::"
         "CanonicalIdentity"
         "NecessaryFormIdentity")))))

(00001001 semantic-authority-claim?
  (00001000 (source)
    (contains-any?
      source
      (00000001
        ("semantic-authority-source"
         "authority-source"
         "source-of-truth"
         "semantic-source"
         "Authority:"
         "generated-from-host")))))

(00001001 violation-class
  (00001000 (path source)
    (00000111
      ; Host/runtime/compiler/backend files are intentionally unrestricted.
      ; They may have local meaning tables, enums, fallbacks, dispatch, etc.
      ((00100001 (language-authority-source? path))
       (00000001 allowed-local-implementation))
      ; A protected Lisp-owned source may mention Rust as evidence/history.
      ; It becomes a violation only when host implementation is explicitly
      ; claimed as a semantic authority/source of truth.
      ((10011010
         (host-marker? source)
         (semantic-authority-claim? source))
       (00000001 host-to-language-authority-leak))
      (t (00000001 allowed-language-source)))))

(00001001 scan
  (00001000 (rows)
    (00000111
      ((00000010 rows) () (00000001 (semantic-authority-ok)))
      (t
       (10011101 ((row (00000101 rows))
              (kind (00000101 row))
              (path (00101111 row)))
         (00000111
           ; Deletion shrinks the authority surface. The path no longer has
           ; source bytes to inspect, so accept the deletion and continue.
           ((00000011 kind (00000001 deleted))
            (scan (00000110 rows)))
           ; Crucial asymmetry: do not even inspect host implementation text.
           ((00100001 (language-authority-source? path))
            (scan (00000110 rows)))
           (t
            (10011100 ((raw-source (10100110 path)))
              (00000111
                ((00100001 (00100100 raw-source))
                 (00100111
                   (00000001 semantic-authority-violation)
                   path
                   (00000001 unreadable-language-authority-source)
                   "protected Lisp language source must be readable text"))
                (t
                 (10011100 ((class (violation-class path raw-source)))
                   (00000111
                     ((00000011 class (00000001 host-to-language-authority-leak))
                      (00100111
                        (00000001 semantic-authority-violation)
                        path
                        class
                        "Lisp language authority must not derive semantic truth from host/Rust implementation artifacts"))
                     (t
                      (scan (00000110 rows)))))))))))))))

(01001000 (scan changed))
