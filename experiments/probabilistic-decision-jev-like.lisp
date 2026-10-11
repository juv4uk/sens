; probabilistic-decision-jev-like.lisp — first pure-Lisp System One / Jev-like slice.
;
; This is an experimental mechanism/data layer. It does NOT create a semantic SID,
; does not add a runtime Value variant, and does not treat probability/confidence
; as truth. A future model adapter may produce these observations, but my-lisp
; owns the typed question, validation, provenance and deterministic policy.
;
; Fixed 2026-09-24: `atom`/`eq`/`equal?` and the custom `pd-*?` predicates below
; return structural records (`(structural-kind ...)`, `(identity-relation ...)`)
; or the classic `t`/`()` pair — never exact-Q 1/0. Every canonical-cond clause
; that tested one of those against a literal `1`/`0` tag could never match,
; surfacing as "canonical cond: no query matched" at runtime. Only the raw
; arithmetic comparisons (`<`, `=`) genuinely return exact-Q 1/0, and keep their
; literal tag. Every other clause below uses the two-part migration-compatible
; form instead, which `evaluate_cond` resolves via generic/structural truthiness.

(0011 pd-question-choice
  (0010 (name options)
    (1110 (001 choice-question/1) name options)))

(0011 pd-question-noul
  (0010 (name)
    (1110 (001 noul-question/1) name)))

(0011 pd-question-score
  (0010 (name levels)
    (1110 (001 score-question/1) name levels)))

(0011 pd-member?
  (0010 (value values)
    (110
      ((010 values) () (001 ()))
      ((010 values) (1) (001 ()))
      ((11110111 value (100 values)) (1) t)
      (t (pd-member? value (011 values))))))

(0011 pd-proper-list?
  (0010 (value)
    (110
      ((010 value) () (110
         ((101 value (001 ())) t)
         (t (001 ()))))
      ((010 value) (1) (110
         ((101 value (001 ())) t)
         (t (001 ()))))
      (t (pd-proper-list? (011 value))))))

(0011 pd-probability-valid?
  (0010 (probability)
    (110
      ((11010 probability 0) 1 (001 ()))
      ((11010 1 probability) 1 (001 ()))
      (t t))))

(0011 pd-sum-probabilities
  (0010 (distribution)
    (110
      ((010 distribution) () 0)
      ((010 distribution) (1) 0)
      (t
       (01010 (1001 (100 distribution))
          (pd-sum-probabilities (011 distribution)))))))

(0011 pd-distribution-entries-valid?
  (0010 (distribution options seen)
    (110
      ((010 distribution) () t)
      ((010 distribution) (1) t)
      (t
       (001000 ((entry (100 distribution)))
         (110
           ((11110111 (000000 entry) 2) 1
            (001000 ((entry-key-ref (100 entry))
                  (probability (1001 entry)))
              (110
                ((pd-member? entry-key-ref options)
                 (110
                   ((pd-member? entry-key-ref seen) (001 ()))
                   ((pd-probability-valid? probability)
                    (pd-distribution-entries-valid?
                      (011 distribution)
                      options
                      (111 entry-key-ref seen)))
                   (t (001 ()))))
                (t (001 ())))))
           (t (001 ()))))))))

(0011 pd-all-options-present?
  (0010 (options distribution)
    (110
      ((010 options) () t)
      ((010 options) (1) t)
      (t
       (110
         ((pd-member? (100 options) (101000 (0010 (entry) (100 entry)) distribution))
          (pd-all-options-present? (011 options) distribution))
         (t (001 ())))))))

(0011 pd-distribution-valid?
  (0010 (options distribution)
    (110
      ((pd-proper-list? options)
       (110
         ((pd-proper-list? distribution)
          (110
            ((010 options) () (001 ()))
            ((010 options) (1) (001 ()))
            ((010 distribution) () (001 ()))
            ((010 distribution) (1) (001 ()))
            ((pd-distribution-entries-valid? distribution options (001 ()))
             (110
               ((11110111 (pd-sum-probabilities distribution) 1) 1
                (pd-all-options-present? options distribution))
               (t (001 ()))))
            (t (001 ()))))
         (t (001 ()))))
      (t (001 ())))))

(0011 pd-max-probability
  (0010 (distribution current)
    (110
      ((010 distribution) () current)
      ((010 distribution) (1) current)
      (t
       (001000 ((probability (1001 (100 distribution))))
         (110
           ((11010 current probability) 1
            (pd-max-probability (011 distribution) probability))
           (t
            (pd-max-probability (011 distribution) current))))))))

(0011 pd-confidence
  (0010 (distribution)
    (pd-max-probability distribution 0)))

