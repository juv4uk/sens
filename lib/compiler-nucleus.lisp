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


; #3839 — whole-program compiler traversal.
;
; Program data is the source-shaped tree ratified by compiler-program-data/1:
; exact DomainCall nodes are ordinary lists whose head is an exact
; DomainIdentity.  SHAPE-OR-EMPTY is a representation-only host mechanism:
; DomainIdentity -> (width bits), every other value -> ().
;
; The traversal owns semantic request selection in SENS and returns:
;   (D1-success-bit request...)
; so an unsupported exact-domain node cannot be confused with an empty
; subtree.  Backend lowering/installation remains outside this program.

(визначити compiler-request-from-laws
  (функція (decompose identity d3-law d4-law d3-proof d4-proof provenance)
    (за-умовою
      ((тотожне?
         (compiler-shape-width (decompose identity))
         (compiler-law-width d3-law))
       (compiler-request-from-role
         identity
         identity
         (compiler-lowering-role-from-l1-l5 decompose identity d3-law)
         d3-proof
         provenance))
      ((тотожне?
         (compiler-shape-width (decompose identity))
         (compiler-d4-law-width d4-law))
       (compiler-request-from-role
         identity
         identity
         (compiler-role-from-d4-bootstrap decompose identity d4-law)
         d4-proof
         provenance))
      ((compiler-true identity) ()))))

(визначити compiler-result-ok
  (функція (requests)
    (сполучити (compiler-true ()) requests)))

(визначити compiler-result-fail
  (функція ()
    (сполучити (compiler-false ()) ())))

(визначити compiler-result-success
  (функція (result)
    (перше result)))

(визначити compiler-result-requests
  (функція (result)
    (решта result)))

(визначити compiler-append
  (функція (left right)
    (за-умовою
      ((атом? left) right)
      ((compiler-true ())
       (сполучити
         (перше left)
         (compiler-append (решта left) right))))))

(визначити compiler-merge-results
  (функція (left right)
    (за-умовою
      ((compiler-result-success left)
       (за-умовою
         ((compiler-result-success right)
          (compiler-result-ok
            (compiler-append
              (compiler-result-requests left)
              (compiler-result-requests right))))
         ((compiler-true ()) (compiler-result-fail))))
      ((compiler-true ()) (compiler-result-fail)))))

(визначити compiler-request-role
  (функція (request)
    (перше (решта request))))

; Validate source shape only after SENS has already derived the abstract role.
; This is deliberately role -> arity/shape, never domain-bits -> shape.
(визначити compiler-exactly-one
  (функція (arguments)
    (за-умовою
      ((атом? arguments) (compiler-false ()))
      ((атом? (решта arguments))
       (за-умовою
         ((тотожне? (решта arguments) ()) (compiler-true ()))
         ((compiler-true ()) (compiler-false ()))))
      ((compiler-true ()) (compiler-false ())))))

(визначити compiler-exactly-two
  (функція (arguments)
    (за-умовою
      ((атом? arguments) (compiler-false ()))
      ((атом? (решта arguments)) (compiler-false ()))
      ((атом? (решта (решта arguments)))
       (за-умовою
         ((тотожне? (решта (решта arguments)) ()) (compiler-true ()))
         ((compiler-true ()) (compiler-false ()))))
      ((compiler-true ()) (compiler-false ())))))

; D4 LAMBDA is parameters plus one-or-more body expressions.
; Runtime create_lambda enforces the same minimum arity and preserves every
; body expression, so the compiler shape law must match that variadic body.
(визначити compiler-at-least-two
  (функція (arguments)
    (за-умовою
      ((атом? arguments) (compiler-false ()))
      ((атом? (решта arguments)) (compiler-false ()))
      ((compiler-true ()) (compiler-true ())))))

; Exact D3 COND is a non-empty sequence of two-part (test expression) clauses.
(визначити compiler-cond-clauses-valid
  (функція (clauses)
    (за-умовою
      ((атом? clauses) (compiler-true ()))
      ((compiler-exactly-two (перше clauses))
       (compiler-cond-clauses-valid (решта clauses)))
      ((compiler-true ()) (compiler-false ())))))

(визначити compiler-role-shape-valid
  (функція (request arguments)
    (за-умовою
      ((атом? request) (compiler-false ()))
      ((тотожне? (compiler-request-role request) (як-є quote-form))
       (compiler-exactly-one arguments))
      ((тотожне? (compiler-request-role request) (як-є atom-predicate))
       (compiler-exactly-one arguments))
      ((тотожне? (compiler-request-role request) (як-є selector-tail))
       (compiler-exactly-one arguments))
      ((тотожне? (compiler-request-role request) (як-є selector-head))
       (compiler-exactly-one arguments))
      ((тотожне? (compiler-request-role request) (як-є atom-equality))
       (compiler-exactly-two arguments))
      ((тотожне? (compiler-request-role request) (як-є pair-construct))
       (compiler-exactly-two arguments))
      ((тотожне? (compiler-request-role request) (як-є lambda-form))
       (compiler-at-least-two arguments))
      ((тотожне? (compiler-request-role request) (як-є define-form))
       (compiler-exactly-two arguments))
      ((тотожне? (compiler-request-role request) (як-є cond-form))
       (за-умовою
         ((атом? arguments) (compiler-false ()))
         ((compiler-true ()) (compiler-cond-clauses-valid arguments))))
      ((compiler-true ()) (compiler-false ())))))

