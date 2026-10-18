; reason.lisp — backward-chaining Advice Taker inference engine.
; Unconditional COND fallbacks are exact D1:1, never synthetic D3 ATOM(()) truth.
; Rules are `(head . body)`. `reason` preserves its historical public result:
; a list of `(substitution proof)` pairs, or `()` when no proof is found.
;
; B5 indexing remains ordinary finite Lisp data. A rule set is indexed only
; when every rule head and the current goal have a safely observable symbol
; predicate. Variable heads/goals and other unusual historical shapes fall
; back to the exact linear scan. The small alist index is also capped at 64
; distinct predicates so an adversarial unique-predicate corpus cannot turn
; index construction into an unbounded O(N^2) walk.

(визначити *reason-index-schema* (як-є reason-index/1))
; 64 структурні комірки-бюджети, без числової арифметики.
; Один НОВИЙ предикат споживає одну комірку, повторний — жодної.
; Це звичайні цитовані дані (64 порожні списки), не 64 функції.
(визначити *reason-index-fuel*
  (як-є
    (() () () () () () () () () () () () () () () ()
     () () () () () () () () () () () () () () () ()
     () () () () () () () () () () () () () () () ()
     () () () () () () () () () () () () () () () ())))

; Shape: (reason-index/1 indexed|linear ORIGINAL-RULES BUCKETS)
; A bucket is (PREDICATE RULE...), with rules restored to original order.
; D4:1001 CADR, D5:10011 CADDR, D3:011 CDR: no named selector alias.
; Canonical index schema: (schema mode original-rules buckets).
; D6:100111 CADDDR is ratified data, not silently callable here.
(визначити reason-index-mode
  (функція (index)
    (друге index)))
(визначити reason-index-rules
  (функція (index)
    (третє index)))
(визначити reason-index-buckets
  (функція (index)
    (третє (решта index))))

; Повертаємо точний D1 без обхідного ATOM(QUOTE(...)).
; Перевірка schema лишається D3 EQ виключно після guard ATOM(value).
(визначити reason-index?
  (функція (value)
    (за-умовою
      ((атом? value) ні)
      ((порожній? value) ні)
      ; An ordinary rule list can start with a compound CAR.
      ; D3 EQ accepts atoms only, so establish ATOM(CAR(value)) first.
      ((атом? (перше value))
       (за-умовою
         ((тотожне? (перше value) *reason-index-schema*) так)
         (так ні)))
      (так ні))))

; Власний точний D3 пошук кошика: CORE ASSOC у старому профілі
; заходить у CAR(CAR ()) на порожньому alist; тут ніколи не робимо CAR
; до перевірки D3 ATOM. Голова кошика мусить бути атомом.
; Nested pair selectors use ratified exact D4, not repeated D3 chains:
; D4:1000 CAAR = CAR(CAR), D4:0110 CDAR = CDR(CAR).
; These are admitted call heads; D7 is text/data only.

(визначити міркування-пошук-кошика
  (функція (predicate buckets)
    (за-умовою
      ((атом? buckets) (як-є ()))
      ((атом? (перше buckets)) (як-є ()))
      ((атом? (перше-першого buckets))
       (за-умовою
         ((тотожне? predicate (перше-першого buckets)) (перше buckets))
         (так (міркування-пошук-кошика predicate (решта buckets)))))
      (так (як-є ())))))

(визначити reason-index-linear
  (функція (rules)
    (список *reason-index-schema* (як-є linear) rules (як-є ()))))

; Only ordinary predicate-headed compound terms are safe index keys.
; `(var x)` is deliberately excluded: as a logic variable it can unify with
; any rule head and must therefore retain the historical full scan.
; Власний D3-предикат змінної, без непрозорого SID8 або D9-виклику.
; EQ приймає лише атоми: тому спочатку ATOM(term), потім ATOM(CAR(term)).
(визначити reason-var-form?
  (функція (term)
    (за-умовою
      ((атом? term) ні)
      ((атом? (перше term))
       (за-умовою
         ((тотожне? (перше term) (як-є var)) так)
         (так ні)))
      (так ні))))

; Невідомі/складені голови залишаються на лінійному шляху.
(визначити reason-term-predicate
  (функція (term)
    (за-умовою
      ((атом? term) (як-є ()))
      ((reason-var-form? term) (як-є ()))
      ((атом? (перше term)) (перше term))
      (так (як-є ())))))

