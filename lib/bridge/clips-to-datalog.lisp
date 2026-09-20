; #718 — bounded CLIPS working-memory observation -> Datalog fact candidate projection.
;
; Semantic authority stays in Lisp. This bridge accepts only explicitly decoded
; CLIPS fact data. Producer-native count-only observations are insufficient and
; fail closed; agenda/firing information is recorded as projection loss and is
; never reinterpreted as Datalog closure/derivation semantics.
;
; Accepted input:
;   (clips-working-memory-observation
;     (source-ref REF)
;     (facts ((REL ARG ...) ...))
;     (agenda-fired N))
;
; Output:
;   (projection-result
;     (projection clips-working-memory-to-datalog-facts)
;     (source-ref REF)
;     (facts ((REL ARG ...) ...))
;     (loss ((agenda-fired not-preserved-as-datalog-semantics))))
;
; Named failure examples:
;   missing-source-ref
;   missing-facts
;   malformed-facts
;   count-only-observation-insufficient

(def clips-datalog-fact-list-valid?
  (lambda (facts)
    (cond
      ((atom facts) (structural-kind empty-list) t)
      ((atom facts) (structural-kind atom) (quote ()))
      ((atom facts) (structural-kind pair)
       (let ((fact (car facts)))
         (cond
           ((atom fact) (structural-kind pair)
            (clips-datalog-fact-list-valid? (cdr facts)))
           ((atom fact) (structural-kind empty-list) (quote ()))
           ((atom fact) (structural-kind atom) (quote ())))))))))

(def clips-working-memory-to-datalog-facts
  (lambda (observation)
    (let ((source-ref-row (assoc (quote source-ref) (cdr observation)))
          (facts-row (assoc (quote facts) (cdr observation)))
          (facts-before-row (assoc (quote facts-before) (cdr observation)))
          (facts-after-row (assoc (quote facts-after) (cdr observation)))
          (agenda-fired-row (assoc (quote agenda-fired) (cdr observation))))
      (cond
        ((atom source-ref-row) (structural-kind empty-list)
         (list (quote projection-failure) (quote missing-source-ref)))
        ((atom source-ref-row) (structural-kind atom)
         (list (quote projection-failure) (quote malformed-source-ref)))
        ((atom source-ref-row) (structural-kind pair)
         (cond
           ((atom facts-row) (structural-kind empty-list)
            (cond
              ((atom facts-before-row) (structural-kind pair)
               (list
                 (quote projection-failure)
                 (quote count-only-observation-insufficient)))
              ((atom facts-after-row) (structural-kind pair)
               (list
                 (quote projection-failure)
                 (quote count-only-observation-insufficient)))
              (t
               (list (quote projection-failure) (quote missing-facts)))))
           ((atom facts-row) (structural-kind atom)
            (list (quote projection-failure) (quote malformed-facts)))
           ((atom facts-row) (structural-kind pair)
            (let ((facts (cdr facts-row)))
              (cond
                ((clips-datalog-fact-list-valid? facts)
                 (list
                   (quote projection-result)
                   (list (quote projection)
                         (quote clips-working-memory-to-datalog-facts))
                   (list (quote source-ref)
                         (car (cdr source-ref-row)))
                   (list (quote facts) facts)
                   (list
                     (quote loss)
                     (list
                       (list
                         (quote agenda-fired)
                         (quote not-preserved-as-datalog-semantics))))))
                (t
                 (list
                   (quote projection-failure)
                   (quote malformed-facts))))))))))))

(def clips-datalog-agenda-observation-present?
  (lambda (observation)
    (let ((agenda-fired-row (assoc (quote agenda-fired) (cdr observation))))
      (cond
        ((atom agenda-fired-row) (structural-kind pair) t)
        ((atom agenda-fired-row) (structural-kind empty-list) (quote ()))
        ((atom agenda-fired-row) (structural-kind atom) (quote ()))))))


; Reverse bounded slice: decoded Datalog relation rows -> CLIPS fact candidates.
;
; Accepted input:
;   (datalog-relation-observation
;     (source-ref REF)
;     (relation REL)
;     (tuples ((ARG ...) ...))
;     (derivation-generation N))
;
; Output keeps relational tuples as CLIPS fact candidates only. Datalog
; derivation/generation history is explicitly not preserved as CLIPS agenda,
; salience, or firing semantics.

(def datalog-clips-tuple-list-valid?
  (lambda (tuples)
    (cond
      ((atom tuples) (structural-kind empty-list) t)
      ((atom tuples) (structural-kind atom) (quote ()))
      ((atom tuples) (structural-kind pair)
       (let ((tuple (car tuples)))
         (cond
           ((atom tuple) (structural-kind pair)
            (datalog-clips-tuple-list-valid? (cdr tuples)))
           ((atom tuple) (structural-kind empty-list)
            (datalog-clips-tuple-list-valid? (cdr tuples)))
           ((atom tuple) (structural-kind atom) (quote ())))))))))

