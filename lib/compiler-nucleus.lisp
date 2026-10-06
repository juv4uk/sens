; lib/compiler-nucleus.lisp
; sens#3759 / #3803 — first executable compiler nucleus slice owned by SENS.
;
; N0 is deliberately smaller than the final self-hosted compiler:
; - exact DomainIdentity is already a first-class runtime value;
; - authority rows are supplied as data by the bootstrap boundary;
; - this program performs the authority lookup/normalization itself;
; - it contains no D3 coordinate table, no Sid8/Sens8 identity, and no backend
;   opcode/mechanism table.
;
; Authority row shape for this bounded slice:
;
;   (exact-domain-identity execution-role proof-ref provenance)
;
; The role/proof/provenance payload is opaque here.  #3806 moves construction
; of that authority projection from the Rust/bootstrap oracle into executable
; SENS-owned law.  Until then this file is a real compiler component, but only
; a PARTIAL nucleus and not a self-host/fixed-point claim.
;
; Ukrainian spellings below are source/UI projections only.  They are chosen
; because the current registry routes Ukrainian D3/D4 surfaces directly to
; exact-domain identities.  The focused guard lowers this file before execution
; and rejects any historical Sid/Call node.

(визначити compiler-authority-find
  (функція (identity rows)
    (за-умовою
      ((атом? rows) ())
      ((тотожне? identity (перше (перше rows))) (перше rows))
      ((атом? ()) (compiler-authority-find identity (решта rows))))))

(визначити compiler-nucleus
  (функція (identity authority)
    (compiler-authority-find identity authority)))


; Representation-only bootstrap seam for #3808.
; DECOMPOSE is an explicitly supplied first-class mechanism.  The language
; chooses when to invoke it; the host function may reveal only exact width/bits
; and has no identity->meaning authority.
(визначити compiler-domain-shape
  (функція (decompose identity)
    (decompose identity)))


; #3809 — bounded compiler-role derivation from generated, provenance-bound
; D3 L1-L5 structural law data.  There is deliberately no D3 coordinate→role
; table here.
;
; LAW is transported from knowledge/bija3-l1-l5-structure-projection.json:
;   (domain-width l1-empty-bits l4-xor-mask l5-spine)
;
; The projection itself is mechanically generated from owner-ratified #3202.
; It carries no compiler role names.  SENS assigns the bounded compiler roles
; by executing the ratified structural relationships:
;   head selector = third ordered L5 spine member
;   tail selector = L4 dual(head selector)
;   pair construct = L4 dual(L1 empty)
;
; DECOMPOSE is the representation-only mechanism from #3808.

(визначити compiler-true
  (функція (seed)
    (атом? seed)))

(визначити compiler-false
  (функція (seed)
    (атом? (сполучити seed ()))))

(визначити compiler-bits-equal
  (функція (seed left right)
    (за-умовою
      ((атом? left) (атом? right))
      ((атом? right) (compiler-false seed))
      ((тотожне? (перше left) (перше right))
       (compiler-bits-equal seed (решта left) (решта right)))
      ((compiler-true seed) (compiler-false seed)))))

(визначити compiler-bit-xor
  (функція (seed left right)
    (за-умовою
      ((тотожне? left right) (compiler-false seed))
      ((compiler-true seed) (compiler-true seed)))))

(визначити compiler-xor-bits
  (функція (seed left right)
    (за-умовою
      ((атом? left)
       (за-умовою
         ((атом? right) ())
         ((compiler-true seed) ())))
      ((атом? right) ())
      ((compiler-true seed)
       (сполучити
         (compiler-bit-xor seed (перше left) (перше right))
         (compiler-xor-bits seed (решта left) (решта right)))))))

(визначити compiler-shape-width
  (функція (shape)
    (перше shape)))

(визначити compiler-shape-bits
  (функція (shape)
    (перше (решта shape))))

(визначити compiler-law-width
  (функція (law)
    (перше law)))

(визначити compiler-law-empty-bits
  (функція (law)
    (перше (решта law))))

(визначити compiler-law-xor-mask
  (функція (law)
    (перше (решта (решта law)))))

(визначити compiler-law-l5-spine
  (функція (law)
    (перше (решта (решта (решта law))))))

(визначити compiler-law-l5-atom-bits
  (функція (law)
    (перше (решта (compiler-law-l5-spine law)))))

(визначити compiler-law-l5-head-bits
  (функція (law)
    (перше (решта (решта (compiler-law-l5-spine law))))))

(визначити compiler-law-l5-cond-bits
  (функція (law)
    (перше (решта (решта (решта (compiler-law-l5-spine law)))))))

