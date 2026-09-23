; #1131 — авторитетний контракт чотирьох Core-профілів.
;
; Це Lisp-owned архітектурний контракт. Він НЕ створює чотири окремі мови.
;
; Інваріант:
;
;   спільна SID / Canon identity
;             ↓
;       вибраний Core
;             ↓
;   профільний law/result-domain
;             ↓
;      допустимий mechanism
;
; SID відповідає на питання "що це за операція/ідентичність".
; Core відповідає на питання "за яким профільним законом ця ідентичність
; поводиться в цій історичній/експериментальній лінії".
; Backend/kernel відповідає лише за механізм виконання або native observation.
;
; Тому профіль не може створювати чи перенумеровувати SID, але різні Core
; можуть законно мати різні law/result-domain для тієї самої SID identity.
; Це свідомо виправляє застарілу модель PR #1136 "one law for all profiles".
;
; Схема:
;   (core-profile-contract/2 SECTION ...)

(core-profile-contract/2
  ((identity . authority)
   (owner . my-lisp)
   (sid-identity . shared)
   (canon-identity . shared)
   (semantic-registry . shared)
   (surface-identity-source . semantic-registry-sid)
   (profile-law-selection . required)
   (profile-may-mint-sid . forbidden)
   (profile-may-renumber-sid . forbidden)
   (backend-may-own-sid-meaning . forbidden)
   (single-law-for-all-profiles . forbidden)
   (cross-profile-projection . explicit))

  ((identity . core1)
   (profile-number . 1)
   (role . bootstrap-historical-root)
   (law-source . "contracts/core1-bootstrap-contract.lisp")
   (execution-source . "lib/core1.lisp")
   (historical-mechanism-map . "contracts/core1-historical-sid-map.lisp")
   (status . admitted)
   (historical-contract . pre-versioned-root)
   (result-domain-family . historical-t-nil)
   (mechanism-family . mccarthy-eval)
   (unsupported-operation . fail-closed))

  ((identity . core2)
   (profile-number . 2)
   (role . frozen-legacy-compatibility)
   (target-source . "lib/core2.lisp")
   (status . source-admitted-activation-pending)
   (historical-contract . (6 0))
   (historical-source-pin . "35c88142548dad137689cd69ca91c430da148bea")
   (compatibility-projection . explicit)
   (legacy-truth-domain . historical-t-nil)
   (legacy-two-part-cond . admitted-profile-behavior)
   (core4-law-import . forbidden)
   (unsupported-operation . fail-closed))

  ((identity . core3)
   (profile-number . 3)
   (role . experimental-kernel-laboratory)
   (target-source . "lib/core3.lisp")
   (status . partial-selector-admitted-round-trip-pending)
   (law-source . "contracts/core3-profile-contract.lisp")
   (execution-source . "lib/core3.lisp")
   (historical-contract . (7 0))
   (historical-contract-pin . "fae8d8f8ea6713d94db1f1fd7e8df4398279317e")
   (mechanism-families . (common-lisp prolog clips datalog))
   (selector-owner . my-lisp)
   (lowering-owner . my-lisp)
   (native-observation-preserved . yes)
   (native-observation-is-language-law . no)
   (experiment-may-propose-core4-law . evidence-required)
   (backend-may-ratify-law . no)
   (unsupported-operation . fail-closed))

  ((identity . core4)
   (profile-number . 4)
   (role . current-creative-language)
   (target-source . "lib/core4.lisp")
   (execution-source . "lib/core4.lisp")
   (fasl-source . "lib/core4.lisp.fasl")
   (compatibility-donor . "lib/core.lisp")
   (status . admitted)
   (historical-contract . (8 0))
   (historical-contract-pin . "f665f541f5ab1befab23f1daf9f6c0afa51fbab0")
   (law-authority . language-contract.lisp)
   (legacy-core2-compatibility . out-of-profile)
   (core3-native-observation-as-law . forbidden)
   (unsupported-operation . fail-closed))

  ((identity . public-api-discovery)
   (current-profile-source . "lib/core4.lisp")
   (public-api-excluded-source . "lib/core.lisp")
   (public-api-excluded-source . "lib/core1.lisp")
   (public-api-excluded-source . "lib/core2.lisp")
   (public-api-excluded-source . "lib/core3.lisp"))

  ((identity . profile-selection)
   (same-sid-across-profiles . required)
   (same-sid-may-select-profile-specific-law . yes)
   (same-sid-may-select-profile-specific-result-domain . yes)
   (profile-selection-precedes-mechanism-selection . yes)
   (mechanism-selection-may-change-sid-identity . no)
   (mechanism-selection-may-ratify-language-law . no)
   (missing-profile-implementation . fail-closed)
   (implicit-fallback-to-another-profile . forbidden))

  ((identity . migration-state)
   (core1-source . admitted)
   (core2-source . present-activation-pending)
   (core3-source . partial)
   (core4-source . admitted)
   (current-lib-core-role . core4-compatibility-donor)
   (current-lib-core-is-core1 . no)
   (copy-current-core-four-times . forbidden)
   (next-authoritative-profile-files . ())))
