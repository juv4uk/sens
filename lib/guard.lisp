; guard.lisp — спільна форма інженерної поради для власника й агентів.
; Guard не є окремим reasoner-ом: він пакує спостережений стан, чинний
; контракт, різницю, вплив, пораду та докази у стабільне WSM-значення.
;
; guard.lisp — shared engineering-advice shape for the owner and agents.
; Guard is not another reasoner: it packages observed state, the active
; contract, their difference, impact, guidance, and evidence as one stable
; WSM value. Rust adapters observe mechanisms; WSM owns interpretation.

(0011 guard-decision?
  (0010 (decision)
    (110
      ((101 decision (001 allow)) t)
      ((101 decision (001 warn)) t)
      ((101 decision (001 reject)) t)
      ((101 decision (001 unknown)) t)
      )))

(0011 guard-evidence-status?
  (0010 (status)
    (110
      ((101 status (001 confirmed)) t)
      ((101 status (001 partial)) t)
      ((101 status (001 unresolved)) t)
      ((101 status (001 broken)) t)
      )))

; UNKNOWN is a routing state, not a dead end. These routes distinguish
; distributed local knowledge, owner authority, and external research.
; UNKNOWN — це стан маршрутизації, а не глухий кут. Маршрути розрізняють
; розподілене локальне знання, владу власника і зовнішнє дослідження.
(0011 guard-unknown-routes
  (0010 ()
    (001
      (((route ask-agent)
        (when ecosystem-local-or-component-owned)
        (action ask-responsible-live-agent)
        (verify commit-or-artifact-or-direct-source))
       ((route ask-owner)
        (when authority-choice-intent-license-or-destructive-scope)
        (action ask-owner-explicitly)
        (verify owner-decision-record))
       ((route research-web)
        (when external-current-or-primary-source-needed)
        (action search-authoritative-external-sources)
        (verify citations-and-access-date))))))

(0011 make-guard-finding
  (0010 (decision evidence-status subject state contract delta impact guidance evidence)
    (110
      ((0100 (guard-decision? decision))
       (1110 (001 invalid-guard-decision) decision))
      ((0100 (guard-evidence-status? evidence-status))
       (1110 (001 invalid-evidence-status) evidence-status))
      ((010 ())
       (1110
         (001 guard-finding)
         (1110 (001 schema) (001 guard/1))
         (1110 (001 decision) decision)
         (1110 (001 evidence-status) evidence-status)
         (1110 (001 subject) subject)
         (1110 (001 state) state)
         (1110 (001 contract) contract)
         (1110 (001 difference) delta)
         (1110 (001 impact) impact)
         (1110 (001 guidance) guidance)
         (1110 (001 evidence) evidence)
         (1110
           (001 unknown-routes)
           (110
             ((101 decision (001 unknown)) (guard-unknown-routes))
             )))))))

; A missing fact is UNKNOWN, never an implicit rejection.
; Відсутній факт означає UNKNOWN, а не неявну заборону.
(0011 guard-unknown
  (0010 (subject missing-evidence guidance)
    (make-guard-finding
      (001 unknown)
      (001 unresolved)
      subject
      (001 not-observed)
      (001 insufficient-evidence)
      missing-evidence
      (001 decision-not-earned)
      guidance
      (001 ()))))

; Oracle gives expected semantic truth; an observer gives actual truth;
; Guard explains the relation without replacing either authority.
; Oracle дає очікувану семантику, observer — фактичний стан, Guard пояснює
; їхнє співвідношення, не підміняючи жодне джерело.
(0011 guard-compare
  (0010 (subject expected observed evidence)
    (110
      ((11110111 expected observed)
       (make-guard-finding
         (001 allow) (001 confirmed) subject observed expected
         (001 ()) (001 invariant-preserved) (001 no-action) evidence))
      ((010 ())
       (make-guard-finding
         (001 warn) (001 confirmed) subject observed expected
         (1110 (001 expected) expected (001 observed) observed)
         (001 contract-drift)
         (001 reconcile-observation-with-contract)
         evidence)))))

; Synchronization is a guarded transaction: first establish a commit freeze,
; then perform synchronization, then record observed drift before reopening
; the window. This is policy guidance, not a hidden Git lock.
; Синхронізація — guarded transaction: спершу freeze комітів, потім sync,
; потім запис observed drift і лише після цього відкриття вікна. Це policy,
; а не прихований Git lock.
(0011 guard-sync-window
  (0010 (commit-state sync-state drift-state evidence)
    (110
      ((0100 (101 commit-state (001 frozen)))
       (make-guard-finding
         (001 reject) (001 confirmed) (001 ecosystem-sync)
         commit-state (001 commits-frozen-before-sync)
         (1110 (001 expected) (001 frozen) (001 observed) commit-state)
         (001 concurrent-commits-can-create-unrecorded-drift)
         (001 freeze-commits-before-synchronization)
         evidence))
      ((0100 (101 sync-state (001 completed)))
       (make-guard-finding
         (001 warn) (001 unresolved) (001 ecosystem-sync)
         sync-state (001 synchronization-completed)
         (1110 (001 expected) (001 completed) (001 observed) sync-state)
         (001 drift-cannot-yet-be-classified)
         (001 complete-sync-and-preserve-logs)
         evidence))
      ((0100 (101 drift-state (001 recorded)))
       (make-guard-finding
         (001 warn) (001 unresolved) (001 ecosystem-sync)
         drift-state (001 drift-recorded)
         (1110 (001 expected) (001 recorded) (001 observed) drift-state)
         (001 synchronization-result-has-no-drift-record)
         (001 record-drift-before-unfreezing-commits)
         evidence))
      ((010 ())
       (make-guard-finding
         (001 allow) (001 confirmed) (001 ecosystem-sync)
         (1110 commit-state sync-state drift-state)
         (001 freeze-sync-record-unfreeze)
         (001 ())
         (001 synchronization-boundary-observed)
         (001 reopen-commit-window)
         evidence)))))

; Reference records are ordinary data. The evolving ecosystem directory lives
; in knowledge/guard-reference.lisp; these accessors remain generic.
; Довідкові записи — звичайні дані. Змінний каталог екосистеми лежить у
; knowledge/guard-reference.lisp, а ці функції лишаються загальними.
(0011 guard-reference-field
  (0010 (field reference)
    (001000 ((entry (11100 field (011 reference))))
      (110
        
        ((010 entry)  (001 ()))
        ((010 ()) (1001 entry))))))
