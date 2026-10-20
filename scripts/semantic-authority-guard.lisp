; #1347 ASYMMETRIC-SEMANTIC-FIREWALL
;
; This guard no longer restricts local semantics in Rust/host/backend code.
; The protected direction is only:
;
;   host/backend implementation semantics -> Lisp language authority
;
; Rust may depend on my-lisp. Lisp language authority must not become
; semantically derived from Rust implementation artifacts.

(визначити changed
  (рядок-містить? (читати-файл "tests/semantic-authority-changes.lisp")))

(визначити exact-text?
  (функція (left right)
    (за-умовою
      ((однакові? left right) (так) так)
      (так так ()))))

(визначити contains-any?
  (функція (source needles)
    (за-умовою
      ((атом? needles) () ())
      ((рядок-містить? (перше needles) source) так)
      (так (contains-any? source (решта needles))))))

(визначити language-authority-source?
  (функція (path)
    (або
      (рядок-префікс? "lib/" path)
      (рядок-префікс? "contracts/" path)
      (exact-text? path "language-contract.lisp")
      (exact-text? path "my-lisp-constitution.lisp")
      ; Synthetic protected path used only by the guard self-test.
      (exact-text? path "tests/semantic-authority-guard-probe.lisp")
      ; Підтримувані (не канонічні) розширення СЕНС теж захищені.
      (exact-text? path "tests/semantic-authority-guard-probe.сенс"))))

(визначити host-marker?
  (функція (source)
    (contains-any?
      source
      (як-є
        (".rs"
         "crates/"
         "Rust"
         "rust::"
         "Value::"
         "ExprKind::"
         "CanonicalIdentity"
         "NecessaryFormIdentity")))))

(визначити semantic-authority-claim?
  (функція (source)
    (contains-any?
      source
      (як-є
        ("semantic-authority-source"
         "authority-source"
         "source-of-truth"
         "semantic-source"
         "Authority:"
         "generated-from-host")))))

(визначити violation-class
  (функція (path source)
    (за-умовою
      ; Host/runtime/compiler/backend files are intentionally unrestricted.
      ; They may have local meaning tables, enums, fallbacks, dispatch, etc.
      ((хибне? (language-authority-source? path))
       (як-є allowed-local-implementation))
      ; A protected Lisp-owned source may mention Rust as evidence/history.
      ; It becomes a violation only when host implementation is explicitly
      ; claimed as a semantic authority/source of truth.
      ((та
         (host-marker? source)
         (semantic-authority-claim? source))
       (як-є host-to-language-authority-leak))
      (так (як-є allowed-language-source)))))

(визначити scan
  (функція (rows)
    (за-умовою
      ((атом? rows) () (як-є (semantic-authority-ok)))
      (так
       (нехай-послідовно ((row (перше rows))
               (path (друге row)))
          (за-умовою
            ; Crucial asymmetry: do not even inspect host implementation text.
            ((хибне? (language-authority-source? path))
             (накопичувати (решта rows)))
            (так
             (нехай ((raw-source (читати-файл path)))
               (за-умовою
                 ((хибне? (рядок? raw-source))
                  (список
                    (як-є semantic-authority-violation)
                    path
                    (як-є unreadable-language-authority-source)
                    "protected Lisp language source must be readable text"))
                 (так
                  (нехай ((class (violation-class path raw-source)))
                    (за-умовою
                      ((тотожне? class (як-є host-to-language-authority-leak))
                       (список
                         (як-є semantic-authority-violation)
                         path
                         class
                         "Lisp language authority must not derive semantic truth from host/Rust implementation artifacts"))
                      (так
                       (накопичувати (решта rows)))))))))))))))

(друкувати (накопичувати changed))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити однакові? EQUAL)
(визначити список LIST)
(визначити рядок-містить? STRING-CONTAINS?)
(визначити рядок-префікс? STRING-PREFIX?)
(визначити рядок? STRINGP)
(визначити накопичувати scan)
