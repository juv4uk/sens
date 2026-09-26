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

(00001011 *reason-index-schema* (00000001 reason-index/1))
(00001011 *reason-index-max-predicates* 64)

; Shape: (reason-index/1 indexed|linear ORIGINAL-RULES BUCKETS)
; A bucket is (PREDICATE RULE...), with rules restored to original order.
(00001011 reason-index-mode second)
(00001011 reason-index-rules third)
(00001011 reason-index-buckets fourth)

(00001011 reason-index?
  (00001000 (value)
    (00000111
      ((00000010 value) (00000001 ()))
      ((00000010 (00000101 value))
       (00000111
         ((00000011 (00000101 value) *reason-index-schema*) t)
         (t (00000001 ()))))
      (t (00000001 ())))))

(00001011 reason-index-linear
  (00001000 (rules)
    (list *reason-index-schema* (00000001 linear) rules (00000001 ()))))

; Only ordinary predicate-headed compound terms are safe index keys.
; `(var x)` is deliberately excluded: as a logic variable it can unify with
; any rule head and must therefore retain the historical full scan.
(00001011 reason-term-predicate
  (00001000 (term)
    (00000111
      ((00000010 term) (00000001 ()))
      ((var? term) (00000001 ()))
      ((00000010 (00000101 term))
       (00000111
         ((symbol? (00000101 term)) (00000101 term))
         (t (00000001 ()))))
      (t (00000001 ())))))

(00001011 reason-rule-predicate
  (00001000 (rule)
    (00000111
      ((00000010 rule) (00000001 ()))
      (t (reason-term-predicate (00000101 rule))))))

; Buckets are accumulated with each bucket's rules reversed. Predicate count
; is bounded, so this structural alist update has a fixed worst-case bucket
; walk rather than an unbounded distinct-predicate walk.
(00001011 reason-index-add-reversed
  (00001000 (predicate rule buckets)
    (00000111
      ((00000010 buckets) (list (list predicate rule)))
      ((00000011 predicate (00000101 (00000101 buckets)))
       (00000100
         (00000100 predicate (00000100 rule (00000110 (00000101 buckets))))
         (00000110 buckets)))
      (t
       (00000100
         (00000101 buckets)
         (reason-index-add-reversed predicate rule (00000110 buckets)))))))

(00001011 reason-index-normalize-buckets
  (00001000 (buckets)
    (00000111
      ((00000010 buckets) (00000001 ()))
      (t
       (00000100
         (00000100 (00000101 (00000101 buckets)) (reverse (00000110 (00000101 buckets))))
         (reason-index-normalize-buckets (00000110 buckets)))))))

(00001011 reason-index-build-scan
  (00001000 (remaining original buckets predicate-count)
    (00000111
      ((00000010 remaining)
       (list
         *reason-index-schema*
         (00000001 indexed)
         original
         (reason-index-normalize-buckets buckets)))
      (t
       (let ((predicate (reason-rule-predicate (00000101 remaining))))
         (00000111
           ; One non-indexable head is enough to require the exact historical
           ; scan, because that head may unify with predicates outside a bucket.
           ((00000011 predicate (00000001 ())) (reason-index-linear original))
           (t
            (let ((entry (assoc predicate buckets)))
              (00000111
                ((00000010 entry)
                 (00000111
                   ((< predicate-count *reason-index-max-predicates*) 1
                    (reason-index-build-scan
                      (00000110 remaining)
                      original
                      (reason-index-add-reversed
                        predicate (00000101 remaining) buckets)
                      (00001100 predicate-count 1)))
                   ((< predicate-count *reason-index-max-predicates*) 0
                    (reason-index-linear original))))
                (t
                 (reason-index-build-scan
                   (00000110 remaining)
                   original
                   (reason-index-add-reversed
                     predicate (00000101 remaining) buckets)
                   predicate-count)))))))))))

(00001011 reason-make-index
  (00001000 (rules)
    (reason-index-build-scan rules rules (00000001 ()) 0)))

(00001011 reason-ensure-index
  (00001000 (rules-or-index)
    (00000111
      ((reason-index? rules-or-index) rules-or-index)
      (t (reason-make-index rules-or-index)))))

