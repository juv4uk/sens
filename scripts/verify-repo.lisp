; Перевірки документації й політик репозиторію — мовою.
; Перша частина перенесення `cargo xtask verify` (crates/xtask/src/checks.rs).
; Разом з українськими перевірками — повна заміна `cargo xtask verify`.
;
; Usage: sens scripts/verify-repo.lisp
; Друкує кожну перевірку; за першої ж проблеми — помилка й ненульовий вихід.

(00001001 str+
  (00001000 args
    (00111001 (00001000 (acc s) (00111010 acc s)) "" args)))

(00001001 fail
  (00001000 (message)
    (00101111 (00100111 (01001000 (str+ "FAIL: " message)) (00000101 (00000001 ()))))))

(00001001 pass
  (00001000 (name)
    (01001000 (str+ "ok: " name))))

(00001001 contains? (00001000 (text needle) (00111110 needle text)))

; Кожна голка з needles має бути в тексті; повертає перелік відсутніх.
(00001001 missing-needles
  (00001000 (text needles)
    (00000111
      ((00000010 needles) () (00000001 ()))
      ((00000010 needles) (0)
       (00000111
         ((contains? text (00000101 needles)) t (missing-needles text (00000110 needles)))
         (t t (00000100 (00000101 needles) (missing-needles text (00000110 needles)))))))))

(00001001 require-needles
  (00001000 (name path needles)
    (10011100 ((missing (missing-needles (10100110 path) needles)))
      (00000111
        ((00000010 missing) () (pass name))
        ((00000010 missing) (0) (fail (str+ name ": " path " missing " (01001100 missing))))))))

(00001001 forbid-needle
  (00001000 (name path needle)
    (00000111
      ((contains? (10100110 path) needle) t
       (fail (str+ name ": " path " must not contain " (01001100 needle))))
      (t t t))))

(00001001 any-needle?
  (00001000 (text needles)
    (00000111
      ((00000010 needles) () (00000001 ()))
      ((00000010 needles) (0)
       (00000111
         ((contains? text (00000101 needles)) t t)
         (t t (any-needle? text (00000110 needles))))))))