; Full D3 compiler closure is derived only from the ratified L1/L4/L5
; structure.  The three spine roles are read by ordered position; their duals
; are obtained with the one L4 XOR law.  No raw D3 coordinate is embedded here.
(визначити compiler-role-from-l1-l5-bits
  (функція (seed bits law)
    (за-умовою
      ((compiler-bits-equal seed bits (compiler-law-l5-head-bits law))
       (як-є selector-head))
      ((compiler-bits-equal
         seed bits
         (compiler-xor-bits
           seed
           (compiler-law-l5-head-bits law)
           (compiler-law-xor-mask law)))
       (як-є selector-tail))
      ((compiler-bits-equal
         seed bits
         (compiler-xor-bits
           seed
           (compiler-law-empty-bits law)
           (compiler-law-xor-mask law)))
       (як-є pair-construct))
      ((compiler-true seed) ()))))

; Full D3 lowering closure for self-hosting.  It deliberately has a separate
; name so the already-merged three-role execution API remains stable.
(визначити compiler-lowering-role-from-l1-l5-bits
  (функція (seed bits law)
    (за-умовою
      ((compiler-bits-equal
         seed bits
         (compiler-xor-bits
           seed
           (compiler-law-l5-cond-bits law)
           (compiler-law-xor-mask law)))
       (як-є quote-form))
      ((compiler-bits-equal seed bits (compiler-law-l5-atom-bits law))
       (як-є atom-predicate))
      ((compiler-bits-equal
         seed bits
         (compiler-xor-bits
           seed
           (compiler-law-l5-head-bits law)
           (compiler-law-xor-mask law)))
       (як-є selector-tail))
      ((compiler-bits-equal seed bits (compiler-law-l5-head-bits law))
       (як-є selector-head))
      ((compiler-bits-equal
         seed bits
         (compiler-xor-bits
           seed
           (compiler-law-l5-atom-bits law)
           (compiler-law-xor-mask law)))
       (як-є atom-equality))
      ((compiler-bits-equal seed bits (compiler-law-l5-cond-bits law))
       (як-є cond-form))
      ((compiler-bits-equal
         seed bits
         (compiler-xor-bits
           seed
           (compiler-law-empty-bits law)
           (compiler-law-xor-mask law)))
       (як-є pair-construct))
      ((compiler-true seed) ()))))

(визначити compiler-role-from-l1-l5
  (функція (decompose identity law)
    (за-умовою
      ((тотожне?
         (compiler-shape-width (decompose identity))
         (compiler-law-width law))
       (compiler-role-from-l1-l5-bits
         identity
         (compiler-shape-bits (decompose identity))
         law))
      ((compiler-true identity) ()))))


; #3824 — D4 bootstrap-role derivation from the ordered owner-ratified fibre.
; D4-LAW is transported as:
;   (domain-width parent-bits ordered-children)
; where ordered-children is the exact two-child fibre generated from #3272.
; The structure carries no role names.  SENS assigns the first/second
; irreducible bootstrap child to LambdaForm/DefineForm respectively.
(визначити compiler-d4-law-width
  (функція (law)
    (перше law)))

(визначити compiler-d4-law-children
  (функція (law)
    (перше (решта (решта law)))))

(визначити compiler-d4-law-first-child
  (функція (law)
    (перше (compiler-d4-law-children law))))

(визначити compiler-d4-law-second-child
  (функція (law)
    (перше (решта (compiler-d4-law-children law)))))

(визначити compiler-role-from-d4-bootstrap-bits
  (функція (seed bits law)
    (за-умовою
      ((compiler-bits-equal seed bits (compiler-d4-law-first-child law))
       (як-є lambda-form))
      ((compiler-bits-equal seed bits (compiler-d4-law-second-child law))
       (як-є define-form))
      ((compiler-true seed) ()))))

(визначити compiler-role-from-d4-bootstrap
  (функція (decompose identity law)
    (за-умовою
      ((тотожне?
         (compiler-shape-width (decompose identity))
         (compiler-d4-law-width law))
       (compiler-role-from-d4-bootstrap-bits
         identity
         (compiler-shape-bits (decompose identity))
         law))
      ((compiler-true identity) ()))))

; One production role query for the whole current compiler nucleus.  Domain
; width selects which already-ratified structural law is applicable; neither
; the host nor this function infers meaning from an equal packed payload.
(визначити compiler-lowering-role-from-l1-l5
  (функція (decompose identity law)
    (за-умовою
      ((тотожне?
         (compiler-shape-width (decompose identity))
         (compiler-law-width law))
       (compiler-lowering-role-from-l1-l5-bits
         identity
         (compiler-shape-bits (decompose identity))
         law))
      ((compiler-true identity) ()))))

