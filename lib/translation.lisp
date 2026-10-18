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

(визначити translation-status
  (функція (proposal) (друге proposal)))

(визначити translation-kind
  (функція (proposal) (третє proposal)))

(визначити translation-source
  (функція (proposal) (четверте proposal)))

(визначити translation-payload
  (функція (proposal) (п'ятий proposal)))

(визначити translation-status-valid?
  (функція (status)
    (за-умовою
      ((тотожне? (символ? status) (як-є ())) (як-є ()))
      ((тотожне? status (як-є candidate)) так)
      ((тотожне? status (як-є ambiguous)) так)
      ((тотожне? status (як-є rejected)) так)
      (так (як-є ())))))

(визначити translation-kind-valid?
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
(визначити translation-envelope-valid?
  (функція (proposal)
    (за-умовою
      ((атом? proposal) (як-є ()))
      ((тотожне? (правильно-структурований-список-знань? proposal) (як-є ())) (як-є ()))
      ((101 (101 (000000 proposal) 5) (001 ())) (001 ()))
      ((101 (110101100 (100 proposal)) (001 ())) (001 ()))
      ((тотожне? (перше proposal) *translation-schema*)
       (за-умовою
         ((тотожне? (статус-запису-перекладу-коректний? (переклад-стан proposal)) (як-є ()))
          (як-є ()))
         ((тотожне? (вид-кандидата-перекладу-коректний? (переклад-вид proposal)) (як-є ()))
          (як-є ()))
         ((string-membership-helper (переклад-джерело proposal))
          (як-є ()))
         (#d1:1 #d1:1)))
      (#d1:1 (001 ())))))

(визначити translation-batch-valid?
  (функція (payload)
    (за-умовою
      ((атом? payload) (як-є ()))
      ((тотожне? (правильно-структурований-список-знань? payload) (як-є ())) (як-є ()))
      (так (клаузи-бази-знань-коректні? payload)))))

(визначити translation-candidate-payload-valid?
  (функція (kind payload)
    (за-умовою
      ((тотожне? kind (як-є clause)) (клауза-бази-знань-коректна? payload))
      ((тотожне? kind (як-є batch)) (пакет-кандидатів-перекладу-коректний? payload))
      ((тотожне? kind (як-є query)) (ціль-бази-знань-коректна? payload))
      (#d1:1 (001 ())))))

(визначити translation-alternatives-valid?
  (функція (kind alternatives)
    (за-умовою
      ((атом? alternatives) (як-є ()))
      ((вміст-кандидата-перекладу-коректний? kind (перше alternatives))
       (за-умовою
         ((010 (011 alternatives)) #d1:1)
         (так (альтернативні-варіанти-перекладу-коректні? kind (решта alternatives)))))
      (#d1:1 (001 ())))))

; Ambiguity is evidence only when the translator exposes at least two valid
; alternatives. One alternative is just a candidate; zero is not ambiguity.
(визначити translation-ambiguity-valid?
  (функція (kind payload)
    (за-умовою
      ((тотожне? (правильно-структурований-список-знань? payload) (як-є ())) (як-є ()))
      ((атом? (решта payload)) (як-є ()))
      (так (альтернативні-варіанти-перекладу-коректні? kind payload)))))

(визначити make-translation-review
  (функція (status code proposal detail)
    (список *translation-review-schema* status code proposal detail)))

(визначити translation-review-status
  (функція (review) (друге review)))

(визначити translation-review-code
  (функція (review) (третє review)))

(визначити translation-review-proposal
  (функція (review) (четверте review)))

(визначити translation-review-detail
  (функція (review) (п'ятий review)))

(визначити translation-review-status-valid?
  (функція (status)
    (за-умовою
      ((101 (110101100 status) (001 ())) (001 ()))
      ((101 status (001 accepted)) #d1:1)
      ((101 status (001 rejected)) #d1:1)
      ((101 status (001 ambiguous)) #d1:1)
      (#d1:1 (001 ())))))

(визначити translation-review-valid?
  (функція (review)
    (за-умовою
      ((атом? review) (як-є ()))
      ((тотожне? (правильно-структурований-список-знань? review) (як-є ())) (як-є ()))
      ((101 (101 (000000 review) 5) (001 ())) (001 ()))
      ((101 (110101100 (100 review)) (001 ())) (001 ()))
      ((тотожне? (перше review) *translation-review-schema*)
       (за-умовою
         ((тотожне? (статус-огляду-кандидата-перекладу-коректний? (переклад-перевірка-стан review)) (як-є ()))
          (як-є ()))
         ((тотожне? (символ? (переклад-перевірка-код review)) (як-є ()))
          (як-є ()))
         (#d1:1 #d1:1)))
      (#d1:1 (001 ())))))

(визначити translation-review-advice-decision
  (функція (proposal decision)
    (за-умовою
      ((атом? decision)
       (створити-переклад-перевірка
         (як-є rejected) (як-є malformed-advice-decision) proposal decision))
      ((101 (110101100 (100 decision)) (001 ()))
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
      (#d1:1
       (створити-переклад-перевірка
         (як-є rejected) (як-є malformed-advice-decision) proposal decision)))))

(визначити translation-review-candidate
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
        (#d1:1
         (створити-переклад-перевірка
           (як-є rejected) (як-є invalid-kind) proposal kind))))
     (переклад-вид proposal)
     (переклад-вміст proposal))))

; `translation-review` is pure with respect to knowledge state. Even a review
; classified as accepted has NOT written anything. Admission remains an
; explicit later call to `advise` or `advise-all` by the Lisp/embedding layer.
(визначити translation-review
  (функція (module-name proposal)
    (за-умовою
      ((101 (110101100 module-name) (001 ()))
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
         (#d1:1
          (створити-переклад-перевірка
            (як-є rejected) (як-є invalid-ambiguity)
            proposal (переклад-вміст proposal)))))
      ((тотожне? (переклад-стан proposal) (як-є rejected))
       (за-умовою
         ((символ? (переклад-вміст proposal))
          (створити-переклад-перевірка
            (як-є rejected) (як-є translator-rejected)
            proposal (переклад-вміст proposal)))
         (#d1:1
          (створити-переклад-перевірка
            (як-є rejected) (як-є invalid-rejection)
            proposal (переклад-вміст proposal)))))
      (#d1:1
       (створити-переклад-перевірка
         (як-є rejected) (як-є invalid-translation) proposal proposal)))))

; Only accepted knowledge candidates expose an admission payload. Queries are
; accepted questions, not knowledge writes. Rejected/ambiguous reviews cannot
; accidentally be fed to advise through this helper.
(визначити translation-admittable?
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
               (#d1:1 (001 ()))))
            (#d1:1 (001 ()))))
        (переклад-перевірка-пропозиція review)))
      (#d1:1 (001 ())))))

(визначити translation-admission-payload
  (функція (review)
    (за-умовою
      ((переклад-допустимий? review)
       (переклад-вміст (переклад-перевірка-пропозиція review)))
      (#d1:1 (001 ())))))

; Rejected and ambiguous translations are observations, not knowledge.
(визначити translation-evidence-worthy?
  (функція (review)
    (за-умовою
      ((тотожне? (запис-огляду-перекладу-коректний? review) (як-є ())) (як-є ()))
      ((тотожне? (переклад-перевірка-стан review) (як-є rejected)) так)
      ((тотожне? (переклад-перевірка-стан review) (як-є ambiguous)) так)
      (#d1:1 (001 ())))))

(визначити translation-evidence-entry
  (функція (review)
    (список *translation-evidence-schema* review)))

(визначити translation-evidence-next
  (функція (review journal)
    (за-умовою
      ((переклад-доказ-вартий? review)
       (сполучити (переклад-доказ-запис review) journal))
      (#d1:1 journal))))

(визначити translation-review-with-evidence
  (функція (module-name proposal journal)
    ((функція (review)
       (список review (переклад-доказ-наступний review journal)))
     (переклад-перевірка module-name proposal))))

; Ukrainian D9 projections of the already-owned SENS translation laws.
; Identical closures and arity; no new domain codes or host review path.
; D9:000101000
(визначити переклад-перевірка translation-review)
; D9:000110111
(визначити переклад-допустимий? translation-admittable?)
; D9:000000010
(визначити переклад-допуск-вміст translation-admission-payload)
; D9:000010010
(визначити переклад-перевірка-з-доказ translation-review-with-evidence)
