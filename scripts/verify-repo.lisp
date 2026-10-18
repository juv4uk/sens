; Перевірки документації й політик репозиторію — мовою.
; Перша частина перенесення `cargo xtask verify` (crates/xtask/src/checks.rs).
; Разом з українськими перевірками — повна заміна `cargo xtask verify`.
;
; Usage: sens scripts/verify-repo.lisp
; Друкує кожну перевірку; за першої ж проблеми — помилка й ненульовий вихід.

(визначити str+
  (функція args
    (згорнути (функція (acc s) (рядок-додати acc s)) "" args)))

(визначити fail
  (функція (message)
    (друге (список (11011011 (str+ "FAIL: " message)) (перше (як-є ()))))))

(визначити pass
  (функція (name)
    (11011011 (str+ "ok: " name))))

(визначити contains? (функція (text needle) (110101000 needle text)))

; Кожна голка з needles має бути в тексті; повертає перелік відсутніх.
(визначити missing-needles
  (функція (text needles)
    (за-умовою
      ((атом? needles) () (як-є ()))
      ((атом? needles) (0)
       (за-умовою
         ((contains? text (перше needles)) t (missing-needles text (решта needles)))
         (t t (сполучити (перше needles) (missing-needles text (решта needles)))))))))

(визначити require-needles
  (функція (name path needles)
    (001000 ((missing (missing-needles (110110111 path) needles)))
      (за-умовою
        ((атом? missing) () (pass name))
        ((атом? missing) (ні) (провал (str+ name ": " path " missing " (значення-у-текст missing))))))))

(визначити forbid-needle
  (функція (name path needle)
    (за-умовою
      ((contains? (110110111 path) needle) t
       (провал (str+ name ": " path " must not contain " (значення-у-текст needle))))
      (t t t))))

(визначити any-needle?
  (функція (text needles)
    (за-умовою
      ((атом? needles) () (як-є ()))
      ((атом? needles) (0)
       (за-умовою
         ((contains? text (перше needles)) t t)
         (t t (any-needle? text (решта needles))))))))

; --- public-docs-share-current-project-identity-and-extension ---
(визначити check-doc-identity
  (функція (path)
    (001000 ((doc (110110111 path)))
      (за-умовою
        ((any-needle? doc (як-є ("reference implementation" "reference Rust implementation" "референсна реалізація" "референсна реалізація Rust")))
         t
         (за-умовою
           ((any-needle? doc (як-є ("canonical Rust implementation" "канонічна реалізація на Rust" "kanonische Rust-Implementierung")))
            t
            (провал (str+ path ": implementation wording must not imply that Rust itself owns semantics")))
           (t t
            (за-умовою
              ((any-needle? doc (як-є ("канонічне розширення вихідного коду — **`.lisp`**"
                                        "Канонічне розширення вихідного коду — **`.lisp`**"
                                        "canonical source extension is **`.lisp`**"
                                        "current canonical source extension is **`.lisp`**")))
               t
               (за-умовою
                 ((any-needle? doc (як-є ("legacy alias" "legacy aliases")))
                  t
                  (за-умовою
                    ((contains? doc "`.wsm`") t
                     (за-умовою
                       ((contains? doc "`.my`") t t)
                       (t t (провал (str+ path ": must name `.my` as a legacy alias")))))
                    (t t (провал (str+ path ": must name `.wsm` as a legacy alias")))))
                 (t t (провал (str+ path ": must call `.wsm`/`.my` legacy aliases")))))
              (t t (провал (str+ path ": must state `.lisp` as the canonical extension")))))))
        (t t (провал (str+ path ": must describe Rust as a reference implementation")))))))

(check-doc-identity "README.md")
(check-doc-identity "docs/language-core.md")
(pass "public-docs-share-current-project-identity-and-extension")

; --- cargo-workspace-has-no-my-lisp-package-prefix ---
; Назва пакета (рядок одразу після `[package]`) з префіксом my-lisp — регресія.
; Бінарники з назвою my-lisp (сумісні псевдоніми CLI) — не пакет, їх не чіпаємо.
(визначити check-manifests
  (функція (entries)
    (за-умовою
      ((атом? entries) () t)
      ((атом? entries) (0)
       (001000 ((manifest (str+ "crates/" (перше entries) "/Cargo.toml")))
         (001000 ((text (110110111 manifest)))
           (за-умовою
             ((contains? text "[package]\nname = \"my-lisp") t
              (провал (str+ "cargo package prefix regression: " manifest " uses my-lisp*")))
             (t t (check-manifests (решта entries))))))))))