(визначити reason-rule-predicate
  (функція (rule)
    (за-умовою
      
      ((атом? rule)  (як-є ()))
      (так (reason-term-predicate (перше rule))))))

; Buckets accumulate reversed source order. Finite structural fuel bounds the
; number of DISTINCT predicates, without unqualified numeric arithmetic.
(визначити reason-index-add-reversed
  (функція (predicate rule buckets)
    (за-умовою
      
      ((атом? buckets)  (список (список predicate rule)))
      ((тотожне? predicate (перше-першого buckets))
       (сполучити
         (сполучити predicate (сполучити rule (решта-першого buckets)))
         (решта buckets)))
      (так
       (сполучити
         (перше buckets)
         (reason-index-add-reversed predicate rule (решта buckets)))))))

(визначити reason-index-normalize-buckets
  (функція (buckets)
    (за-умовою
      
      ((атом? buckets)  (як-є ()))
      (так
       (сполучити
         (сполучити (перше-першого buckets) (зворот (решта-першого buckets)))
         (reason-index-normalize-buckets (решта buckets)))))))

(визначити reason-index-build-scan
  (функція (remaining original buckets fuel)
    (за-умовою
      
      ((атом? remaining)  (список
         *reason-index-schema*
         (як-є indexed)
         original
         (reason-index-normalize-buckets buckets)))
      (так
       (нехай ((predicate (reason-rule-predicate (перше remaining))))
         (за-умовою
           ; One non-indexable head is enough to require the exact historical
           ; scan, because that head may unify with predicates outside a bucket.
           ((тотожне? predicate (як-є ())) (reason-index-linear original))
           (так
            (нехай ((entry (міркування-пошук-кошика predicate buckets)))
              (за-умовою
                
                ; Новий ключ: порожній запас => чесний linear fallback.
                ((атом? entry)
                 (за-умовою
                   ((атом? fuel) (reason-index-linear original))
                   (так
                    (reason-index-build-scan
                      (решта remaining)
                      original
                      (reason-index-add-reversed
                        predicate (перше remaining) buckets)
                      (решта fuel)))))
                ; Повторений ключ не займає жодного нового біта бюджету.
                (так
                 (reason-index-build-scan
                   (решта remaining)
                   original
                   (reason-index-add-reversed
                     predicate (перше remaining) buckets)
                   fuel)))))))))))

(визначити reason-make-index
  (функція (rules)
    (reason-index-build-scan rules rules (як-є ()) *reason-index-fuel*)))

(визначити reason-ensure-index
  (функція (rules-or-index)
    (за-умовою
      ((reason-index? rules-or-index) rules-or-index)
      (так (reason-make-index rules-or-index)))))

; If indexing is safe, only rules whose head starts with the same predicate
; can unify with this goal. Bucket order is exactly source rule order. Any
; unsafe goal or disabled index returns every original rule unchanged.
(визначити reason-index-candidates
  (функція (goal rules-or-index)
    (нехай ((index (reason-ensure-index rules-or-index)))
      (за-умовою
        ((тотожне? (reason-index-mode index) (як-є linear))
         (reason-index-rules index))
        (так
         (нехай ((predicate (reason-term-predicate goal)))
           (за-умовою
             ((тотожне? predicate (як-є ())) (reason-index-rules index))
             (так
              (нехай ((entry (міркування-пошук-кошика predicate (reason-index-buckets index))))
                (за-умовою
                  
                  ((атом? entry)  (як-є ()))
                  (так (решта entry))))))))))))

; Окремий структурний лічильник перейменування: початкова цитована
; одноелементна структура, потім D3:111 CONS(QUOTE (), depth) на кожен рівень.
; Глибина не є D1 числом або арифметикою D24+, а лише тегом змінної.
; Public `reason` accepts either the historical rule list or an already-built
; finite `reason-index/1`. Plain callers are unchanged; repeated-query callers
; may explicitly retain an immutable index snapshot and avoid rebuilding it.
; There is no hidden cache or invalidation: an index continues to describe the
; exact rule list captured when it was constructed.
(визначити reason
  (функція (goal rules-or-index)
    (нехай ((index (reason-ensure-index rules-or-index)))
      (довести-ціль
        goal
        (reason-index-candidates goal index)
        (як-є ())
        index
        (як-є (()))))))