; Program traversal policy is semantic and therefore SENS-owned.
; QUOTE payload is data.  LAMBDA parameters and DEFINE name are data.
; Other admitted forms recursively compile every argument position.
(визначити compiler-domain-children
  (функція (request arguments)
    (за-умовою
      ((атом? request) ())
      ((тотожне? (compiler-request-role request) (як-є quote-form)) ())
      ((тотожне? (compiler-request-role request) (як-є lambda-form))
       (решта arguments))
      ((тотожне? (compiler-request-role request) (як-є define-form))
       (решта arguments))
      ((compiler-true ()) arguments))))

(визначити compiler-domain-result
  (функція
    (request arguments child-result)
    (за-умовою
      ((атом? request) (compiler-result-fail))
      ((compiler-role-shape-valid request arguments)
       (за-умовою
         ((compiler-result-success child-result)
          (compiler-result-ok
            (сполучити
              request
              (compiler-result-requests child-result))))
         ((compiler-true ()) (compiler-result-fail))))
      ((compiler-true ()) (compiler-result-fail)))))

(визначити compiler-program-list
  (функція
    (shape-or-empty decompose nodes d3-law d4-law d3-proof d4-proof provenance)
    (за-умовою
      ((атом? nodes) (compiler-result-ok ()))
      ((compiler-true ())
       (compiler-merge-results
         (compiler-program-node
           shape-or-empty
           decompose
           (перше nodes)
           d3-law
           d4-law
           d3-proof
           d4-proof
           provenance)
         (compiler-program-list
           shape-or-empty
           decompose
           (решта nodes)
           d3-law
           d4-law
           d3-proof
           d4-proof
           provenance))))))

(визначити compiler-program-node
  (функція
    (shape-or-empty decompose node d3-law d4-law d3-proof d4-proof provenance)
    (за-умовою
      ((атом? node) (compiler-result-ok ()))
      ((атом? (shape-or-empty (перше node)))
       (compiler-program-list
         shape-or-empty
         decompose
         node
         d3-law
         d4-law
         d3-proof
         d4-proof
         provenance))
      ((compiler-true ())
       (compiler-domain-result
         (compiler-request-from-laws
           decompose
           (перше node)
           d3-law
           d4-law
           d3-proof
           d4-proof
           provenance)
         (решта node)
         (compiler-program-list
           shape-or-empty
           decompose
           (compiler-domain-children
             (compiler-request-from-laws
               decompose
               (перше node)
               d3-law
               d4-law
               d3-proof
               d4-proof
               provenance)
             (решта node))
           d3-law
           d4-law
           d3-proof
           d4-proof
           provenance))))))

(визначити compiler-compile-program
  (функція
    (shape-or-empty decompose program d3-law d4-law d3-proof d4-proof provenance)
    (compiler-program-list
      shape-or-empty
      decompose
      program
      d3-law
      d4-law
      d3-proof
      d4-proof
      provenance)))


; #3839 whole-program artifact composition.
;
; The host supplies only mechanical provenance values:
; - exact canonical SW\x01 program-byte digest,
; - exact pinned SENS revision,
; - exact compiler-nucleus source digest,
; - and one representation-only digest mechanism.
;
; SENS itself chooses the ordered semantic-request value to hash and composes
; the whole backend-neutral artifact. The digest mechanism owns no identity
; meaning, role/proof routing or backend policy.
(визначити compiler-artifact-field
  (функція (name value)
    (сполучити name (сполучити value ()))))

(визначити compiler-artifact-from-result
  (функція
    (digest program-wire-sha256 artifact-provenance result)
    (за-умовою
      ((compiler-result-success result)
       (сполучити
         (як-є compiler-compilation-artifact/1)
         (сполучити
           (compiler-artifact-field
             (як-є artifact-kind)
             (як-є whole-program))
           (сполучити
             (compiler-artifact-field
               (як-є program-wire-sha256)
               program-wire-sha256)
             (сполучити
               (compiler-artifact-field
                 (як-є semantic-requests-sha256)
                 (digest (compiler-result-requests result)))
               (сполучити
                 (compiler-artifact-field
                   (як-є authority-provenance)
                   artifact-provenance)
                 (сполучити
                   (compiler-artifact-field
                     (як-є semantic-requests)
                     (compiler-result-requests result))
                   (сполучити
                     (compiler-artifact-field
                       (як-є required-capabilities)
                       ())
                     (сполучити
                       (compiler-artifact-field
                         (як-є artifact-status)
                         (як-є canonical-backend-neutral))
                       ())))))))))
      ((compiler-true ())
       (сполучити
         (як-є compiler-compilation-error/1)
         (сполучити
           (compiler-artifact-field
             (як-є program-wire-sha256)
             program-wire-sha256)
           (сполучити
             (compiler-artifact-field
               (як-є error)
               (як-є compiler-program-rejected))
             ())))))))

(визначити compiler-compile-program-artifact
  (функція
    (shape-or-empty decompose digest program d3-law d4-law d3-proof d4-proof request-provenance artifact-provenance program-wire-sha256)
    (compiler-artifact-from-result
      digest
      program-wire-sha256
      artifact-provenance
      (compiler-compile-program
        shape-or-empty
        decompose
        program
        d3-law
        d4-law
        d3-proof
        d4-proof
        request-provenance))))
