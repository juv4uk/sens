; yantraos-bridge-contract.lisp — v1 data-only boundary between
; my-lisp semantic authority and yantraOS execution.
;
; my-lisp owns intent/meaning/policy/provenance.
; yantraOS owns host routing, confirmation, sandboxing, execution and audit.
; Neither side may reinterpret the other's authority.
;
; This is a contract document, not a new semantic primitive or public SID.

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