; Accumulate one rule's result list onto a reversed global accumulator.
; Walking `results` left-to-right and consing each item means `acc` is always
; exactly the reverse of every result seen so far.
(визначити prove-goal-accumulate
  (функція (results acc)
    (за-умовою
      
      ((атом? results)  acc)
      (так (prove-goal-accumulate
           (решта results)
           (сполучити (перше results) acc))))))

; Tail-recursive rule scan. `all-rules` may be a plain historical rule list or
; a B5 reason-index/1. We normalize it once here; recursive body goals then
; reuse the same finite index instead of rebuilding it at every depth.
(визначити prove-goal
  (функція (goal rules bindings all-rules depth)
    (prove-goal-scan
      goal
      rules
      bindings
      (reason-ensure-index all-rules)
      depth
      (як-є ()))))

(визначити prove-goal-scan
  (функція (goal rules bindings all-rules depth acc)
    (за-умовою
      
      ((атом? rules)  (зворот acc))
      (так
       (нехай ((rule-results
               (prove-rule goal (перше rules) bindings all-rules depth)))
         (prove-goal-scan
           goal
           (решта rules)
           bindings
           all-rules
           depth
           (prove-goal-accumulate rule-results acc)))))))

; Recursively rename variables in a term to include the depth counter.
(визначити rename-vars
  (функція (term depth)
    (за-умовою
      ((атом? term) term)
      ((reason-var-form? term)
       (список (як-є var) (сполучити (друге term) depth)))
      (так (сполучити (розрізнити-логічні-змінні-правила-на-глибині (перше term) depth)
                   (розрізнити-логічні-змінні-правила-на-глибині (решта term) depth))))))

(визначити map-proofs
  (функція (f lst)
    (за-умовою
      
      ((атом? lst)  (як-є ()))
      (так (сполучити (f (перше lst)) (map-proofs f (решта lst)))))))

; Try one rule, then wrap every successful body result in its proof node.
(визначити prove-rule
  (функція (goal rule bindings all-rules depth)
    (нехай ((renamed-rule (розрізнити-логічні-змінні-правила-на-глибині rule depth)))
      (нехай ((new-subst (уніфікувати goal (перше renamed-rule) bindings)))
        (за-умовою
          ((failed-subst? new-subst) (як-є ()))
          (так
           (нехай ((body-results
                   (довести-цілі
                     (решта renamed-rule)
                     new-subst
                     all-rules
                     (сполучити (як-є ()) depth))))
             (map-proofs
               (функція (res)
                 (список
                   (перше res)
                   (список
                     (як-є proved)
                     goal
                     (перше renamed-rule)
                     (друге res))))
               body-results))))))))

; Prove a conjunction while threading `(subst proofs)` through the shared
; conjunction walker from lib/unify.lisp.
(визначити prove-goals
  (функція (goals bindings all-rules depth)
    (thread-conjunction
      goals
      (список bindings (як-є ()))
      (функція (goal state)
        (довести-мету-зі-збереженням-підстановок-та-доказів goal state all-rules depth)))))

; A body goal, including `(not P)`, is an ordinary reasoning goal. Historical
; negation-as-failure fabricated `(proved-not P)` merely because P had no proof.
; Under #219/#244 that absence remains Canon 0. Explicit negative evidence may
; still prove `(not P)` through an actual rule/fact whose head is `(not P)`.
(визначити prove-goal-state
  (функція (goal state all-rules depth)
    (нехай ((bindings (перше state))
          (proofs (друге state))
          (index (reason-ensure-index all-rules)))
      (приєднати-докази-до-кожної-успішної-підстановки
        (довести-ціль
          goal
          (reason-index-candidates goal index)
          bindings
          index
          depth)
        proofs))))

(визначити map-goal-results
  (функція (results proofs)
    (за-умовою
      
      ((атом? results)  (як-є ()))
      (так
       (сполучити
         (список
           (перше-першого results)
           (приєднати proofs (список (друге (перше results)))))
         (приєднати-докази-до-кожної-успішної-підстановки (решта results) proofs))))))

(визначити explain-proof
  (функція (proof)
    (explain-proof-node proof 0)))

