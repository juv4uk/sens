; Перевірки документації й політик репозиторію — мовою.
; Перша частина перенесення `cargo xtask verify` (crates/xtask/src/checks.rs).
; Разом з українськими перевірками — повна заміна `cargo xtask verify`.
;
; Usage: sens scripts/verify-repo.lisp
; Друкує кожну перевірку; за першої ж проблеми — помилка й ненульовий вихід.

(0011 str+
  (0010 args
    (101110 (0010 (acc s) (110011110 acc s)) "" args)))

(0011 fail
  (0010 (message)
    (1001 (1110 (11011011 (str+ "FAIL: " message)) (100 (001 ()))))))

(0011 pass
  (0010 (name)
    (11011011 (str+ "ok: " name))))

(0011 contains? (0010 (text needle) (110101000 needle text)))

; Кожна голка з needles має бути в тексті; повертає перелік відсутніх.
(0011 missing-needles
  (0010 (text needles)
    (110
      ((010 needles) () (001 ()))
      ((010 needles) (0)
       (110
         ((contains? text (100 needles)) t (missing-needles text (011 needles)))
         (t t (111 (100 needles) (missing-needles text (011 needles)))))))))

(0011 require-needles
  (0010 (name path needles)
    (001000 ((missing (missing-needles (110110111 path) needles)))
      (110
        ((010 missing) () (pass name))
        ((010 missing) (0) (fail (str+ name ": " path " missing " (11110100 missing))))))))

(0011 forbid-needle
  (0010 (name path needle)
    (110
      ((contains? (110110111 path) needle) t
       (fail (str+ name ": " path " must not contain " (11110100 needle))))
      (t t t))))

(0011 any-needle?
  (0010 (text needles)
    (110
      ((010 needles) () (001 ()))
      ((010 needles) (0)
       (110
         ((contains? text (100 needles)) t t)
         (t t (any-needle? text (011 needles))))))))

