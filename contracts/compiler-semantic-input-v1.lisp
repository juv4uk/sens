; contracts/compiler-semantic-input-v1.lisp
; #3757 — єдина межа семантичного вводу для evaluator/compiler.
;
; Цей файл НЕ визначає значення жодної функції й НЕ дублює карти D1–D8.
; Семантична влада лишається в language-contract.lisp та чинних
; доменних законах/ратифікаціях. Тут визначено лише форму доказового пакета,
; який споживач має перевірити ПЕРЕД lowering/виконанням.
;
; Основний закон межі:
;
;   exact identity
;   + exact authority provenance
;   + admitted law/proof reference
;   + explicit mechanism status
;   -> compiler/evaluator may consume
;
; Біти без домену, домен без закону, або семантика зі stale provenance
; не є допустимим compiler input.
;
; Статус proposal навмисний: merge цього файла є implementation decision,
; а не новою ратифікацією мовної семантики.

(
  (schema . compiler-semantic-input/1)
  (status . proposed-implementation-contract)
  (issue . #3757)

  (authority
    . ((semantic-root . "language-contract.lisp")
       (foundation-chain . "contracts/d1-d7-foundation-ratification.lisp")
       (meaning-owned-by . sens)
       (compiler-may-infer-meaning . no)
       (backend-may-infer-meaning . no)
       (host-name-authority . forbidden)
       (packed-byte-authority . forbidden)
       (legacy-sens8-authority . forbidden)))

  ; Один request несе identity, а не людське ім'я.
  ; width не дублюється окремим числом: він є властивістю exact domain/bits
  ; і має бути перевірений доменним carrier/law.
  (request-shape
    . ((identity
        . ((domain . required)
           (bits . required-exact)
           (surface . optional-non-authoritative)))
       (law
        . ((authority-ref . required)
           (proof-ref . required)
           (semantic-status . required)))
       (mechanism
        . ((execution-role . required)
           (mechanism-status . required)
           (mechanism-ref . required-when-admitted)))
       (provenance
        . ((repository . required)
           (revision . required-full-sha)
           (authority-path . required)
           (authority-sha256 . required)
           (language-contract-version . required))))))

  ; semantic-status і mechanism-status — різні факти.
  ; Поточна semantic residency не обіцяє наявність executable mechanism.
  (status-separation
    . ((semantic-status . (current research unallocated unknown))
       (mechanism-status . (admitted blocked-mechanism not-required unknown))
       (current-implies-mechanism . no)
       (mechanism-implies-semantic-admission . no)))

  (production-admission
    . ((require-exact-domain-bits . yes)
       (require-current-semantic-status . yes)
       (require-admitted-law-proof . yes)
       (require-authority-provenance-match . yes)
       (require-mechanism-when-execution-needs-it . yes)
       (research-domain-policy . reject)
       (unknown-status-policy . reject)
       (stale-provenance-policy . reject)
       (legacy-width-coercion-policy . reject)
       (human-name-roundtrip-policy . reject)))

  ; Відмова має бути категоризована до backend execution, щоб помилка
  ; семантичної влади не маскувалася як target/toolchain failure.
  (fail-closed-categories
    . (missing-domain
       width-domain-mismatch
       unallocated-identity
       unratified-or-research-domain
       missing-law-proof
       stale-authority-revision
       authority-digest-mismatch
       blocked-mechanism
       legacy-identity-coercion
       host-name-semantic-roundtrip))

  ; Обидва споживачі мають приймати той самий перевірений пакет.
  ; Вони можуть реалізувати різні механізми, але не різні значення.
  (consumer-law
    . ((evaluator-input . verified-semantic-request)
       (compiler-input . verified-semantic-request)
       (same-authority-bundle . required)
       (same-semantic-verdict . required)
       (mechanism-may-differ . yes)))

  ; Cross-repo consumer зобов'язаний перевірити не лише номер Contract,
  ; а exact revision+digest. Номер версії є пояснювальним provenance,
  ; digest — захистом від "11.6, але інший файл".
  (cross-repository-law
    . ((pin-revision . required)
       (pin-authority-sha256 . required)
       (verify-before-lowering . required)
       (stale-pin-fallback . forbidden)
       (auto-upgrade-semantic-meaning . forbidden)))

  ; Перший bounded witness належить #3758/cml#494.
  ; Конкретні координати навмисно НЕ повторюються тут: вони беруться
  ; з поточної SENS authority, щоб цей contract не став другою картою.
  (first-witness
    . ((producer . sens)
       (consumer . cml)
       (scope . current-d3-selectors)
       (semantic-oracle . evaluator)
       (compiler-mechanism . cml)
       (coordinate-table-owned-here . no)))

  (non-goals
    . (define-domain-maps
       ratify-d8
       mint-compiler-opcodes-as-language-identity
       redefine-evaluator-semantics
       preserve-universal-sid8-ontology))
)
