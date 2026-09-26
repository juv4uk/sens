; Перевірки документації й політик репозиторію — мовою.
; Перша частина перенесення `cargo xtask verify` (crates/xtask/src/checks.rs).
; Перевірки української документації й розкладки поки лишаються в xtask.
;
; Usage: sens scripts/verify-repo.lisp
; Друкує кожну перевірку; за першої ж проблеми — помилка й ненульовий вихід.

(def str+
  (lambda args
    (reduce (lambda (acc s) (string-append acc s)) "" args)))

(def fail
  (lambda (message)
    (second (list (print (str+ "FAIL: " message)) (car (quote ()))))))

(def pass
  (lambda (name)
    (print (str+ "ok: " name))))

(def contains? (lambda (text needle) (string-contains? needle text)))

; Кожна голка з needles має бути в тексті; повертає перелік відсутніх.
(def missing-needles
  (lambda (text needles)
    (cond
      ((atom? needles) () (quote ()))
      ((atom? needles) (0)
       (cond
         ((contains? text (car needles)) t (missing-needles text (cdr needles)))
         (t t (cons (car needles) (missing-needles text (cdr needles)))))))))

(def require-needles
  (lambda (name path needles)
    (let ((missing (missing-needles (read-file path) needles)))
      (cond
        ((atom? missing) () (pass name))
        ((atom? missing) (0) (fail (str+ name ": " path " missing " (write-to-string missing))))))))

(def forbid-needle
  (lambda (name path needle)
    (cond
      ((contains? (read-file path) needle) t
       (fail (str+ name ": " path " must not contain " (write-to-string needle))))
      (t t t))))

(def any-needle?
  (lambda (text needles)
    (cond
      ((atom? needles) () (quote ()))
      ((atom? needles) (0)
       (cond
         ((contains? text (car needles)) t t)
         (t t (any-needle? text (cdr needles))))))))

; --- public-docs-share-current-project-identity-and-extension ---
(def check-doc-identity
  (lambda (path)
    (let ((doc (read-file path)))
      (cond
        ((any-needle? doc (quote ("reference implementation" "референсна реалізація")))
         t
         (cond
           ((any-needle? doc (quote ("canonical Rust implementation" "канонічна реалізація на Rust" "kanonische Rust-Implementierung")))
            t
            (fail (str+ path ": implementation wording must not imply that Rust itself owns semantics")))
           (t t
            (cond
              ((any-needle? doc (quote ("канонічне розширення вихідного коду — **`.lisp`**"
                                        "Канонічне розширення вихідного коду — **`.lisp`**"
                                        "canonical source extension is **`.lisp`**"
                                        "current canonical source extension is **`.lisp`**")))
               t
               (cond
                 ((any-needle? doc (quote ("legacy alias" "legacy aliases")))
                  t
                  (cond
                    ((contains? doc "`.wsm`") t
                     (cond
                       ((contains? doc "`.my`") t t)
                       (t t (fail (str+ path ": must name `.my` as a legacy alias")))))
                    (t t (fail (str+ path ": must name `.wsm` as a legacy alias")))))
                 (t t (fail (str+ path ": must call `.wsm`/`.my` legacy aliases")))))
              (t t (fail (str+ path ": must state `.lisp` as the canonical extension")))))))
        (t t (fail (str+ path ": must describe Rust as a reference implementation")))))))

(check-doc-identity "README.md")
(check-doc-identity "docs/language-core.md")
(pass "public-docs-share-current-project-identity-and-extension")

; --- cargo-workspace-has-no-my-lisp-package-prefix ---
; Назва пакета (рядок одразу після `[package]`) з префіксом my-lisp — регресія.
; Бінарники з назвою my-lisp (сумісні псевдоніми CLI) — не пакет, їх не чіпаємо.
(def check-manifests
  (lambda (entries)
    (cond
      ((atom? entries) () t)
      ((atom? entries) (0)
       (let ((manifest (str+ "crates/" (car entries) "/Cargo.toml")))
         (let ((text (read-file manifest)))
           (cond
             ((contains? text "[package]\nname = \"my-lisp") t
              (fail (str+ "cargo package prefix regression: " manifest " uses my-lisp*")))
             (t t (check-manifests (cdr entries))))))))))

(check-manifests (read-dir "crates"))
(pass "cargo-workspace-has-no-my-lisp-package-prefix")

