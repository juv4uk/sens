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

(def *translation-schema* (quote translation/1))
(def *translation-review-schema* (quote translation-review/1))
(def *translation-evidence-schema* (quote translation-evidence/1))
(def *translation-evidence* (quote ()))

(def translation-status
  (lambda (proposal) (second proposal)))

(def translation-kind
  (lambda (proposal) (third proposal)))

(def translation-source
  (lambda (proposal) (fourth proposal)))

(def translation-payload
  (lambda (proposal) (fifth proposal)))

(def translation-status-valid?
  (lambda (status)
    (cond
      ((eq? (symbol? status) (quote ())) (quote ()))
      ((eq? status (quote candidate)) t)
      ((eq? status (quote ambiguous)) t)
      ((eq? status (quote rejected)) t)
      (t (quote ())))))

(def translation-kind-valid?
  (lambda (kind)
    (cond
      ((eq? (symbol? kind) (quote ())) (quote ()))
      ((eq? kind (quote clause)) t)
      ((eq? kind (quote batch)) t)
      ((eq? kind (quote query)) t)
      (t (quote ())))))

; Envelope validation owns only the protocol shell. Payload meaning is checked
; separately so a well-shaped translator message containing malformed semantic
; data can be named `invalid-candidate` instead of collapsing into a generic
; transport/envelope failure.
(def translation-envelope-valid?
  (lambda (proposal)
    (cond
      ((atom? proposal) (quote ()))
      ((eq? (knowledge-proper-list? proposal) (quote ())) (quote ()))
      ((eq? (= (length proposal) 5) (quote ())) (quote ()))
      ((eq? (symbol? (car proposal)) (quote ())) (quote ()))
      ((eq? (car proposal) *translation-schema*)
       (cond
         ((eq? (translation-status-valid? (translation-status proposal)) (quote ()))
          (quote ()))
         ((eq? (translation-kind-valid? (translation-kind proposal)) (quote ()))
          (quote ()))
         ((string-membership-helper (translation-source proposal))
          (class-membership string nonmember)
          (quote ()))
         (t t)))
      (t (quote ())))))

(def translation-batch-valid?
  (lambda (payload)
    (cond
      ((atom? payload) (quote ()))
      ((eq? (knowledge-proper-list? payload) (quote ())) (quote ()))
      (t (knowledge-clauses-valid? payload)))))

(def translation-candidate-payload-valid?
  (lambda (kind payload)
    (cond
      ((eq? kind (quote clause)) (knowledge-clause-valid? payload))
      ((eq? kind (quote batch)) (translation-batch-valid? payload))
      ((eq? kind (quote query)) (knowledge-goal-valid? payload))
      (t (quote ())))))

(def translation-alternatives-valid?
  (lambda (kind alternatives)
    (cond
      ((atom? alternatives) (quote ()))
      ((translation-candidate-payload-valid? kind (car alternatives))
       (cond
         ((atom? (cdr alternatives)) t)
         (t (translation-alternatives-valid? kind (cdr alternatives)))))
      (t (quote ())))))

; Ambiguity is evidence only when the translator exposes at least two valid
; alternatives. One alternative is just a candidate; zero is not ambiguity.
(def translation-ambiguity-valid?
  (lambda (kind payload)
    (cond
      ((atom? payload) (quote ()))
      ((eq? (knowledge-proper-list? payload) (quote ())) (quote ()))
      ((atom? (cdr payload)) (quote ()))
      (t (translation-alternatives-valid? kind payload)))))

(def make-translation-review
  (lambda (status code proposal detail)
    (list *translation-review-schema* status code proposal detail)))

(def translation-review-status
  (lambda (review) (second review)))

(def translation-review-code
  (lambda (review) (third review)))

(def translation-review-proposal
  (lambda (review) (fourth review)))

(def translation-review-detail
  (lambda (review) (fifth review)))

(def translation-review-status-valid?
  (lambda (status)
    (cond
      ((eq? (symbol? status) (quote ())) (quote ()))
      ((eq? status (quote accepted)) t)
      ((eq? status (quote rejected)) t)
      ((eq? status (quote ambiguous)) t)
      (t (quote ())))))

(def translation-review-valid?
  (lambda (review)
    (cond
      ((atom? review) (quote ()))
      ((eq? (knowledge-proper-list? review) (quote ())) (quote ()))
      ((eq? (= (length review) 5) (quote ())) (quote ()))
      ((eq? (symbol? (car review)) (quote ())) (quote ()))
      ((eq? (car review) *translation-review-schema*)
       (cond
         ((eq? (translation-review-status-valid? (translation-review-status review)) (quote ()))
          (quote ()))
         ((eq? (symbol? (translation-review-code review)) (quote ()))
          (quote ()))
         (t t)))
      (t (quote ())))))

