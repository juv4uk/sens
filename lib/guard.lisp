; guard.lisp — спільна форма інженерної поради для власника й агентів.
; Guard не є окремим reasoner-ом: він пакує спостережений стан, чинний
; контракт, різницю, вплив, пораду та докази у стабільне WSM-значення.
;
; guard.lisp — shared engineering-advice shape for the owner and agents.
; Guard is not another reasoner: it packages observed state, the active
; contract, their difference, impact, guidance, and evidence as one stable
; WSM value. Rust adapters observe mechanisms; WSM owns interpretation.

(00001011 guard-decision?
  (00001000 (decision)
    (00000111
      ((00000011 decision (00000001 allow)) (00000010 (00000001 ())))
      ((00000011 decision (00000001 warn)) (00000010 (00000001 ())))
      ((00000011 decision (00000001 reject)) (00000010 (00000001 ())))
      ((00000011 decision (00000001 unknown)) (00000010 (00000001 ())))
      ((00000010 (00000001 ())) (00000001 ())))))

(00001011 guard-evidence-status?
  (00001000 (status)
    (00000111
      ((00000011 status (00000001 confirmed)) (00000010 (00000001 ())))
      ((00000011 status (00000001 partial)) (00000010 (00000001 ())))
      ((00000011 status (00000001 unresolved)) (00000010 (00000001 ())))
      ((00000011 status (00000001 broken)) (00000010 (00000001 ())))
      ((00000010 (00000001 ())) (00000001 ())))))

; UNKNOWN is a routing state, not a dead end. These routes distinguish
; distributed local knowledge, owner authority, and external research.
; UNKNOWN — це стан маршрутизації, а не глухий кут. Маршрути розрізняють
; розподілене локальне знання, владу власника і зовнішнє дослідження.
(00001011 guard-unknown-routes
  (00001000 ()
    (00000001
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

(00001011 make-guard-finding
  (00001000 (decision evidence-status subject state contract delta impact guidance evidence)
    (00000111
      ((00100001 (guard-decision? decision))
       (00100111 (00000001 invalid-guard-decision) decision))
      ((00100001 (guard-evidence-status? evidence-status))
       (00100111 (00000001 invalid-evidence-status) evidence-status))
      ((00000010 (00000001 ()))
       (00100111
         (00000001 guard-finding)
         (00100111 (00000001 schema) (00000001 guard/1))
         (00100111 (00000001 decision) decision)
         (00100111 (00000001 evidence-status) evidence-status)
         (00100111 (00000001 subject) subject)
         (00100111 (00000001 state) state)
         (00100111 (00000001 contract) contract)
         (00100111 (00000001 difference) delta)
         (00100111 (00000001 impact) impact)
         (00100111 (00000001 guidance) guidance)
         (00100111 (00000001 evidence) evidence)
         (00100111
           (00000001 unknown-routes)
           (00000111
             ((00000011 decision (00000001 unknown)) (guard-unknown-routes))
             ((00000010 (00000001 ())) (00000001 ())))))))))

; A missing fact is UNKNOWN, never an implicit rejection.
; Відсутній факт означає UNKNOWN, а не неявну заборону.
(00001011 guard-unknown
  (00001000 (subject missing-evidence guidance)
    (make-guard-finding
      (00000001 unknown)
      (00000001 unresolved)
      subject
      (00000001 not-observed)
      (00000001 insufficient-evidence)
      missing-evidence
      (00000001 decision-not-earned)
      guidance
      (00000001 ()))))

; Oracle gives expected semantic truth; an observer gives actual truth;
; Guard explains the relation without replacing either authority.
; Oracle дає очікувану семантику, observer — фактичний стан, Guard пояснює
; їхнє співвідношення, не підміняючи жодне джерело.
(00001011 guard-compare
  (00001000 (subject expected observed evidence)
    (00000111
      ((00100010 expected observed)
       (make-guard-finding
         (00000001 allow) (00000001 confirmed) subject observed expected
         (00000001 ()) (00000001 invariant-preserved) (00000001 no-action) evidence))
      ((00000010 (00000001 ()))
       (make-guard-finding
         (00000001 warn) (00000001 confirmed) subject observed expected
         (00100111 (00000001 expected) expected (00000001 observed) observed)
         (00000001 contract-drift)
         (00000001 reconcile-observation-with-contract)
         evidence)))))

; Synchronization is a guarded transaction: first establish a commit freeze,
; then perform synchronization, then record observed drift before reopening
; the window. This is policy guidance, not a hidden Git lock.
; Синхронізація — guarded transaction: спершу freeze комітів, потім sync,
; потім запис observed drift і лише після цього відкриття вікна. Це policy,
; а не прихований Git lock.
(00001011 guard-sync-window
  (00001000 (commit-state sync-state drift-state evidence)
    (00000111
      ((00100001 (00000011 commit-state (00000001 frozen)))
       (make-guard-finding
         (00000001 reject) (00000001 confirmed) (00000001 ecosystem-sync)
         commit-state (00000001 commits-frozen-before-sync)
         (00100111 (00000001 expected) (00000001 frozen) (00000001 observed) commit-state)
         (00000001 concurrent-commits-can-create-unrecorded-drift)
         (00000001 freeze-commits-before-synchronization)
         evidence))
      ((00100001 (00000011 sync-state (00000001 completed)))
       (make-guard-finding
         (00000001 warn) (00000001 unresolved) (00000001 ecosystem-sync)
         sync-state (00000001 synchronization-completed)
         (00100111 (00000001 expected) (00000001 completed) (00000001 observed) sync-state)
         (00000001 drift-cannot-yet-be-classified)
         (00000001 complete-sync-and-preserve-logs)
         evidence))
      ((00100001 (00000011 drift-state (00000001 recorded)))
       (make-guard-finding
         (00000001 warn) (00000001 unresolved) (00000001 ecosystem-sync)
         drift-state (00000001 drift-recorded)
         (00100111 (00000001 expected) (00000001 recorded) (00000001 observed) drift-state)
         (00000001 synchronization-result-has-no-drift-record)
         (00000001 record-drift-before-unfreezing-commits)
         evidence))
      ((00000010 (00000001 ()))
       (make-guard-finding
         (00000001 allow) (00000001 confirmed) (00000001 ecosystem-sync)
         (00100111 commit-state sync-state drift-state)
         (00000001 freeze-sync-record-unfreeze)
         (00000001 ())
         (00000001 synchronization-boundary-observed)
         (00000001 reopen-commit-window)
         evidence)))))

; Reference records are ordinary data. The evolving ecosystem directory lives
; in knowledge/guard-reference.lisp; these accessors remain generic.
; Довідкові записи — звичайні дані. Змінний каталог екосистеми лежить у
; knowledge/guard-reference.lisp, а ці функції лишаються загальними.
(00001011 guard-reference-field
  (00001000 (field reference)
    (10011100 ((entry (00101101 field (00000110 reference))))
      (00000111
        ((00000010 entry) (00000001 ()))
        ((00000010 (00000001 ())) (00101111 entry))))))
