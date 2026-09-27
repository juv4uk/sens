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

(00001001 pd-question-choice
  (00001000 (name options)
    (00100111 (00000001 choice-question/1) name options)))

(00001001 pd-question-noul
  (00001000 (name)
    (00100111 (00000001 noul-question/1) name)))

(00001001 pd-question-score
  (00001000 (name levels)
    (00100111 (00000001 score-question/1) name levels)))

(00001001 pd-member?
  (00001000 (value values)
    (00000111
      ((00000010 values) () (00000001 ()))
      ((00000010 values) (1) (00000001 ()))
      ((00100010 value (00000101 values)) (1) t)
      (t (pd-member? value (00000110 values))))))

(00001001 pd-proper-list?
  (00001000 (value)
    (00000111
      ((00000010 value) () (00000111
         ((00000011 value (00000001 ())) t)
         (t (00000001 ()))))
      ((00000010 value) (1) (00000111
         ((00000011 value (00000001 ())) t)
         (t (00000001 ()))))
      (t (pd-proper-list? (00000110 value))))))

(00001001 pd-probability-valid?
  (00001000 (probability)
    (00000111
      ((00011010 probability 0) 1 (00000001 ()))
      ((00011010 1 probability) 1 (00000001 ()))
      (t t))))

(00001001 pd-sum-probabilities
  (00001000 (distribution)
    (00000111
      ((00000010 distribution) () 0)
      ((00000010 distribution) (1) 0)
      (t
       (00001100 (00101111 (00000101 distribution))
          (pd-sum-probabilities (00000110 distribution)))))))

(00001001 pd-distribution-entries-valid?
  (00001000 (distribution options seen)
    (00000111
      ((00000010 distribution) () t)
      ((00000010 distribution) (1) t)
      (t
       (10011100 ((entry (00000101 distribution)))
         (00000111
           ((00011100 (00101000 entry) 2) 1
            (10011100 ((label (00000101 entry))
                  (probability (00101111 entry)))
              (00000111
                ((pd-member? label options)
                 (00000111
                   ((pd-member? label seen) (00000001 ()))
                   ((pd-probability-valid? probability)
                    (pd-distribution-entries-valid?
                      (00000110 distribution)
                      options
                      (00000100 label seen)))
                   (t (00000001 ()))))
                (t (00000001 ())))))
           (t (00000001 ()))))))))

(00001001 pd-all-options-present?
  (00001000 (options distribution)
    (00000111
      ((00000010 options) () t)
      ((00000010 options) (1) t)
      (t
       (00000111
         ((pd-member? (00000101 options) (00110111 car distribution))
          (pd-all-options-present? (00000110 options) distribution))
         (t (00000001 ())))))))

(00001001 pd-distribution-valid?
  (00001000 (options distribution)
    (00000111
      ((pd-proper-list? options)
       (00000111
         ((pd-proper-list? distribution)
          (00000111
            ((00000010 options) () (00000001 ()))
            ((00000010 options) (1) (00000001 ()))
            ((00000010 distribution) () (00000001 ()))
            ((00000010 distribution) (1) (00000001 ()))
            ((pd-distribution-entries-valid? distribution options (00000001 ()))
             (00000111
               ((00011100 (pd-sum-probabilities distribution) 1) 1
                (pd-all-options-present? options distribution))
               (t (00000001 ()))))
            (t (00000001 ()))))
         (t (00000001 ()))))
      (t (00000001 ())))))

(00001001 pd-max-probability
  (00001000 (distribution current)
    (00000111
      ((00000010 distribution) () current)
      ((00000010 distribution) (1) current)
      (t
       (10011100 ((probability (00101111 (00000101 distribution))))
         (00000111
           ((00011010 current probability) 1
            (pd-max-probability (00000110 distribution) probability))
           (t
            (pd-max-probability (00000110 distribution) current))))))))

(00001001 pd-confidence
  (00001000 (distribution)
    (pd-max-probability distribution 0)))

(00001001 pd-choice-observe
  (00001000 (question distribution source)
    (00000111
      ((pd-distribution-valid? (00110000 question) distribution)
       (00100111
         (00000001 choice-observation/1)
         question
         distribution
         (pd-confidence distribution)
         source))
      (t
       (make-invalid
         (00000001 malformed-choice-distribution)
         (00100111 question distribution))))))

