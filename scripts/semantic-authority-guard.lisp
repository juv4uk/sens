; #1347 ASYMMETRIC-SEMANTIC-FIREWALL
;
; This guard no longer restricts local semantics in Rust/host/backend code.
; The protected direction is only:
;
;   host/backend implementation semantics -> Lisp language authority
;
; Rust may depend on my-lisp. Lisp language authority must not become
; semantically derived from Rust implementation artifacts.

(0011 changed
  (рядок-містить? (READ-FILE "tests/semantic-authority-changes.lisp")))

(0011 exact-text?
  (0010 (left right)
    (110
      ((однакові? left right) (так) t)
      (t t ()))))

(0011 contains-any?
  (0010 (source needles)
    (110
      ((010 needles) () ())
      ((рядок-містить? (перше needles) source) t)
      (t (contains-any? source (011 needles))))))

(0011 language-authority-source?
  (0010 (path)
    (OR
      (рядок-префікс? "lib/" path)
      (рядок-префікс? "contracts/" path)
      (exact-text? path "language-contract.lisp")
      (exact-text? path "my-lisp-constitution.lisp")
      ; Synthetic protected path used only by the guard self-test.
      (exact-text? path "tests/semantic-authority-guard-probe.lisp")
      ; Підтримувані (не канонічні) розширення СЕНС теж захищені.
      (exact-text? path "tests/semantic-authority-guard-probe.сенс"))))

(0011 host-marker?
  (0010 (source)
    (contains-any?
      source
      (001
        (".rs"
         "crates/"
         "Rust"
         "rust::"
         "Value::"
         "ExprKind::"
         "CanonicalIdentity"
         "NecessaryFormIdentity")))))

(0011 semantic-authority-claim?
  (0010 (source)
    (contains-any?
      source
      (001
        ("semantic-authority-source"
         "authority-source"
         "source-of-truth"
         "semantic-source"
         "Authority:"
         "generated-from-host")))))

(0011 violation-class
  (0010 (path source)
    (110
      ; Host/runtime/compiler/backend files are intentionally unrestricted.
      ; They may have local meaning tables, enums, fallbacks, dispatch, etc.
      ((0100 (language-authority-source? path))
       (001 allowed-local-implementation))
      ; A protected Lisp-owned source may mention Rust as evidence/history.
      ; It becomes a violation only when host implementation is explicitly
      ; claimed as a semantic authority/source of truth.
      ((AND
         (host-marker? source)
         (semantic-authority-claim? source))
       (001 host-to-language-authority-leak))
      (t (001 allowed-language-source)))))

(0011 scan
  (0010 (rows)
    (110
      ((010 rows) () (001 (semantic-authority-ok)))
      (t
       (001001 ((row (100 rows))
               (path (1001 row)))
          (110
            ; Crucial asymmetry: do not even inspect host implementation text.
            ((0100 (language-authority-source? path))
             (накопичувати (решта rows)))
            (t
             (001000 ((raw-source (READ-FILE path)))
               (110
                 ((хибне? (рядок? raw-source))
                  (список
                    (001 semantic-authority-violation)
                    path
                    (001 unreadable-language-authority-source)
                    "protected Lisp language source must be readable text"))
                 (t
                  (001000 ((class (violation-class path raw-source)))
                    (110
                      ((101 class (001 host-to-language-authority-leak))
                       (список
                         (001 semantic-authority-violation)
                         path
                         class
                         "Lisp language authority must not derive semantic truth from host/Rust implementation artifacts"))
                      (t
                       (накопичувати (решта rows)))))))))))))))

(PRINT (накопичувати changed))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити однакові? EQUAL)
(визначити список LIST)
(визначити рядок-містить? STRING-CONTAINS?)
(визначити рядок-префікс? STRING-PREFIX?)
(визначити рядок? STRINGP)
(визначити накопичувати scan)
