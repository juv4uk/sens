; #2376 — mechanism laboratory authority under one active Core.
;
; Historical "Core3" named the experimental multi-kernel lane. Under #2367 /
; #2410 it is no longer a language core or semantic profile. This contract
; preserves the experiment while making the authority boundary explicit.
;
; Backend observations may test implementations. They cannot ratify SENS law.

(mechanism-lab-contract/1
  ((identity . authority)
   (owner . sens)
   (kind . mechanism-laboratory)
   (language-core . no)
   (historical-name . core3)
   (semantic-identity-source . "lib/surface/semantic-registry.lisp")
   (lab-may-mint-semantic-identity . forbidden)
   (backend-may-ratify-law . no)
   (native-observation-is-language-law . no))

  ((identity . historical-provenance)
   (former-profile . core3)
   (former-language-contract-pin . (7 0))
   (former-contract-pin . "fae8d8f8ea6713d94db1f1fd7e8df4398279317e")
   (historical-cond-family . contract-7-truthiness-provenance-only)
   (active-semantic-authority . no))

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
   (source . "lib/mechanism-lab.lisp")
   (role . explicit-mechanism-laboratory)
   (duplicates-mechanism-table . no)
   (duplicates-semantic-table . no)
   (imports-private-core-law . no))

  ((identity . acceptance-state)
   (mechanism-lab-source . present)
   (selector-reused . yes)
   (all-four-routes-selectable . yes)
   (all-four-real-native-result-observations . yes)
   (native-result-provenance-across-kernel-boundary . yes)
   (canon-operation-four-island-round-trip . pending-issue-992)
   (zero-semantic-tables-duplicated-in-hosts . required)
   (status . partial-native-observation-admitted-canon-operation-pending)))