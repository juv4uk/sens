; External translation boundary for Advice Taker.
;
; Migrated: bare host truthiness t → exact D1:YES text projection #d1:1.
; Two-field COND. Reuses knowledge.lisp validators and advice-decision surface.
; Width is identity; every bit of the domain address is valued.
;
; The translator is deliberately NOT a semantic authority. It may emit only
; finite Lisp data in the versioned shape below. Lisp validates that data,
; asks the existing advice boundary whether proposed knowledge is admissible,
; and classifies the review. Nothing in this file writes *knowledge-journal*.
;
; Canonical proposal shape:
;   (translation/1 STATUS KIND SOURCE PAYLOAD)
;
; STATUS: candidate | ambiguous | rejected
; KIND:   clause | batch | query
;
; Review shape:
;   (translation-review/1 STATUS CODE PROPOSAL DETAIL)
; Review STATUS is accepted | rejected | ambiguous.

(визначити *translation-schema* (як-є translation/1))
(визначити *translation-review-schema* (як-є translation-review/1))
(визначити *translation-evidence-schema* (як-є translation-evidence/1))
(визначити *translation-evidence* (як-є ()))

(визначити переклад-стан
  (функція (proposal) (друге proposal)))

(визначити переклад-вид
  (функція (proposal) (третє proposal)))

(визначити переклад-джерело
  (функція (proposal) (четверте proposal)))

