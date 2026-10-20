; yantraos-bridge-contract.lisp — версія 1, межа обміну лише даними між
; семантичними повноваженнями СЕНС і виконанням у yantraOS.
;
; СЕНС відповідає за намір, значення, політику та походження даних.
; yantraOS відповідає за маршрутизацію на хості, підтвердження, ізоляцію, виконання та аудит.
; Жодна зі сторін не має права переосмислювати повноваження іншої.
;
; Це контракт, а не новий семантичний примітив чи загальнодоступний SID.

(yantraos-bridge-contract/1
  ((envelope
     (required-fields
       (protocol intent action parameters verification provenance approval))
     (protocol-version (1 0))
     (intent-form
       (goal requires stop-on produces))
     (action-form
       (capability operation target))
     (parameter-form data)
     (verification-form explicit-data)
     (provenance-form explicit-data)
     (approval-values (required optional denied)))
   (execution-observation
     (required-fields
       (protocol result route evidence audit-ref provenance))
     (protocol-version (1 0))
     (result-values (accepted rejected blocked executed failed unknown))
     (route-form typed-data)
     (evidence-form explicit-data)
     (audit-ref-form explicit-data)
     (provenance-form explicit-data))
   (authority
     (semantic-owner my-lisp)
     (execution-owner yantraos)
     (model-owner neither)
     (policy-owner my-lisp)
     (audit-owner yantraos)
     (raw-shell-in-envelope forbidden)
     (raw-shell-command-field forbidden)
     (generic-value->bool forbidden)
     (new-semantic-sid forbidden)
     (new-rust-value-variant forbidden))
   (round-trip
     (request-provenance-preserved yes)
     (request-intent-preserved yes)
     (response-provenance-correlated yes)
     (execution-result-treated-as-observation yes))))
