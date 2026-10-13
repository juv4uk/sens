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

(0011 *reason-index-schema* (001 reason-index/1))
; 64 структурні комірки-бюджети, без числової арифметики.
; Один НОВИЙ предикат споживає одну комірку, повторний — жодної.
; Це звичайні цитовані дані (64 порожні списки), не 64 функції.
(0011 *reason-index-fuel*
  (001
    (() () () () () () () () () () () () () () () ()
     () () () () () () () () () () () () () () () ()
     () () () () () () () () () () () () () () () ()
     () () () () () () () () () () () () () () () ())))

; Shape: (reason-index/1 indexed|linear ORIGINAL-RULES BUCKETS)
; A bucket is (PREDICATE RULE...), with rules restored to original order.
(0011 reason-index-mode second)
(0011 reason-index-rules third)
(0011 reason-index-buckets fourth)

; Повертаємо точний D1 без обхідного ATOM(QUOTE(...)).
; Перевірка schema лишається D3 EQ виключно після guard ATOM(value).
(0011 reason-index?
  (0010 (value)
    (110
      ((010 value) #d1:0)
      ((0101 value) #d1:0)
      ; CAR(value) can be a compound rule. ATOM guard must precede EQ.
      ((010 (100 value))
       (110
         ((101 (100 value) *reason-index-schema*) #d1:1)
         (#d1:1 #d1:0)))
      (#d1:1 #d1:0))))

; Власний точний D3 пошук кошика: CORE ASSOC у старому профілі
; заходить у CAR(CAR ()) на порожньому alist; тут ніколи не робимо CAR
; до перевірки D3 ATOM. Голова кошика мусить бути атомом.
(0011 міркування-пошук-кошика
  (0010 (predicate buckets)
    (110
      ((010 buckets) (001 ()))
      ((010 (100 buckets)) (001 ()))
      ((010 (100 (100 buckets)))
       (110
         ((101 predicate (100 (100 buckets))) (100 buckets))
         (#d1:1 (міркування-пошук-кошика predicate (011 buckets)))))
      (#d1:1 (001 ())))))

(0011 reason-index-linear
  (0010 (rules)
    (1110 *reason-index-schema* (001 linear) rules (001 ()))))

; Only ordinary predicate-headed compound terms are safe index keys.
; `(var x)` is deliberately excluded: as a logic variable it can unify with
; any rule head and must therefore retain the historical full scan.
(0011 reason-term-predicate
  (0010 (term)
    (110
      
      ((010 term)  (001 ()))
      ((101100100 term) (001 ()))
      
      ((010 (100 term))  (110
         ((110101100 (100 term)) (100 term))
         ))
      )))

(0011 reason-rule-predicate
  (0010 (rule)
    (110
      
      ((010 rule)  (001 ()))
      ((010 ()) (reason-term-predicate (100 rule))))))

; Buckets accumulate reversed source order. Finite structural fuel bounds the
; number of DISTINCT predicates, without unqualified numeric arithmetic.
(0011 reason-index-add-reversed
  (0010 (predicate rule buckets)
    (110
      
      ((010 buckets)  (1110 (1110 predicate rule)))
      ((101 predicate (100 (100 buckets)))
       (111
         (111 predicate (111 rule (011 (100 buckets))))
         (011 buckets)))
      ((010 ())
       (111
         (100 buckets)
         (reason-index-add-reversed predicate rule (011 buckets)))))))

(0011 reason-index-normalize-buckets
  (0010 (buckets)
    (110
      
      ((010 buckets)  (001 ()))
      ((010 ())
       (111
         (111 (100 (100 buckets)) (10100 (011 (100 buckets))))
         (reason-index-normalize-buckets (011 buckets)))))))

(0011 reason-index-build-scan
  (0010 (remaining original buckets fuel)
    (110
      
      ((010 remaining)  (1110
         *reason-index-schema*
         (001 indexed)
         original
         (reason-index-normalize-buckets buckets)))
      ((010 ())
       (001000 ((predicate (reason-rule-predicate (100 remaining))))
         (110
           ; One non-indexable head is enough to require the exact historical
           ; scan, because that head may unify with predicates outside a bucket.
           ((101 predicate (001 ())) (reason-index-linear original))
           ((010 ())
            (001000 ((entry (міркування-пошук-кошика predicate buckets)))
              (110
                
                ; Новий ключ: порожній запас => чесний linear fallback.
                ((010 entry)
                 (110
                   ((010 fuel) (reason-index-linear original))
                   (#d1:1
                    (reason-index-build-scan
                      (011 remaining)
                      original
                      (reason-index-add-reversed
                        predicate (100 remaining) buckets)
                      (011 fuel)))))
                ; Повторений ключ не займає жодного нового біта бюджету.
                (#d1:1
                 (reason-index-build-scan
                   (011 remaining)
                   original
                   (reason-index-add-reversed
                     predicate (100 remaining) buckets)
                   fuel)))))))))))

(0011 reason-make-index
  (0010 (rules)
    (reason-index-build-scan rules rules (001 ()) *reason-index-fuel*)))

(0011 reason-ensure-index
  (0010 (rules-or-index)
    (110
      ((reason-index? rules-or-index) rules-or-index)
      ((010 ()) (reason-make-index rules-or-index)))))

; If indexing is safe, only rules whose head starts with the same predicate
; can unify with this goal. Bucket order is exactly source rule order. Any
; unsafe goal or disabled index returns every original rule unchanged.
(0011 reason-index-candidates
  (0010 (goal rules-or-index)
    (001000 ((index (reason-ensure-index rules-or-index)))
      (110
        ((101 (reason-index-mode index) (001 linear))
         (reason-index-rules index))
        ((010 ())
         (001000 ((predicate (reason-term-predicate goal)))
           (110
             ((101 predicate (001 ())) (reason-index-rules index))
             ((010 ())
              (001000 ((entry (міркування-пошук-кошика predicate (reason-index-buckets index))))
                (110
                  
                  ((010 entry)  (001 ()))
                  ((010 ()) (011 entry))))))))))))

; Public `reason` accepts either the historical rule list or an already-built
; finite `reason-index/1`. Plain callers are unchanged; repeated-query callers
; may explicitly retain an immutable index snapshot and avoid rebuilding it.
; There is no hidden cache or invalidation: an index continues to describe the
; exact rule list captured when it was constructed.
(0011 reason
  (0010 (goal rules-or-index)
    (001000 ((index (reason-ensure-index rules-or-index)))
      (101011011
        goal
        (reason-index-candidates goal index)
        (001 ())
        index
        0))))

; Accumulate one rule's result list onto a reversed global accumulator.
; Walking `results` left-to-right and consing each item means `acc` is always
; exactly the reverse of every result seen so far.
(0011 prove-goal-accumulate
  (0010 (results acc)
    (110
      
      ((010 results)  acc)
      ((010 ()) (prove-goal-accumulate
           (011 results)
           (111 (100 results) acc))))))

; Tail-recursive rule scan. `all-rules` may be a plain historical rule list or
; a B5 reason-index/1. We normalize it once here; recursive body goals then
; reuse the same finite index instead of rebuilding it at every depth.
(0011 prove-goal
  (0010 (goal rules bindings all-rules depth)
    (prove-goal-scan
      goal
      rules
      bindings
      (reason-ensure-index all-rules)
      depth
      (001 ()))))

(0011 prove-goal-scan
  (0010 (goal rules bindings all-rules depth acc)
    (110
      
      ((010 rules)  (10100 acc))
      ((010 ())
       (001000 ((rule-results
               (prove-rule goal (100 rules) bindings all-rules depth)))
         (prove-goal-scan
           goal
           (011 rules)
           bindings
           all-rules
           depth
           (prove-goal-accumulate rule-results acc)))))))

; Recursively rename variables in a term to include the depth counter.
(0011 rename-vars
  (0010 (term depth)
    (110
      
      ((010 term)  term)
      ((101100100 term) (1110 (001 var) (111 (1001 term) depth)))
      ((010 ()) (111 (rename-vars (100 term) depth)
                   (rename-vars (011 term) depth))))))

(0011 map-proofs
  (0010 (f lst)
    (110
      
      ((010 lst)  (001 ()))
      ((010 ()) (111 (f (100 lst)) (map-proofs f (011 lst)))))))

; Try one rule, then wrap every successful body result in its proof node.
(0011 prove-rule
  (0010 (goal rule bindings all-rules depth)
    (001000 ((renamed-rule (rename-vars rule depth)))
      (001000 ((new-subst (101010000 goal (100 renamed-rule) bindings)))
        (110
          ((failed-subst? new-subst) (001 ()))
          ((010 ())
           (001000 ((body-results
                   (101010001
                     (011 renamed-rule)
                     new-subst
                     all-rules
                     (01010 depth 1))))
             (map-proofs
               (0010 (res)
                 (1110
                   (100 res)
                   (1110
                     (001 proved)
                     goal
                     (100 renamed-rule)
                     (1001 res))))
               body-results))))))))

; Prove a conjunction while threading `(subst proofs)` through the shared
; conjunction walker from lib/unify.lisp.
(0011 prove-goals
  (0010 (goals bindings all-rules depth)
    (thread-conjunction
      goals
      (1110 bindings (001 ()))
      (0010 (goal state)
        (prove-goal-state goal state all-rules depth)))))

; A body goal, including `(not P)`, is an ordinary reasoning goal. Historical
; negation-as-failure fabricated `(proved-not P)` merely because P had no proof.
; Under #219/#244 that absence remains Canon 0. Explicit negative evidence may
; still prove `(not P)` through an actual rule/fact whose head is `(not P)`.
(0011 prove-goal-state
  (0010 (goal state all-rules depth)
    (001000 ((bindings (100 state))
          (proofs (1001 state))
          (index (reason-ensure-index all-rules)))
      (map-goal-results
        (101011011
          goal
          (reason-index-candidates goal index)
          bindings
          index
          depth)
        proofs))))

(0011 map-goal-results
  (0010 (results proofs)
    (110
      
      ((010 results)  (001 ()))
      ((010 ())
       (111
         (1110
           (100 (100 results))
           (1111 proofs (1110 (1001 (100 results)))))
         (map-goal-results (011 results) proofs))))))

(0011 explain-proof
  (0010 (proof)
    (explain-proof-node proof 0)))

(0011 explain-proof-node
  (0010 (node level)
    (110
      ((101 (100 node) (001 proved))
       (001001 ((_2 (11011011 (001 Proved:)))
              (_3 (11011011 (1001 node)))
              (_4 (11011011 (001 using)))
              (_5 (11011011 (001 rule:)))
              (_6 (11011011 (10011 node))))
         (explain-proof-list (100111 node) (01010 level 1))))
      ((101 (100 node) (001 proved-not))
       (001001 ((_2 (11011011 (001 Proved)))
              (_3 (11011011 (001 by)))
              (_4 (11011011 (001 failure:)))
              (_5 (11011011 (001 not)))
              (_6 (11011011 (1001 node))))
         (001 ())))
      )))

(0011 explain-proof-list
  (0010 (nodes level)
    (110
      
      ((010 nodes)  (001 ()))
      ((010 ())
       (001001 ((_1 (print-indent level))
              (_2 (11011011 (001 |-)))
              (_3 (explain-proof-node (100 nodes) level)))
         (explain-proof-list (011 nodes) level))))))

(0011 print-indent
  (0010 (level)
    (110
      ((101 level 0) (001 ()))
      ((010 ())
       (001000 ((_ (11011011 (001 ..))))
         (print-indent (01011 level 1)))))))

; Human-facing compatibility explanation. Structured reasoning outcomes are
; provided separately by lib/result-status.lisp / reason-observe.
(0011 reason-explain
  (0010 (goal rules)
    (001000 ((results (101001110 goal rules)))
      (110
        
        ((010 results)  (001001 ((_1 (11011011 (001 Cannot)))
                (_2 (11011011 (001 prove:)))
                (_3 (11011011 goal)))
           (001 ())))
        ((010 ()) (101001011 (1001 (100 results))))))))

(0011 add-usage
  (0010 (entry alist)
    (110
      
      ((010 alist)  (1110 entry))
      ((unify-equal? (100 (100 alist)) (100 entry))
       (111
         (111
           (100 entry)
           (01010 (011 entry) (011 (100 alist))))
         (011 alist)))
      ((010 ()) (111 (100 alist) (add-usage entry (011 alist)))))))

(0011 merge-usage
  (0010 (a b)
    (110
      
      ((010 a)  b)
      ((010 ()) (merge-usage (011 a) (add-usage (100 a) b))))))

(0011 count-usage
  (0010 (node)
    (110
      ((101 (100 node) (001 proved))
       (add-usage
         (111 (10011 node) 1)
         (count-usage-list (100111 node))))
      )))

(0011 count-usage-list
  (0010 (nodes)
    (110
      
      ((010 nodes)  (001 ()))
      ((010 ())
       (merge-usage
         (count-usage (100 nodes))
         (count-usage-list (011 nodes)))))))

(0011 source-of
  (0010 (node)
    (110
      
      ((010 (100111 node))  (001 fact))
      ((010 ()) (001 rule)))))

(0011 provenance
  (0010 (node)
    (110
      ((101 (100 node) (001 proved))
       (1110
         (001 statement)
         (1001 node)
         (1110 (001 source) (101110000 node))
         (1110 (001 rule) (10011 node))
         (1110
           (001 derived-from)
           (provenance-list (100111 node)))))
      ((010 ())
       (1110
         (001 statement)
         (1001 node)
         (1110 (001 source) (001 not-proved)))))))

(0011 provenance-list
  (0010 (nodes)
    (110
      
      ((010 nodes)  (001 ()))
      ((010 ())
       (111
         (101101111 (100 nodes))
         (provenance-list (011 nodes)))))))
