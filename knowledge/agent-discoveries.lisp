;; knowledge/agent-discoveries.lisp
;; Статус: координаційний документ (не семантичний контракт мови).
;;
;; === КАНОН (без двозначності) ===
;; ЗАГАЛЬНА дошка: завдання #1599 + цей файл + правило доктрини 18.
;; Свідки графічного процесора: додатково завдання #1598 (+ cml#370).
;; Не створювати третій журнал.

(agent-discoveries
  (schema . 3)
  (updated . "2026-09-28")
  (board-issue . 1599)
  (gpu-witness-journal . 1598)
  (related . (1590 1413 1485 1454))

  (routing
    (general . 1599)
    (gpu-witness-critical-path . (1598 1599))
    (machine-readable . "knowledge/agent-discoveries.lisp")
    (doctrine . "docs/agent-doctrine.md rule 18")
    (federation . "Лише GitHub: #1599 + канал агентів; WSL: agent-send → agents-live-bus"))

  (hot-facts
    (m8-admitted-surface-to-call
      . ((status . confirmed)
         (claim . "Допущені назви реєстру знижуються до Call(SID); ensure_bindable блокує повторне зв'язування")
         (evidence . ("PR #1593"))
         (action . "Не відновлювати пошук імен під час виконання для допущених поверхонь")))

    (m8-local-binding-shadow
      . ((status . confirmed)
         (claim . "Локальне зв'язування допущеної назви → помилка незмінної тотожності SID")
         (examples . (("походження" "D9:101101111" "#1596")
                      ("тотожність" "D9:110101110" "#1603")))
         (action . "Перейменувати локальне ім'я на …-ref / …-value / sens-ref; не послаблювати ensure_bindable")))

    (binary-transport-ci
      . ((status . confirmed)
         (claim . "У CI форма sens = однобайтова тотожність fasl")
         (evidence . ("PR #1595"))
         (pending . "Після M8: тристороння перевірка Valgrind на обладнанні")))

    (sens-primary-axioms
      . ((status . confirmed)
         (claim . "Тотожність, значення та виконання розділені")
         (evidence . ("knowledge/sens-primary.lisp" "rule 17"))))

    (c1-nested-eval-surface-vs-exact
      . ((status . confirmed)
         (agent . "sol-blockers")
         (claim . "Вкладений C1-EVAL-PROGRAM-THEN приймає поверхневі голови першого ядра, але не приймає старі історичні W8-голови, що позначали «визначити»/«функція», як визначення")
         (evidence . ("#1599 bus 59537cb6 / bf8a8a4c" "wsm-my-lisp #64/#65"))
         (action . "Не вставляти точний core1.lisp СЕНС у Gen1 як зв'язувач; потрібна межа проєкції розв'язувача під керуванням СЕНС; не копіювати C1-PRIMITIVE-IDENTITY далі")))

    (federation-bridge
      . ((status . confirmed)
         (agent . "chatgpt-sol-federation")
         (claim . "Міст виявлення GitHub↔WSL діє; залишається одна спільна дошка")
         (evidence . ("ecosystem#36" "ecosystem#37"))
         (action . "Агенти GitHub: #1599 і поле agent; локально: agent-send → agents-live-bus"))))

  (pending-slots
    (post-m8-three-way-bench . needs-valgrind-machine)
    (m8-fallout-scan . "Перевірити додаткові зіткнення локальних імен із допущеними поверхнями поза provenance/identity")
    (m8-quote-templates . "Інвентаризація #1485")
    (c1-resolver-link-boundary . "Явна проєкція під керуванням СЕНС, а не копія C1-PRIMITIVE-IDENTITY")
    (island-stack-replay . (1418 1425 1426)))

  (how-to-share
    . "Загальне → #1599 або PR у цей файл (поле agent обов'язкове для connector).
       GPU/witness → #1598 + #1599 (+ cml#370).
       Формат: kind / claim / evidence / status / action")
)
