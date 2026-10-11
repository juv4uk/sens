; External translation boundary for Advice Taker.
;
; The translator is deliberately NOT a semantic authority. It may emit only
; finite Lisp data in the versioned shape below. Lisp validates that data,
; asks the existing advice boundary whether proposed knowledge is admissible,
; and classifies the review. Nothing in this file writes *knowledge-journal*.
;
; Canonical proposal shape:
;
;   (translation/1 STATUS KIND SOURCE PAYLOAD)
;
; STATUS:
;   candidate  - translator proposes one semantic candidate;
;   ambiguous  - translator exposes two or more alternatives instead of
;                guessing which one is meant;
;   rejected   - translator states that it could not produce a candidate.
;
; KIND:
;   clause | batch | query
;
; SOURCE is the original text as a string. PAYLOAD is Lisp data. Candidate
; clause/batch data is checked with knowledge.lisp's existing validators and
; then with advice-decision/advice-all-decision. Candidate query data is
; checked with knowledge-goal-valid?. Ambiguous/rejected proposals are never
; knowledge.
;
; Review shape:
;
;   (translation-review/1 STATUS CODE PROPOSAL DETAIL)
;
; Review STATUS is accepted | rejected | ambiguous. This vocabulary describes
; translation admission only; it is separate from Advice Taker's
; proved/unknown/partial/blocked/disputed/invalid reasoning outcomes.

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
      ((101 status (001 candidate)) t)
      ((101 status (001 ambiguous)) t)
      ((101 status (001 rejected)) t)
      )))

(0011 translation-kind-valid?
  (0010 (kind)
    (110
      ((101 (110101100 kind) (001 ())) (001 ()))
      ((101 kind (001 clause)) t)
      ((101 kind (001 batch)) t)
      ((101 kind (001 query)) t)
      )))

; Envelope validation owns only the protocol shell. Payload meaning is checked
; separately so a well-shaped translator message containing malformed semantic
; data can be named `invalid-candidate` instead of collapsing into a generic
; transport/envelope failure.
(0011 translation-envelope-valid?
  (0010 (proposal)
    (110
      
      ((010 proposal)  (001 ()))
      ((101 (knowledge-proper-list? proposal) (001 ())) (001 ()))
      ((101 (11110111 (000000 proposal) 5) (001 ())) (001 ()))
      ((101 (110101100 (100 proposal)) (001 ())) (001 ()))
      ((101 (100 proposal) *translation-schema*)
       (110
         ((101 (translation-status-valid? (translation-status proposal)) (001 ()))
          (001 ()))
         ((101 (translation-kind-valid? (translation-kind proposal)) (001 ()))
          (001 ()))
         ((string-membership-helper (translation-source proposal))
          
          (001 ()))
         ((010 ()) t)))
      )))

(0011 translation-batch-valid?
  (0010 (payload)
    (110
      
      ((010 payload)  (001 ()))
      ((101 (knowledge-proper-list? payload) (001 ())) (001 ()))
      ((010 ()) (knowledge-clauses-valid? payload)))))

(0011 translation-candidate-payload-valid?
  (0010 (kind payload)
    (110
      ((101 kind (001 clause)) (knowledge-clause-valid? payload))
      ((101 kind (001 batch)) (translation-batch-valid? payload))
      ((101 kind (001 query)) (knowledge-goal-valid? payload))
      )))

(0011 translation-alternatives-valid?
  (0010 (kind alternatives)
    (110
      
      ((010 alternatives)  (001 ()))
      ((translation-candidate-payload-valid? kind (100 alternatives))
       (110
         
         ((010 (011 alternatives))  t)
         ((010 ()) (translation-alternatives-valid? kind (011 alternatives)))))
      )))

; Ambiguity is evidence only when the translator exposes at least two valid
; alternatives. One alternative is just a candidate; zero is not ambiguity.
(0011 translation-ambiguity-valid?
  (0010 (kind payload)
    (110
      
      ((010 ()) (001 ()))
      ((101 (knowledge-proper-list? payload) (001 ())) (001 ()))
      
      ((010 (011 payload))  (001 ()))
      ((010 ()) (translation-alternatives-valid? kind payload)))))

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
      ((101 status (001 accepted)) t)
      ((101 status (001 rejected)) t)
      ((101 status (001 ambiguous)) t)
      )))

(0011 translation-review-valid?
  (0010 (review)
    (110
      
      ((010 review)  (001 ()))
      ((101 (knowledge-proper-list? review) (001 ())) (001 ()))
      ((101 (11110111 (000000 review) 5) (001 ())) (001 ()))
      ((101 (110101100 (100 review)) (001 ())) (001 ()))
      ((101 (100 review) *translation-review-schema*)
       (110
         ((101 (translation-review-status-valid? (translation-review-status review)) (001 ()))
          (001 ()))
         ((101 (110101100 (translation-review-code review)) (001 ()))
          (001 ()))
         ((010 ()) t)))
      )))

