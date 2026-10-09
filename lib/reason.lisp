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
      ((00000010 value) () (00000001 ()))
      ((00000010 value) (1) (00000001 ()))
      ((00000010 (00000101 value)) () (00000111
         ((00000011 (00000101 value) *reason-index-schema*) t)
         (t (00000001 ()))))
      ((00000010 (00000101 value)) (1) (00000111
         ((00000011 (00000101 value) *reason-index-schema*) t)
         (t (00000001 ()))))
      (t (00000001 ())))))

(00001011 reason-index-linear
  (00001000 (rules)
    (00100111 *reason-index-schema* (00000001 linear) rules (00000001 ()))))

; Only ordinary predicate-headed compound terms are safe index keys.
; `(var x)` is deliberately excluded: as a logic variable it can unify with
; any rule head and must therefore retain the historical full scan.
(00001011 reason-term-predicate
  (00001000 (term)
    (00000111
      ((00000010 term) () (00000001 ()))
      ((00000010 term) (1) (00000001 ()))
      ((10001001 term) (00000001 ()))
      ((00000010 (00000101 term)) () (00000111
         ((00100011 (00000101 term)) (00000101 term))
         (t (00000001 ()))))
      ((00000010 (00000101 term)) (1) (00000111
         ((00100011 (00000101 term)) (00000101 term))
         (t (00000001 ()))))
      (t (00000001 ())))))

(00001011 reason-rule-predicate
  (00001000 (rule)
    (00000111
      ((00000010 rule) () (00000001 ()))
      ((00000010 rule) (1) (00000001 ()))
      (t (reason-term-predicate (00000101 rule))))))

; Buckets are accumulated with each bucket's rules reversed. Predicate count
; is bounded, so this structural alist update has a fixed worst-case bucket
; walk rather than an unbounded distinct-predicate walk.
(00001011 reason-index-add-reversed
  (00001000 (predicate rule buckets)
    (00000111
      ((00000010 buckets) () (00100111 (00100111 predicate rule)))
      ((00000010 buckets) (1) (00100111 (00100111 predicate rule)))
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
      ((00000010 buckets) () (00000001 ()))
      ((00000010 buckets) (1) (00000001 ()))
      (t
       (00000100
         (00000100 (00000101 (00000101 buckets)) (00101010 (00000110 (00000101 buckets))))
         (reason-index-normalize-buckets (00000110 buckets)))))))

