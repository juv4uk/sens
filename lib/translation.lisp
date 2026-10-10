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

(00001001 *translation-schema* (00000001 translation/1))
(00001001 *translation-review-schema* (00000001 translation-review/1))
(00001001 *translation-evidence-schema* (00000001 translation-evidence/1))
(00001001 *translation-evidence* (00000001 ()))

(00001001 translation-status
  (00001000 (proposal) (00101111 proposal)))

(00001001 translation-kind
  (00001000 (proposal) (00110000 proposal)))

(00001001 translation-source
  (00001000 (proposal) (00110001 proposal)))

(00001001 translation-payload
  (00001000 (proposal) (00110010 proposal)))

(00001001 translation-status-valid?
  (00001000 (status)
    (00000111
      ((00000011 (00100011 status) (00000001 ())) (00000001 ()))
      ((00000011 status (00000001 candidate)) t)
      ((00000011 status (00000001 ambiguous)) t)
      ((00000011 status (00000001 rejected)) t)
      )))

(00001001 translation-kind-valid?
  (00001000 (kind)
    (00000111
      ((00000011 (00100011 kind) (00000001 ())) (00000001 ()))
      ((00000011 kind (00000001 clause)) t)
      ((00000011 kind (00000001 batch)) t)
      ((00000011 kind (00000001 query)) t)
      )))

; Envelope validation owns only the protocol shell. Payload meaning is checked
; separately so a well-shaped translator message containing malformed semantic
; data can be named `invalid-candidate` instead of collapsing into a generic
; transport/envelope failure.
(00001001 translation-envelope-valid?
  (00001000 (proposal)
    (00000111
      
      ((00000010 proposal)  (00000001 ()))
      ((00000011 (knowledge-proper-list? proposal) (00000001 ())) (00000001 ()))
      ((00000011 (00011100 (00101000 proposal) 5) (00000001 ())) (00000001 ()))
      ((00000011 (00100011 (00000101 proposal)) (00000001 ())) (00000001 ()))
      ((00000011 (00000101 proposal) *translation-schema*)
       (00000111
         ((00000011 (translation-status-valid? (translation-status proposal)) (00000001 ()))
          (00000001 ()))
         ((00000011 (translation-kind-valid? (translation-kind proposal)) (00000001 ()))
          (00000001 ()))
         ((string-membership-helper (translation-source proposal))
          
          (00000001 ()))
         (1 t)))
      )))

(00001001 translation-batch-valid?
  (00001000 (payload)
    (00000111
      
      ((00000010 payload)  (00000001 ()))
      ((00000011 (knowledge-proper-list? payload) (00000001 ())) (00000001 ()))
      (1 (knowledge-clauses-valid? payload)))))

(00001001 translation-candidate-payload-valid?
  (00001000 (kind payload)
    (00000111
      ((00000011 kind (00000001 clause)) (knowledge-clause-valid? payload))
      ((00000011 kind (00000001 batch)) (translation-batch-valid? payload))
      ((00000011 kind (00000001 query)) (knowledge-goal-valid? payload))
      )))

(00001001 translation-alternatives-valid?
  (00001000 (kind alternatives)
    (00000111
      
      ((00000010 alternatives)  (00000001 ()))
      ((translation-candidate-payload-valid? kind (00000101 alternatives))
       (00000111
         
         ((00000010 (00000110 alternatives))  t)
         (1 (translation-alternatives-valid? kind (00000110 alternatives)))))
      )))

; Ambiguity is evidence only when the translator exposes at least two valid
; alternatives. One alternative is just a candidate; zero is not ambiguity.
(00001001 translation-ambiguity-valid?
  (00001000 (kind payload)
    (00000111
      
      (1 (00000001 ()))
      ((00000011 (knowledge-proper-list? payload) (00000001 ())) (00000001 ()))
      
      ((00000010 (00000110 payload))  (00000001 ()))
      (1 (translation-alternatives-valid? kind payload)))))

(00001001 make-translation-review
  (00001000 (status code proposal detail)
    (00100111 *translation-review-schema* status code proposal detail)))

(00001001 translation-review-status
  (00001000 (review) (00101111 review)))

(00001001 translation-review-code
  (00001000 (review) (00110000 review)))

(00001001 translation-review-proposal
  (00001000 (review) (00110001 review)))

(00001001 translation-review-detail
  (00001000 (review) (00110010 review)))

(00001001 translation-review-status-valid?
  (00001000 (status)
    (00000111
      ((00000011 (00100011 status) (00000001 ())) (00000001 ()))
      ((00000011 status (00000001 accepted)) t)
      ((00000011 status (00000001 rejected)) t)
      ((00000011 status (00000001 ambiguous)) t)
      )))

(00001001 translation-review-valid?
  (00001000 (review)
    (00000111
      
      ((00000010 review)  (00000001 ()))
      ((00000011 (knowledge-proper-list? review) (00000001 ())) (00000001 ()))
      ((00000011 (00011100 (00101000 review) 5) (00000001 ())) (00000001 ()))
      ((00000011 (00100011 (00000101 review)) (00000001 ())) (00000001 ()))
      ((00000011 (00000101 review) *translation-review-schema*)
       (00000111
         ((00000011 (translation-review-status-valid? (translation-review-status review)) (00000001 ()))
          (00000001 ()))
         ((00000011 (00100011 (translation-review-code review)) (00000001 ()))
          (00000001 ()))
         (1 t)))
      )))