(def translation-review-advice-decision
  (lambda (proposal decision)
    (cond
      ((atom? decision)
       (make-translation-review
         (quote rejected) (quote malformed-advice-decision) proposal decision))
      ((eq? (symbol? (car decision)) (quote ()))
       (make-translation-review
         (quote rejected) (quote malformed-advice-decision) proposal decision))
      ((eq? (car decision) (quote accepted))
       (make-translation-review
         (quote accepted) (quote knowledge-accepted) proposal decision))
      ((eq? (car decision) (quote conflict))
       (make-translation-review
         (quote rejected) (quote knowledge-conflict) proposal decision))
      ((eq? (car decision) (quote rejected))
       (make-translation-review
         (quote rejected) (quote knowledge-rejected) proposal decision))
      (t
       (make-translation-review
         (quote rejected) (quote malformed-advice-decision) proposal decision)))))

(def translation-review-candidate
  (lambda (module-name proposal)
    (let ((kind (translation-kind proposal))
          (payload (translation-payload proposal)))
      (cond
        ((eq? (translation-candidate-payload-valid? kind payload) (quote ()))
         (make-translation-review
           (quote rejected) (quote invalid-candidate) proposal payload))
        ((eq? kind (quote query))
         (make-translation-review
           (quote accepted) (quote query) proposal payload))
        ((eq? kind (quote clause))
         (translation-review-advice-decision
           proposal (advice-decision module-name payload)))
        ((eq? kind (quote batch))
         (translation-review-advice-decision
           proposal (advice-all-decision module-name payload)))
        (t
         (make-translation-review
           (quote rejected) (quote invalid-kind) proposal kind))))))

; `translation-review` is pure with respect to knowledge state. Even a review
; classified as accepted has NOT written anything. Admission remains an
; explicit later call to `advise` or `advise-all` by the Lisp/embedding layer.
(def translation-review
  (lambda (module-name proposal)
    (cond
      ((eq? (symbol? module-name) (quote ()))
       (make-translation-review
         (quote rejected) (quote invalid-module) proposal module-name))
      ((eq? (translation-envelope-valid? proposal) (quote ()))
       (make-translation-review
         (quote rejected) (quote invalid-translation) proposal proposal))
      ((eq? (translation-status proposal) (quote candidate))
       (translation-review-candidate module-name proposal))
      ((eq? (translation-status proposal) (quote ambiguous))
       (cond
         ((translation-ambiguity-valid?
            (translation-kind proposal) (translation-payload proposal))
          (make-translation-review
            (quote ambiguous) (quote translator-ambiguous)
            proposal (translation-payload proposal)))
         (t
          (make-translation-review
            (quote rejected) (quote invalid-ambiguity)
            proposal (translation-payload proposal)))))
      ((eq? (translation-status proposal) (quote rejected))
       (cond
         ((symbol? (translation-payload proposal))
          (make-translation-review
            (quote rejected) (quote translator-rejected)
            proposal (translation-payload proposal)))
         (t
          (make-translation-review
            (quote rejected) (quote invalid-rejection)
            proposal (translation-payload proposal)))))
      (t
       (make-translation-review
         (quote rejected) (quote invalid-translation) proposal proposal)))))

; Only accepted knowledge candidates expose an admission payload. Queries are
; accepted questions, not knowledge writes. Rejected/ambiguous reviews cannot
; accidentally be fed to advise through this helper.
(def translation-admittable?
  (lambda (review)
    (cond
      ((eq? (translation-review-valid? review) (quote ())) (quote ()))
      ((eq? (translation-review-status review) (quote accepted))
       (let ((proposal (translation-review-proposal review)))
         (cond
           ((eq? (translation-envelope-valid? proposal) (quote ())) (quote ()))
           ((eq? (translation-status proposal) (quote candidate))
            (cond
              ((eq? (translation-kind proposal) (quote clause)) t)
              ((eq? (translation-kind proposal) (quote batch)) t)
              (t (quote ()))))
           (t (quote ())))))
      (t (quote ())))))

(def translation-admission-payload
  (lambda (review)
    (cond
      ((translation-admittable? review)
       (translation-payload (translation-review-proposal review)))
      (t (quote ())))))

; Rejected and ambiguous translations are observations, not knowledge. The
; evidence path is also pure: callers decide where/when to persist the returned
; journal, so this library never acquires a hidden second write authority.
(def translation-evidence-worthy?
  (lambda (review)
    (cond
      ((eq? (translation-review-valid? review) (quote ())) (quote ()))
      ((eq? (translation-review-status review) (quote rejected)) t)
      ((eq? (translation-review-status review) (quote ambiguous)) t)
      (t (quote ())))))

(def translation-evidence-entry
  (lambda (review)
    (list *translation-evidence-schema* review)))

(def translation-evidence-next
  (lambda (review journal)
    (cond
      ((translation-evidence-worthy? review)
       (cons (translation-evidence-entry review) journal))
      (t journal))))

(def translation-review-with-evidence
  (lambda (module-name proposal journal)
    (let ((review (translation-review module-name proposal)))
      (list review (translation-evidence-next review journal)))))
