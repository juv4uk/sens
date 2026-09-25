; reason.lisp — backward-chaining Advice Taker inference engine.
; Rules are `(head . body)`. `reason` preserves its historical public result:
; a list of `(substitution proof)` pairs, or `()` when no proof is found.
;
; B5 indexing remains ordinary finite Lisp data. A rule set is indexed only
; when every rule head and the current goal have a safely observable symbol
; predicate. Variable heads/goals and other unusual historical shapes fall
; back to the exact linear scan. The small alist index is also capped at 64
; distinct predicates so an adversarial unique-predicate corpus cannot turn
; index construction into an unbounded O(N^2) walk.

(def *reason-index-schema* (quote reason-index/1))
(def *reason-index-max-predicates* 64)

; Shape: (reason-index/1 indexed|linear ORIGINAL-RULES BUCKETS)
; A bucket is (PREDICATE RULE...), with rules restored to original order.
(def reason-index-mode second)
(def reason-index-rules third)
(def reason-index-buckets fourth)

(def reason-index?
  (lambda (value)
    (cond
      ((atom? value) (quote ()))
      ((atom? (car value))
       (cond
         ((eq? (car value) *reason-index-schema*) t)
         (t (quote ()))))
      (t (quote ())))))

(def reason-index-linear
  (lambda (rules)
    (list *reason-index-schema* (quote linear) rules (quote ()))))

; Only ordinary predicate-headed compound terms are safe index keys.
; `(var x)` is deliberately excluded: as a logic variable it can unify with
; any rule head and must therefore retain the historical full scan.
(def reason-term-predicate
  (lambda (term)
    (cond
      ((atom? term) (quote ()))
      ((var? term) (quote ()))
      ((atom? (car term))
       (cond
         ((symbol? (car term)) (car term))
         (t (quote ()))))
      (t (quote ())))))

(def reason-rule-predicate
  (lambda (rule)
    (cond
      ((atom? rule) (quote ()))
      (t (reason-term-predicate (car rule))))))

; Buckets are accumulated with each bucket's rules reversed. Predicate count
; is bounded, so this structural alist update has a fixed worst-case bucket
; walk rather than an unbounded distinct-predicate walk.
(def reason-index-add-reversed
  (lambda (predicate rule buckets)
    (cond
      ((atom? buckets) (list (list predicate rule)))
      ((eq? predicate (car (car buckets)))
       (cons
         (cons predicate (cons rule (cdr (car buckets))))
         (cdr buckets)))
      (t
       (cons
         (car buckets)
         (reason-index-add-reversed predicate rule (cdr buckets)))))))

(def reason-index-normalize-buckets
  (lambda (buckets)
    (cond
      ((atom? buckets) (quote ()))
      (t
       (cons
         (cons (car (car buckets)) (reverse (cdr (car buckets))))
         (reason-index-normalize-buckets (cdr buckets)))))))

(def reason-index-build-scan
  (lambda (remaining original buckets predicate-count)
    (cond
      ((atom? remaining)
       (list
         *reason-index-schema*
         (quote indexed)
         original
         (reason-index-normalize-buckets buckets)))
      (t
       (let ((predicate (reason-rule-predicate (car remaining))))
         (cond
           ; One non-indexable head is enough to require the exact historical
           ; scan, because that head may unify with predicates outside a bucket.
           ((eq? predicate (quote ())) (reason-index-linear original))
           (t
            (let ((entry (assoc predicate buckets)))
              (cond
                ((atom? entry)
                 (cond
                   ((< predicate-count *reason-index-max-predicates*) 1
                    (reason-index-build-scan
                      (cdr remaining)
                      original
                      (reason-index-add-reversed
                        predicate (car remaining) buckets)
                      (+ predicate-count 1)))
                   ((< predicate-count *reason-index-max-predicates*) 0
                    (reason-index-linear original))))
                (t
                 (reason-index-build-scan
                   (cdr remaining)
                   original
                   (reason-index-add-reversed
                     predicate (car remaining) buckets)
                   predicate-count)))))))))))

(def reason-make-index
  (lambda (rules)
    (reason-index-build-scan rules rules (quote ()) 0)))

