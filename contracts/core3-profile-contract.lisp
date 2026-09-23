; #1134 — authoritative Core3 experimental kernel profile.
;
; Core3 is pinned to Language Contract 7.0 and exists as the laboratory in
; which multiple execution kernels may compete under one shared SID identity.
; It never permits a backend result to become language law by accident.
;
; Current implementation status is intentionally PARTIAL:
; - mechanism selection is merged in lib/mechanism-selector.lisp (#1047/#1152);
; - Lisp-owned lowering is merged on main via #1158;
; - CLIPS producer-native result observation is merged via #1164;
; - four real kernels preserve native domains and the shared invocation SID;
; - #992 is still required because the current four-kernel witness uses one
;   opaque INVOKE_ID plus mechanism-specific native payloads, not one
;   Canon/function-table operation lowered from one Lisp-owned corpus row.
;
; This file is Lisp-owned authority data.

(core3-profile-contract/1
  ((identity . authority)
   (owner . my-lisp)
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
   (canonical-cond-family . historical-truthiness)
   (unsatisfied-conditional . not-yet-contract8))

  ((identity . mechanism-architecture)
   (selector-source . "lib/mechanism-selector.lisp")
   (lowering-source . "lib/island-lowering.lisp")
   (selector-owner . my-lisp)
   (lowering-owner . my-lisp)
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