(00001011 reason-index-build-scan
  (00001000 (remaining original buckets predicate-count)
    (00000111
      ((00000010 remaining) () (00100111
         *reason-index-schema*
         (00000001 indexed)
         original
         (reason-index-normalize-buckets buckets)))
      ((00000010 remaining) (1) (00100111
         *reason-index-schema*
         (00000001 indexed)
         original
         (reason-index-normalize-buckets buckets)))
      (t
       (10011100 ((predicate (reason-rule-predicate (00000101 remaining))))
         (00000111
           ; One non-indexable head is enough to require the exact historical
           ; scan, because that head may unify with predicates outside a bucket.
           ((00000011 predicate (00000001 ())) (reason-index-linear original))
           (t
            (10011100 ((entry (00101101 predicate buckets)))
              (00000111
                ((00000010 entry) () (00000111
                   ((00011010 predicate-count *reason-index-max-predicates*)
                    (reason-index-build-scan
                      (00000110 remaining)
                      original
                      (reason-index-add-reversed
                        predicate (00000101 remaining) buckets)
                      (00001100 predicate-count 1)))
                   ((00100010
                      (00011010 predicate-count *reason-index-max-predicates*)
                      (00000010 (00000001 (x))))
                    (reason-index-linear original))))
                ((00000010 entry) (1) (00000111
                   ((00011010 predicate-count *reason-index-max-predicates*)
                    (reason-index-build-scan
                      (00000110 remaining)
                      original
                      (reason-index-add-reversed
                        predicate (00000101 remaining) buckets)
                      (00001100 predicate-count 1)))
                   ((00100010
                      (00011010 predicate-count *reason-index-max-predicates*)
                      (00000010 (00000001 (x))))
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
    (10011100 ((index (reason-ensure-index rules-or-index)))
      (00000111
        ((00000011 (reason-index-mode index) (00000001 linear))
         (reason-index-rules index))
        (t
         (10011100 ((predicate (reason-term-predicate goal)))
           (00000111
             ((00000011 predicate (00000001 ())) (reason-index-rules index))
             (t
              (10011100 ((entry (00101101 predicate (reason-index-buckets index))))
                (00000111
                  ((00000010 entry) () (00000001 ()))
                  ((00000010 entry) (1) (00000001 ()))
                  (t (00000110 entry))))))))))))

; Public `reason` accepts either the historical rule list or an already-built
; finite `reason-index/1`. Plain callers are unchanged; repeated-query callers
; may explicitly retain an immutable index snapshot and avoid rebuilding it.
; There is no hidden cache or invalidation: an index continues to describe the
; exact rule list captured when it was constructed.
(00001011 reason
  (00001000 (goal rules-or-index)
    (10011100 ((index (reason-ensure-index rules-or-index)))
      (10000000
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
      ((00000010 results) () acc)
      ((00000010 results) (1) acc)
      (t (prove-goal-accumulate
           (00000110 results)
           (00000100 (00000101 results) acc))))))

; Tail-recursive rule scan. `all-rules` may be a plain historical rule list or
; a B5 reason-index/1. We normalize it once here; recursive body goals then
; reuse the same finite index instead of rebuilding it at every depth.
(00001011 prove-goal
  (00001000 (goal rules bindings all-rules depth)
    (prove-goal-scan
      goal
      rules
      bindings
      (reason-ensure-index all-rules)
      depth
      (00000001 ()))))

(00001011 prove-goal-scan
  (00001000 (goal rules bindings all-rules depth acc)
    (00000111
      ((00000010 rules) () (00101010 acc))
      ((00000010 rules) (1) (00101010 acc))
      (t
       (10011100 ((rule-results
               (prove-rule goal (00000101 rules) bindings all-rules depth)))
         (prove-goal-scan
           goal
           (00000110 rules)
           bindings
           all-rules
           depth
           (prove-goal-accumulate rule-results acc)))))))

; Recursively rename variables in a term to include the depth counter.
(00001011 rename-vars
  (00001000 (term depth)
    (00000111
      ((00000010 term) () term)
      ((00000010 term) (1) term)
      ((10001001 term) (00100111 (00000001 var) (00000100 (00101111 term) depth)))
      (t (00000100 (rename-vars (00000101 term) depth)
                   (rename-vars (00000110 term) depth))))))

(00001011 map-proofs
  (00001000 (f lst)
    (00000111
      ((00000010 lst) () (00000001 ()))
      ((00000010 lst) (1) (00000001 ()))
      (t (00000100 (f (00000101 lst)) (map-proofs f (00000110 lst)))))))

; Try one rule, then wrap every successful body result in its proof node.
(00001011 prove-rule
  (00001000 (goal rule bindings all-rules depth)
    (10011100 ((renamed-rule (rename-vars rule depth)))
      (10011100 ((new-subst (10000111 goal (00000101 renamed-rule) bindings)))
        (00000111
          ((failed-subst? new-subst) (00000001 ()))
          (t
           (10011100 ((body-results
                   (10000001
                     (00000110 renamed-rule)
                     new-subst
                     all-rules
                     (00001100 depth 1))))
             (map-proofs
               (00001000 (res)
                 (00100111
                   (00000101 res)
                   (00100111
                     (00000001 proved)
                     goal
                     (00000101 renamed-rule)
                     (00110100 res))))
               body-results))))))))

; Prove a conjunction while threading `(subst proofs)` through the shared
; conjunction walker from lib/unify.lisp.
(00001011 prove-goals
  (00001000 (goals bindings all-rules depth)
    (thread-conjunction
      goals
      (00100111 bindings (00000001 ()))
      (00001000 (goal state)
        (prove-goal-state goal state all-rules depth)))))

; A body goal, including `(not P)`, is an ordinary reasoning goal. Historical
; negation-as-failure fabricated `(proved-not P)` merely because P had no proof.
; Under #219/#244 that absence remains Canon 0. Explicit negative evidence may
; still prove `(not P)` through an actual rule/fact whose head is `(not P)`.
(00001011 prove-goal-state
  (00001000 (goal state all-rules depth)
    (10011100 ((bindings (00000101 state))
          (proofs (00101111 state))
          (index (reason-ensure-index all-rules)))
      (map-goal-results
        (10000000
          goal
          (reason-index-candidates goal index)
          bindings
          index
          depth)
        proofs))))

(00001011 map-goal-results
  (00001000 (results proofs)
    (00000111
      ((00000010 results) () (00000001 ()))
      ((00000010 results) (1) (00000001 ()))
      (t
       (00000100
         (00100111
           (00000101 (00000101 results))
           (00101001 proofs (00100111 (00101111 (00000101 results)))))
         (map-goal-results (00000110 results) proofs))))))

(00001011 explain-proof
  (00001000 (proof)
    (explain-proof-node proof 0)))

(00001011 explain-proof-node
  (00001000 (node level)
    (00000111
      ((00000011 (00000101 node) (00000001 proved))
       (10011101 ((_2 (01001000 (00000001 Proved:)))
              (_3 (01001000 (00101111 node)))
              (_4 (01001000 (00000001 using)))
              (_5 (01001000 (00000001 rule:)))
              (_6 (01001000 (00110000 node))))
         (explain-proof-list (00110110 node) (00001100 level 1))))
      ((00000011 (00000101 node) (00000001 proved-not))
       (10011101 ((_2 (01001000 (00000001 Proved)))
              (_3 (01001000 (00000001 by)))
              (_4 (01001000 (00000001 failure:)))
              (_5 (01001000 (00000001 not)))
              (_6 (01001000 (00101111 node))))
         (00000001 ())))
      (t (00000001 ())))))

(00001011 explain-proof-list
  (00001000 (nodes level)
    (00000111
      ((00000010 nodes) () (00000001 ()))
      ((00000010 nodes) (1) (00000001 ()))
      (t
       (10011101 ((_1 (print-indent level))
              (_2 (01001000 (00000001 |-)))
              (_3 (explain-proof-node (00000101 nodes) level)))
         (explain-proof-list (00000110 nodes) level))))))

(00001011 print-indent
  (00001000 (level)
    (00000111
      ((00000011 level 0) (00000001 ()))
      (t
       (10011100 ((_ (01001000 (00000001 ..))))
         (print-indent (00001101 level 1)))))))

; Human-facing compatibility explanation. Structured reasoning outcomes are
; provided separately by lib/result-status.lisp / reason-observe.
(00001011 reason-explain
  (00001000 (goal rules)
    (10011100 ((results (10000101 goal rules)))
      (00000111
        ((00000010 results) () (10011101 ((_1 (01001000 (00000001 Cannot)))
                (_2 (01001000 (00000001 prove:)))
                (_3 (01001000 goal)))
           (00000001 ())))
        ((00000010 results) (1) (10011101 ((_1 (01001000 (00000001 Cannot)))
                (_2 (01001000 (00000001 prove:)))
                (_3 (01001000 goal)))
           (00000001 ())))
        (t (10000010 (00101111 (00000101 results))))))))

(00001011 add-usage
  (00001000 (entry alist)
    (00000111
      ((00000010 alist) () (00100111 entry))
      ((00000010 alist) (1) (00100111 entry))
      ((00100010 (00000101 (00000101 alist)) (00000101 entry))
       (00000100
         (00000100
           (00000101 entry)
           (00001100 (00000110 entry) (00000110 (00000101 alist))))
         (00000110 alist)))
      (t (00000100 (00000101 alist) (add-usage entry (00000110 alist)))))))

(00001011 merge-usage
  (00001000 (a b)
    (00000111
      ((00000010 a) () b)
      ((00000010 a) (1) b)
      (t (merge-usage (00000110 a) (add-usage (00000101 a) b))))))

(00001011 count-usage
  (00001000 (node)
    (00000111
      ((00000011 (00000101 node) (00000001 proved))
       (add-usage
         (00000100 (00110000 node) 1)
         (count-usage-list (00110110 node))))
      (t (00000001 ())))))

(00001011 count-usage-list
  (00001000 (nodes)
    (00000111
      ((00000010 nodes) () (00000001 ()))
      ((00000010 nodes) (1) (00000001 ()))
      (t
       (merge-usage
         (count-usage (00000101 nodes))
         (count-usage-list (00000110 nodes)))))))

(00001011 source-of
  (00001000 (node)
    (00000111
      ((00000010 (00110110 node)) () (00000001 fact))
      ((00000010 (00110110 node)) (1) (00000001 fact))
      (t (00000001 rule)))))

(00001011 provenance
  (00001000 (node)
    (00000111
      ((00000011 (00000101 node) (00000001 proved))
       (00100111
         (00000001 statement)
         (00101111 node)
         (00100111 (00000001 source) (10000011 node))
         (00100111 (00000001 rule) (00110000 node))
         (00100111
           (00000001 derived-from)
           (provenance-list (00110110 node)))))
      (t
       (00100111
         (00000001 statement)
         (00101111 node)
         (00100111 (00000001 source) (00000001 not-proved)))))))

(00001011 provenance-list
  (00001000 (nodes)
    (00000111
      ((00000010 nodes) () (00000001 ()))
      ((00000010 nodes) (1) (00000001 ()))
      (t
       (00000100
         (10000100 (00000101 nodes))
         (provenance-list (00000110 nodes)))))))
