; #1115 — чинний контракт раннього зведення українського коду СЕНС.
; Історичне ім'я файла лишається provenance і сумісною адресою.
; Вісім бітів старого SID8/Sens8 не визначають домен і не дають виклику.
; Ратифіковані `lib/domains/d1.lisp` ... `d10.lisp` володіють
; (домен, точне бітове слово), а колонка «укр» є людською проєкцією.
; Нижній механізм отримує код і аргументи, не вибирає семантику.
; Це контракт на дані; не додаткова таблиця тотожностей та не evaluator.

(early-sid-lowering-contract-1
  ((resolution
     (owner sens)
     (source ratified-domain-tables)
     (input full-ukr-projection)
     (output exact-domain-and-bits)
     (peer-surfaces-same-identity only-when-unambiguous))
   (backend-entry
     (required-fields (доменний-код аргументи договір))
     (surface-name forbidden)
     (historical-sid8-or-sens8 forbidden)
     (native-operator-name forbidden)
     (domain-reinterpretation forbidden))
   (data-separation
     (quoted-symbol-remains-data yes)
     (string-remains-data yes))
   (failure
     (unadmitted-surface rejected)
     (ambiguous-projection rejected)
     (unadmitted-domain-mechanism rejected)
     (backend-surface-routing rejected))
   (round-trip
     (domain-preserved yes)
     (exact-bits-preserved yes)
     (leading-zeroes-preserved yes))))
