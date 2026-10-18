; guard.lisp — спільна форма інженерної поради для власника й агентів.
; Guard не є окремим reasoner-ом: він пакує спостережений стан, чинний
; контракт, різницю, вплив, пораду та докази у стабільне WSM-значення.
;
; guard.lisp — shared engineering-advice shape for the owner and agents.
; Guard is not another reasoner: it packages observed state, the active
; contract, their difference, impact, guidance, and evidence as one stable
; WSM value. Rust adapters observe mechanisms; WSM owns interpretation.
;
; Predicate results now use direct typed one-bit W1 projections without ATOM/NOT.
; Two-field COND only. Width is identity; every bit of the domain address valued.

(визначити захист-рішення?
  (функція (decision)
    (за-умовою
      ((тотожне? decision (як-є allow)) так)
      ((тотожне? decision (як-є warn)) так)
      ((тотожне? decision (як-є reject)) так)
      ((тотожне? decision (як-є unknown)) так)
      (так ні))))

(визначити захист-доказ-стан?
  (функція (status)
    (за-умовою
      ((тотожне? status (як-є confirmed)) так)
      ((тотожне? status (як-є partial)) так)
      ((тотожне? status (як-є unresolved)) так)
      ((тотожне? status (як-є broken)) так)
      (так ні))))