(check-manifests (read-dir "crates"))
(pass "cargo-workspace-has-no-my-lisp-package-prefix")

; --- public-docs-point-to-semantic-authority ---
(require-needles "public-docs-point-to-semantic-authority" "README.md"
  (як-є ("docs/semantic-authority-map.md")))
(require-needles "public-docs-point-to-semantic-authority" "docs/language-core.md"
  (як-є ("semantic-authority-map.md")))
(require-needles "public-docs-point-to-semantic-authority" "docs/semantic-authority-map.md"
  (як-є ("language-contract.lisp")))
; Rust шукав без урахування регістру; у документі — «Ratified ADRs» і
; «executable conformance» / «Executable conformance».
(за-умовою
  ((any-needle? (110110111 "docs/semantic-authority-map.md") (як-є ("Ratified ADR" "ratified ADR"))) t t)
  (t t (провал "docs/semantic-authority-map.md must mention ratified ADRs")))
(за-умовою
  ((any-needle? (110110111 "docs/semantic-authority-map.md") (як-є ("Executable conformance" "executable conformance"))) t t)
  (t t (провал "docs/semantic-authority-map.md must mention executable conformance")))
(pass "public-docs-point-to-semantic-authority")

; --- host-semantic-surface-documentation-tracks-time-ownership ---
; Раніше шукало текст "unix-time-now" у builtins.rs; після #1477 вбудовані —
; примітиви за кодом, тож джерело — таблиця функцій і її метадані.
(require-needles "host-semantic-surface-documentation-tracks-time-ownership"
  "docs/host-semantic-surface.md"
  (як-є ("mono-ns" "unix-time-now"
          "`utc-now` | `lib/time.lisp` | derived public clock meaning | HOST REMOVED")))
(require-needles "host-semantic-surface-documentation-tracks-time-ownership"
  "lib/time.lisp"
  (як-є ("mono-ms" "utc-now")))
(require-needles "host-semantic-surface-documentation-tracks-time-ownership"
  "lib/surface/function-signatures.lisp"
  (як-є ("(01011011 (kind builtin)")))
(forbid-needle "host-semantic-surface-documentation-tracks-time-ownership"
  "lib/surface/function-signatures.lisp" "(utc-now)")

; --- agent-onboarding / current-agent-authority / human-migration-doc ---
(require-needles "agent-onboarding-records-removed-coordination-surface" "AGENTS.md"
  (як-є ("sens :9999" "swarm-node :910x"
          "Стара coordination surface на `:9999` фізично видалена"
          "мають повертати `unknown op`"
          "knowledge/swarm-legacy-deprecation.lisp"
          "Current coordination authority:" "`swarm-node`")))
(forbid-needle "agent-onboarding-records-removed-coordination-surface" "AGENTS.md"
  "This is a\n  first-class pattern, not a fallback")
(require-needles "agent-onboarding-records-removed-coordination-surface"
  "knowledge/swarm-legacy-deprecation.lisp"
  (як-є ("(status . deprecated)" "(physical-status . removed)"
          "(runtime-rejection . confirmed)" "(coordination-authority . swarm-node)")))
(require-needles "human-migration-doc-keeps-semantic-and-coordination-planes-separate"
  "docs/swarm-mesh-v2.md"
  (як-є ("sens :9999" "swarm-node :910x"
          "no longer the\ncoordination path going forward" "semantic oracle")))

; --- s2-explicitly-contracts-category-not-error-wording ---
(require-needles "s2-explicitly-contracts-category-not-error-wording"
  "docs/language-core-axioms.md"
  (як-є ("The wording may differ; the *category* is the contract.")))
(require-needles "s2-explicitly-contracts-category-not-error-wording"
  "crates/sens/src/error.rs"
  (як-є ("non-contractual: `kind` is what S2 ratifies")))

; --- Python-перевірки (поки викликаються; перенесення самих скриптів — окремо) ---
(визначити run-python
  (функція (name script args)
    (001000 ((result (110101111 "python3" (сполучити script args))))
      (за-умовою
        ((11110111 (перше result) 0) (1) (pass name))
        ((11110111 (перше result) 0) (0)
         (провал (str+ name " failed\n" (друге result) (третє result))))))))