; --- public-docs-share-current-project-identity-and-extension ---
(00001001 check-doc-identity
  (00001000 (path)
    (10011100 ((doc (10100110 path)))
      (00000111
        ((any-needle? doc (00000001 ("reference implementation" "reference Rust implementation" "референсна реалізація" "референсна реалізація Rust")))
         t
         (00000111
           ((any-needle? doc (00000001 ("canonical Rust implementation" "канонічна реалізація на Rust" "kanonische Rust-Implementierung")))
            t
            (fail (str+ path ": implementation wording must not imply that Rust itself owns semantics")))
           (t t
            (00000111
              ((any-needle? doc (00000001 ("канонічне розширення вихідного коду — **`.lisp`**"
                                        "Канонічне розширення вихідного коду — **`.lisp`**"
                                        "canonical source extension is **`.lisp`**"
                                        "current canonical source extension is **`.lisp`**")))
               t
               (00000111
                 ((any-needle? doc (00000001 ("legacy alias" "legacy aliases")))
                  t
                  (00000111
                    ((contains? doc "`.wsm`") t
                     (00000111
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
(00001001 check-manifests
  (00001000 (entries)
    (00000111
      ((00000010 entries) () t)
      ((00000010 entries) (0)
       (10011100 ((manifest (str+ "crates/" (00000101 entries) "/Cargo.toml")))
         (10011100 ((text (10100110 manifest)))
           (00000111
             ((contains? text "[package]\nname = \"my-lisp") t
              (fail (str+ "cargo package prefix regression: " manifest " uses my-lisp*")))
             (t t (check-manifests (00000110 entries))))))))))

(check-manifests (read-dir "crates"))
(pass "cargo-workspace-has-no-my-lisp-package-prefix")

; --- public-docs-point-to-semantic-authority ---
(require-needles "public-docs-point-to-semantic-authority" "README.md"
  (00000001 ("docs/semantic-authority-map.md")))
(require-needles "public-docs-point-to-semantic-authority" "docs/language-core.md"
  (00000001 ("semantic-authority-map.md")))
(require-needles "public-docs-point-to-semantic-authority" "docs/semantic-authority-map.md"
  (00000001 ("language-contract.lisp")))
; Rust шукав без урахування регістру; у документі — «Ratified ADRs» і
; «executable conformance» / «Executable conformance».
(00000111
  ((any-needle? (10100110 "docs/semantic-authority-map.md") (00000001 ("Ratified ADR" "ratified ADR"))) t t)
  (t t (fail "docs/semantic-authority-map.md must mention ratified ADRs")))
(00000111
  ((any-needle? (10100110 "docs/semantic-authority-map.md") (00000001 ("Executable conformance" "executable conformance"))) t t)
  (t t (fail "docs/semantic-authority-map.md must mention executable conformance")))
(pass "public-docs-point-to-semantic-authority")

; --- host-semantic-surface-documentation-tracks-time-ownership ---
; Раніше шукало текст "unix-time-now" у builtins.rs; після #1477 вбудовані —
; примітиви за кодом, тож джерело — таблиця функцій і її метадані.
(require-needles "host-semantic-surface-documentation-tracks-time-ownership"
  "docs/host-semantic-surface.md"
  (00000001 ("mono-ns" "unix-time-now"
          "`utc-now` | `lib/time.lisp` | derived public clock meaning | HOST REMOVED")))
(require-needles "host-semantic-surface-documentation-tracks-time-ownership"
  "lib/time.lisp"
  (00000001 ("mono-ms" "utc-now")))
(require-needles "host-semantic-surface-documentation-tracks-time-ownership"
  "lib/surface/function-signatures.lisp"
  (00000001 ("(01011011 (kind builtin)")))
(forbid-needle "host-semantic-surface-documentation-tracks-time-ownership"
  "lib/surface/function-signatures.lisp" "(utc-now)")

; --- agent-onboarding / current-agent-authority / human-migration-doc ---
(require-needles "agent-onboarding-records-removed-coordination-surface" "AGENTS.md"
  (00000001 ("sens :9999" "swarm-node :910x"
          "Стара coordination surface на `:9999` фізично видалена"
          "мають повертати `unknown op`"
          "knowledge/swarm-legacy-deprecation.lisp"
          "Current coordination authority:" "`swarm-node`")))
(forbid-needle "agent-onboarding-records-removed-coordination-surface" "AGENTS.md"
  "This is a\n  first-class pattern, not a fallback")
(require-needles "agent-onboarding-records-removed-coordination-surface"
  "knowledge/swarm-legacy-deprecation.lisp"
  (00000001 ("(status . deprecated)" "(physical-status . removed)"
          "(runtime-rejection . confirmed)" "(coordination-authority . swarm-node)")))
(require-needles "human-migration-doc-keeps-semantic-and-coordination-planes-separate"
  "docs/swarm-mesh-v2.md"
  (00000001 ("sens :9999" "swarm-node :910x"
          "no longer the\ncoordination path going forward" "semantic oracle")))

; --- s2-explicitly-contracts-category-not-error-wording ---
(require-needles "s2-explicitly-contracts-category-not-error-wording"
  "docs/language-core-axioms.md"
  (00000001 ("The wording may differ; the *category* is the contract.")))
(require-needles "s2-explicitly-contracts-category-not-error-wording"
  "crates/sens/src/error.rs"
  (00000001 ("non-contractual: `kind` is what S2 ratifies")))

; --- Python-перевірки (поки викликаються; перенесення самих скриптів — окремо) ---
(00001001 run-python
  (00001000 (name script args)
    (10011100 ((result (10100010 "python3" (00000100 script args))))
      (00000111
        ((00100010 (00000101 result) 0) (1) (pass name))
        ((00100010 (00000101 result) 0) (0)
         (fail (str+ name " failed\n" (00101111 result) (00110000 result))))))))

(run-python "meta-eval-evidence-matrix" "scripts/check-meta-eval-evidence.py" (00000001 ()))
(run-python "meta-eval-human-evidence-projection" "scripts/generate-meta-eval-evidence.py" (00000001 ("--check")))
(run-python "semantic-ownership-map-in-sync" "scripts/semantic-ownership.py" (00000001 ("--check")))

;; ===== Українська документація й розкладка (з xtask verify) =====

(00001001 field (00001000 (key form) (00101111 (00101101 key (00000110 form)))))

(00001001 count-items
  (00001000 (items)
    (00000111
      ((00000010 items) () 0)
      ((00000010 items) (0) (00001100 1 (count-items (00000110 items)))))))

(00001001 last-char
  (00001000 (text)
    (01000001 text (00001101 (00111011 text) 1) (00111011 text))))

; Стабільні українські назви з таблиці функцій: ((бітовий-код . назва) ...).
(00001001 registry-rows (00000101 (01001011 (10100110 "lib/surface/semantic-registry.lisp"))))

(00001001 stable-uk-pairs
  (00001000 (rows)
    (00000111
      ((00000010 rows) () (00000001 ()))
      ((00000010 rows) (0)
       (10011100 ((name (field (00000001 ук) (00000101 rows))))
         (00000111
           ((00000010 name) (1)
            (00000100 (00000100 (01001100 (00000101 (00000101 rows))) (01000010 name))
                  (stable-uk-pairs (00000110 rows))))
           (t t (stable-uk-pairs (00000110 rows)))))))))

(00001001 stable-uk (stable-uk-pairs registry-rows))

; Документаційний індекс: (doc категорія КОД вид "сигнатура" "опис"), КОД — голі 8 біт.
(00001001 uk-docs (00000110 (00101101 (00000001 docs) (00000110 (00000101 (01001011 (10100110 "lib/surface/uk-docs.lisp")))))))
; Текстовий запис SENS для перевірок і join: голі 8 біт дають рівно 8 знаків,
; а SENS у лапках (текстовий сурогат) — 10, і перевірка його відкидає.
(00001001 doc-id (00001000 (doc) (01001100 (00110000 doc))))
(00001001 doc-kind (00001000 (doc) (00110001 doc)))
(00001001 api-md (10100110 "docs/ukrainian-api.md"))

(00001001 uk-name-for
  (00001000 (id)
    (10011100 ((found (00101101 id stable-uk)))
      (00000111
        ((00000010 found) (0) (00000110 found))
        (t t (fail (str+ "документаційний ID " id " не має stable UK projection у registry")))))))

(00001001 all-bits?
  (00001000 (text)
    (00000111
      ((00111100 text) (1) t)
      ((00111110 (00111111 text) "01") t (all-bits? (01000000 text)))
      (t t (00000001 ())))))

(00001001 check-docs
  (00001000 (docs predicates mutations)
    (00000111
      ((00000010 docs) ()
       (00000111
         ((00011010 10 predicates) 1
          (00000111
            ((00011010 0 mutations) 1 t)
            (t t (fail "публічний каталог мутацій схлопнувся"))))
         (t t (fail "публічний каталог предикатів схлопнувся"))))
      ((00000010 docs) (0)
       (10011100 ((id (doc-id (00000101 docs))) (kind (doc-kind (00000101 docs))))
         (00000111
           ((00100010 (00111011 id) 8) (0)
            (fail (str+ "документаційний join key має бути 8-бітним SID: " id)))
           ((all-bits? id) () (fail (str+ "документаційний join key має бути 8-бітним SID: " id)))
           (t t
            (10011100 ((uk (uk-name-for id)))
              (10011100 ((question (00100010 (last-char uk) "?"))
                    (bang (00100010 (last-char uk) "!"))
                    (predicate (00100010 kind (00000001 predicate)))
                    (mutation (00100010 kind (00000001 mutation))))
                (00000111
                  ((00100010 question predicate) (0)
                   (fail (str+ "українська назва " uk ": знак ? і predicate мусять збігатися")))
                  ((00100010 bang mutation) (0)
                   (fail (str+ uk ": ! зарезервований для мутації")))
                  (mutation (1)
                   (00000111
                     ((00100010 uk "встановити-елемент-вектора!") (1)
                      (check-docs (00000110 docs) predicates (00001100 mutations 1)))
                     (t t (fail (str+ "несподівана мутація: " uk)))))
                  (predicate (1)
                   (check-docs (00000110 docs) (00001100 predicates 1) mutations))
                  (t t (check-docs (00000110 docs) predicates mutations))))))))))))

(check-docs uk-docs 0 0)
(pass "dokumentatsiinyi-kliuch-ie-tilky-numeric")
(pass "znak-pytannia-tochno-vidpovidaie-predykatam")
(pass "znak-oklyku-tochno-vidpovidaie-mutatsii")

; Усі ID документації є в таблиці; усі задокументовані назви — у Markdown.
(00001001 check-md-rows
  (00001000 (pairs)
    (00000111
      ((00000010 pairs) () t)
      ((00000010 pairs) (0)
       (10011100 ((id (00000101 (00000101 pairs))) (uk (00000110 (00000101 pairs))))
         (00000111
           ((00000010 (00101101 id (00110111 (00001000 (doc) (00000100 (doc-id doc) t)) uk-docs))) ()
            (check-md-rows (00000110 pairs)))
           ((00111110 (str+ "| `" uk "` |") api-md) t (check-md-rows (00000110 pairs)))
           (t t (fail (str+ "публічне українське ім'я відсутнє у Markdown-довіднику: " uk)))))))))

(00000111
  ((00011010 50 (count-items stable-uk)) 1 (check-md-rows stable-uk))
  (t t (fail "замало stable UK-назв у таблиці")))
(pass "vsi-stable-ukrainski-nazvy-maiut-numeric-zapys-u-dovidnyku")

; Смисловий аудит назв: підсумок збігається з даними.
(00001001 audit (00000101 (01001011 (10100110 "lib/surface/uk-name-audit.lisp"))))
(00001001 audit-renames (00000110 (00101101 (00000001 renames) (00000110 audit))))
(00001001 reviewed (field (00000001 stable-reviewed) audit))
(00001001 renamed (field (00000001 renamed) audit))
(00001001 retained (field (00000001 retained) audit))
(00000111
  ((00100010 reviewed (00001100 renamed retained)) (1)
   (00000111
     ((00100010 renamed (count-items audit-renames)) (1)
      (00000111
        ((00100010 reviewed (count-items uk-docs)) (1) t)
        (t t (fail "смисловий аудит мусить покривати рівно documented UK-покриття"))))
     (t t (fail "(renamed N) розійшовся з фактичною кількістю (rename ...)"))))
  (t t (fail "stable-reviewed мусить дорівнювати renamed+retained")))
(pass "smyslovyi-audyt-summary-zbihaietsia-z-faktychnymy-danymy")

(00001001 uk-surface (10100110 "lib/surface/uk.lisp"))
(00001001 semantic-registry
  (00000101 (01001011 (10100110 "lib/surface/semantic-registry.lisp"))))
; EN surface -> exact SENS, derived from the single semantic registry.
(00001001 registry-sens-for-en
  (00001000 (name rows)
    (00000111
      ((00000010 rows) () ())
      ((00100010 (field (00000001 en) (00000101 rows)) name) (1)
       (00000101 (00000101 rows)))
      (t t (registry-sens-for-en name (00000110 rows))))))

; Every audited compatibility alias carries the exact SENS derived above.
; This keeps both host primitives and Lisp-owned callables free of runtime EN-name authority.

; Позиція першого входження marker у s від i; -1 якщо нема.
(00001001 pos-of
  (00001000 (s marker i)
    (00000111
      ((00111100 s) (1) -1)
      ((00111101 marker s) t i)
      (t t (pos-of (01000000 s) marker (00001100 i 1))))))

(00000111
  ((00011010 (pos-of uk-surface "(00001001 середовище env)" 0) 0) t
   (fail "uk.lisp: (00001001 середовище env) мусить бути лише в реєстрі, не в поверхні"))
  (t t t))
(pass "seredovyshche-ne-maie-povtornoho-surface-binding")

(00001001 check-aliases
  (00001000 (renames)
    (00000111
      ((00000010 renames) () t)
      ((00000010 renames) (0)
       (10011100 ((en-symbol (00101111 (00000101 renames)))
             (old-symbol (00110000 (00000101 renames)))
             (sens (registry-sens-for-en
                     (00101111 (00000101 renames))
                     semantic-registry)))
         (00000111
           ((00000010 sens) ()
            (fail
              (str+ "audit EN surface missing from semantic registry: "
                    (01000010 en-symbol))))
           ((00111110
              (str+ "(00001001 " (01000010 old-symbol) " " (01001100 sens) ")")
              uk-surface)
            t
            (check-aliases (00000110 renames)))
           (t t
            (fail
              (str+ "missing exact-SENS compatibility alias (00001001 "
                    (01000010 old-symbol) " " (01001100 sens) ")")))))))))
(check-aliases audit-renames)
(pass "stari-nazvy-smystovoho-audytu-lyshaiutsia-aliasamy-sumisnosti")

; Розкладка: українські назви набираються без латиниці.
(00001001 uk-layout
  "абвгґдеєжзиіїйклмнопрстуфхцчшщьюяАБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ0123456789-?!'*")

(00001001 typeable?
  (00001000 (text)
    (00000111
      ((00111100 text) (1) t)
      ((00111110 (00111111 text) uk-layout) t (typeable? (01000000 text)))
      (t t (00000001 ())))))

(00001001 check-typeable
  (00001000 (pairs)
    (00000111
      ((00000010 pairs) () t)
      ((00000010 pairs) (0)
       (00000111
         ((typeable? (00000110 (00000101 pairs))) t (check-typeable (00000110 pairs)))
         (t t (fail (str+ "Ukrainian name needs another keyboard layout: " (00000110 (00000101 pairs))))))))))
(check-typeable stable-uk)
(pass "every-stable-ukrainian-name-is-typeable-on-the-ukrainian-layout")

(00001001 latin-letter?
  (00001000 (char)
    (10011100 ((code (01000101 char)))
      (00000111
        ((00011010 code 65) 1 (00000001 ()))
        ((00011010 code 91) 1 t)
        ((00011010 code 97) 1 (00000001 ()))
        ((00011010 code 123) 1 t)
        (t t (00000001 ()))))))

; Латинські літери у виконуваному коді: поза рядками й коментарями.
(00001001 latin-in-code
  (00001000 (text in-string in-comment found)
    (00000111
      ((00111100 text) (1) found)
      (t t
       (10011100 ((c (00111111 text)) (rest (01000000 text)))
         (00000111
           ((00100010 in-comment t) (1)
            (latin-in-code rest () (00000111 ((00100010 c "\n") (1) ()) (t t t)) found))
           ((00100010 in-string t) (1)
            (00000111
              ((00100010 c "\\") (1) (latin-in-code (01000000 rest) t () found))
              ((00100010 c "\"") (1) (latin-in-code rest () () found))
              (t t (latin-in-code rest t () found))))
           ((00100010 c ";") (1) (latin-in-code rest () t found))
           ((00100010 c "\"") (1) (latin-in-code rest t () found))
           ((latin-letter? c) t (latin-in-code rest () () (00111010 found c)))
           (t t (latin-in-code rest () () found))))))))

(00001001 require-no-latin
  (00001000 (name path)
    (10011100 ((found (latin-in-code (10100110 path) () () "")))
      (00000111
        ((00111100 found) (1) (pass name))
        (t t (fail (str+ name ": латинські літери у виконуваному коді " path ": " found)))))))

(require-no-latin "ukrainian-acceptance-program-code-never-requires-latin-layout"
  "lib/surface/uk-acceptance.lisp")
(require-no-latin "ukrainska-prohrama-pryinnyattia-ne-potrebuie-latynskoi-rozkladky"
  "tests/fixtures/rivnopravnist-uk.lisp")

;; ===== Workflow контракту мови — канонічні шляхи .lisp (з xtask) =====
(00001001 check-contract-workflow
  (00001000 (path)
    (10011100 ((text (10100110 path)))
      (00000111
        ((00111110 "language-contract.my" text) t
         (fail (str+ path " still contains removed path language-contract.my")))
        ((00111110 "contracts/my-lisp/lock.my" text) t
         (fail (str+ path " still contains removed path contracts/my-lisp/lock.my")))
        (t t
         (require-needles "contract-workflows-use-canonical-lisp-paths" path
           (00000001 ("default: contracts/my-lisp/language-contract.lisp"
                   "default: contracts/my-lisp/lock.lisp"
                   "UPSTREAM_PATH: language-contract.lisp"))))))))
(check-contract-workflow ".github/workflows/sync-language-contract.yml")
(check-contract-workflow ".github/workflows/verify-language-contract.yml")

(01001000 "verify-repo: all checks passed")