(def reason-ensure-index
  (lambda (rules-or-index)
    (cond
      ((reason-index? rules-or-index) rules-or-index)
      (t (reason-make-index rules-or-index)))))

; If indexing is safe, only rules whose head starts with the same predicate
; can unify with this goal. Bucket order is exactly source rule order. Any
; unsafe goal or disabled index returns every original rule unchanged.
(def reason-index-candidates
  (lambda (goal rules-or-index)
    (let ((index (reason-ensure-index rules-or-index)))
      (cond
        ((eq? (reason-index-mode index) (quote linear))
         (reason-index-rules index))
        (t
         (let ((predicate (reason-term-predicate goal)))
           (cond
             ((eq? predicate (quote ())) (reason-index-rules index))
             (t
              (let ((entry (assoc predicate (reason-index-buckets index))))
                (cond
                  ((atom? entry) (quote ()))
                  (t (cdr entry))))))))))))

; Public `reason` accepts either the historical rule list or an already-built
; finite `reason-index/1`. Plain callers are unchanged; repeated-query callers
; may explicitly retain an immutable index snapshot and avoid rebuilding it.
; There is no hidden cache or invalidation: an index continues to describe the
; exact rule list captured when it was constructed.
(def reason
  (lambda (goal rules-or-index)
    (let ((index (reason-ensure-index rules-or-index)))
      (prove-goal
        goal
        (reason-index-candidates goal index)
        (quote ())
        index
        0))))

; Accumulate one rule's result list onto a reversed global accumulator.
; Walking `results` left-to-right and consing each item means `acc` is always
; exactly the reverse of every result seen so far.
(def prove-goal-accumulate
  (lambda (results acc)
    (cond
      ((atom? results) acc)
      (t (prove-goal-accumulate
           (cdr results)
           (cons (car results) acc))))))

; Tail-recursive rule scan. `all-rules` may be a plain historical rule list or
; a B5 reason-index/1. We normalize it once here; recursive body goals then
; reuse the same finite index instead of rebuilding it at every depth.
(def prove-goal
  (lambda (goal rules subst all-rules depth)
    (prove-goal-scan
      goal
      rules
      subst
      (reason-ensure-index all-rules)
      depth
      (quote ()))))

(def prove-goal-scan
  (lambda (goal rules subst all-rules depth acc)
    (cond
      ((atom? rules) (reverse acc))
      (t
       (let ((rule-results
               (prove-rule goal (car rules) subst all-rules depth)))
         (prove-goal-scan
           goal
           (cdr rules)
           subst
           all-rules
           depth
           (prove-goal-accumulate rule-results acc)))))))

; Recursively rename variables in a term to include the depth counter.
(def rename-vars
  (lambda (term depth)
    (cond
      ((atom? term) term)
      ((var? term) (list (quote var) (cons (second term) depth)))
      (t (cons (rename-vars (car term) depth)
               (rename-vars (cdr term) depth))))))

(def map-proofs
  (lambda (f lst)
    (cond
      ((atom? lst) (quote ()))
      (t (cons (f (car lst)) (map-proofs f (cdr lst)))))))

; Try one rule, then wrap every successful body result in its proof node.
(def prove-rule
  (lambda (goal rule subst all-rules depth)
    (let ((renamed-rule (rename-vars rule depth)))
      (let ((new-subst (unify goal (car renamed-rule) subst)))
        (cond
          ((failed-subst? new-subst) (quote ()))
          (t
           (let ((body-results
                   (prove-goals
                     (cdr renamed-rule)
                     new-subst
                     all-rules
                     (+ depth 1))))
             (map-proofs
               (lambda (res)
                 (list
                   (car res)
                   (list
                     (quote proved)
                     goal
                     (car renamed-rule)
                     (cadr res))))
               body-results))))))))

; Prove a conjunction while threading `(subst proofs)` through the shared
; conjunction walker from lib/unify.lisp.
(def prove-goals
  (lambda (goals subst all-rules depth)
    (thread-conjunction
      goals
      (list subst (quote ()))
      (lambda (goal state)
        (prove-goal-state goal state all-rules depth)))))