(run-python "meta-eval-evidence-matrix" "scripts/check-meta-eval-evidence.py" (як-є ()))
(run-python "meta-eval-human-evidence-projection" "scripts/generate-meta-eval-evidence.py" (як-є ("--check")))
(run-python "semantic-ownership-map-in-sync" "scripts/semantic-ownership.py" (як-є ("--check")))

;; ===== Українська документація й розкладка (з xtask verify) =====

(визначити field (функція (key form) (друге (11100 key (решта form)))))

(визначити count-items
  (функція (items)
    (за-умовою
      ((атом? items) () 0)
      ((атом? items) (0) (01010 1 (count-items (решта items)))))))

(визначити last-char
  (функція (text)
    (110100011 text (01011 (110100010 text) 1) (110100010 text))))

; Стабільні українські назви з таблиці функцій: ((бітовий-код . назва) ...).
(визначити registry-rows (перше (110101001 (110110111 "lib/surface/semantic-registry.lisp"))))

(визначити stable-uk-pairs
  (функція (rows)
    (за-умовою
      ((атом? rows) () (як-є ()))
      ((атом? rows) (0)
       (001000 ((name (field (як-є ук) (перше rows))))
         (за-умовою
           ((атом? name) (1)
            (сполучити (сполучити (11110100 (перше (перше rows))) (11101110 name))
                  (stable-uk-pairs (решта rows))))
           (t t (stable-uk-pairs (решта rows)))))))))

(визначити stable-uk (stable-uk-pairs registry-rows))

; Документаційний індекс: (doc категорія КОД вид "сигнатура" "опис"), КОД — голі 8 біт.
(визначити uk-docs (решта (11100 (як-є docs) (решта (перше (110101001 (110110111 "lib/surface/uk-docs.lisp")))))))
; Текстовий запис SENS для перевірок і join: голі 8 біт дають рівно 8 знаків,
; а SENS у лапках (текстовий сурогат) — 10, і перевірка його відкидає.
(визначити doc-id (функція (doc) (11110100 (10011 doc))))
(визначити doc-kind (функція (doc) (100111 doc)))
(визначити api-md (110110111 "docs/ukrainian-api.md"))

(визначити uk-name-for
  (функція (id)
    (001000 ((found (11100 id stable-uk)))
      (за-умовою
        ((атом? found) (0) (решта found))
        (t t (провал (str+ "документаційний ID " id " не має stable UK projection у registry")))))))

(визначити all-bits?
  (функція (text)
    (за-умовою
      ((110011100 text) (1) t)
      ((110101000 (110101011 text) "01") t (all-bits? (110011101 text)))
      (t t (як-є ())))))

(визначити check-docs
  (функція (docs predicates mutations)
    (за-умовою
      ((атом? docs) ()
       (за-умовою
         ((11010 10 predicates) 1
          (за-умовою
            ((11010 0 mutations) 1 t)
            (t t (провал "публічний каталог мутацій схлопнувся"))))
         (t t (провал "публічний каталог предикатів схлопнувся"))))
      ((атом? docs) (0)
       (001000 ((id (doc-id (перше docs))) (kind (doc-kind (перше docs))))
         (за-умовою
           ((11110111 (110100010 id) 8) (0)
            (провал (str+ "документаційний join key має бути 8-бітним SID: " id)))
           ((all-bits? id) () (провал (str+ "документаційний join key має бути 8-бітним SID: " id)))
           (t t
            (001000 ((uk (uk-name-for id)))
              (001000 ((question (11110111 (last-char uk) "?"))
                    (bang (11110111 (last-char uk) "!"))
                    (predicate (11110111 kind (як-є predicate)))
                    (mutation (11110111 kind (як-є mutation))))
                (за-умовою
                  ((11110111 question predicate) (0)
                   (провал (str+ "українська назва " uk ": знак ? і predicate мусять збігатися")))
                  ((11110111 bang mutation) (0)
                   (провал (str+ uk ": ! зарезервований для мутації")))
                  (mutation (1)
                   (за-умовою
                     ((11110111 uk "встановити-елемент-вектора!") (1)
                      (check-docs (решта docs) predicates (01010 mutations 1)))
                     (t t (провал (str+ "несподівана мутація: " uk)))))
                  (predicate (1)
                   (check-docs (решта docs) (01010 predicates 1) mutations))
                  (t t (check-docs (решта docs) predicates mutations))))))))))))