(визначити compiler-lowering-role-from-laws
  (функція (decompose identity d3-law d4-law)
    (за-умовою
      ((тотожне?
         (compiler-shape-width (decompose identity))
         (compiler-law-width d3-law))
       (compiler-lowering-role-from-l1-l5 decompose identity d3-law))
      ((тотожне?
         (compiler-shape-width (decompose identity))
         (compiler-d4-law-width d4-law))
       (compiler-role-from-d4-bootstrap decompose identity d4-law))
      ((compiler-true identity) ()))))


; #3810 — production request cutover.
; Role meaning comes only from compiler-role-from-l1-l5 above.  The host may
; transport LAW/proof/provenance values, but it does not select the role.

(визначити compiler-request-from-role
  (функція (seed identity role proof-ref provenance)
    (за-умовою
      ((тотожне? role ()) ())
      ((compiler-true seed)
       (сполучити
         identity
         (сполучити
           role
           (сполучити
             proof-ref
             (сполучити provenance ()))))))))

(визначити compiler-request-from-l1-l5
  (функція (decompose identity law proof-ref provenance)
    (compiler-request-from-role
      identity
      identity
      (compiler-role-from-l1-l5 decompose identity law)
      proof-ref
      provenance)))


; #3837 — bounded whole-program compiler body for the current self-host nucleus.
;
; Canonical program transport is representation-only:
;   (domain-call exact-identity (arg-node ...))
;   (list (node ...))
;   (pair head-node tail-node)
;   (atom opaque-literal)
;
; Only this SENS-written code walks that tree for compiler meaning.  The host may
; parse/reify source into this shape, but it must not choose roles or requests.
; Output order is deterministic preorder over exact DomainCall nodes.

(визначити compiler-result-ok
  (функція (requests)
    (сполучити (як-є ok) (сполучити requests ()))))

(визначити compiler-result-error
  (функція (reason)
    (сполучити (як-є error) (сполучити reason ()))))

(визначити compiler-result-ok?
  (функція (result)
    (тотожне? (перше result) (як-є ok))))

(визначити compiler-result-payload
  (функція (result)
    (перше (решта result))))

(визначити compiler-append
  (функція (left right)
    (за-умовою
      ((атом? left) right)
      ((compiler-true left)
       (сполучити (перше left) (compiler-append (решта left) right))))))

(визначити compiler-merge-results
  (функція (left right)
    (за-умовою
      ((compiler-result-ok? left)
       (за-умовою
         ((compiler-result-ok? right)
          (compiler-result-ok
            (compiler-append
              (compiler-result-payload left)
              (compiler-result-payload right))))
         ((compiler-true left) right)))
      ((compiler-true right) left))))

(визначити compiler-one-arg?
  (функція (seed args)
    (за-умовою
      ((атом? args) (compiler-false seed))
      ((атом? (решта args)) (compiler-true seed))
      ((compiler-true seed) (compiler-false seed)))))

(визначити compiler-two-args?
  (функція (seed args)
    (за-умовою
      ((атом? args) (compiler-false seed))
      ((атом? (решта args)) (compiler-false seed))
      ((атом? (решта (решта args))) (compiler-true seed))
      ((compiler-true seed) (compiler-false seed)))))

(визначити compiler-nonempty-args?
  (функція (seed args)
    (за-умовою
      ((атом? args) (compiler-false seed))
      ((compiler-true seed) (compiler-true seed)))))

(визначити compiler-role-arity-ok?
  (функція (seed role args)
    (за-умовою
      ((тотожне? role (як-є quote-form))
       (compiler-one-arg? seed args))
      ((тотожне? role (як-є atom-predicate))
       (compiler-one-arg? seed args))
      ((тотожне? role (як-є selector-tail))
       (compiler-one-arg? seed args))
      ((тотожне? role (як-є selector-head))
       (compiler-one-arg? seed args))
      ((тотожне? role (як-є atom-equality))
       (compiler-two-args? seed args))
      ((тотожне? role (як-є cond-form))
       (compiler-nonempty-args? seed args))
      ((тотожне? role (як-є pair-construct))
       (compiler-two-args? seed args))
      ((тотожне? role (як-є lambda-form))
       (compiler-two-args? seed args))
      ((тотожне? role (як-є define-form))
       (compiler-two-args? seed args))
      ((compiler-true seed) (compiler-false seed)))))

(визначити compiler-proof-ref-for-identity
  (функція (decompose identity d3-law d4-law d3-proof-ref d4-proof-ref)
    (за-умовою
      ((тотожне?
         (compiler-shape-width (decompose identity))
         (compiler-law-width d3-law))
       d3-proof-ref)
      ((тотожне?
         (compiler-shape-width (decompose identity))
         (compiler-d4-law-width d4-law))
       d4-proof-ref)
      ((compiler-true identity) ()))))

