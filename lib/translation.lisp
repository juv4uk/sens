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

(0011 *translation-schema* (001 translation/1))
(0011 *translation-review-schema* (001 translation-review/1))
(0011 *translation-evidence-schema* (001 translation-evidence/1))
(0011 *translation-evidence* (001 ()))

(0011 translation-status
  (0010 (proposal) (1001 proposal)))

(0011 translation-kind
  (0010 (proposal) (10011 proposal)))

(0011 translation-source
  (0010 (proposal) (100111 proposal)))

(0011 translation-payload
  (0010 (proposal) (110110101 proposal)))

(0011 translation-status-valid?
  (0010 (status)
    (110
      ((101 (110101100 status) (001 ())) (001 ()))
      ((101 status (001 candidate)) #d1:1)
      ((101 status (001 ambiguous)) #d1:1)
      ((101 status (001 rejected)) #d1:1)
      (#d1:1 (001 ())))))

(0011 translation-kind-valid?
  (0010 (kind)
    (110
      ((101 (110101100 kind) (001 ())) (001 ()))
      ((101 kind (001 clause)) #d1:1)
      ((101 kind (001 batch)) #d1:1)
      ((101 kind (001 query)) #d1:1)
      (#d1:1 (001 ())))))

; Envelope validation owns only the protocol shell. Payload meaning is checked
; separately so a well-shaped translator message containing malformed semantic
; data can be named `invalid-candidate` instead of collapsing into a generic
; transport/envelope failure.
(0011 translation-envelope-valid?
  (0010 (proposal)
    (110
      ((010 proposal) (001 ()))
      ((101 (правильно-структурований-список-знань? proposal) (001 ())) (001 ()))
      ((101 (101 (000000 proposal) 5) (001 ())) (001 ()))
      ((101 (110101100 (100 proposal)) (001 ())) (001 ()))
      ((101 (100 proposal) *translation-schema*)
       (110
         ((101 (статус-запису-перекладу-коректний? (переклад-стан proposal)) (001 ()))
          (001 ()))
         ((101 (вид-кандидата-перекладу-коректний? (переклад-вид proposal)) (001 ()))
          (001 ()))
         ((string-membership-helper (переклад-джерело proposal))
          (001 ()))
         (#d1:1 #d1:1)))
      (#d1:1 (001 ())))))

(0011 translation-batch-valid?
  (0010 (payload)
    (110
      ((010 payload) (001 ()))
      ((101 (правильно-структурований-список-знань? payload) (001 ())) (001 ()))
      (#d1:1 (клаузи-бази-знань-коректні? payload)))))

(0011 translation-candidate-payload-valid?
  (0010 (kind payload)
    (110
      ((101 kind (001 clause)) (клауза-бази-знань-коректна? payload))
      ((101 kind (001 batch)) (пакет-кандидатів-перекладу-коректний? payload))
      ((101 kind (001 query)) (ціль-бази-знань-коректна? payload))
      (#d1:1 (001 ())))))

(0011 translation-alternatives-valid?
  (0010 (kind alternatives)
    (110
      ((010 alternatives) (001 ()))
      ((вміст-кандидата-перекладу-коректний? kind (100 alternatives))
       (110
         ((010 (011 alternatives)) #d1:1)
         (#d1:1 (альтернативні-варіанти-перекладу-коректні? kind (011 alternatives)))))
      (#d1:1 (001 ())))))

; Ambiguity is evidence only when the translator exposes at least two valid
; alternatives. One alternative is just a candidate; zero is not ambiguity.
(0011 translation-ambiguity-valid?
  (0010 (kind payload)
    (110
      ((101 (правильно-структурований-список-знань? payload) (001 ())) (001 ()))
      ((010 (011 payload)) (001 ()))
      (#d1:1 (альтернативні-варіанти-перекладу-коректні? kind payload)))))

(0011 make-translation-review
  (0010 (status code proposal detail)
    (1110 *translation-review-schema* status code proposal detail)))

(0011 translation-review-status
  (0010 (review) (1001 review)))

(0011 translation-review-code
  (0010 (review) (10011 review)))

(0011 translation-review-proposal
  (0010 (review) (100111 review)))

(0011 translation-review-detail
  (0010 (review) (110110101 review)))

(0011 translation-review-status-valid?
  (0010 (status)
    (110
      ((101 (110101100 status) (001 ())) (001 ()))
      ((101 status (001 accepted)) #d1:1)
      ((101 status (001 rejected)) #d1:1)
      ((101 status (001 ambiguous)) #d1:1)
      (#d1:1 (001 ())))))

(0011 translation-review-valid?
  (0010 (review)
    (110
      ((010 review) (001 ()))
      ((101 (правильно-структурований-список-знань? review) (001 ())) (001 ()))
      ((101 (101 (000000 review) 5) (001 ())) (001 ()))
      ((101 (110101100 (100 review)) (001 ())) (001 ()))
      ((101 (100 review) *translation-review-schema*)
       (110
         ((101 (статус-огляду-кандидата-перекладу-коректний? (переклад-перевірка-стан review)) (001 ()))
          (001 ()))
         ((101 (110101100 (переклад-перевірка-код review)) (001 ()))
          (001 ()))
         (#d1:1 #d1:1)))
      (#d1:1 (001 ())))))

(0011 translation-review-advice-decision
  (0010 (proposal decision)
    (110
      ((010 decision)
       (створити-переклад-перевірка
         (001 rejected) (001 malformed-advice-decision) proposal decision))
      ((101 (110101100 (100 decision)) (001 ()))
       (створити-переклад-перевірка
         (001 rejected) (001 malformed-advice-decision) proposal decision))
      ((101 (100 decision) (001 accepted))
       (створити-переклад-перевірка
         (001 accepted) (001 knowledge-accepted) proposal decision))
      ((101 (100 decision) (001 conflict))
       (створити-переклад-перевірка
         (001 rejected) (001 knowledge-conflict) proposal decision))
      ((101 (100 decision) (001 rejected))
       (створити-переклад-перевірка
         (001 rejected) (001 knowledge-rejected) proposal decision))
      (#d1:1
       (створити-переклад-перевірка
         (001 rejected) (001 malformed-advice-decision) proposal decision)))))

(0011 translation-review-candidate
  (0010 (module-name proposal)
    ((0010 (kind payload)
      (110
        ((101 (вміст-кандидата-перекладу-коректний? kind payload) (001 ()))
         (створити-переклад-перевірка
           (001 rejected) (001 invalid-candidate) proposal payload))
        ((101 kind (001 query))
         (створити-переклад-перевірка
           (001 accepted) (001 query) proposal payload))
        ((101 kind (001 clause))
         (рішення-на-основі-огляду-перекладу-й-поради
           proposal (отримати-рішення-за-порадою module-name payload)))
        ((101 kind (001 batch))
         (рішення-на-основі-огляду-перекладу-й-поради
           proposal (узагальнене-рішення-за-всіма-порадами module-name payload)))
        (#d1:1
         (створити-переклад-перевірка
           (001 rejected) (001 invalid-kind) proposal kind))))
     (переклад-вид proposal)
     (переклад-вміст proposal))))

; `translation-review` is pure with respect to knowledge state. Even a review
; classified as accepted has NOT written anything. Admission remains an
; explicit later call to `advise` or `advise-all` by the Lisp/embedding layer.
(0011 translation-review
  (0010 (module-name proposal)
    (110
      ((101 (110101100 module-name) (001 ()))
       (створити-переклад-перевірка
         (001 rejected) (001 invalid-module) proposal module-name))
      ((101 (структура-обгортки-перекладу-коректна? proposal) (001 ()))
       (створити-переклад-перевірка
         (001 rejected) (001 invalid-translation) proposal proposal))
      ((101 (переклад-стан proposal) (001 candidate))
       (отримати-кандидата-на-огляд-перекладу module-name proposal))
      ((101 (переклад-стан proposal) (001 ambiguous))
       (110
         ((опис-неоднозначності-перекладу-коректний?
            (переклад-вид proposal) (переклад-вміст proposal))
          (створити-переклад-перевірка
            (001 ambiguous) (001 translator-ambiguous)
            proposal (переклад-вміст proposal)))
         (#d1:1
          (створити-переклад-перевірка
            (001 rejected) (001 invalid-ambiguity)
            proposal (переклад-вміст proposal)))))
      ((101 (переклад-стан proposal) (001 rejected))
       (110
         ((110101100 (переклад-вміст proposal))
          (створити-переклад-перевірка
            (001 rejected) (001 translator-rejected)
            proposal (переклад-вміст proposal)))
         (#d1:1
          (створити-переклад-перевірка
            (001 rejected) (001 invalid-rejection)
            proposal (переклад-вміст proposal)))))
      (#d1:1
       (створити-переклад-перевірка
         (001 rejected) (001 invalid-translation) proposal proposal)))))

; Only accepted knowledge candidates expose an admission payload. Queries are
; accepted questions, not knowledge writes. Rejected/ambiguous reviews cannot
; accidentally be fed to advise through this helper.
(0011 translation-admittable?
  (0010 (review)
    (110
      ((101 (запис-огляду-перекладу-коректний? review) (001 ())) (001 ()))
      ((101 (переклад-перевірка-стан review) (001 accepted))
       ((0010 (proposal)
          (110
            ((101 (структура-обгортки-перекладу-коректна? proposal) (001 ())) (001 ()))
            ((101 (переклад-стан proposal) (001 candidate))
             (110
               ((101 (переклад-вид proposal) (001 clause)) #d1:1)
               ((101 (переклад-вид proposal) (001 batch)) #d1:1)
               (#d1:1 (001 ()))))
            (#d1:1 (001 ()))))
        (переклад-перевірка-пропозиція review)))
      (#d1:1 (001 ())))))

(0011 translation-admission-payload
  (0010 (review)
    (110
      ((переклад-допустимий? review)
       (переклад-вміст (переклад-перевірка-пропозиція review)))
      (#d1:1 (001 ())))))

; Rejected and ambiguous translations are observations, not knowledge.
(0011 translation-evidence-worthy?
  (0010 (review)
    (110
      ((101 (запис-огляду-перекладу-коректний? review) (001 ())) (001 ()))
      ((101 (переклад-перевірка-стан review) (001 rejected)) #d1:1)
      ((101 (переклад-перевірка-стан review) (001 ambiguous)) #d1:1)
      (#d1:1 (001 ())))))

(0011 translation-evidence-entry
  (0010 (review)
    (1110 *translation-evidence-schema* review)))

(0011 translation-evidence-next
  (0010 (review journal)
    (110
      ((переклад-доказ-вартий? review)
       (111 (переклад-доказ-запис review) journal))
      (#d1:1 journal))))

(0011 translation-review-with-evidence
  (0010 (module-name proposal journal)
    ((0010 (review)
       (1110 review (переклад-доказ-наступний review journal)))
     (переклад-перевірка module-name proposal))))

; Ukrainian D9 projections of the already-owned SENS translation laws.
; Identical closures and arity; no new domain codes or host review path.
; D9:000101000
(0011 переклад-перевірка translation-review)
; D9:000110111
(0011 переклад-допустимий? translation-admittable?)
; D9:000000010
(0011 переклад-допуск-вміст translation-admission-payload)
; D9:000010010
(0011 переклад-перевірка-з-доказ translation-review-with-evidence)
