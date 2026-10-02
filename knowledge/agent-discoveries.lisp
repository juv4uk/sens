;; knowledge/agent-discoveries.lisp
;; Статус: coordination authority (не semantic contract мови).
;;
;; === КАНОН (без двозначності) ===
;; ЗАГАЛЬНА дошка: issue #1599 + цей файл + doctrine rule 18.
;; GPU/witness: issue #1598 (+ cml#370) додатково.
;; Не створювати третій журнал.

(agent-discoveries
  (schema . 3)
  (updated . "2026-10-02")
  (board-issue . 1599)
  (gpu-witness-journal . 1598)
  (related . (1590 1413 1485 1454))

  (routing
    (general . 1599)
    (gpu-witness-critical-path . (1598 1599))
    (machine-readable . "knowledge/agent-discoveries.lisp")
    (doctrine . "docs/agent-doctrine.md rule 18")
    (federation . "GitHub-only: #1599 + agent lane; WSL: agent-send → agents-live-bus"))

  (hot-facts
    (m8-admitted-surface-to-call
      . ((status . confirmed)
         (claim . "admitted registry surfaces lower to Call(SID); ensure_bindable blocks binding them")
         (evidence . ("PR #1593"))
         (action . "do not reintroduce runtime name lookup for admitted surfaces")))

    (m8-local-binding-shadow
      . ((status . confirmed)
         (claim . "local binding matching admitted surface → immutable SID error")
         (examples . (("provenance" . "10000100" "#1596")
                      ("identity" . "10011000" "#1603")))
         (action . "rename local to …-ref / …-value / sens-ref; never weaken ensure_bindable")))

    (binary-transport-ci
      . ((status . confirmed)
         (claim . "CI form=sens = fasl 1-byte identity")
         (evidence . ("PR #1595"))
         (pending . "post-M8 valgrind three-way on hardware")))

    (sens-primary-axioms
      . ((status . confirmed)
         (claim . "identity / meaning / execution separated")
         (evidence . ("knowledge/sens-primary.lisp" "rule 17"))))

    (c1-nested-eval-surface-vs-exact
      . ((status . confirmed)
         (agent . "sol-blockers")
         (claim . "C1-EVAL-PROGRAM-THEN nested accepts Core1 surface define/lambda but NOT exact heads 00001001/00001000 as definition")
         (evidence . ("#1599 bus 59537cb6 / bf8a8a4c" "wsm-my-lisp #64/#65"))
         (action . "do not inject exact-SENS core1.lisp into Gen1 program as linker; need SENS-owned resolver projection boundary; do not copy C1-PRIMITIVE-IDENTITY downstream")))

    (federation-bridge
      . ((status . confirmed)
         (agent . "chatgpt-sol-federation")
         (claim . "GitHub↔WSL discovery bridge live; one board only")
         (evidence . ("ecosystem#36" "ecosystem#37"))
         (action . "GitHub agents: #1599 + agent field; local: agent-send → agents-live-bus"))))

    (one-core-and-core-math
      . ((status . owner-ratified-direction)
         (agent . "chatgpt-sol")
         (claim . "one active Core: lib/core.lisp contains only ratified domains; D5/D6 closeout separately; D7 researches Sound+Number; lib/core-math.lisp is research-only mathematics")
         (evidence . ("#2410" "#2411" "#2414" "#2415" "PR #2417" "#1599 comment 5957748054"))
         (action . "do not create numbered Core profiles; route math hypotheses through core-math and require separate owner ratification before core admission"))))

  (pending-slots
    (post-m8-three-way-bench . needs-valgrind-machine)
    (m8-fallout-scan . "more locals vs admitted surfaces beyond provenance/identity")
    (m8-quote-templates . "#1485 inventory")
    (c1-resolver-link-boundary . "explicit SENS-owned projection; not C1-PRIMITIVE-IDENTITY copy")
    (island-stack-replay . (1418 1425 1426)))

  (how-to-share
    . "Загальне → #1599 або PR у цей файл (поле agent обов'язкове для connector).
       GPU/witness → #1598 + #1599 (+ cml#370).
       Формат: kind / claim / evidence / status / action"))
)
