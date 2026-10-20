; #1664 — спільна двійкова основа АТОМ/ТОТОЖНІСТЬ/УМОВА для Core1–4.
;
; Це один виконуваний контракт основи для Core1, Core2, Core3 і Core4.
; Спільна основа навмисно мала й стабільна. Експериментальна логіка
; Core4 не має права перевизначати її.
; Профілі ядра можуть розширюватися, але не розділяють основу
; предикатів і керування на несумісні варіанти.
;
; Наведений нижче закон визначає спостережувану поведінку,
; а не людське написання назв. Корпус доказів зберігається
; у `tests/fixtures/semantic/` (#1709); його використовують,
; а не дублюють у цьому контракті.

(core-universal-contract/1

  ((scope . core1-core4-universal-foundation)
   (governs . "#1664")
   (corpus . "tests/fixtures/semantic")
   (principle . "Профілі ядра можуть розширюватися, але не розділяють основу предикатів і керування."))

  ((predicate-answer . one-bit)
   (yes . 1)
   (no . 0)
   (graded-answers . forbidden)
   (empty-list-as-predicate-result . forbidden)
   (host-boolean-defines-semantics . forbidden)
   (governs . "#1699"))

  (("010" . ((compat-function8 . "00000010")
             (empty-structure . 1)
             (non-pair . 1)
             (pair-structure . 0)))
   (governs . "#1704"))

  (("111" . ((compat-function8 . "00000011")
             (same-admitted-atom . 1)
             (distinct-admitted-atom . 0)
             (pair-operand . named-error)))
   (governs . "#1705"))

  (("011" . ((compat-function8 . "00000111")
             (clause-shape . two-part)
             (test-1 . select)
             (test-0 . skip)
             (unselected-expression . not-evaluated)
             (exhaustion . ())
             (three-part-clause . rejected)))
   (governs . "#1713"))

  ((reader . ((malformed-source . rejected-not-repaired)))
   (governs . "#1709"))

  ((shared-identities . ("00000001" "00000010" "00000011" "00000100"
                         "00000101" "00000110" "00000111"))
   (identity-scope . observable-law-not-spelling))

  ((negative-laws . (graded-predicate-answer
                     empty-list-predicate-result
                     structural-kind-substitution
                     host-truth-substitution))
   (host-truth-defines-semantics . forbidden))

  ((profile-coverage . ((native . proven)
                        (core3 . proven)
                        (core2 . measured-blocked)
                        (core1 . not-yet-exercisable)
                        (core4 . not-yet-exercisable)))
   (divergence-is-a-defect . t)
   (note . "Покриття вимірюється, а не припускається: для core2 зафіксовано непрохідний стан, а core1/core4 ще не мають завантажувача корпусу.")))