; If indexing is safe, only rules whose head starts with the same predicate
; can unify with this goal. Bucket order is exactly source rule order. Any
; unsafe goal or disabled index returns every original rule unchanged.
(00001011 reason-index-candidates
  (00001000 (goal rules-or-index)
    (let ((index (reason-ensure-index rules-or-index)))
      (00000111
        ((00000011 (reason-index-mode index) (00000001 linear))
         (reason-index-rules index))
        (t
         (let ((predicate (reason-term-predicate goal)))
           (00000111
             ((00000011 predicate (00000001 ())) (reason-index-rules index))
             (t
              (let ((entry (assoc predicate (reason-index-buckets index))))
                (00000111
                  ((00000010 entry) (00000001 ()))
                  (t (00000110 entry))))))))))))

; Public `reason` accepts either the historical rule list or an already-built
; finite `reason-index/1`. Plain callers are unchanged; repeated-query callers
; may explicitly retain an immutable index snapshot and avoid rebuilding it.
; There is no hidden cache or invalidation: an index continues to describe the
; exact rule list captured when it was constructed.
(00001011 reason
  (00001000 (goal rules-or-index)
    (let ((index (reason-ensure-index rules-or-index)))
      (prove-goal
        goal
        (reason-index-candidates goal index)
        (00000001 ())
        index
        0))))

; Accumulate one rule's result list onto a reversed global accumulator.
; Walking `results` left-to-right and consing each item means `acc` is always
; exactly the reverse of every result seen so far.
(00001011 prove-goal-accumulate
  (00001000 (results acc)
    (00000111
      ((00000010 results) acc)
      (t (prove-goal-accumulate
           (00000110 results)
           (00000100 (00000101 results) acc))))))

; Tail-recursive rule scan. `all-rules` may be a plain historical rule list or
; a B5 reason-index/1. We normalize it once here; recursive body goals then
; reuse the same finite index instead of rebuilding it at every depth.
(00001011 prove-goal
  (00001000 (goal rules subst all-rules depth)
    (prove-goal-scan
      goal
      rules
      subst
      (reason-ensure-index all-rules)
      depth
      (00000001 ()))))

(00001011 prove-goal-scan
  (00001000 (goal rules subst all-rules depth acc)
    (00000111
      ((00000010 rules) (reverse acc))
      (t
       (let ((rule-results
               (prove-rule goal (00000101 rules) subst all-rules depth)))
         (prove-goal-scan
           goal
           (00000110 rules)
           subst
           all-rules
           depth
           (prove-goal-accumulate rule-results acc)))))))

; Recursively rename variables in a term to include the depth counter.
(00001011 rename-vars
  (00001000 (term depth)
    (00000111
      ((00000010 term) term)
      ((var? term) (list (00000001 var) (00000100 (second term) depth)))
      (t (00000100 (rename-vars (00000101 term) depth)
                   (rename-vars (00000110 term) depth))))))

(00001011 map-proofs
  (00001000 (f lst)
    (00000111
      ((00000010 lst) (00000001 ()))
      (t (00000100 (f (00000101 lst)) (map-proofs f (00000110 lst)))))))

; Try one rule, then wrap every successful body result in its proof node.
(00001011 prove-rule
  (00001000 (goal rule subst all-rules depth)
    (let ((renamed-rule (rename-vars rule depth)))
      (let ((new-subst (unify goal (00000101 renamed-rule) subst)))
        (00000111
          ((failed-subst? new-subst) (00000001 ()))
          (t
           (let ((body-results
                   (prove-goals
                     (00000110 renamed-rule)
                     new-subst
                     all-rules
                     (00001100 depth 1))))
             (map-proofs
               (00001000 (res)
                 (list
                   (00000101 res)
                   (list
                     (00000001 proved)
                     goal
                     (00000101 renamed-rule)
                     (cadr res))))
               body-results))))))))

; Prove a conjunction while threading `(subst proofs)` through the shared
; conjunction walker from lib/unify.lisp.
(00001011 prove-goals
  (00001000 (goals subst all-rules depth)
    (thread-conjunction
      goals
      (list subst (00000001 ()))
      (00001000 (goal state)
        (prove-goal-state goal state all-rules depth)))))

