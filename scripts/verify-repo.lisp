; Перевірки документації й політик репозиторію — мовою.
; Перша частина перенесення `cargo xtask verify` (crates/xtask/src/checks.rs).
; Разом з українськими перевірками — повна заміна `cargo xtask verify`.
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

;; ===== Українська документація й розкладка (з xtask verify) =====

(def field (lambda (key form) (second (assoc key (cdr form)))))

(def count-items
  (lambda (items)
    (cond
      ((atom? items) () 0)
      ((atom? items) (0) (+ 1 (count-items (cdr items)))))))

(def last-char
  (lambda (text)
    (string-slice text (- (string-length text) 1) (string-length text))))

; Стабільні українські назви з таблиці функцій: ((бітовий-код . назва) ...).
(def registry-rows (car (read-all (read-file "lib/surface/semantic-registry.lisp"))))

(def stable-uk-pairs
  (lambda (rows)
    (cond
      ((atom? rows) () (quote ()))
      ((atom? rows) (0)
       (let ((name (field (quote ук) (car rows))))
         (cond
           ((atom? name) (1)
            (cons (cons (write-to-string (car (car rows))) (symbol->string name))
                  (stable-uk-pairs (cdr rows))))
           (t t (stable-uk-pairs (cdr rows)))))))))

(def stable-uk (stable-uk-pairs registry-rows))

; Документаційний індекс: (doc категорія "КОД" вид "сигнатура" "опис").
(def uk-docs (cdr (assoc (quote docs) (cdr (car (read-all (read-file "lib/surface/uk-docs.lisp")))))))
(def doc-id (lambda (doc) (third doc)))
(def doc-kind (lambda (doc) (fourth doc)))
(def api-md (read-file "docs/ukrainian-api.md"))

(def uk-name-for
  (lambda (id)
    (let ((pair (assoc id stable-uk)))
      (cond
        ((atom? pair) (0) (cdr pair))
        (t t (fail (str+ "документаційний ID " id " не має stable UK projection у registry")))))))

(def all-bits?
  (lambda (text)
    (cond
      ((string-empty? text) (1) t)
      ((string-contains? (string-first text) "01") t (all-bits? (string-rest text)))
      (t t (quote ())))))

(def check-docs
  (lambda (docs predicates mutations)
    (cond
      ((atom? docs) ()
       (cond
         ((< 10 predicates) 1
          (cond
            ((< 0 mutations) 1 t)
            (t t (fail "публічний каталог мутацій схлопнувся"))))
         (t t (fail "публічний каталог предикатів схлопнувся"))))
      ((atom? docs) (0)
       (let ((id (doc-id (car docs))) (kind (doc-kind (car docs))))
         (cond
           ((equal? (string-length id) 8) (0)
            (fail (str+ "документаційний join key має бути 8-бітним SID: " id)))
           ((all-bits? id) () (fail (str+ "документаційний join key має бути 8-бітним SID: " id)))
           (t t
            (let ((uk (uk-name-for id)))
              (let ((question (equal? (last-char uk) "?"))
                    (bang (equal? (last-char uk) "!"))
                    (predicate (equal? kind (quote predicate)))
                    (mutation (equal? kind (quote mutation))))
                (cond
                  ((equal? question predicate) (0)
                   (fail (str+ "українська назва " uk ": знак ? і predicate мусять збігатися")))
                  ((equal? bang mutation) (0)
                   (fail (str+ uk ": ! зарезервований для мутації")))
                  (mutation (1)
                   (cond
                     ((equal? uk "встановити-елемент-вектора!") (1)
                      (check-docs (cdr docs) predicates (+ mutations 1)))
                     (t t (fail (str+ "несподівана мутація: " uk)))))
                  (predicate (1)
                   (check-docs (cdr docs) (+ predicates 1) mutations))
                  (t t (check-docs (cdr docs) predicates mutations))))))))))))

(check-docs uk-docs 0 0)
(pass "dokumentatsiinyi-kliuch-ie-tilky-numeric")
(pass "znak-pytannia-tochno-vidpovidaie-predykatam")
(pass "znak-oklyku-tochno-vidpovidaie-mutatsii")

; Усі ID документації є в таблиці; усі задокументовані назви — у Markdown.
(def check-md-rows
  (lambda (pairs)
    (cond
      ((atom? pairs) () t)
      ((atom? pairs) (0)
       (let ((id (car (car pairs))) (uk (cdr (car pairs))))
         (cond
           ((atom? (assoc id (map (lambda (doc) (cons (doc-id doc) t)) uk-docs))) ()
            (check-md-rows (cdr pairs)))
           ((string-contains? (str+ "| `" uk "` |") api-md) t (check-md-rows (cdr pairs)))
           (t t (fail (str+ "публічне українське ім'я відсутнє у Markdown-довіднику: " uk)))))))))

(cond
  ((< 50 (count-items stable-uk)) 1 (check-md-rows stable-uk))
  (t t (fail "замало stable UK-назв у таблиці")))
(pass "vsi-stable-ukrainski-nazvy-maiut-numeric-zapys-u-dovidnyku")

; Смисловий аудит назв: підсумок збігається з даними.
(def audit (car (read-all (read-file "lib/surface/uk-name-audit.lisp"))))
(def audit-renames (cdr (assoc (quote renames) (cdr audit))))
(def reviewed (field (quote stable-reviewed) audit))
(def renamed (field (quote renamed) audit))
(def retained (field (quote retained) audit))
(cond
  ((equal? reviewed (+ renamed retained)) (1)
   (cond
     ((equal? renamed (count-items audit-renames)) (1)
      (cond
        ((equal? reviewed (count-items uk-docs)) (1) t)
        (t t (fail "смисловий аудит мусить покривати рівно documented UK-покриття"))))
     (t t (fail "(renamed N) розійшовся з фактичною кількістю (rename ...)"))))
  (t t (fail "stable-reviewed мусить дорівнювати renamed+retained")))