(визначити переклад-вміст
  (функція (proposal) (п'ятий proposal)))

(визначити статус-запису-перекладу-коректний?
  (функція (status)
    (за-умовою
      ((тотожне? (символ? status) (як-є ())) (як-є ()))
      ((тотожне? status (як-є candidate)) так)
      ((тотожне? status (як-є ambiguous)) так)
      ((тотожне? status (як-є rejected)) так)
      (так (як-є ())))))

(визначити вид-кандидата-перекладу-коректний?
  (функція (kind)
    (за-умовою
      ((тотожне? (символ? kind) (як-є ())) (як-є ()))
      ((тотожне? kind (як-є clause)) так)
      ((тотожне? kind (як-є batch)) так)
      ((тотожне? kind (як-є query)) так)
      (так (як-є ())))))

; Envelope validation owns only the protocol shell. Payload meaning is checked
; separately so a well-shaped translator message containing malformed semantic
; data can be named `invalid-candidate` instead of collapsing into a generic
; transport/envelope failure.
(визначити структура-обгортки-перекладу-коректна?
  (функція (proposal)
    (за-умовою
      ((атом? proposal) (як-є ()))
      ((тотожне? (правильно-структурований-список-знань? proposal) (як-є ())) (як-є ()))
      ((тотожне? (тотожне? (довжина proposal) 5) (як-є ())) (як-є ()))
      ((тотожне? (символ? (перше proposal)) (як-є ())) (як-є ()))
      ((тотожне? (перше proposal) *translation-schema*)
       (за-умовою
         ((тотожне? (статус-запису-перекладу-коректний? (переклад-стан proposal)) (як-є ()))
          (як-є ()))
         ((тотожне? (вид-кандидата-перекладу-коректний? (переклад-вид proposal)) (як-є ()))
          (як-є ()))
         ((класифікувати-рядкове-значення (переклад-джерело proposal))
          (як-є ()))
         (так так)))
      (так (як-є ())))))

(визначити пакет-кандидатів-перекладу-коректний?
  (функція (payload)
    (за-умовою
      ((атом? payload) (як-є ()))
      ((тотожне? (правильно-структурований-список-знань? payload) (як-є ())) (як-є ()))
      (так (клаузи-бази-знань-коректні? payload)))))

(визначити вміст-кандидата-перекладу-коректний?
  (функція (kind payload)
    (за-умовою
      ((тотожне? kind (як-є clause)) (клауза-бази-знань-коректна? payload))
      ((тотожне? kind (як-є batch)) (пакет-кандидатів-перекладу-коректний? payload))
      ((тотожне? kind (як-є query)) (ціль-бази-знань-коректна? payload))
      (так (як-є ())))))

(визначити альтернативні-варіанти-перекладу-коректні?
  (функція (kind alternatives)
    (за-умовою
      ((атом? alternatives) (як-є ()))
      ((вміст-кандидата-перекладу-коректний? kind (перше alternatives))
       (за-умовою
         ((атом? (решта alternatives)) так)
         (так (альтернативні-варіанти-перекладу-коректні? kind (решта alternatives)))))
      (так (як-є ())))))

; Ambiguity is evidence only when the translator exposes at least two valid
; alternatives. One alternative is just a candidate; zero is not ambiguity.
(визначити опис-неоднозначності-перекладу-коректний?
  (функція (kind payload)
    (за-умовою
      ((тотожне? (правильно-структурований-список-знань? payload) (як-є ())) (як-є ()))
      ((атом? (решта payload)) (як-є ()))
      (так (альтернативні-варіанти-перекладу-коректні? kind payload)))))

(визначити створити-переклад-перевірка
  (функція (status code proposal detail)
    (список *translation-review-schema* status code proposal detail)))

(визначити переклад-перевірка-стан
  (функція (review) (друге review)))

(визначити переклад-перевірка-код
  (функція (review) (третє review)))

(визначити переклад-перевірка-пропозиція
  (функція (review) (четверте review)))

(визначити переклад-перевірка-деталь
  (функція (review) (п'ятий review)))

(визначити статус-огляду-кандидата-перекладу-коректний?
  (функція (status)
    (за-умовою
      ((тотожне? (символ? status) (як-є ())) (як-є ()))
      ((тотожне? status (як-є accepted)) так)
      ((тотожне? status (як-є rejected)) так)
      ((тотожне? status (як-є ambiguous)) так)
      (так (як-є ())))))

(визначити запис-огляду-перекладу-коректний?
  (функція (review)
    (за-умовою
      ((атом? review) (як-є ()))
      ((тотожне? (правильно-структурований-список-знань? review) (як-є ())) (як-є ()))
      ((тотожне? (тотожне? (довжина review) 5) (як-є ())) (як-є ()))
      ((тотожне? (символ? (перше review)) (як-є ())) (як-є ()))
      ((тотожне? (перше review) *translation-review-schema*)
       (за-умовою
         ((тотожне? (статус-огляду-кандидата-перекладу-коректний? (переклад-перевірка-стан review)) (як-є ()))
          (як-є ()))
         ((тотожне? (символ? (переклад-перевірка-код review)) (як-є ()))
          (як-є ()))
         (так так)))
      (так (як-є ())))))

(визначити рішення-на-основі-огляду-перекладу-й-поради
  (функція (proposal decision)
    (за-умовою
      ((атом? decision)
       (створити-переклад-перевірка
         (як-є rejected) (як-є malformed-advice-decision) proposal decision))
      ((тотожне? (символ? (перше decision)) (як-є ()))
       (створити-переклад-перевірка
         (як-є rejected) (як-є malformed-advice-decision) proposal decision))
      ((тотожне? (перше decision) (як-є accepted))
       (створити-переклад-перевірка
         (як-є accepted) (як-є knowledge-accepted) proposal decision))
      ((тотожне? (перше decision) (як-є conflict))
       (створити-переклад-перевірка
         (як-є rejected) (як-є knowledge-conflict) proposal decision))
      ((тотожне? (перше decision) (як-є rejected))
       (створити-переклад-перевірка
         (як-є rejected) (як-є knowledge-rejected) proposal decision))
      (так
       (створити-переклад-перевірка
         (як-є rejected) (як-є malformed-advice-decision) proposal decision)))))

(визначити отримати-кандидата-на-огляд-перекладу
  (функція (module-name proposal)
    ((функція (kind payload)
      (за-умовою
        ((тотожне? (вміст-кандидата-перекладу-коректний? kind payload) (як-є ()))
         (створити-переклад-перевірка
           (як-є rejected) (як-є invalid-candidate) proposal payload))
        ((тотожне? kind (як-є query))
         (створити-переклад-перевірка
           (як-є accepted) (як-є query) proposal payload))
        ((тотожне? kind (як-є clause))
         (рішення-на-основі-огляду-перекладу-й-поради
           proposal (отримати-рішення-за-порадою module-name payload)))
        ((тотожне? kind (як-є batch))
         (рішення-на-основі-огляду-перекладу-й-поради
           proposal (узагальнене-рішення-за-всіма-порадами module-name payload)))
        (так
         (створити-переклад-перевірка
           (як-є rejected) (як-є invalid-kind) proposal kind))))
     (переклад-вид proposal)
     (переклад-вміст proposal))))

; `translation-review` is pure with respect to knowledge state. Even a review
; classified as accepted has NOT written anything. Admission remains an
; explicit later call to `advise` or `advise-all` by the Lisp/embedding layer.
(визначити переклад-перевірка
  (функція (module-name proposal)
    (за-умовою
      ((тотожне? (символ? module-name) (як-є ()))
       (створити-переклад-перевірка
         (як-є rejected) (як-є invalid-module) proposal module-name))
      ((тотожне? (структура-обгортки-перекладу-коректна? proposal) (як-є ()))
       (створити-переклад-перевірка
         (як-є rejected) (як-є invalid-translation) proposal proposal))
      ((тотожне? (переклад-стан proposal) (як-є candidate))
       (отримати-кандидата-на-огляд-перекладу module-name proposal))
      ((тотожне? (переклад-стан proposal) (як-є ambiguous))
       (за-умовою
         ((опис-неоднозначності-перекладу-коректний?
            (переклад-вид proposal) (переклад-вміст proposal))
          (створити-переклад-перевірка
            (як-є ambiguous) (як-є translator-ambiguous)
            proposal (переклад-вміст proposal)))
         (так
          (створити-переклад-перевірка
            (як-є rejected) (як-є invalid-ambiguity)
            proposal (переклад-вміст proposal)))))
      ((тотожне? (переклад-стан proposal) (як-є rejected))
       (за-умовою
         ((символ? (переклад-вміст proposal))
          (створити-переклад-перевірка
            (як-є rejected) (як-є translator-rejected)
            proposal (переклад-вміст proposal)))
         (так
          (створити-переклад-перевірка
            (як-є rejected) (як-є invalid-rejection)
            proposal (переклад-вміст proposal)))))
      (так
       (створити-переклад-перевірка
         (як-є rejected) (як-є invalid-translation) proposal proposal)))))

; Only accepted knowledge candidates expose an admission payload. Queries are
; accepted questions, not knowledge writes. Rejected/ambiguous reviews cannot
; accidentally be fed to advise through this helper.
(визначити переклад-допустимий?
  (функція (review)
    (за-умовою
      ((тотожне? (запис-огляду-перекладу-коректний? review) (як-є ())) (як-є ()))
      ((тотожне? (переклад-перевірка-стан review) (як-є accepted))
       ((функція (proposal)
          (за-умовою
            ((тотожне? (структура-обгортки-перекладу-коректна? proposal) (як-є ())) (як-є ()))
            ((тотожне? (переклад-стан proposal) (як-є candidate))
             (за-умовою
               ((тотожне? (переклад-вид proposal) (як-є clause)) так)
               ((тотожне? (переклад-вид proposal) (як-є batch)) так)
               (так (як-є ()))))
            (так (як-є ()))))
        (переклад-перевірка-пропозиція review)))
      (так (як-є ())))))

(визначити переклад-допуск-вміст
  (функція (review)
    (за-умовою
      ((переклад-допустимий? review)
       (переклад-вміст (переклад-перевірка-пропозиція review)))
      (так (як-є ())))))

; Rejected and ambiguous translations are observations, not knowledge.
(визначити переклад-доказ-вартий?
  (функція (review)
    (за-умовою
      ((тотожне? (запис-огляду-перекладу-коректний? review) (як-є ())) (як-є ()))
      ((тотожне? (переклад-перевірка-стан review) (як-є rejected)) так)
      ((тотожне? (переклад-перевірка-стан review) (як-є ambiguous)) так)
      (так (як-є ())))))

(визначити переклад-доказ-запис
  (функція (review)
    (список *translation-evidence-schema* review)))

(визначити переклад-доказ-наступний
  (функція (review journal)
    (за-умовою
      ((переклад-доказ-вартий? review)
       (сполучити (переклад-доказ-запис review) journal))
      (так journal))))

(визначити переклад-перевірка-з-доказ
  (функція (module-name proposal journal)
    ((функція (review)
       (список review (переклад-доказ-наступний review journal)))
     (переклад-перевірка module-name proposal))))

; Повні українські назви — первинні визначення за точними проєкціями D9/D10.
; Англійські назви нижче лише посилаються на ті самі Lisp-замикання.
; Це не робить координати доменів самостійними викличними головами.
(визначити translation-status переклад-стан)
(визначити translation-kind переклад-вид)
(визначити translation-source переклад-джерело)
(визначити translation-payload переклад-вміст)
(визначити translation-status-valid? статус-запису-перекладу-коректний?)
(визначити translation-kind-valid? вид-кандидата-перекладу-коректний?)
(визначити translation-envelope-valid? структура-обгортки-перекладу-коректна?)
(визначити translation-batch-valid? пакет-кандидатів-перекладу-коректний?)
(визначити translation-candidate-payload-valid? вміст-кандидата-перекладу-коректний?)
(визначити translation-alternatives-valid? альтернативні-варіанти-перекладу-коректні?)
(визначити translation-ambiguity-valid? опис-неоднозначності-перекладу-коректний?)
(визначити make-translation-review створити-переклад-перевірка)
(визначити translation-review-status переклад-перевірка-стан)
(визначити translation-review-code переклад-перевірка-код)
(визначити translation-review-proposal переклад-перевірка-пропозиція)
(визначити translation-review-detail переклад-перевірка-деталь)
(визначити translation-review-status-valid? статус-огляду-кандидата-перекладу-коректний?)
(визначити translation-review-valid? запис-огляду-перекладу-коректний?)
(визначити translation-review-advice-decision рішення-на-основі-огляду-перекладу-й-поради)
(визначити translation-review-candidate отримати-кандидата-на-огляд-перекладу)
(визначити translation-review переклад-перевірка)
(визначити translation-admittable? переклад-допустимий?)
(визначити translation-admission-payload переклад-допуск-вміст)
(визначити translation-evidence-worthy? переклад-доказ-вартий?)
(визначити translation-evidence-entry переклад-доказ-запис)
(визначити translation-evidence-next переклад-доказ-наступний)
(визначити translation-review-with-evidence переклад-перевірка-з-доказ)
