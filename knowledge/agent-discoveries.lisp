;; knowledge/agent-discoveries.lisp
;; Статус: coordination authority (не semantic contract мови).
;; Призначення: спільна дошка відкриттів рою — щоб жоден агент
;; не тримав finding лише в PR-коментарі чи локальній пам'яті.
;;
;; Протокол (doctrine rule 18):
;; 1. Знайшов несподіване → запис сюди або коментар у issue #1599.
;; 2. Формат: kind / claim / evidence / status / action
;; 3. Не дублювати semantic authority — лише координаційні факти.
;; 4. Перед CLAIM: прочитай цей файл + open comments на #1590/#1599.

(agent-discoveries
  (schema . 1)
  (updated . "2026-09-28")
  (board-issue . 1599)
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
    . "Додай (discovery ...) у цей файл у PR, АБО коментар на issue #1599:
       ### discovery
       - kind: m8-fallout | bench | island | transport | other
       - claim: одне речення
       - evidence: PR/SHA/path
       - status: confirmed|partial|hypothesis
       - action: що робити іншим агентам"))
)