; UNKNOWN is a routing state, not a dead end. These routes distinguish
; distributed local knowledge, owner authority, and external research.
; UNKNOWN — це стан маршрутизації, а не глухий кут. Маршрути розрізняють
; розподілене локальне знання, владу власника і зовнішнє дослідження.
(визначити захист-невідоме-маршрути
  (функція ()
    (як-є
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

(визначити створити-захист-висновок
  (функція (decision evidence-status subject state contract delta impact guidance evidence)
    (за-умовою
      ((хибне? (захист-рішення? decision))
       (список (як-є invalid-guard-decision) decision))
      ((хибне? (захист-доказ-стан? evidence-status))
       (список (як-є invalid-evidence-status) evidence-status))
      (так
       (список
         (як-є guard-finding)
         (список (як-є schema) (як-є guard/1))
         (список (як-є decision) decision)
         (список (як-є evidence-status) evidence-status)
         (список (як-є subject) subject)
         (список (як-є state) state)
         (список (як-є contract) contract)
         (список (як-є difference) delta)
         (список (як-є impact) impact)
         (список (як-є guidance) guidance)
         (список (як-є evidence) evidence)
         (список
           (як-є unknown-routes)
           (за-умовою
             ((тотожне? decision (як-є unknown)) (захист-невідоме-маршрути))
             (так (як-є ())))))))))

; A missing fact is UNKNOWN, never an implicit rejection.
; Відсутній факт означає UNKNOWN, а не неявну заборону.
(визначити guard-unknown
  (функція (subject missing-evidence guidance)
    (створити-захист-висновок
      (як-є unknown)
      (як-є unresolved)
      subject
      (як-є not-observed)
      (як-є insufficient-evidence)
      missing-evidence
      (як-є decision-not-earned)
      guidance
      (як-є ()))))

; Oracle gives expected semantic truth; an observer gives actual truth;
; Guard explains the relation without replacing either authority.
; Oracle дає очікувану семантику, observer — фактичний стан, Guard пояснює
; їхнє співвідношення, не підміняючи жодне джерело.

; Структурний закон Guard належить двійковому SENS, не Rust і не W8.
; D3:010 ATOM, 101 EQ лише для атомів, 100 CAR, 011 CDR, 110 COND.
; Повертає рівно D1 PredicateBit; невідомий механізм не допускається.
(визначити сторожа--рівні?
  (функція (ліве праве)
    (за-умовою
      ((атом? ліве)
       (за-умовою
         ((атом? праве) (тотожне? ліве праве))
         (так ні)))
      ((атом? праве) ні)
      ((сторожа--рівні? (перше ліве) (перше праве))
       (сторожа--рівні? (решта ліве) (решта праве)))
      (так ні))))

(визначити guard-compare
  (функція (subject expected observed evidence)
    (за-умовою
      ((сторожа--рівні? expected observed)
       (створити-захист-висновок
         (як-є allow) (як-є confirmed) subject observed expected
         (як-є ()) (як-є invariant-preserved) (як-є no-action) evidence))
      (так
       (створити-захист-висновок
         (як-є warn) (як-є confirmed) subject observed expected
         (список (як-є expected) expected (як-є observed) observed)
         (як-є contract-drift)
         (як-є reconcile-observation-with-contract)
         evidence)))))

; Synchronization is a guarded transaction: first establish a commit freeze,
; then perform synchronization, then record observed drift before reopening
; the window. This is policy guidance, not a hidden Git lock.
; Синхронізація — guarded transaction: спершу freeze комітів, потім sync,
; потім запис observed drift і лише після цього відкриття вікна. Це policy,
; а не прихований Git lock.
(визначити guard-sync-window
  (функція (commit-state sync-state drift-state evidence)
    (за-умовою
      ((хибне? (тотожне? commit-state (як-є frozen)))
       (створити-захист-висновок
         (як-є reject) (як-є confirmed) (як-є ecosystem-sync)
         commit-state (як-є commits-frozen-before-sync)
         (список (як-є expected) (як-є frozen) (як-є observed) commit-state)
         (як-є concurrent-commits-can-create-unrecorded-drift)
         (як-є freeze-commits-before-synchronization)
         evidence))
      ((хибне? (тотожне? sync-state (як-є completed)))
       (створити-захист-висновок
         (як-є warn) (як-є unresolved) (як-є ecosystem-sync)
         sync-state (як-є synchronization-completed)
         (список (як-є expected) (як-є completed) (як-є observed) sync-state)
         (як-є drift-cannot-yet-be-classified)
         (як-є complete-sync-and-preserve-logs)
         evidence))
      ((хибне? (тотожне? drift-state (як-є recorded)))
       (створити-захист-висновок
         (як-є warn) (як-є unresolved) (як-є ecosystem-sync)
         drift-state (як-є drift-recorded)
         (список (як-є expected) (як-є recorded) (як-є observed) drift-state)
         (як-є synchronization-result-has-no-drift-record)
         (як-є record-drift-before-unfreezing-commits)
         evidence))
      (так
       (створити-захист-висновок
         (як-є allow) (як-є confirmed) (як-є ecosystem-sync)
         (список commit-state sync-state drift-state)
         (як-є freeze-sync-record-unfreeze)
         (як-є ())
         (як-є synchronization-boundary-observed)
         (як-є reopen-commit-window)
         evidence)))))

; Reference records are ordinary data. The evolving ecosystem directory lives
; in knowledge/guard-reference.lisp; these accessors remain generic.
; Довідкові записи — звичайні дані. Змінний каталог екосистеми лежить у
; knowledge/guard-reference.lisp, а ці функції лишаються загальними.
(визначити guard-reference-field
  (функція (поле посилання)
    ((функція (запис)
       (за-умовою
         ((атом? запис) (як-є ()))
         (так (друге запис))))
     (знайти-за-ключем поле (решта посилання)))))

; --- OWNER LANGUAGE FIREWALL 2026-10-16 ---
; SENS Lisp owns semantics. Zig handles domain-ladder codes. Rust consumes them.
; Unknown language or wrong role is always rejected.
(визначити guard-language-allowed?
  (функція (language role)
    (за-умовою
      ((тотожне? language (як-є sens))
       (за-умовою ((тотожне? role (як-є semantics)) так) (так ні)))
      ((тотожне? language (як-є lisp))
       (за-умовою ((тотожне? role (як-є semantics)) так) (так ні)))
      ((тотожне? language (як-є zig))
       (за-умовою ((тотожне? role (як-є domain-ladder)) так) (так ні)))
      ((тотожне? language (як-є rust))
       (за-умовою ((тотожне? role (як-є domain-consumer)) так) (так ні)))
      (так ні))))

(визначити guard-language-decision
  (функція (language role)
    (за-умовою ((guard-language-allowed? language role) (як-є allow))
         (так (як-є reject)))))

; D9:000110011 GUARD-SYNC-WINDOW — українська поверхня SENS.
; Чинний закон guard-sync-window залишається джерелом семантики;
; це не host fallback і не direct D9 opcode.
(визначити захист-синхронізувати-вікно guard-sync-window)

; Історичні викличні поверхні Guard — ті самі closure, без дублювання.
(визначити guard-decision? захист-рішення?)
(визначити guard-evidence-status? захист-доказ-стан?)
(визначити guard-unknown-routes захист-невідоме-маршрути)
(визначити make-guard-finding створити-захист-висновок)