(pass "smyslovyi-audyt-summary-zbihaietsia-z-faktychnymy-danymy")

(def uk-surface (read-file "lib/surface/uk.lisp"))

; Позиція першого входження marker у s від i; -1 якщо нема.
(def pos-of
  (lambda (s marker i)
    (cond
      ((string-empty? s) (1) -1)
      ((string-prefix? marker s) t i)
      (t t (pos-of (string-rest s) marker (+ i 1))))))

(let ((first (pos-of uk-surface "(define середовище env)" 0)))
  (cond
    ((< first 0) 1 (fail "uk.lisp: немає (define середовище env)"))
    (t t
     (cond
       ((string-contains? "(define середовище env)"
                          (string-slice uk-surface (+ first 1) 1000000000)) t
        (fail "uk.lisp: (define середовище env) більше одного разу"))
       (t t t)))))
(pass "seredovyshche-ne-maie-povtornoho-surface-binding")

(def check-aliases
  (lambda (renames)
    (cond
      ((atom? renames) () t)
      ((atom? renames) (0)
       (let ((en (symbol->string (second (car renames))))
             (old (symbol->string (third (car renames)))))
         (cond
           ((string-contains? (str+ "(define " old " " en ")") uk-surface) t
            (check-aliases (cdr renames)))
           (t t (fail (str+ "missing alias (define " old " " en ")")))))))))
(check-aliases audit-renames)
(pass "stari-nazvy-smystovoho-audytu-lyshaiutsia-aliasamy-sumisnosti")

; Розкладка: українські назви набираються без латиниці.
(def uk-layout
  "абвгґдеєжзиіїйклмнопрстуфхцчшщьюяАБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ0123456789-?!'*")

(def typeable?
  (lambda (text)
    (cond
      ((string-empty? text) (1) t)
      ((string-contains? (string-first text) uk-layout) t (typeable? (string-rest text)))
      (t t (quote ())))))

(def check-typeable
  (lambda (pairs)
    (cond
      ((atom? pairs) () t)
      ((atom? pairs) (0)
       (cond
         ((typeable? (cdr (car pairs))) t (check-typeable (cdr pairs)))
         (t t (fail (str+ "Ukrainian name needs another keyboard layout: " (cdr (car pairs))))))))))
(check-typeable stable-uk)
(pass "every-stable-ukrainian-name-is-typeable-on-the-ukrainian-layout")

(def latin-letter?
  (lambda (char)
    (let ((code (string->codepoint char)))
      (cond
        ((< code 65) 1 (quote ()))
        ((< code 91) 1 t)
        ((< code 97) 1 (quote ()))
        ((< code 123) 1 t)
        (t t (quote ()))))))

; Латинські літери у виконуваному коді: поза рядками й коментарями.
(def latin-in-code
  (lambda (text in-string in-comment found)
    (cond
      ((string-empty? text) (1) found)
      (t t
       (let ((c (string-first text)) (rest (string-rest text)))
         (cond
           ((equal? in-comment t) (1)
            (latin-in-code rest () (cond ((equal? c "\n") (1) ()) (t t t)) found))
           ((equal? in-string t) (1)
            (cond
              ((equal? c "\\") (1) (latin-in-code (string-rest rest) t () found))
              ((equal? c "\"") (1) (latin-in-code rest () () found))
              (t t (latin-in-code rest t () found))))
           ((equal? c ";") (1) (latin-in-code rest () t found))
           ((equal? c "\"") (1) (latin-in-code rest t () found))
           ((latin-letter? c) t (latin-in-code rest () () (string-append found c)))
           (t t (latin-in-code rest () () found))))))))

(def require-no-latin
  (lambda (name path)
    (let ((found (latin-in-code (read-file path) () () "")))
      (cond
        ((string-empty? found) (1) (pass name))
        (t t (fail (str+ name ": латинські літери у виконуваному коді " path ": " found)))))))

(require-no-latin "ukrainian-acceptance-program-code-never-requires-latin-layout"
  "lib/surface/uk-acceptance.lisp")
(require-no-latin "ukrainska-prohrama-pryinnyattia-ne-potrebuie-latynskoi-rozkladky"
  "tests/fixtures/rivnopravnist-uk.lisp")

;; ===== Workflow контракту мови — канонічні шляхи .lisp (з xtask) =====
(def check-contract-workflow
  (lambda (path)
    (let ((text (read-file path)))
      (cond
        ((string-contains? "language-contract.my" text) t
         (fail (str+ path " still contains removed path language-contract.my")))
        ((string-contains? "contracts/my-lisp/lock.my" text) t
         (fail (str+ path " still contains removed path contracts/my-lisp/lock.my")))
        (t t
         (require-needles "contract-workflows-use-canonical-lisp-paths" path
           (quote ("default: contracts/my-lisp/language-contract.lisp"
                   "default: contracts/my-lisp/lock.lisp"
                   "UPSTREAM_PATH: language-contract.lisp"))))))))
(check-contract-workflow ".github/workflows/sync-language-contract.yml")
(check-contract-workflow ".github/workflows/verify-language-contract.yml")

(print "verify-repo: all checks passed")