(check-docs uk-docs 0 0)
(pass "dokumentatsiinyi-kliuch-ie-tilky-numeric")
(pass "znak-pytannia-tochno-vidpovidaie-predykatam")
(pass "znak-oklyku-tochno-vidpovidaie-mutatsii")

; Усі ID документації є в таблиці; усі задокументовані назви — у Markdown.
(визначити check-md-rows
  (функція (pairs)
    (за-умовою
      ((атом? pairs) () t)
      ((атом? pairs) (0)
       (001000 ((id (перше (перше pairs))) (uk (решта (перше pairs))))
         (за-умовою
           ((атом? (11100 id (101000 (функція (doc) (сполучити (doc-id doc) t)) uk-docs))) ()
            (check-md-rows (решта pairs)))
           ((110101000 (str+ "| `" uk "` |") api-md) t (check-md-rows (решта pairs)))
           (t t (провал (str+ "публічне українське ім'я відсутнє у Markdown-довіднику: " uk)))))))))

(за-умовою
  ((11010 50 (count-items stable-uk)) 1 (check-md-rows stable-uk))
  (t t (провал "замало stable UK-назв у таблиці")))
(pass "vsi-stable-ukrainski-nazvy-maiut-numeric-zapys-u-dovidnyku")

; Смисловий аудит назв: підсумок збігається з даними.
(визначити audit (перше (110101001 (110110111 "lib/surface/uk-name-audit.lisp"))))
(визначити audit-renames (решта (11100 (як-є renames) (решта audit))))
(визначити reviewed (field (як-є stable-reviewed) audit))
(визначити renamed (field (як-є renamed) audit))
(визначити retained (field (як-є retained) audit))
(за-умовою
  ((11110111 reviewed (01010 renamed retained)) (1)
   (за-умовою
     ((11110111 renamed (count-items audit-renames)) (1)
      (за-умовою
        ((11110111 reviewed (count-items uk-docs)) (1) t)
        (t t (провал "смисловий аудит мусить покривати рівно documented UK-покриття"))))
     (t t (провал "(renamed N) розійшовся з фактичною кількістю (rename ...)"))))
  (t t (провал "stable-reviewed мусить дорівнювати renamed+retained")))
(pass "smyslovyi-audyt-summary-zbihaietsia-z-faktychnymy-danymy")

(визначити uk-surface (110110111 "lib/surface/uk.lisp"))
(визначити semantic-registry
  (перше (110101001 (110110111 "lib/surface/semantic-registry.lisp"))))
; EN surface -> exact SENS, derived from the single semantic registry.
(визначити registry-sens-for-en
  (функція (name rows)
    (за-умовою
      ((атом? rows) () ())
      ((11110111 (field (як-є en) (перше rows)) name) (1)
       (перше (перше rows)))
      (t t (registry-sens-for-en name (решта rows))))))

; Every audited compatibility alias carries the exact SENS derived above.
; This keeps both host primitives and Lisp-owned callables free of runtime EN-name authority.

; Позиція першого входження marker у s від i; -1 якщо нема.
(визначити pos-of
  (функція (s marker i)
    (за-умовою
      ((110011100 s) (1) -1)
      ((110101010 marker s) t i)
      (t t (pos-of (110011101 s) marker (01010 i 1))))))

(за-умовою
  ((11010 (pos-of uk-surface "(00001001 середовище env)" 0) 0) t
   (провал "uk.lisp: (00001001 середовище env) мусить бути лише в реєстрі, не в поверхні"))
  (t t t))
(pass "seredovyshche-ne-maie-povtornoho-surface-binding")

(визначити check-aliases
  (функція (renames)
    (за-умовою
      ((атом? renames) () t)
      ((атом? renames) (0)
       (001000 ((en-symbol (друге (перше renames)))
             (old-symbol (10011 (перше renames)))
             (sens (registry-sens-for-en
                     (друге (перше renames))
                     semantic-registry)))
         (за-умовою
           ((атом? sens) ()
            (провал
              (str+ "audit EN surface missing from semantic registry: "
                    (11101110 en-symbol))))
           ((110101000
              (str+ "(00001001 " (11101110 old-symbol) " " (11110100 sens) ")")
              uk-surface)
            t
            (check-aliases (решта renames)))
           (t t
            (провал
              (str+ "missing exact-SENS compatibility alias (00001001 "
                    (11101110 old-symbol) " " (11110100 sens) ")")))))))))