; --- public-docs-share-current-project-identity-and-extension ---
(0011 check-doc-identity
  (0010 (path)
    (001000 ((doc (110110111 path)))
      (110
        ((any-needle? doc (001 ("reference implementation" "reference Rust implementation" "референсна реалізація" "референсна реалізація Rust")))
         t
         (110
           ((any-needle? doc (001 ("canonical Rust implementation" "канонічна реалізація на Rust" "kanonische Rust-Implementierung")))
            t
            (fail (str+ path ": implementation wording must not imply that Rust itself owns semantics")))
           (t t
            (110
              ((any-needle? doc (001 ("канонічне розширення вихідного коду — **`.lisp`**"
                                        "Канонічне розширення вихідного коду — **`.lisp`**"
                                        "canonical source extension is **`.lisp`**"
                                        "current canonical source extension is **`.lisp`**")))
               t
               (110
                 ((any-needle? doc (001 ("legacy alias" "legacy aliases")))
                  t
                  (110
                    ((contains? doc "`.wsm`") t
                     (110
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
(0011 check-manifests
  (0010 (entries)
    (110
      ((010 entries) () t)
      ((010 entries) (0)
       (001000 ((manifest (str+ "crates/" (100 entries) "/Cargo.toml")))
         (001000 ((text (110110111 manifest)))
           (110
             ((contains? text "[package]\nname = \"my-lisp") t
              (fail (str+ "cargo package prefix regression: " manifest " uses my-lisp*")))
             (t t (check-manifests (011 entries))))))))))

(check-manifests (read-dir "crates"))
(pass "cargo-workspace-has-no-my-lisp-package-prefix")

; --- public-docs-point-to-semantic-authority ---
(require-needles "public-docs-point-to-semantic-authority" "README.md"
  (001 ("docs/semantic-authority-map.md")))
(require-needles "public-docs-point-to-semantic-authority" "docs/language-core.md"
  (001 ("semantic-authority-map.md")))
(require-needles "public-docs-point-to-semantic-authority" "docs/semantic-authority-map.md"
  (001 ("language-contract.lisp")))
; Rust шукав без урахування регістру; у документі — «Ratified ADRs» і
; «executable conformance» / «Executable conformance».
(110
  ((any-needle? (110110111 "docs/semantic-authority-map.md") (001 ("Ratified ADR" "ratified ADR"))) t t)
  (t t (fail "docs/semantic-authority-map.md must mention ratified ADRs")))
(110
  ((any-needle? (110110111 "docs/semantic-authority-map.md") (001 ("Executable conformance" "executable conformance"))) t t)
  (t t (fail "docs/semantic-authority-map.md must mention executable conformance")))
(pass "public-docs-point-to-semantic-authority")

; --- host-semantic-surface-documentation-tracks-time-ownership ---
; Раніше шукало текст "unix-time-now" у builtins.rs; після #1477 вбудовані —
; примітиви за кодом, тож джерело — таблиця функцій і її метадані.
(require-needles "host-semantic-surface-documentation-tracks-time-ownership"
  "docs/host-semantic-surface.md"
  (001 ("mono-ns" "unix-time-now"
          "`utc-now` | `lib/time.lisp` | derived public clock meaning | HOST REMOVED")))
(require-needles "host-semantic-surface-documentation-tracks-time-ownership"
  "lib/time.lisp"
  (001 ("mono-ms" "utc-now")))
(require-needles "host-semantic-surface-documentation-tracks-time-ownership"
  "lib/surface/function-signatures.lisp"
  (001 ("(01011011 (kind builtin)")))
(forbid-needle "host-semantic-surface-documentation-tracks-time-ownership"
  "lib/surface/function-signatures.lisp" "(utc-now)")

; --- agent-onboarding / current-agent-authority / human-migration-doc ---
(require-needles "agent-onboarding-records-removed-coordination-surface" "AGENTS.md"
  (001 ("sens :9999" "swarm-node :910x"
          "Стара coordination surface на `:9999` фізично видалена"
          "мають повертати `unknown op`"
          "knowledge/swarm-legacy-deprecation.lisp"
          "Current coordination authority:" "`swarm-node`")))
(forbid-needle "agent-onboarding-records-removed-coordination-surface" "AGENTS.md"
  "This is a\n  first-class pattern, not a fallback")
(require-needles "agent-onboarding-records-removed-coordination-surface"
  "knowledge/swarm-legacy-deprecation.lisp"
  (001 ("(status . deprecated)" "(physical-status . removed)"
          "(runtime-rejection . confirmed)" "(coordination-authority . swarm-node)")))
(require-needles "human-migration-doc-keeps-semantic-and-coordination-planes-separate"
  "docs/swarm-mesh-v2.md"
  (001 ("sens :9999" "swarm-node :910x"
          "no longer the\ncoordination path going forward" "semantic oracle")))

; --- s2-explicitly-contracts-category-not-error-wording ---
(require-needles "s2-explicitly-contracts-category-not-error-wording"
  "docs/language-core-axioms.md"
  (001 ("The wording may differ; the *category* is the contract.")))
(require-needles "s2-explicitly-contracts-category-not-error-wording"
  "crates/sens/src/error.rs"
  (001 ("non-contractual: `kind` is what S2 ratifies")))

; --- Python-перевірки (поки викликаються; перенесення самих скриптів — окремо) ---
(0011 run-python
  (0010 (name script args)
    (001000 ((result (110101111 "python3" (111 script args))))
      (110
        ((11110111 (100 result) 0) (1) (pass name))
        ((11110111 (100 result) 0) (0)
         (fail (str+ name " failed\n" (1001 result) (10011 result))))))))

(run-python "meta-eval-evidence-matrix" "scripts/check-meta-eval-evidence.py" (001 ()))
(run-python "meta-eval-human-evidence-projection" "scripts/generate-meta-eval-evidence.py" (001 ("--check")))
(run-python "semantic-ownership-map-in-sync" "scripts/semantic-ownership.py" (001 ("--check")))

;; ===== Українська документація й розкладка (з xtask verify) =====

(0011 field (0010 (key form) (1001 (11100 key (011 form)))))

(0011 count-items
  (0010 (items)
    (110
      ((010 items) () 0)
      ((010 items) (0) (01010 1 (count-items (011 items)))))))

(0011 last-char
  (0010 (text)
    (110100011 text (01011 (110100010 text) 1) (110100010 text))))

; Стабільні українські назви з таблиці функцій: ((бітовий-код . назва) ...).
(0011 registry-rows (100 (110101001 (110110111 "lib/surface/semantic-registry.lisp"))))

(0011 stable-uk-pairs
  (0010 (rows)
    (110
      ((010 rows) () (001 ()))
      ((010 rows) (0)
       (001000 ((name (field (001 ук) (100 rows))))
         (110
           ((010 name) (1)
            (111 (111 (11110100 (100 (100 rows))) (11101110 name))
                  (stable-uk-pairs (011 rows))))
           (t t (stable-uk-pairs (011 rows)))))))))

(0011 stable-uk (stable-uk-pairs registry-rows))

; Документаційний індекс: (doc категорія КОД вид "сигнатура" "опис"), КОД — голі 8 біт.
(0011 uk-docs (011 (11100 (001 docs) (011 (100 (110101001 (110110111 "lib/surface/uk-docs.lisp")))))))
; Текстовий запис SENS для перевірок і join: голі 8 біт дають рівно 8 знаків,
; а SENS у лапках (текстовий сурогат) — 10, і перевірка його відкидає.
(0011 doc-id (0010 (doc) (11110100 (10011 doc))))
(0011 doc-kind (0010 (doc) (100111 doc)))
(0011 api-md (110110111 "docs/ukrainian-api.md"))

(0011 uk-name-for
  (0010 (id)
    (001000 ((found (11100 id stable-uk)))
      (110
        ((010 found) (0) (011 found))
        (t t (fail (str+ "документаційний ID " id " не має stable UK projection у registry")))))))

(0011 all-bits?
  (0010 (text)
    (110
      ((110011100 text) (1) t)
      ((110101000 (110101011 text) "01") t (all-bits? (110011101 text)))
      (t t (001 ())))))

(0011 check-docs
  (0010 (docs predicates mutations)
    (110
      ((010 docs) ()
       (110
         ((11010 10 predicates) 1
          (110
            ((11010 0 mutations) 1 t)
            (t t (fail "публічний каталог мутацій схлопнувся"))))
         (t t (fail "публічний каталог предикатів схлопнувся"))))
      ((010 docs) (0)
       (001000 ((id (doc-id (100 docs))) (kind (doc-kind (100 docs))))
         (110
           ((11110111 (110100010 id) 8) (0)
            (fail (str+ "документаційний join key має бути 8-бітним SID: " id)))
           ((all-bits? id) () (fail (str+ "документаційний join key має бути 8-бітним SID: " id)))
           (t t
            (001000 ((uk (uk-name-for id)))
              (001000 ((question (11110111 (last-char uk) "?"))
                    (bang (11110111 (last-char uk) "!"))
                    (predicate (11110111 kind (001 predicate)))
                    (mutation (11110111 kind (001 mutation))))
                (110
                  ((11110111 question predicate) (0)
                   (fail (str+ "українська назва " uk ": знак ? і predicate мусять збігатися")))
                  ((11110111 bang mutation) (0)
                   (fail (str+ uk ": ! зарезервований для мутації")))
                  (mutation (1)
                   (110
                     ((11110111 uk "встановити-елемент-вектора!") (1)
                      (check-docs (011 docs) predicates (01010 mutations 1)))
                     (t t (fail (str+ "несподівана мутація: " uk)))))
                  (predicate (1)
                   (check-docs (011 docs) (01010 predicates 1) mutations))
                  (t t (check-docs (011 docs) predicates mutations))))))))))))

(check-docs uk-docs 0 0)
(pass "dokumentatsiinyi-kliuch-ie-tilky-numeric")
(pass "znak-pytannia-tochno-vidpovidaie-predykatam")
(pass "znak-oklyku-tochno-vidpovidaie-mutatsii")

; Усі ID документації є в таблиці; усі задокументовані назви — у Markdown.
(0011 check-md-rows
  (0010 (pairs)
    (110
      ((010 pairs) () t)
      ((010 pairs) (0)
       (001000 ((id (100 (100 pairs))) (uk (011 (100 pairs))))
         (110
           ((010 (11100 id (101000 (0010 (doc) (111 (doc-id doc) t)) uk-docs))) ()
            (check-md-rows (011 pairs)))
           ((110101000 (str+ "| `" uk "` |") api-md) t (check-md-rows (011 pairs)))
           (t t (fail (str+ "публічне українське ім'я відсутнє у Markdown-довіднику: " uk)))))))))

(110
  ((11010 50 (count-items stable-uk)) 1 (check-md-rows stable-uk))
  (t t (fail "замало stable UK-назв у таблиці")))
(pass "vsi-stable-ukrainski-nazvy-maiut-numeric-zapys-u-dovidnyku")

; Смисловий аудит назв: підсумок збігається з даними.
(0011 audit (100 (110101001 (110110111 "lib/surface/uk-name-audit.lisp"))))
(0011 audit-renames (011 (11100 (001 renames) (011 audit))))
(0011 reviewed (field (001 stable-reviewed) audit))
(0011 renamed (field (001 renamed) audit))
(0011 retained (field (001 retained) audit))
(110
  ((11110111 reviewed (01010 renamed retained)) (1)
   (110
     ((11110111 renamed (count-items audit-renames)) (1)
      (110
        ((11110111 reviewed (count-items uk-docs)) (1) t)
        (t t (fail "смисловий аудит мусить покривати рівно documented UK-покриття"))))
     (t t (fail "(renamed N) розійшовся з фактичною кількістю (rename ...)"))))
  (t t (fail "stable-reviewed мусить дорівнювати renamed+retained")))
(pass "smyslovyi-audyt-summary-zbihaietsia-z-faktychnymy-danymy")

(0011 uk-surface (110110111 "lib/surface/uk.lisp"))
(0011 semantic-registry
  (100 (110101001 (110110111 "lib/surface/semantic-registry.lisp"))))
; EN surface -> exact SENS, derived from the single semantic registry.
(0011 registry-sens-for-en
  (0010 (name rows)
    (110
      ((010 rows) () ())
      ((11110111 (field (001 en) (100 rows)) name) (1)
       (100 (100 rows)))
      (t t (registry-sens-for-en name (011 rows))))))

; Every audited compatibility alias carries the exact SENS derived above.
; This keeps both host primitives and Lisp-owned callables free of runtime EN-name authority.

; Позиція першого входження marker у s від i; -1 якщо нема.
(0011 pos-of
  (0010 (s marker i)
    (110
      ((110011100 s) (1) -1)
      ((110101010 marker s) t i)
      (t t (pos-of (110011101 s) marker (01010 i 1))))))

(110
  ((11010 (pos-of uk-surface "(00001001 середовище env)" 0) 0) t
   (fail "uk.lisp: (00001001 середовище env) мусить бути лише в реєстрі, не в поверхні"))
  (t t t))
(pass "seredovyshche-ne-maie-povtornoho-surface-binding")

(0011 check-aliases
  (0010 (renames)
    (110
      ((010 renames) () t)
      ((010 renames) (0)
       (001000 ((en-symbol (1001 (100 renames)))
             (old-symbol (10011 (100 renames)))
             (sens (registry-sens-for-en
                     (1001 (100 renames))
                     semantic-registry)))
         (110
           ((010 sens) ()
            (fail
              (str+ "audit EN surface missing from semantic registry: "
                    (11101110 en-symbol))))
           ((110101000
              (str+ "(00001001 " (11101110 old-symbol) " " (11110100 sens) ")")
              uk-surface)
            t
            (check-aliases (011 renames)))
           (t t
            (fail
              (str+ "missing exact-SENS compatibility alias (00001001 "
                    (11101110 old-symbol) " " (11110100 sens) ")")))))))))
(check-aliases audit-renames)
(pass "stari-nazvy-smystovoho-audytu-lyshaiutsia-aliasamy-sumisnosti")

; Розкладка: українські назви набираються без латиниці.
(0011 uk-layout
  "абвгґдеєжзиіїйклмнопрстуфхцчшщьюяАБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ0123456789-?!'*")

(0011 typeable?
  (0010 (text)
    (110
      ((110011100 text) (1) t)
      ((110101000 (110101011 text) uk-layout) t (typeable? (110011101 text)))
      (t t (001 ())))))

(0011 check-typeable
  (0010 (pairs)
    (110
      ((010 pairs) () t)
      ((010 pairs) (0)
       (110
         ((typeable? (011 (100 pairs))) t (check-typeable (011 pairs)))
         (t t (fail (str+ "Ukrainian name needs another keyboard layout: " (011 (100 pairs))))))))))
(check-typeable stable-uk)
(pass "every-stable-ukrainian-name-is-typeable-on-the-ukrainian-layout")

(0011 latin-letter?
  (0010 (char)
    (001000 ((code (11100000 char)))
      (110
        ((11010 code 65) 1 (001 ()))
        ((11010 code 91) 1 t)
        ((11010 code 97) 1 (001 ()))
        ((11010 code 123) 1 t)
        (t t (001 ()))))))

; Латинські літери у виконуваному коді: поза рядками й коментарями.
(0011 latin-in-code
  (0010 (text in-string in-comment found)
    (110
      ((110011100 text) (1) found)
      (t t
       (001000 ((c (110101011 text)) (rest (110011101 text)))
         (110
           ((11110111 in-comment t) (1)
            (latin-in-code rest () (110 ((11110111 c "\n") (1) ()) (t t t)) found))
           ((11110111 in-string t) (1)
            (110
              ((11110111 c "\\") (1) (latin-in-code (110011101 rest) t () found))
              ((11110111 c "\"") (1) (latin-in-code rest () () found))
              (t t (latin-in-code rest t () found))))
           ((11110111 c ";") (1) (latin-in-code rest () t found))
           ((11110111 c "\"") (1) (latin-in-code rest t () found))
           ((latin-letter? c) t (latin-in-code rest () () (110011110 found c)))
           (t t (latin-in-code rest () () found))))))))

(0011 require-no-latin
  (0010 (name path)
    (001000 ((found (latin-in-code (110110111 path) () () "")))
      (110
        ((110011100 found) (1) (pass name))
        (t t (fail (str+ name ": латинські літери у виконуваному коді " path ": " found)))))))

(require-no-latin "ukrainian-acceptance-program-code-never-requires-latin-layout"
  "lib/surface/uk-acceptance.lisp")
(require-no-latin "ukrainska-prohrama-pryinnyattia-ne-potrebuie-latynskoi-rozkladky"
  "tests/fixtures/rivnopravnist-uk.lisp")

;; ===== Workflow контракту мови — канонічні шляхи .lisp (з xtask) =====
(0011 check-contract-workflow
  (0010 (path)
    (001000 ((text (110110111 path)))
      (110
        ((110101000 "language-contract.my" text) t
         (fail (str+ path " still contains removed path language-contract.my")))
        ((110101000 "contracts/my-lisp/lock.my" text) t
         (fail (str+ path " still contains removed path contracts/my-lisp/lock.my")))
        (t t
         (require-needles "contract-workflows-use-canonical-lisp-paths" path
           (001 ("default: contracts/my-lisp/language-contract.lisp"
                   "default: contracts/my-lisp/lock.lisp"
                   "UPSTREAM_PATH: language-contract.lisp"))))))))
(check-contract-workflow ".github/workflows/sync-language-contract.yml")
(check-contract-workflow ".github/workflows/verify-language-contract.yml")

(11011011 "verify-repo: all checks passed")
