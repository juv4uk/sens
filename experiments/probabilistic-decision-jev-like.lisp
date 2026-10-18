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

(визначити pd-question-choice
  (функція (name options)
    (список (як-є choice-question/1) name options)))

(визначити pd-question-noul
  (функція (name)
    (список (як-є noul-question/1) name)))

(визначити pd-question-score
  (функція (name levels)
    (список (як-є score-question/1) name levels)))

(визначити pd-member?
  (функція (value values)
    (за-умовою
      ((010 values) () (001 ()))
      ((010 values) (1) (001 ()))
      ((11110111 value (100 values)) (1) t)
      (t (pd-member? value (решта values))))))

(визначити pd-proper-list?
  (функція (value)
    (за-умовою
      ((010 value) () (110
         ((101 value (001 ())) t)
         (t (як-є ()))))
      ((010 value) (1) (110
         ((101 value (001 ())) t)
         (t (як-є ()))))
      (t (pd-proper-list? (решта value))))))

(визначити pd-probability-valid?
  (функція (probability)
    (за-умовою
      ((11010 probability 0) 1 (001 ()))
      ((11010 1 probability) 1 (001 ()))
      (t t))))

(визначити pd-sum-probabilities
  (функція (distribution)
    (за-умовою
      ((010 distribution) () 0)
      ((010 distribution) (1) 0)
      (t
       (01010 (1001 (100 distribution))
          (pd-sum-probabilities (решта distribution)))))))

(визначити pd-distribution-entries-valid?
  (функція (distribution options seen)
    (за-умовою
      ((010 distribution) () t)
      ((010 distribution) (1) t)
      (t
       (001000 ((entry (100 distribution)))
         (за-умовою
           ((11110111 (000000 entry) 2) 1
            (001000 ((entry-key-ref (100 entry))
                  (probability (друге entry)))
              (за-умовою
                ((pd-member? entry-key-ref options)
                 (за-умовою
                   ((pd-member? entry-key-ref seen) (як-є ()))
                   ((pd-probability-valid? probability)
                    (pd-distribution-entries-valid?
                      (решта distribution)
                      options
                      (сполучити entry-key-ref seen)))
                   (t (як-є ()))))
                (t (як-є ())))))
           (t (як-є ()))))))))

(визначити pd-all-options-present?
  (функція (options distribution)
    (за-умовою
      ((010 options) () t)
      ((010 options) (1) t)
      (t
       (за-умовою
         ((pd-member? (100 options) (101000 (0010 (entry) (100 entry)) distribution))
          (pd-all-options-present? (решта options) distribution))
         (t (як-є ())))))))

(визначити pd-distribution-valid?
  (функція (options distribution)
    (за-умовою
      ((pd-proper-list? options)
       (за-умовою
         ((pd-proper-list? distribution)
          (за-умовою
            ((010 options) () (001 ()))
            ((010 options) (1) (001 ()))
            ((010 distribution) () (001 ()))
            ((010 distribution) (1) (001 ()))
            ((pd-distribution-entries-valid? distribution options (001 ()))
             (за-умовою
               ((11110111 (pd-sum-probabilities distribution) 1) 1
                (pd-all-options-present? options distribution))
               (t (як-є ()))))
            (t (як-є ()))))
         (t (як-є ()))))
      (t (як-є ())))))

(визначити pd-max-probability
  (функція (distribution current)
    (за-умовою
      ((010 distribution) () current)
      ((010 distribution) (1) current)
      (t
       (001000 ((probability (1001 (100 distribution))))
         (за-умовою
           ((11010 current probability) 1
            (pd-max-probability (решта distribution) probability))
           (t
            (pd-max-probability (решта distribution) current))))))))

(визначити pd-confidence
  (функція (distribution)
    (pd-max-probability distribution 0)))

(визначити pd-choice-observe
  (функція (question distribution source)
    (за-умовою
      ((pd-distribution-valid? (10011 question) distribution)
       (список
         (як-є choice-observation/1)
         question
         distribution
         (pd-confidence distribution)
         source))
      (t
       (make-invalid
         (як-є malformed-choice-distribution)
         (список question distribution))))))