(def datalog-tuples-to-clips-facts
  (lambda (relation tuples)
    (cond
      ((atom tuples) (structural-kind empty-list) (quote ()))
      ((atom tuples) (structural-kind pair)
       (cons
         (cons relation (car tuples))
         (datalog-tuples-to-clips-facts relation (cdr tuples)))))))

(def datalog-relation-to-clips-facts
  (lambda (observation)
    (let ((source-ref-row (assoc (quote source-ref) (cdr observation)))
          (relation-row (assoc (quote relation) (cdr observation)))
          (tuples-row (assoc (quote tuples) (cdr observation)))
          (relation-count-row (assoc (quote relation-count) (cdr observation))))
      (cond
        ((atom source-ref-row) (structural-kind empty-list)
         (list (quote projection-failure) (quote missing-source-ref)))
        ((atom source-ref-row) (structural-kind atom)
         (list (quote projection-failure) (quote malformed-source-ref)))
        ((atom source-ref-row) (structural-kind pair)
         (cond
           ((atom relation-row) (structural-kind empty-list)
            (list (quote projection-failure) (quote missing-relation)))
           ((atom relation-row) (structural-kind atom)
            (list (quote projection-failure) (quote malformed-relation)))
           ((atom relation-row) (structural-kind pair)
            (cond
              ((atom tuples-row) (structural-kind empty-list)
               (cond
                 ((atom relation-count-row) (structural-kind pair)
                  (list
                    (quote projection-failure)
                    (quote count-only-observation-insufficient)))
                 (t
                  (list (quote projection-failure) (quote missing-tuples)))))
              ((atom tuples-row) (structural-kind atom)
               (list (quote projection-failure) (quote malformed-tuples)))
              ((atom tuples-row) (structural-kind pair)
               (let ((tuples (cdr tuples-row))
                     (relation (car (cdr relation-row))))
                 (cond
                   ((datalog-clips-tuple-list-valid? tuples)
                    (list
                      (quote projection-result)
                      (list (quote projection)
                            (quote datalog-relation-to-clips-facts))
                      (list (quote source-ref)
                            (car (cdr source-ref-row)))
                      (list
                        (quote facts)
                        (datalog-tuples-to-clips-facts relation tuples))
                      (list
                        (quote loss)
                        (list
                          (list
                            (quote derivation-generation)
                            (quote not-preserved-as-clips-agenda-semantics))))))
                   (t
                    (list
                      (quote projection-failure)
                      (quote malformed-tuples))))))))))))))


; Lisp data -> CLIPS fact candidate.
;
; This is a representational projection only. It does not assert into a CLIPS
; environment, schedule rules, or claim that arbitrary Lisp structure is a
; CLIPS rule/fact ontology.
;
; Accepted:
;   (lisp-fact-candidate (relation REL) (arguments (ARG ...)))
;
; Output:
;   (projection-result
;     (projection lisp-data-to-clips-fact)
;     (fact (REL ARG ...))
;     (loss ((lisp-evaluation-history not-preserved))))

(def lisp-data-to-clips-fact
  (lambda (candidate)
    (let ((relation-row (assoc (quote relation) (cdr candidate)))
          (arguments-row (assoc (quote arguments) (cdr candidate))))
      (cond
        ((atom relation-row) (structural-kind empty-list)
         (list (quote projection-failure) (quote missing-relation)))
        ((atom relation-row) (structural-kind atom)
         (list (quote projection-failure) (quote malformed-relation)))
        ((atom relation-row) (structural-kind pair)
         (cond
           ((atom arguments-row) (structural-kind empty-list)
            (list (quote projection-failure) (quote missing-arguments)))
           ((atom arguments-row) (structural-kind atom)
            (list (quote projection-failure) (quote malformed-arguments)))
           ((atom arguments-row) (structural-kind pair)
            (let ((arguments (cdr arguments-row))
                  (relation (car (cdr relation-row))))
              (cond
                ((atom arguments) (structural-kind atom)
                 (list (quote projection-failure) (quote malformed-arguments)))
                ((atom arguments) (structural-kind empty-list)
                 (list
                   (quote projection-result)
                   (list (quote projection) (quote lisp-data-to-clips-fact))
                   (list (quote fact) (list relation))
                   (list
                     (quote loss)
                     (list
                       (list
                         (quote lisp-evaluation-history)
                         (quote not-preserved))))))
                ((atom arguments) (structural-kind pair)
                 (list
                   (quote projection-result)
                   (list (quote projection) (quote lisp-data-to-clips-fact))
                   (list (quote fact) (cons relation arguments))
                   (list
                     (quote loss)
                     (list
                       (list
                         (quote lisp-evaluation-history)
                         (quote not-preserved)))))))))))))))
