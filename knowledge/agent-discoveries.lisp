;; knowledge/agent-discoveries.lisp
;; Статус: coordination authority (не semantic contract мови).
;; Призначення: спільна дошка відкриттів рою — щоб жоден агент
;; не тримав finding лише в PR-коментарі чи локальній пам'яті.
;;
;; Протокол (також doctrine rule 18):
;; 1. Знайшов несподіване (RED після M8, колізія surface, layout cost,
;;    bench gap, island admission) → запис сюди або коментар у issue
;;    «Agent discovery board» з посиланням на evidence/PR/SHA.
;; 2. Формат запису: (discovery (date ...) (agent ...) (kind ...) (claim ...)
;;    (evidence ...) (status confirmed|partial|hypothesis) (action ...))
;; 3. Не дублювати semantic authority — лише координаційні факти.
;; 4. Перед CLAIM нової задачі: прочитай цей файл + open comments на #1590/#1598.

(agent-discoveries
  (schema . 1)
  (updated . "2026-09-28")
  (board-issue . 1598)
  (related . (1590 1413))

  (hot-facts
    (m8-admitted-surface-to-call
      . ((status . confirmed)
         (main-sha-hint . "37f31edd")
         (claim . "admitted registry surfaces lower to Call(SID); ensure_bindable blocks binding them")
         (evidence . ("PR #1593" "crates/sens/src/eval/lower.rs" "crates/sens/src/eval/canon.rs"))
         (action . "do not reintroduce runtime name lookup for + - * / admitted names")))

    (m8-local-binding-shadow
      . ((status . confirmed)
         (claim . "local Lisp binding matching admitted surface name fails: surface routes to immutable function SID")
         (example . "provenance -> 10000100 in life-1-scheduler")
         (evidence . ("PR #1596"))
         (action . "rename local to …-ref / …-value; never weaken ensure_bindable")))

    (binary-transport-ci
      . ((status . confirmed)
         (claim . "CI form=sens encodes via fasl; function identity = 1 byte")
         (evidence . ("evidence/sens-binary-transport-2026-09-28.md" "benchmarks/sens-surface/ci_bench.sh"))
         (pending . "post-M8 three-way valgrind remeasure on hardware")))

    (sens-primary-axioms
      . ((status . confirmed)
         (claim . "identity / meaning / execution separated; backends are witnesses")
         (evidence . ("knowledge/sens-primary.lisp" "docs/agent-doctrine.md rule 17")))))

  (pending-slots
    (post-m8-three-way-bench . needs-valgrind-machine)
    (island-stack-replay . (1418 1425 1426))
    (m8-fallout-scan . "grep local bindings that collide with admitted surfaces"))

  (how-to-share
    . "Додай (discovery ...) у цей файл у PR, АБО коментар на issue #1598:
       ### discovery
       - kind: m8-fallout | bench | island | transport | other
       - claim: одне речення
       - evidence: PR/SHA/path
       - status: confirmed|partial|hypothesis
       - action: що робити іншим агентам"))
)