(check-aliases audit-renames)
(pass "stari-nazvy-smystovoho-audytu-lyshaiutsia-aliasamy-sumisnosti")

; Розкладка: українські назви набираються без латиниці.
(визначити uk-layout
  "абвгґдеєжзиіїйклмнопрстуфхцчшщьюяАБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ0123456789-?!'*")

(визначити typeable?
  (функція (text)
    (за-умовою
      ((110011100 text) (1) t)
      ((110101000 (110101011 text) uk-layout) t (typeable? (110011101 text)))
      (t t (як-є ())))))

(визначити check-typeable
  (функція (pairs)
    (за-умовою
      ((атом? pairs) () t)
      ((атом? pairs) (0)
       (за-умовою
         ((typeable? (решта (перше pairs))) t (check-typeable (решта pairs)))
         (t t (провал (str+ "Ukrainian name needs another keyboard layout: " (решта (перше pairs))))))))))
(check-typeable stable-uk)
(pass "every-stable-ukrainian-name-is-typeable-on-the-ukrainian-layout")

(визначити latin-letter?
  (функція (char)
    (001000 ((code (11100000 char)))
      (за-умовою
        ((11010 code 65) 1 (як-є ()))
        ((11010 code 91) 1 t)
        ((11010 code 97) 1 (як-є ()))
        ((11010 code 123) 1 t)
        (t t (як-є ()))))))

; Латинські літери у виконуваному коді: поза рядками й коментарями.
(визначити latin-in-code
  (функція (text in-string in-comment found)
    (за-умовою
      ((110011100 text) (1) found)
      (t t
       (001000 ((c (110101011 text)) (rest (110011101 text)))
         (за-умовою
           ((11110111 in-comment t) (1)
            (latin-in-code rest () (за-умовою ((11110111 c "\n") (1) ()) (t t t)) found))
           ((11110111 in-string t) (1)
            (за-умовою
              ((11110111 c "\\") (1) (latin-in-code (110011101 rest) t () found))
              ((11110111 c "\"") (1) (latin-in-code rest () () found))
              (t t (latin-in-code rest t () found))))
           ((11110111 c ";") (1) (latin-in-code rest () t found))
           ((11110111 c "\"") (1) (latin-in-code rest t () found))
           ((latin-letter? c) t (latin-in-code rest () () (110011110 found c)))
           (t t (latin-in-code rest () () found))))))))

(визначити require-no-latin
  (функція (name path)
    (001000 ((found (latin-in-code (110110111 path) () () "")))
      (за-умовою
        ((110011100 found) (1) (pass name))
        (t t (провал (str+ name ": латинські літери у виконуваному коді " path ": " found)))))))

(require-no-latin "ukrainian-acceptance-program-code-never-requires-latin-layout"
  "lib/surface/uk-acceptance.lisp")
(require-no-latin "ukrainska-prohrama-pryinnyattia-ne-potrebuie-latynskoi-rozkladky"
  "tests/fixtures/rivnopravnist-uk.lisp")

;; ===== Workflow контракту мови — канонічні шляхи .lisp (з xtask) =====
(визначити check-contract-workflow
  (функція (path)
    (001000 ((text (110110111 path)))
      (за-умовою
        ((110101000 "language-contract.my" text) t
         (провал (str+ path " still contains removed path language-contract.my")))
        ((110101000 "contracts/my-lisp/lock.my" text) t
         (провал (str+ path " still contains removed path contracts/my-lisp/lock.my")))
        (t t
         (require-needles "contract-workflows-use-canonical-lisp-paths" path
           (як-є ("default: contracts/my-lisp/language-contract.lisp"
                   "default: contracts/my-lisp/lock.lisp"
                   "UPSTREAM_PATH: language-contract.lisp"))))))))
(check-contract-workflow ".github/workflows/sync-language-contract.yml")
(check-contract-workflow ".github/workflows/verify-language-contract.yml")

(11011011 "verify-repo: all checks passed")

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити провал fail)
(визначити згорнути reduce)
(визначити рядок-додати string-append)
