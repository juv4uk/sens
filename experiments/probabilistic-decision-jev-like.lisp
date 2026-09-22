; probabilistic-decision-jev-like.lisp — first pure-Lisp System One / Jev-like slice.
;
; This is an experimental mechanism/data layer. It does NOT create a semantic SID,
; does not add a runtime Value variant, and does not treat probability/confidence
; as truth. A future model adapter may produce these observations, but my-lisp
; owns the typed question, validation, provenance and deterministic policy.

(def pd-question-choice
  (lambda (name options)
    (list (quote choice-question/1) name options)))

(def pd-question-noul
  (lambda (name)
    (list (quote noul-question/1) name)))

(def pd-question-score
  (lambda (name levels)
    (list (quote score-question/1) name levels)))

(def pd-member?
  (lambda (value values)
    (cond
      ((atom values) 1 (quote ()))
      ((equal? value (car values)) (structural-relation same) t)
      (t 1 (pd-member? value (cdr values))))))

(def pd-proper-list?
  (lambda (value)
    (cond
      ((atom value)
       (cond
         ((eq value (quote ())) 1 t)
         (t 1 (quote ()))))
      (t 1 (pd-proper-list? (cdr value))))))

(def pd-probability-valid?
  (lambda (probability)
    (cond
      ((< probability 0) 1 (quote ()))
      ((< 1 probability) 1 (quote ()))
      (t 1 t))))

(def pd-sum-probabilities
  (lambda (distribution)
    (cond
      ((atom distribution) 1 0)
      (t
       (+ (second (car distribution))
          (pd-sum-probabilities (cdr distribution)))))))

(def pd-distribution-entries-valid?
  (lambda (distribution options seen)
    (cond
      ((atom distribution) 1 t)
      (t
       (let ((entry (car distribution)))
         (cond
           ((= (length entry) 2) 1
            (let ((label (car entry))
                  (probability (second entry)))
              (cond
                ((pd-member? label options) 1
                 (cond
                   ((pd-member? label seen) 1 (quote ()))
                   ((pd-probability-valid? probability) 1
                    (pd-distribution-entries-valid?
                      (cdr distribution)
                      options
                      (cons label seen)))
                   (t 1 (quote ()))))
                (t 1 (quote ())))))
           (t 1 (quote ())))))))

(def pd-distribution-labels
  (lambda (distribution)
    (cond
      ((atom distribution) 1 (quote ()))
      (t (cons (car (car distribution))
               (pd-distribution-labels (cdr distribution)))))))

(def pd-all-options-present?
  (lambda (options distribution)
    (cond
      ((atom options) 1 t)
      (t
       (cond
         ((pd-member? (car options) (pd-distribution-labels distribution)) 1
          (pd-all-options-present? (cdr options) distribution))
         (t 1 (quote ())))))))

(def pd-distribution-valid?
  (lambda (options distribution)
    (cond
      ((pd-proper-list? options) 1
       (cond
         ((pd-proper-list? distribution) 1
          (cond
            ((atom options) 1 (quote ()))
            ((atom distribution) 1 (quote ()))
            ((pd-distribution-entries-valid? distribution options (quote ())) 1
             (cond
               ((= (pd-sum-probabilities distribution) 1) 1
                (pd-all-options-present? options distribution))
               (t 1 (quote ()))))
            (t 1 (quote ()))))
         (t 1 (quote ()))))
      (t 1 (quote ()))))

(def pd-max-probability
  (lambda (distribution current)
    (cond
      ((atom distribution) 1 current)
      (t
       (let ((probability (second (car distribution))))
         (cond
           ((< current probability) 1
            (pd-max-probability (cdr distribution) probability))
           (t 1
            (pd-max-probability (cdr distribution) current))))))))

(def pd-confidence
  (lambda (distribution)
    (pd-max-probability distribution 0)))

(def pd-choice-observe
  (lambda (question distribution source)
    (cond
      ((pd-distribution-valid? (third question) distribution) 1
       (list
         (quote choice-observation/1)
         question
         distribution
         (pd-confidence distribution)
         source))
      (t 1
       (make-invalid
         (quote malformed-choice-distribution)
         (list question distribution))))))

(def pd-noul-observe
  (lambda (question yes-probability source)
    (cond
      ((pd-probability-valid? yes-probability) 1
       (let ((distribution
               (list
                 (list (quote yes) yes-probability)
                 (list (quote no) (- 1 yes-probability)))))
         (list
           (quote noul-observation/1)
           question
           distribution
           (pd-confidence distribution)
           source)))
      (t 1
       (make-invalid
         (quote malformed-noul-probability)
         (list question yes-probability))))))

(def pd-score-observe
  (lambda (question distribution source)
    (cond
      ((pd-distribution-valid? (third question) distribution) 1
       (list
         (quote score-observation/1)
         question
         distribution
         (pd-confidence distribution)
         source))
      (t 1
       (make-invalid
         (quote malformed-score-distribution)
         (list question distribution))))))

(def pd-observation-confidence
  (lambda (observation)
    (fourth observation)))

(def pd-observation-provenance
  (lambda (observation)
    (fifth observation)))

(def pd-noul-policy
  (lambda (observation threshold)
    (cond
      ((eq (car observation) (quote noul-observation/1)) 1
       (let ((probability (second (car (third observation)))))
         (cond
           ((< probability threshold) 1
            (list (quote decision/1)
                  (quote defer)
                  observation
                  (list (quote threshold) threshold)))
           (t 1
            (list (quote decision/1)
                  (quote accept)
                  observation
                  (list (quote threshold) threshold))))))
      (t 1
       (make-invalid
         (quote unsupported-decision-observation)
         observation)))))

(def pd-choice-policy
  (lambda (observation option threshold)
    (cond
      ((eq (car observation) (quote choice-observation/1)) 1
       (let ((entry (pd-find-option option (third observation))))
         (cond
           ((atom entry) 1
            (make-invalid
              (quote option-not-observed)
              (list option observation)))
           ((< (second entry) threshold) 1
            (list (quote decision/1)
                  (quote defer)
                  observation
                  (list (quote option) option)
                  (list (quote threshold) threshold)))
           (t 1
            (list (quote decision/1)
                  (quote accept)
                  observation
                  (list (quote option) option)
                  (list (quote threshold) threshold))))))
      (t 1
       (make-invalid
         (quote unsupported-decision-observation)
         observation)))))

(def pd-find-option
  (lambda (option distribution)
    (cond
      ((atom distribution) 1 (quote ()))
      ((equal? option (car (car distribution))) (structural-relation same) (car distribution))
      (t 1 (pd-find-option option (cdr distribution))))))

(def pd-two-question-consistency
  (lambda (left right relation)
    (cond
      ((eq relation (quote independent)) 1
       (list
         (quote decision-relation/1)
         (quote independent)
         left
         right))
      ((eq relation (quote agree)) 1
       (cond
         ((equal? (third left) (third right)) (structural-relation same)
          (list (quote decision-relation/1) (quote agree) left right))
         (t 1 (make-disputed (list left right)))))
      (t 1
       (make-invalid
         (quote unsupported-question-relation)
         (list relation left right))))))