(визначити explain-proof-node
  (функція (node level)
    (за-умовою
      ((тотожне? (перше node) (як-є proved))
       (нехай-послідовно ((_2 (друкувати (як-є Proved:)))
              (_3 (друкувати (друге node)))
              (_4 (друкувати (як-є using)))
              (_5 (друкувати (як-є rule:)))
              (_6 (друкувати (третє node))))
         (explain-proof-list (четверте node) (додати level 1))))
      ((тотожне? (перше node) (як-є proved-not))
       (нехай-послідовно ((_2 (друкувати (як-є Proved)))
              (_3 (друкувати (як-є by)))
              (_4 (друкувати (як-є failure:)))
              (_5 (друкувати (як-є not)))
              (_6 (друкувати (друге node))))
         (як-є ())))
      )))

(визначити explain-proof-list
  (функція (nodes level)
    (за-умовою
      
      ((атом? nodes)  (як-є ()))
      (так
       (нехай-послідовно ((_1 (print-indent level))
              (_2 (друкувати (як-є |-)))
              (_3 (explain-proof-node (перше nodes) level)))
         (explain-proof-list (решта nodes) level))))))

(визначити print-indent
  (функція (level)
    (за-умовою
      ((тотожне? level 0) (як-є ()))
      (так
       (нехай ((_ (друкувати (як-є ..))))
         (print-indent (відняти level 1)))))))

; Human-facing compatibility explanation. Structured reasoning outcomes are
; provided separately by lib/result-status.lisp / reason-observe.
(визначити reason-explain
  (функція (goal rules)
    (нехай ((results (міркувати goal rules)))
      (за-умовою
        
        ((атом? results)  (нехай-послідовно ((_1 (друкувати (як-є Cannot)))
                (_2 (друкувати (як-є prove:)))
                (_3 (друкувати goal)))
           (як-є ())))
        (так (пояснити-доказ (друге (перше results))))))))

(визначити add-usage
  (функція (entry alist)
    (за-умовою
      
      ((атом? alist)  (список entry))
      ((unify-equal? (перше-першого alist) (перше entry))
       (сполучити
         (сполучити
           (перше entry)
           (додати (решта entry) (решта (перше alist))))
         (решта alist)))
      (так (сполучити (перше alist) (add-usage entry (решта alist)))))))

(визначити merge-usage
  (функція (a b)
    (за-умовою
      
      ((атом? a)  b)
      (так (підсумувати-лічильники-використання-правил (решта a) (add-usage (перше a) b))))))

(визначити count-usage
  (функція (node)
    (за-умовою
      ((тотожне? (перше node) (як-є proved))
       (add-usage
         (сполучити (третє node) 1)
         (count-usage-list (четверте node))))
      )))

(визначити count-usage-list
  (функція (nodes)
    (за-умовою
      
      ((атом? nodes)  (як-є ()))
      (так
       (підсумувати-лічильники-використання-правил
         (порахувати-правила-у-дереві-доказу (перше nodes))
         (count-usage-list (решта nodes)))))))

(визначити source-of
  (функція (node)
    (за-умовою
      
      ((атом? (четверте node))  (як-є fact))
      (так (як-є rule)))))

(визначити provenance
  (функція (node)
    (за-умовою
      ((тотожне? (перше node) (як-є proved))
       (список
         (як-є statement)
         (друге node)
         (список (як-є source) (джерело-від node))
         (список (як-є rule) (третє node))
         (список
           (як-є derived-from)
           (provenance-list (четверте node)))))
      (так
       (список
         (як-є statement)
         (друге node)
         (список (як-є source) (як-є not-proved)))))))

(визначити provenance-list
  (функція (nodes)
    (за-умовою
      
      ((атом? nodes)  (як-є ()))
      (так
       (сполучити
         (походження (перше nodes))
         (provenance-list (решта nodes)))))))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити порахувати-правила-у-дереві-доказу count-usage)
(визначити приєднати-докази-до-кожної-успішної-підстановки map-goal-results)
(визначити підсумувати-лічильники-використання-правил merge-usage)
(визначити довести-мету-зі-збереженням-підстановок-та-доказів prove-goal-state)
(визначити розрізнити-логічні-змінні-правила-на-глибині rename-vars)