(00001001 pd-noul-observe
  (00001000 (question yes-probability source)
    (00000111
      ((pd-probability-valid? yes-probability)
       (10011100 ((distribution
               (00100111
                 (00100111 (00000001 yes) yes-probability)
                 (00100111 (00000001 no) (00001101 1 yes-probability)))))
         (00100111
           (00000001 noul-observation/1)
           question
           distribution
           (pd-confidence distribution)
           source)))
      (t
       (make-invalid
         (00000001 malformed-noul-probability)
         (00100111 question yes-probability))))))

(00001001 pd-score-observe
  (00001000 (question distribution source)
    (00000111
      ((pd-distribution-valid? (00110000 question) distribution)
       (00100111
         (00000001 score-observation/1)
         question
         distribution
         (pd-confidence distribution)
         source))
      (t
       (make-invalid
         (00000001 malformed-score-distribution)
         (00100111 question distribution))))))

(00001001 pd-observation-confidence
  (00001000 (observation)
    (00110001 observation)))

(00001001 pd-observation-provenance
  (00001000 (observation)
    (00110010 observation)))

(00001001 pd-noul-policy
  (00001000 (observation threshold)
    (00000111
      ((00100010 (00000101 observation) (00000001 noul-observation/1)) (1)
       (00000111
         ((pd-probability-valid? threshold)
          (10011100 ((probability (00101111 (00000101 (00110000 observation)))))
            (00000111
              ((00011010 probability threshold) 1
               (00100111 (00000001 decision/1)
                     (00000001 defer)
                     observation
                     (00100111 (00000001 threshold) threshold)))
              (t
               (00100111 (00000001 decision/1)
                     (00000001 accept)
                     observation
                     (00100111 (00000001 threshold) threshold))))))
         (t
          (make-invalid
            (00000001 malformed-policy-threshold)
            threshold))))
      (t
       (make-invalid
         (00000001 unsupported-decision-observation)
         observation)))))

(00001001 pd-choice-policy
  (00001000 (observation option threshold)
    (00000111
      ((00100010 (00000101 observation) (00000001 choice-observation/1)) (1)
       (00000111
         ((pd-probability-valid? threshold)
          (10011100 ((entry (pd-find-option option (00110000 observation))))
            (00000111
              ((00000010 entry) () (make-invalid
                 (00000001 option-not-observed)
                 (00100111 option observation)))
              ((00000010 entry) (1) (make-invalid
                 (00000001 option-not-observed)
                 (00100111 option observation)))
              ((00011010 (00101111 entry) threshold) 1
               (00100111 (00000001 decision/1)
                     (00000001 defer)
                     observation
                     (00100111 (00000001 option) option)
                     (00100111 (00000001 threshold) threshold)))
              (t
               (00100111 (00000001 decision/1)
                     (00000001 accept)
                     observation
                     (00100111 (00000001 option) option)
                     (00100111 (00000001 threshold) threshold))))))
         (t
          (make-invalid
            (00000001 malformed-policy-threshold)
            threshold))))
      (t
       (make-invalid
         (00000001 unsupported-decision-observation)
         observation)))))

(00001001 pd-find-option
  (00001000 (option distribution)
    (00000111
      ((00000010 distribution) () (00000001 ()))
      ((00000010 distribution) (1) (00000001 ()))
      ((00100010 option (00000101 (00000101 distribution))) (1) (00000101 distribution))
      (t (pd-find-option option (00000110 distribution))))))

(00001001 pd-two-question-consistency
  (00001000 (left right relation)
    (00000111
      ((00000011 relation (00000001 independent)) (1)
       (00100111
         (00000001 decision-relation/1)
         (00000001 independent)
         left
         right))
      ((00000011 relation (00000001 agree)) (1)
       (00000111
         ((00100010 (00110000 left) (00110000 right)) (1)
          (00100111 (00000001 decision-relation/1) (00000001 agree) left right))
         (t (make-disputed (00100111 left right)))))
      (t
       (make-invalid
         (00000001 unsupported-question-relation)
         (00100111 relation left right))))))

(00001001 pd-synthetic-witness
  (00001000 (state choice-question noul-question score-question)
    (00100111
      (00000001 probabilistic-witness/1)
      state
      (pd-choice-observe
        choice-question
        (00000001 ((billing 3/4) (technical 1/4)))
        (00100111 (00000001 source)
              (00000001 synthetic-witness)
              (00000001 state)
              state))
      (pd-noul-observe
        noul-question
        2/3
        (00100111 (00000001 source)
              (00000001 synthetic-witness)
              (00000001 state)
              state))
      (pd-score-observe
        score-question
        (00000001 ((low 1/4) (medium 1/2) (high 1/4)))
        (00100111 (00000001 source)
              (00000001 synthetic-witness)
              (00000001 state)
              state)))))