(визначити pd-noul-observe
  (функція (question yes-probability source)
    (за-умовою
      ((pd-probability-valid? yes-probability)
       (001000 ((distribution
               (1110
                 (1110 (001 yes) yes-probability)
                 (1110 (001 no) (01011 1 yes-probability)))))
         (список
           (як-є noul-observation/1)
           question
           distribution
           (pd-confidence distribution)
           source)))
      (t
       (make-invalid
         (як-є malformed-noul-probability)
         (список question yes-probability))))))

(визначити pd-score-observe
  (функція (question distribution source)
    (за-умовою
      ((pd-distribution-valid? (10011 question) distribution)
       (список
         (як-є score-observation/1)
         question
         distribution
         (pd-confidence distribution)
         source))
      (t
       (make-invalid
         (як-є malformed-score-distribution)
         (список question distribution))))))

(визначити pd-observation-confidence
  (функція (observation)
    (100111 observation)))

(визначити pd-observation-provenance
  (функція (observation)
    (110110101 observation)))

(визначити pd-noul-policy
  (функція (observation threshold)
    (за-умовою
      ((11110111 (100 observation) (001 noul-observation/1)) (1)
       (за-умовою
         ((pd-probability-valid? threshold)
          (001000 ((probability (1001 (100 (10011 observation)))))
            (за-умовою
              ((11010 probability threshold) 1
               (список (як-є decision/1)
                     (як-є defer)
                     observation
                     (список (як-є threshold) threshold)))
              (t
               (список (як-є decision/1)
                     (як-є accept)
                     observation
                     (список (як-є threshold) threshold))))))
         (t
          (make-invalid
            (як-є malformed-policy-threshold)
            threshold))))
      (t
       (make-invalid
         (як-є unsupported-decision-observation)
         observation)))))

(визначити pd-choice-policy
  (функція (observation option threshold)
    (за-умовою
      ((11110111 (100 observation) (001 choice-observation/1)) (1)
       (за-умовою
         ((pd-probability-valid? threshold)
          (001000 ((entry (pd-find-option option (10011 observation))))
            (за-умовою
              ((010 entry) () (make-invalid
                 (як-є option-not-observed)
                 (список option observation)))
              ((010 entry) (1) (make-invalid
                 (як-є option-not-observed)
                 (список option observation)))
              ((11010 (1001 entry) threshold) 1
               (список (як-є decision/1)
                     (як-є defer)
                     observation
                     (список (як-є option) option)
                     (список (як-є threshold) threshold)))
              (t
               (список (як-є decision/1)
                     (як-є accept)
                     observation
                     (список (як-є option) option)
                     (список (як-є threshold) threshold))))))
         (t
          (make-invalid
            (як-є malformed-policy-threshold)
            threshold))))
      (t
       (make-invalid
         (як-є unsupported-decision-observation)
         observation)))))

(визначити pd-find-option
  (функція (option distribution)
    (за-умовою
      ((010 distribution) () (001 ()))
      ((010 distribution) (1) (001 ()))
      ((11110111 option (100 (100 distribution))) (1) (100 distribution))
      (t (pd-find-option option (решта distribution))))))

(визначити pd-two-question-consistency
  (функція (left right relation)
    (за-умовою
      ((101 relation (001 independent)) (1)
       (список
         (як-є decision-relation/1)
         (як-є independent)
         left
         right))
      ((101 relation (001 agree)) (1)
       (за-умовою
         ((11110111 (10011 left) (10011 right)) (1)
          (список (як-є decision-relation/1) (як-є agree) left right))
         (t (make-disputed (список left right)))))
      (t
       (make-invalid
         (як-є unsupported-question-relation)
         (список relation left right))))))

(визначити pd-synthetic-witness
  (функція (state choice-question noul-question score-question)
    (список
      (як-є probabilistic-witness/1)
      state
      (pd-choice-observe
        choice-question
        (як-є ((billing 3/4) (technical 1/4)))
        (список (як-є source)
              (як-є synthetic-witness)
              (як-є state)
              state))
      (pd-noul-observe
        noul-question
        2/3
        (список (як-є source)
              (як-є synthetic-witness)
              (як-є state)
              state))
      (pd-score-observe
        score-question
        (як-є ((low 1/4) (medium 1/2) (high 1/4)))
        (список (як-є source)
              (як-є synthetic-witness)
              (як-є state)
              state)))))