; A body goal, including `(not P)`, is an ordinary reasoning goal. Historical
; negation-as-failure fabricated `(proved-not P)` merely because P had no proof.
; Under #219/#244 that absence remains Canon 0. Explicit negative evidence may
; still prove `(not P)` through an actual rule/fact whose head is `(not P)`.
(def prove-goal-state
  (lambda (goal state all-rules depth)
    (let ((subst (car state))
          (proofs (second state))
          (index (reason-ensure-index all-rules)))
      (map-goal-results
        (prove-goal
          goal
          (reason-index-candidates goal index)
          subst
          index
          depth)
        proofs))))

(def map-goal-results
  (lambda (results proofs)
    (cond
      ((atom? results) (quote ()))
      (t
       (cons
         (list
           (car (car results))
           (append proofs (list (second (car results)))))
         (map-goal-results (cdr results) proofs))))))

(def explain-proof
  (lambda (proof)
    (explain-proof-node proof 0)))

(def explain-proof-node
  (lambda (node level)
    (cond
      ((eq? (car node) (quote proved))
       (let* ((_2 (print (quote Proved:)))
              (_3 (print (second node)))
              (_4 (print (quote using)))
              (_5 (print (quote rule:)))
              (_6 (print (third node))))
         (explain-proof-list (cadddr node) (+ level 1))))
      ((eq? (car node) (quote proved-not))
       (let* ((_2 (print (quote Proved)))
              (_3 (print (quote by)))
              (_4 (print (quote failure:)))
              (_5 (print (quote not)))
              (_6 (print (second node))))
         (quote ())))
      (t (quote ())))))

(def explain-proof-list
  (lambda (nodes level)
    (cond
      ((atom? nodes) (quote ()))
      (t
       (let* ((_1 (print-indent level))
              (_2 (print (quote |-)))
              (_3 (explain-proof-node (car nodes) level)))
         (explain-proof-list (cdr nodes) level))))))

(def print-indent
  (lambda (level)
    (cond
      ((eq? level 0) (quote ()))
      (t
       (let ((_ (print (quote ..))))
         (print-indent (- level 1)))))))

; Human-facing compatibility explanation. Structured reasoning outcomes are
; provided separately by lib/result-status.lisp / reason-observe.
(def reason-explain
  (lambda (goal rules)
    (let ((results (reason goal rules)))
      (cond
        ((atom? results)
         (let* ((_1 (print (quote Cannot)))
                (_2 (print (quote prove:)))
                (_3 (print goal)))
           (quote ())))
        (t (explain-proof (second (car results))))))))

(def add-usage
  (lambda (entry alist)
    (cond
      ((atom? alist) (list entry))
      ((equal? (car (car alist)) (car entry))
       (cons
         (cons
           (car entry)
           (+ (cdr entry) (cdr (car alist))))
         (cdr alist)))
      (t (cons (car alist) (add-usage entry (cdr alist)))))))

(def merge-usage
  (lambda (a b)
    (cond
      ((atom? a) b)
      (t (merge-usage (cdr a) (add-usage (car a) b))))))

(def count-usage
  (lambda (node)
    (cond
      ((eq? (car node) (quote proved))
       (add-usage
         (cons (third node) 1)
         (count-usage-list (cadddr node))))
      (t (quote ())))))

(def count-usage-list
  (lambda (nodes)
    (cond
      ((atom? nodes) (quote ()))
      (t
       (merge-usage
         (count-usage (car nodes))
         (count-usage-list (cdr nodes)))))))

(def source-of
  (lambda (node)
    (cond
      ((atom? (cadddr node)) (quote fact))
      (t (quote rule)))))

(def provenance
  (lambda (node)
    (cond
      ((eq? (car node) (quote proved))
       (list
         (quote statement)
         (second node)
         (list (quote source) (source-of node))
         (list (quote rule) (third node))
         (list
           (quote derived-from)
           (provenance-list (cadddr node)))))
      (t
       (list
         (quote statement)
         (second node)
         (list (quote source) (quote not-proved)))))))

(def provenance-list
  (lambda (nodes)
    (cond
      ((atom? nodes) (quote ()))
      (t
       (cons
         (provenance (car nodes))
         (provenance-list (cdr nodes)))))))