; --- public-docs-point-to-semantic-authority ---
(require-needles "public-docs-point-to-semantic-authority" "README.md"
  (quote ("docs/semantic-authority-map.md")))
(require-needles "public-docs-point-to-semantic-authority" "docs/language-core.md"
  (quote ("semantic-authority-map.md")))
(require-needles "public-docs-point-to-semantic-authority" "docs/semantic-authority-map.md"
  (quote ("language-contract.lisp")))
; Rust шукав без урахування регістру; у документі — «Ratified ADRs» і
; «executable conformance» / «Executable conformance».
(cond
  ((any-needle? (read-file "docs/semantic-authority-map.md") (quote ("Ratified ADR" "ratified ADR"))) t t)
  (t t (fail "docs/semantic-authority-map.md must mention ratified ADRs")))
(cond
  ((any-needle? (read-file "docs/semantic-authority-map.md") (quote ("Executable conformance" "executable conformance"))) t t)
  (t t (fail "docs/semantic-authority-map.md must mention executable conformance")))
(pass "public-docs-point-to-semantic-authority")

; --- host-semantic-surface-documentation-tracks-time-ownership ---
; Раніше шукало текст "unix-time-now" у builtins.rs; після #1477 вбудовані —
; примітиви за кодом, тож джерело — таблиця функцій і її метадані.
(require-needles "host-semantic-surface-documentation-tracks-time-ownership"
  "docs/host-semantic-surface.md"
  (quote ("mono-ns" "unix-time-now"
          "`utc-now` | `lib/time.lisp` | derived public clock meaning | HOST REMOVED")))
(require-needles "host-semantic-surface-documentation-tracks-time-ownership"
  "lib/time.lisp"
  (quote ("mono-ms" "utc-now")))
(require-needles "host-semantic-surface-documentation-tracks-time-ownership"
  "lib/surface/function-signatures.lisp"
  (quote ("(01011011 (kind builtin)")))
(forbid-needle "host-semantic-surface-documentation-tracks-time-ownership"
  "lib/surface/function-signatures.lisp" "(utc-now)")

; --- agent-onboarding / current-agent-authority / human-migration-doc ---
(require-needles "agent-onboarding-records-removed-coordination-surface" "AGENTS.md"
  (quote ("sens :9999" "swarm-node :910x"
          "Стара coordination surface на `:9999` фізично видалена"
          "мають повертати `unknown op`"
          "knowledge/swarm-legacy-deprecation.lisp"
          "Current coordination authority:" "`swarm-node`")))
(forbid-needle "agent-onboarding-records-removed-coordination-surface" "AGENTS.md"
  "This is a\n  first-class pattern, not a fallback")
(require-needles "agent-onboarding-records-removed-coordination-surface"
  "knowledge/swarm-legacy-deprecation.lisp"
  (quote ("(status . deprecated)" "(physical-status . removed)"
          "(runtime-rejection . confirmed)" "(coordination-authority . swarm-node)")))
(require-needles "human-migration-doc-keeps-semantic-and-coordination-planes-separate"
  "docs/swarm-mesh-v2.md"
  (quote ("sens :9999" "swarm-node :910x"
          "no longer the\ncoordination path going forward" "semantic oracle")))

; --- s2-explicitly-contracts-category-not-error-wording ---
(require-needles "s2-explicitly-contracts-category-not-error-wording"
  "docs/language-core-axioms.md"
  (quote ("The wording may differ; the *category* is the contract.")))
(require-needles "s2-explicitly-contracts-category-not-error-wording"
  "crates/sens/src/error.rs"
  (quote ("non-contractual: `kind` is what S2 ratifies")))

; --- Python-перевірки (поки викликаються; перенесення самих скриптів — окремо) ---
(def run-python
  (lambda (name script args)
    (let ((result (process-run "python3" (cons script args))))
      (cond
        ((equal? (car result) 0) (1) (pass name))
        ((equal? (car result) 0) (0)
         (fail (str+ name " failed\n" (second result) (third result))))))))

(run-python "meta-eval-evidence-matrix" "scripts/check-meta-eval-evidence.py" (quote ()))
(run-python "meta-eval-human-evidence-projection" "scripts/generate-meta-eval-evidence.py" (quote ("--check")))
(run-python "semantic-ownership-map-in-sync" "scripts/semantic-ownership.py" (quote ("--check")))

(print "verify-repo: all checks passed")