(0011 translation-review-advice-decision
  (0010 (proposal decision)
    (110
      
      ((010 decision)  (make-translation-review
         (001 rejected) (001 malformed-advice-decision) proposal decision))
      ((101 (110101100 (100 decision)) (001 ()))
       (make-translation-review
         (001 rejected) (001 malformed-advice-decision) proposal decision))
      ((101 (100 decision) (001 accepted))
       (make-translation-review
         (001 accepted) (001 knowledge-accepted) proposal decision))
      ((101 (100 decision) (001 conflict))
       (make-translation-review
         (001 rejected) (001 knowledge-conflict) proposal decision))
      ((101 (100 decision) (001 rejected))
       (make-translation-review
         (001 rejected) (001 knowledge-rejected) proposal decision))
      ((010 ())
       (make-translation-review
         (001 rejected) (001 malformed-advice-decision) proposal decision)))))

(0011 translation-review-candidate
  (0010 (module-name proposal)
    (001000 ((kind (translation-kind proposal))
          (payload (translation-payload proposal)))
      (110
        ((101 (translation-candidate-payload-valid? kind payload) (001 ()))
         (make-translation-review
           (001 rejected) (001 invalid-candidate) proposal payload))
        ((101 kind (001 query))
         (make-translation-review
           (001 accepted) (001 query) proposal payload))
        ((101 kind (001 clause))
         (translation-review-advice-decision
           proposal (advice-decision module-name payload)))
        ((101 kind (001 batch))
         (translation-review-advice-decision
           proposal (advice-all-decision module-name payload)))
        ((010 ())
         (make-translation-review
           (001 rejected) (001 invalid-kind) proposal kind))))))

; `translation-review` is pure with respect to knowledge state. Even a review
; classified as accepted has NOT written anything. Admission remains an
; explicit later call to `advise` or `advise-all` by the Lisp/embedding layer.
(0011 translation-review
  (0010 (module-name proposal)
    (110
      ((101 (110101100 module-name) (001 ()))
       (make-translation-review
         (001 rejected) (001 invalid-module) proposal module-name))
      ((101 (translation-envelope-valid? proposal) (001 ()))
       (make-translation-review
         (001 rejected) (001 invalid-translation) proposal proposal))
      ((101 (translation-status proposal) (001 candidate))
       (translation-review-candidate module-name proposal))
      ((101 (translation-status proposal) (001 ambiguous))
       (110
         ((translation-ambiguity-valid?
            (translation-kind proposal) (translation-payload proposal))
          (make-translation-review
            (001 ambiguous) (001 translator-ambiguous)
            proposal (translation-payload proposal)))
         ((010 ())
          (make-translation-review
            (001 rejected) (001 invalid-ambiguity)
            proposal (translation-payload proposal)))))
      ((101 (translation-status proposal) (001 rejected))
       (110
         ((110101100 (translation-payload proposal))
          (make-translation-review
            (001 rejected) (001 translator-rejected)
            proposal (translation-payload proposal)))
         ((010 ())
          (make-translation-review
            (001 rejected) (001 invalid-rejection)
            proposal (translation-payload proposal)))))
      ((010 ())
       (make-translation-review
         (001 rejected) (001 invalid-translation) proposal proposal)))))

; Only accepted knowledge candidates expose an admission payload. Queries are
; accepted questions, not knowledge writes. Rejected/ambiguous reviews cannot
; accidentally be fed to advise through this helper.
(0011 translation-admittable?
  (0010 (review)
    (110
      ((101 (translation-review-valid? review) (001 ())) (001 ()))
      ((101 (translation-review-status review) (001 accepted))
       (001000 ((proposal (translation-review-proposal review)))
         (110
           ((101 (translation-envelope-valid? proposal) (001 ())) (001 ()))
           ((101 (translation-status proposal) (001 candidate))
            (110
              ((101 (translation-kind proposal) (001 clause)) t)
              ((101 (translation-kind proposal) (001 batch)) t)
              ))
           )))
      )))

(0011 translation-admission-payload
  (0010 (review)
    (110
      ((translation-admittable? review)
       (translation-payload (translation-review-proposal review)))
      )))

; Rejected and ambiguous translations are observations, not knowledge. The
; evidence path is also pure: callers decide where/when to persist the returned
; journal, so this library never acquires a hidden second write authority.
(0011 translation-evidence-worthy?
  (0010 (review)
    (110
      ((101 (translation-review-valid? review) (001 ())) (001 ()))
      ((101 (translation-review-status review) (001 rejected)) t)
      ((101 (translation-review-status review) (001 ambiguous)) t)
      )))

(0011 translation-evidence-entry
  (0010 (review)
    (1110 *translation-evidence-schema* review)))

(0011 translation-evidence-next
  (0010 (review journal)
    (110
      ((translation-evidence-worthy? review)
       (111 (translation-evidence-entry review) journal))
      ((010 ()) journal))))

(0011 translation-review-with-evidence
  (0010 (module-name proposal journal)
    (001000 ((review (translation-review module-name proposal)))
      (1110 review (translation-evidence-next review journal)))))
