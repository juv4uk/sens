; contracts/compiler-semantic-input-v1.lisp
; #3757 — єдина межа семантичного вводу для обчислювача й компілятора.
;
; Цей файл НЕ визначає значення функцій і НЕ дублює таблиць Д1–Д8.
; Семантична влада лишається в language-contract.lisp та чинних
; ратифікованих доменних законах. Тут визначено лише форму пакета свідчень,
; який споживач перевіряє ПЕРЕД зниженням до машинних форм і виконанням.
;
; Основний закон межі:
;
;   точна доменна тотожність
;   + підтверджене походження семантичних повноважень
;   + посилання на допущений закон і доказ
;   + явний статус механізму
;   -> пакет можуть споживати компілятор та обчислювач
;
; Біти без домену, домен без закону чи застарілі свідчення походження
; не допускаються як семантичний вхід компілятора.
;
; Статус пропозиції навмисний: злиття цього файла є рішенням щодо
; реалізації, а не новою ратифікацією мовної семантики.

(
  (schema . compiler-semantic-input/1)
  (status . proposed-implementation-contract)
  (issue . #3757)

  (authority
    . ((semantic-root . "language-contract.lisp")
       (foundation-chain . "contracts/d1-d9-foundation-ratification.lisp")
       (meaning-owned-by . sens)
       (compiler-may-infer-meaning . no)
       (backend-may-infer-meaning . no)
       (host-name-authority . forbidden)
       (packed-byte-authority . forbidden)
       (legacy-sens8-authority . forbidden)))

  ; Запит передає точну тотожність, а не людське ім'я.
  ; Ширина не дублюється окремим числом: вона належить точній парі
  ; домену та бітового слова й перевіряється доменним законом і носієм.
  (request-shape
    . ((ідентичність
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
       (походження
        . ((repository . required)
           (revision . required-full-sha)
           (authority-path . required)
           (authority-sha256 . required)
           (language-contract-version . required)))))

  ; Статус семантичної тотожності та статус механізму — різні факти.
  ; Чинне доменне значення не гарантує наявності виконавчого механізму.
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

  ; Відмову потрібно класифікувати до машинного виконання, щоб помилка
  ; семантичних повноважень не маскувалася як несправність цілі чи інструментів.
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

  ; Споживач в іншому репозиторії перевіряє не лише номер контракту,
  ; а й точну редакцію та контрольний відбиток. Версія пояснює походження,
  ; а відбиток виключає підміну файла зі збереженим номером 11.8.
  (cross-repository-law
    . ((pin-revision . required)
       (pin-authority-sha256 . required)
       (verify-before-lowering . required)
       (stale-pin-fallback . forbidden)
       (auto-upgrade-semantic-meaning . forbidden)))

  ; Перший обмежений доказ належить #3758/cml#494.
  ; Конкретні координати навмисно НЕ повторюються: їх беруть із чинних
  ; доменних таблиць СЕНС, щоб цей контракт не став другою картою.
  (first-witness
    . ((producer . sens)
       (consumer . cml)
       (scope . current-d3-selectors)
       (semantic-oracle . evaluator)
       (compiler-mechanism . cml)
       (coordinate-table-owned-here . no)))

  (non-goals
    . (define-domain-maps
       ratify-domain-maps
       mint-compiler-opcodes-as-language-identity
       redefine-evaluator-semantics
       preserve-universal-sid8-ontology))
)