(визначити compiler-compile-domain-call-with-role
  (функція
    (decompose identity args d3-law d4-law d3-proof-ref d4-proof-ref provenance role)
    (за-умовою
      ((тотожне? role ())
       (compiler-result-error
         (сполучити (як-є unsupported-domain-call) (сполучити identity ()))))
      ((compiler-role-arity-ok? identity role args)
       (compiler-compile-domain-call-with-request
         decompose
         identity
         args
         d3-law
         d4-law
         d3-proof-ref
         d4-proof-ref
         provenance
         (compiler-request-from-role
           identity
           identity
           role
           (compiler-proof-ref-for-identity
             decompose identity d3-law d4-law d3-proof-ref d4-proof-ref)
           provenance)))
      ((compiler-true identity)
       (compiler-result-error
         (сполучити
           (як-є source-shape-mismatch)
           (сполучити identity (сполучити role ()))))))))

(визначити compiler-compile-domain-call-with-request
  (функція
    (decompose identity args d3-law d4-law d3-proof-ref d4-proof-ref provenance request)
    (compiler-prepend-request
      request
      (compiler-compile-sequence
        decompose args d3-law d4-law d3-proof-ref d4-proof-ref provenance))))

(визначити compiler-prepend-request
  (функція (request result)
    (за-умовою
      ((compiler-result-ok? result)
       (compiler-result-ok
         (сполучити request (compiler-result-payload result))))
      ((compiler-true request) result))))

(визначити compiler-compile-domain-call
  (функція
    (decompose identity args d3-law d4-law d3-proof-ref d4-proof-ref provenance)
    (compiler-compile-domain-call-with-role
      decompose
      identity
      args
      d3-law
      d4-law
      d3-proof-ref
      d4-proof-ref
      provenance
      (compiler-lowering-role-from-laws decompose identity d3-law d4-law))))

(визначити compiler-compile-node
  (функція
    (decompose node d3-law d4-law d3-proof-ref d4-proof-ref provenance)
    (за-умовою
      ((атом? node)
       (compiler-result-error (як-є malformed-compiler-ast)))
      ((тотожне? (перше node) (як-є atom))
       (compiler-result-ok ()))
      ((тотожне? (перше node) (як-є list))
       (compiler-compile-sequence
         decompose
         (перше (решта node))
         d3-law d4-law d3-proof-ref d4-proof-ref provenance))
      ((тотожне? (перше node) (як-є pair))
       (compiler-merge-results
         (compiler-compile-node
           decompose
           (перше (решта node))
           d3-law d4-law d3-proof-ref d4-proof-ref provenance)
         (compiler-compile-node
           decompose
           (перше (решта (решта node)))
           d3-law d4-law d3-proof-ref d4-proof-ref provenance)))
      ((тотожне? (перше node) (як-є domain-call))
       (compiler-compile-domain-call
         decompose
         (перше (решта node))
         (перше (решта (решта node)))
         d3-law d4-law d3-proof-ref d4-proof-ref provenance))
      ((compiler-true node)
       (compiler-result-error
         (сполучити (як-є unknown-compiler-ast-node) (сполучити (перше node) ())))))))

(визначити compiler-compile-sequence
  (функція
    (decompose nodes d3-law d4-law d3-proof-ref d4-proof-ref provenance)
    (за-умовою
      ((атом? nodes) (compiler-result-ok ()))
      ((compiler-true nodes)
       (compiler-merge-results
         (compiler-compile-node
           decompose
           (перше nodes)
           d3-law d4-law d3-proof-ref d4-proof-ref provenance)
         (compiler-compile-sequence
           decompose
           (решта nodes)
           d3-law d4-law d3-proof-ref d4-proof-ref provenance))))))

(визначити compiler-finalize-program-artifact
  (функція (source-digest authority-digest result)
    (за-умовою
      ((compiler-result-ok? result)
       (сполучити
         (як-є compiler-compilation-artifact/2)
         (сполучити
           source-digest
           (сполучити
             authority-digest
             (сполучити (compiler-result-payload result) ())))))
      ((compiler-true result)
       (сполучити
         (як-є compiler-compilation-error/1)
         (сполучити (compiler-result-payload result) ()))))))

(визначити compiler-compile-program
  (функція
    (decompose program d3-law d4-law d3-proof-ref d4-proof-ref provenance source-digest authority-digest)
    (compiler-finalize-program-artifact
      source-digest
      authority-digest
      (compiler-compile-sequence
        decompose
        program
        d3-law
        d4-law
        d3-proof-ref
        d4-proof-ref
        provenance))))
