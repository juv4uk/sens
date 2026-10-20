; #1134 — історичний контракт експериментального профілю Core3.
;
; Версія 7.0 та спільний SID у цьому записі свідчать про попередню
; архітектуру. Вони НЕ задають чинної адреси функції з драбини Д1–Д10.
; Нова реалізація мусить брати тотожність із ратифікованого домену
; та точного двійкового слова, без повернення до SID8.
; Відповідь зовнішнього виконавця не може самостійно стати законом мови.
;
; Нижче збережено історичний стан робіт, а не сучасний звіт готовності:
; - добір механізму був доданий у #1047/#1152;
; - мовне зниження — у #1158;
; - спостереження рідних результатів CLIPS — у #1164;
; - чотири ядра зберігали окремі домени та спільний SID виклику;
; - #992 тоді ще вимагав переходу від непрозорого INVOKE_ID
;   до операції Канону з одного мовного рядка.
;
; Контрактні поля, ідентифікатори, хеші та позначки станів є
; історичними даними. Не використовувати їх як нові викличні голови.

(core3-profile-contract/1
  ((identity . authority)
   (owner . sens)
   (profile . core3)
   (sid-identity-source . "lib/surface/semantic-registry.lisp")
   (profile-may-mint-sid . forbidden)
   (backend-may-ratify-law . no)
   (native-observation-is-language-law . no)
   (cross-profile-projection . explicit))

  ((identity . historical-pin)
   (language-contract . (7 0))
   (ratified-date . "2026-09-19")
   (contract-pin . "fae8d8f8ea6713d94db1f1fd7e8df4398279317e")
   (primitive-admission . evidence-based-adr-005)
   (sid-budget . shared-8-bit)
   (historical-cond-family . contract-7-truthiness-provenance-only)
   (unsatisfied-conditional . not-yet-contract8))

  ((identity . mechanism-architecture)
   (selector-source . "lib/mechanism-selector.lisp")
   (lowering-source . "lib/island-lowering.lisp")
   (selector-owner . sens)
   (lowering-owner . sens)
   (transport-semantics . blind)
   (executors . (common-lisp prolog clips datalog))
   (unknown-sid . fail-closed)
   (unknown-executor . fail-closed)
   (unknown-payload . fail-closed))

  ((identity . current-capability)
   (admitted-demo-sid . "00001100")
   (admitted-demo-operation . +)
   (common-lisp-route . available)
   (prolog-route . available)
   (datalog-route . available)
   (clips-route-selection . available)
   (clips-result-observation . available)
   (four-real-kernel-native-domains . available)
   (shared-invoke-sid-provenance . available)
   (canon-operation-four-island-round-trip . pending-issue-992))

  ((identity . library)
   (source . "lib/core3.lisp")
   (role . thin-profile-over-shared-selector)
   (duplicates-mechanism-table . no)
   (duplicates-semantic-table . no)
   (imports-core4-law . no))

  ((identity . acceptance-state)
   (core3-library-source . present)
   (selector-reused . yes)
   (all-four-routes-selectable . yes)
   (all-four-real-native-result-observations . yes)
   (native-result-provenance-across-kernel-boundary . yes)
   (canon-operation-four-island-round-trip . pending-issue-992)
   (zero-semantic-tables-duplicated-in-hosts . required)
   (status . partial-native-observation-admitted-canon-operation-pending)))