(0011 pd-choice-observe
  (0010 (question distribution source)
    (110
      ((pd-distribution-valid? (10011 question) distribution)
       (1110
         (001 choice-observation/1)
         question
         distribution
         (pd-confidence distribution)
         source))
      (t
       (make-invalid
         (001 malformed-choice-distribution)
         (1110 question distribution))))))

(0011 pd-noul-observe
  (0010 (question yes-probability source)
    (110
      ((pd-probability-valid? yes-probability)
       (001000 ((distribution
               (1110
                 (1110 (001 yes) yes-probability)
                 (1110 (001 no) (01011 1 yes-probability)))))
         (1110
           (001 noul-observation/1)
           question
           distribution
           (pd-confidence distribution)
           source)))
      (t
       (make-invalid
         (001 malformed-noul-probability)
         (1110 question yes-probability))))))

(0011 pd-score-observe
  (0010 (question distribution source)
    (110
      ((pd-distribution-valid? (10011 question) distribution)
       (1110
         (001 score-observation/1)
         question
         distribution
         (pd-confidence distribution)
         source))
      (t
       (make-invalid
         (001 malformed-score-distribution)
         (1110 question distribution))))))

(0011 pd-observation-confidence
  (0010 (observation)
    (100111 observation)))

(0011 pd-observation-provenance
  (0010 (observation)
    (110110101 observation)))

(0011 pd-noul-policy
  (0010 (observation threshold)
    (110
      ((11110111 (100 observation) (001 noul-observation/1)) (1)
       (110
         ((pd-probability-valid? threshold)
          (001000 ((probability (1001 (100 (10011 observation)))))
            (110
              ((11010 probability threshold) 1
               (1110 (001 decision/1)
                     (001 defer)
                     observation
                     (1110 (001 threshold) threshold)))
              (t
               (1110 (001 decision/1)
                     (001 accept)
                     observation
                     (1110 (001 threshold) threshold))))))
         (t
          (make-invalid
            (001 malformed-policy-threshold)
            threshold))))
      (t
       (make-invalid
         (001 unsupported-decision-observation)
         observation)))))

(0011 pd-choice-policy
  (0010 (observation option threshold)
    (110
      ((11110111 (100 observation) (001 choice-observation/1)) (1)
       (110
         ((pd-probability-valid? threshold)
          (001000 ((entry (pd-find-option option (10011 observation))))
            (110
              ((010 entry) () (make-invalid
                 (001 option-not-observed)
                 (1110 option observation)))
              ((010 entry) (1) (make-invalid
                 (001 option-not-observed)
                 (1110 option observation)))
              ((11010 (1001 entry) threshold) 1
               (1110 (001 decision/1)
                     (001 defer)
                     observation
                     (1110 (001 option) option)
                     (1110 (001 threshold) threshold)))
              (t
               (1110 (001 decision/1)
                     (001 accept)
                     observation
                     (1110 (001 option) option)
                     (1110 (001 threshold) threshold))))))
         (t
          (make-invalid
            (001 malformed-policy-threshold)
            threshold))))
      (t
       (make-invalid
         (001 unsupported-decision-observation)
         observation)))))

(0011 pd-find-option
  (0010 (option distribution)
    (110
      ((010 distribution) () (001 ()))
      ((010 distribution) (1) (001 ()))
      ((11110111 option (100 (100 distribution))) (1) (100 distribution))
      (t (pd-find-option option (011 distribution))))))

(0011 pd-two-question-consistency
  (0010 (left right relation)
    (110
      ((101 relation (001 independent)) (1)
       (1110
         (001 decision-relation/1)
         (001 independent)
         left
         right))
      ((101 relation (001 agree)) (1)
       (110
         ((11110111 (10011 left) (10011 right)) (1)
          (1110 (001 decision-relation/1) (001 agree) left right))
         (t (make-disputed (1110 left right)))))
      (t
       (make-invalid
         (001 unsupported-question-relation)
         (1110 relation left right))))))

(0011 pd-synthetic-witness
  (0010 (state choice-question noul-question score-question)
    (1110
      (001 probabilistic-witness/1)
      state
      (pd-choice-observe
        choice-question
        (001 ((billing 3/4) (technical 1/4)))
        (1110 (001 source)
              (001 synthetic-witness)
              (001 state)
              state))
      (pd-noul-observe
        noul-question
        2/3
        (1110 (001 source)
              (001 synthetic-witness)
              (001 state)
              state))
      (pd-score-observe
        score-question
        (001 ((low 1/4) (medium 1/2) (high 1/4)))
        (1110 (001 source)
              (001 synthetic-witness)
              (001 state)
              state)))))
