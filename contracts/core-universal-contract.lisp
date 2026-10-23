; #1664 — спільна двійкова основа ATOM/EQ/COND для ядер Core1–Core4.
;
; Це єдиний виконуваний контракт основи чотирьох ядер.
; Основа навмисно мала й стабільна: експериментальна логіка Core4
; не може перевизначати її закони. Профілі можуть розвиватися,
; але не розгалужувати спільні закони предикатів і керування.
;
; Закон задається спостережуваною поведінкою, а не написанням
; викличної назви. Доказовий корпус міститься в
; tests/fixtures/semantic/ (#1709): контракт посилається на нього,
; але не створює другої копії.
; Чинні функціональні ідентичності — Д3 із повною проєкцією укр.
; Історична Function8/SID8 схема лишається лише в історії Git.
;
(core-universal-contract-1

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

  (("010" . ((identity . "D3:010")
             (укр . атом?)
             (empty-structure . 1)
             (non-pair . 1)
             (pair-structure . 0)))
   (governs . "#1704"))

  (("101" . ((identity . "D3:101")
             (укр . тотожне?)
             (same-admitted-atom . 1)
             (distinct-admitted-atom . 0)
             (pair-operand . named-error)))
   (governs . "#1705"))

  (("110" . ((identity . "D3:110")
             (укр . за-умовою)
             (clause-shape . two-part)
             (test-1 . select)
             (test-0 . skip)
             (unselected-expression . not-evaluated)
             (exhaustion . ())
             (three-part-clause . rejected)))
   (governs . "#1713"))

  ((reader . ((malformed-source . rejected-not-repaired)))
   (governs . "#1709"))

  ((shared-identities . ("D3:001" "D3:010" "D3:101" "D3:011"
                         "D3:100" "D3:111" "D3:110"))
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
