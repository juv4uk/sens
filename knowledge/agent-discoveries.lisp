;; knowledge/agent-discoveries.lisp
;; Статус: coordination authority (не semantic contract мови).
;;
;; === КАНОН (без двозначності) ===
;; ЗАГАЛЬНА дошка відкриттів рою: issue #1599 + цей файл + doctrine rule 18.
;; ВУЗЬКИЙ журнал GPU/witness (sens⇄cml): issue #1598 (дзеркало cml#370).
;;
;; Правило маршрутизації:
;; - M8, surface, transport, islands, будь-що загальне → #1599 (обов'язково)
;; - критичний шлях GPU/witness E1–E3 / f32 / cml bridge → #1598 І #1599
;;   (крос-репо: також cml#370)
;; Не створювати третій журнал. Не дублювати semantic authority.

(agent-discoveries
  (schema . 2)
  (updated . "2026-09-28")
  (board-issue . 1599)
  (gpu-witness-journal . 1598)
  (related . (1590 1413))

  (routing
    (general . 1599)
    (gpu-witness-critical-path . (1598 1599))
    (machine-readable . "knowledge/agent-discoveries.lisp")
    (doctrine . "docs/agent-doctrine.md rule 18"))

  (hot-facts
    (m8-admitted-surface-to-call
      . ((status . confirmed)
         (claim . "admitted registry surfaces lower to Call(SID); ensure_bindable blocks binding them")
         (evidence . ("PR #1593"))
         (action . "do not reintroduce runtime name lookup for admitted surfaces")))

    (m8-local-binding-shadow
      . ((status . confirmed)
         (claim . "local binding matching admitted surface → immutable SID error")
         (example . "provenance -> 10000100")
         (evidence . ("PR #1596"))
         (action . "rename local to …-ref / …-value; never weaken ensure_bindable")))

    (binary-transport-ci
      . ((status . confirmed)
         (claim . "CI form=sens = fasl 1-byte identity")
         (evidence . ("PR #1595"))
         (pending . "post-M8 valgrind three-way on hardware")))

    (sens-primary-axioms
      . ((status . confirmed)
         (claim . "identity / meaning / execution separated")
         (evidence . ("knowledge/sens-primary.lisp" "rule 17")))))

  (pending-slots
    (post-m8-three-way-bench . needs-valgrind-machine)
    (island-stack-replay . (1418 1425 1426))
    (m8-fallout-scan . "local bindings vs admitted surfaces"))

  (how-to-share
    . "Загальне → коментар #1599 або PR у цей файл.
       GPU/witness critical path → #1598 + #1599 (+ cml#370).
       Формат: kind / claim / evidence / status / action"))
)