; A body goal, including `(not P)`, is an ordinary reasoning goal. Historical
; negation-as-failure fabricated `(proved-not P)` merely because P had no proof.
; Under #219/#244 that absence remains Canon 0. Explicit negative evidence may
; still prove `(not P)` through an actual rule/fact whose head is `(not P)`.
(00001011 prove-goal-state
  (00001000 (goal state all-rules depth)
    (let ((subst (00000101 state))
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

(00001011 map-goal-results
  (00001000 (results proofs)
    (00000111
      ((00000010 results) (00000001 ()))
      (t
       (00000100
         (list
           (00000101 (00000101 results))
           (append proofs (list (second (00000101 results)))))
         (map-goal-results (00000110 results) proofs))))))

(00001011 explain-proof
  (00001000 (proof)
    (explain-proof-node proof 0)))

(00001011 explain-proof-node
  (00001000 (node level)
    (00000111
      ((00000011 (00000101 node) (00000001 proved))
       (let* ((_2 (print (00000001 Proved:)))
              (_3 (print (second node)))
              (_4 (print (00000001 using)))
              (_5 (print (00000001 rule:)))
              (_6 (print (third node))))
         (explain-proof-list (cadddr node) (00001100 level 1))))
      ((00000011 (00000101 node) (00000001 proved-not))
       (let* ((_2 (print (00000001 Proved)))
              (_3 (print (00000001 by)))
              (_4 (print (00000001 failure:)))
              (_5 (print (00000001 not)))
              (_6 (print (second node))))
         (00000001 ())))
      (t (00000001 ())))))

(00001011 explain-proof-list
  (00001000 (nodes level)
    (00000111
      ((00000010 nodes) (00000001 ()))
      (t
       (let* ((_1 (print-indent level))
              (_2 (print (00000001 |-)))
              (_3 (explain-proof-node (00000101 nodes) level)))
         (explain-proof-list (00000110 nodes) level))))))

(00001011 print-indent
  (00001000 (level)
    (00000111
      ((00000011 level 0) (00000001 ()))
      (t
       (let ((_ (print (00000001 ..))))
         (print-indent (00001101 level 1)))))))

; Human-facing compatibility explanation. Structured reasoning outcomes are
; provided separately by lib/result-status.lisp / reason-observe.
(00001011 reason-explain
  (00001000 (goal rules)
    (let ((results (reason goal rules)))
      (00000111
        ((00000010 results)
         (let* ((_1 (print (00000001 Cannot)))
                (_2 (print (00000001 prove:)))
                (_3 (print goal)))
           (00000001 ())))
        (t (explain-proof (second (00000101 results))))))))

(00001011 add-usage
  (00001000 (entry alist)
    (00000111
      ((00000010 alist) (list entry))
      ((equal? (00000101 (00000101 alist)) (00000101 entry))
       (00000100
         (00000100
           (00000101 entry)
           (00001100 (00000110 entry) (00000110 (00000101 alist))))
         (00000110 alist)))
      (t (00000100 (00000101 alist) (add-usage entry (00000110 alist)))))))

(00001011 merge-usage
  (00001000 (a b)
    (00000111
      ((00000010 a) b)
      (t (merge-usage (00000110 a) (add-usage (00000101 a) b))))))

(00001011 count-usage
  (00001000 (node)
    (00000111
      ((00000011 (00000101 node) (00000001 proved))
       (add-usage
         (00000100 (third node) 1)
         (count-usage-list (cadddr node))))
      (t (00000001 ())))))

(00001011 count-usage-list
  (00001000 (nodes)
    (00000111
      ((00000010 nodes) (00000001 ()))
      (t
       (merge-usage
         (count-usage (00000101 nodes))
         (count-usage-list (00000110 nodes)))))))

(00001011 source-of
  (00001000 (node)
    (00000111
      ((00000010 (cadddr node)) (00000001 fact))
      (t (00000001 rule)))))

(00001011 provenance
  (00001000 (node)
    (00000111
      ((00000011 (00000101 node) (00000001 proved))
       (list
         (00000001 statement)
         (second node)
         (list (00000001 source) (source-of node))
         (list (00000001 rule) (third node))
         (list
           (00000001 derived-from)
           (provenance-list (cadddr node)))))
      (t
       (list
         (00000001 statement)
         (second node)
         (list (00000001 source) (00000001 not-proved)))))))

(00001011 provenance-list
  (00001000 (nodes)
    (00000111
      ((00000010 nodes) (00000001 ()))
      (t
       (00000100
         (provenance (00000101 nodes))
         (provenance-list (00000110 nodes)))))))