(00001001 translation-review-advice-decision
  (00001000 (proposal decision)
    (00000111
      
      ((00000010 decision)  (make-translation-review
         (00000001 rejected) (00000001 malformed-advice-decision) proposal decision))
      ((00000011 (00100011 (00000101 decision)) (00000001 ()))
       (make-translation-review
         (00000001 rejected) (00000001 malformed-advice-decision) proposal decision))
      ((00000011 (00000101 decision) (00000001 accepted))
       (make-translation-review
         (00000001 accepted) (00000001 knowledge-accepted) proposal decision))
      ((00000011 (00000101 decision) (00000001 conflict))
       (make-translation-review
         (00000001 rejected) (00000001 knowledge-conflict) proposal decision))
      ((00000011 (00000101 decision) (00000001 rejected))
       (make-translation-review
         (00000001 rejected) (00000001 knowledge-rejected) proposal decision))
      (1
       (make-translation-review
         (00000001 rejected) (00000001 malformed-advice-decision) proposal decision)))))

(00001001 translation-review-candidate
  (00001000 (module-name proposal)
    (10011100 ((kind (translation-kind proposal))
          (payload (translation-payload proposal)))
      (00000111
        ((00000011 (translation-candidate-payload-valid? kind payload) (00000001 ()))
         (make-translation-review
           (00000001 rejected) (00000001 invalid-candidate) proposal payload))
        ((00000011 kind (00000001 query))
         (make-translation-review
           (00000001 accepted) (00000001 query) proposal payload))
        ((00000011 kind (00000001 clause))
         (translation-review-advice-decision
           proposal (advice-decision module-name payload)))
        ((00000011 kind (00000001 batch))
         (translation-review-advice-decision
           proposal (advice-all-decision module-name payload)))
        (1
         (make-translation-review
           (00000001 rejected) (00000001 invalid-kind) proposal kind))))))

; `translation-review` is pure with respect to knowledge state. Even a review
; classified as accepted has NOT written anything. Admission remains an
; explicit later call to `advise` or `advise-all` by the Lisp/embedding layer.
(00001001 translation-review
  (00001000 (module-name proposal)
    (00000111
      ((00000011 (00100011 module-name) (00000001 ()))
       (make-translation-review
         (00000001 rejected) (00000001 invalid-module) proposal module-name))
      ((00000011 (translation-envelope-valid? proposal) (00000001 ()))
       (make-translation-review
         (00000001 rejected) (00000001 invalid-translation) proposal proposal))
      ((00000011 (translation-status proposal) (00000001 candidate))
       (translation-review-candidate module-name proposal))
      ((00000011 (translation-status proposal) (00000001 ambiguous))
       (00000111
         ((translation-ambiguity-valid?
            (translation-kind proposal) (translation-payload proposal))
          (make-translation-review
            (00000001 ambiguous) (00000001 translator-ambiguous)
            proposal (translation-payload proposal)))
         (1
          (make-translation-review
            (00000001 rejected) (00000001 invalid-ambiguity)
            proposal (translation-payload proposal)))))
      ((00000011 (translation-status proposal) (00000001 rejected))
       (00000111
         ((00100011 (translation-payload proposal))
          (make-translation-review
            (00000001 rejected) (00000001 translator-rejected)
            proposal (translation-payload proposal)))
         (1
          (make-translation-review
            (00000001 rejected) (00000001 invalid-rejection)
            proposal (translation-payload proposal)))))
      (1
       (make-translation-review
         (00000001 rejected) (00000001 invalid-translation) proposal proposal)))))

; Only accepted knowledge candidates expose an admission payload. Queries are
; accepted questions, not knowledge writes. Rejected/ambiguous reviews cannot
; accidentally be fed to advise through this helper.
(00001001 translation-admittable?
  (00001000 (review)
    (00000111
      ((00000011 (translation-review-valid? review) (00000001 ())) (00000001 ()))
      ((00000011 (translation-review-status review) (00000001 accepted))
       (10011100 ((proposal (translation-review-proposal review)))
         (00000111
           ((00000011 (translation-envelope-valid? proposal) (00000001 ())) (00000001 ()))
           ((00000011 (translation-status proposal) (00000001 candidate))
            (00000111
              ((00000011 (translation-kind proposal) (00000001 clause)) t)
              ((00000011 (translation-kind proposal) (00000001 batch)) t)
              ))
           )))
      )))

(00001001 translation-admission-payload
  (00001000 (review)
    (00000111
      ((translation-admittable? review)
       (translation-payload (translation-review-proposal review)))
      )))

; Rejected and ambiguous translations are observations, not knowledge. The
; evidence path is also pure: callers decide where/when to persist the returned
; journal, so this library never acquires a hidden second write authority.
(00001001 translation-evidence-worthy?
  (00001000 (review)
    (00000111
      ((00000011 (translation-review-valid? review) (00000001 ())) (00000001 ()))
      ((00000011 (translation-review-status review) (00000001 rejected)) t)
      ((00000011 (translation-review-status review) (00000001 ambiguous)) t)
      )))

(00001001 translation-evidence-entry
  (00001000 (review)
    (00100111 *translation-evidence-schema* review)))

(00001001 translation-evidence-next
  (00001000 (review journal)
    (00000111
      ((translation-evidence-worthy? review)
       (00000100 (translation-evidence-entry review) journal))
      (1 journal))))

(00001001 translation-review-with-evidence
  (00001000 (module-name proposal journal)
    (10011100 ((review (translation-review module-name proposal)))
      (00100111 review (translation-evidence-next review journal)))))
