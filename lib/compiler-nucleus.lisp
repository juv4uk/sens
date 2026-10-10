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
  (функція (ідентичність rows)
    (за-умовою
      ((атом? rows) ())
      ((тотожне? ідентичність (перше (перше rows))) (перше rows))
      ((атом? ()) (compiler-authority-find ідентичність (решта rows))))))

(визначити compiler-nucleus
  (функція (ідентичність authority)
    (compiler-authority-find ідентичність authority)))


; Representation-only bootstrap seam for #3808.
; DECOMPOSE is an explicitly supplied first-class mechanism.  The language
; chooses when to invoke it; the host function may reveal only exact width/bits
; and has no identity->meaning authority.
(00001001 compiler-domain-shape
  (00001000 (decompose ідентичність)
    (decompose ідентичність)))


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

(00001001 compiler-true
  (00001000 (seed)
    (00000010 seed)))

(00001001 compiler-false
  (00001000 (seed)
    (00000010 (00000100 seed ()))))

(00001001 compiler-bits-equal
  (00001000 (seed left right)
    (00000111
      ((00100010 left (00000001 ()))
       (00100010 right (00000001 ())))
      ((00100010 right (00000001 ()))
       (compiler-false seed))
      ((00000010 left)
       (00000111
         ((00000010 right) (compiler-true seed))
         ((compiler-true seed) (compiler-false seed))))
      ((00000010 right) (compiler-false seed))
      ((00100010 (00000101 left) (00000101 right))
       (compiler-bits-equal seed (00000110 left) (00000110 right)))
      ((compiler-true seed) (compiler-false seed)))))

(00001001 compiler-bit-xor
  (00001000 (seed left right)
    (00000111
      (left
       (00000111
         (right (compiler-false seed))
         ((compiler-true seed) (compiler-true seed))))
      ((00000111
         (right (compiler-true seed))
         ((compiler-true seed) (compiler-false seed)))))))

(00001001 compiler-xor-bits
  (00001000 (seed left right)
    (00000111
      ((00100010 left (00000001 ())) ())
      ((00000010 left)
       (00000111
         ((00100010 right (00000001 ())) ())
         ((compiler-true seed) ())))
      ((00100010 right (00000001 ())) ())
      ((compiler-true seed)
       (00000100
         (compiler-bit-xor seed (00000101 left) (00000101 right))
         (compiler-xor-bits seed (00000110 left) (00000110 right)))))))

(00001001 compiler-shape-width
  (00001000 (shape)
    (00000101 shape)))

(00001001 compiler-shape-bits
  (00001000 (shape)
    (00000101 (00000110 shape))))

(00001001 compiler-law-width
  (00001000 (law)
    (00000101 law)))

(00001001 compiler-law-empty-bits
  (00001000 (law)
    (00000101 (00000110 law))))

(00001001 compiler-law-xor-mask
  (00001000 (law)
    (00000101 (00000110 (00000110 law)))))

(00001001 compiler-law-l5-spine
  (00001000 (law)
    (00000101 (00000110 (00000110 (00000110 law))))))

(00001001 compiler-law-l5-atom-bits
  (00001000 (law)
    (00000101 (00000110 (compiler-law-l5-spine law)))))

(00001001 compiler-law-l5-head-bits
  (00001000 (law)
    (00000101 (00000110 (00000110 (compiler-law-l5-spine law))))))

(00001001 compiler-law-l5-cond-bits
  (00001000 (law)
    (00000101 (00000110 (00000110 (00000110 (compiler-law-l5-spine law)))))))

; Full D3 compiler closure is derived only from the ratified L1/L4/L5
; structure.  The three spine roles are read by ordered position; their duals
; are obtained with the one L4 XOR law.  No raw D3 coordinate is embedded here.
(00001001 compiler-role-from-l1-l5-bits
  (00001000 (seed bits law)
    (00000111
      ((compiler-bits-equal seed bits (compiler-law-l5-head-bits law))
       (00000001 selector-head))
      ((compiler-bits-equal
         seed bits
         (compiler-xor-bits
           seed
           (compiler-law-l5-head-bits law)
           (compiler-law-xor-mask law)))
       (00000001 selector-tail))
      ((compiler-bits-equal
         seed bits
         (compiler-xor-bits
           seed
           (compiler-law-empty-bits law)
           (compiler-law-xor-mask law)))
       (00000001 pair-construct))
      ((compiler-true seed) ()))))

; Full D3 lowering closure for self-hosting.  It deliberately has a separate
; name so the already-merged three-role execution API remains stable.
(00001001 compiler-lowering-role-from-l1-l5-bits
  (00001000 (seed bits law)
    (00000111
      ((compiler-bits-equal
         seed bits
         (compiler-xor-bits
           seed
           (compiler-law-l5-cond-bits law)
           (compiler-law-xor-mask law)))
       (00000001 quote-form))
      ((compiler-bits-equal seed bits (compiler-law-l5-atom-bits law))
       (00000001 atom-predicate))
      ((compiler-bits-equal
         seed bits
         (compiler-xor-bits
           seed
           (compiler-law-l5-head-bits law)
           (compiler-law-xor-mask law)))
       (00000001 selector-tail))
      ((compiler-bits-equal seed bits (compiler-law-l5-head-bits law))
       (00000001 selector-head))
      ((compiler-bits-equal
         seed bits
         (compiler-xor-bits
           seed
           (compiler-law-l5-atom-bits law)
           (compiler-law-xor-mask law)))
       (00000001 atom-equality))
      ((compiler-bits-equal seed bits (compiler-law-l5-cond-bits law))
       (00000001 cond-form))
      ((compiler-bits-equal
         seed bits
         (compiler-xor-bits
           seed
           (compiler-law-empty-bits law)
           (compiler-law-xor-mask law)))
       (00000001 pair-construct))
      ((compiler-true seed) ()))))

(00001001 compiler-role-from-l1-l5
  (00001000 (decompose ідентичність law)
    (00000111
      ((00000011
         (compiler-shape-width (decompose ідентичність))
         (compiler-law-width law))
       (compiler-role-from-l1-l5-bits
         ідентичність
         (compiler-shape-bits (decompose ідентичність))
         law))
      ((compiler-true ідентичність) ()))))


; #3824 — D4 bootstrap-role derivation from the ordered owner-ratified fibre.
; D4-LAW is transported as:
;   (domain-width parent-bits ordered-children)
; where ordered-children is the exact two-child fibre generated from #3272.
; The structure carries no role names.  SENS assigns the first/second
; irreducible bootstrap child to LambdaForm/DefineForm respectively.
(00001001 compiler-d4-law-width
  (00001000 (law)
    (00000101 law)))

(00001001 compiler-d4-law-children
  (00001000 (law)
    (00000101 (00000110 (00000110 law)))))

(00001001 compiler-d4-law-first-child
  (00001000 (law)
    (00000101 (compiler-d4-law-children law))))

(00001001 compiler-d4-law-second-child
  (00001000 (law)
    (00000101 (00000110 (compiler-d4-law-children law)))))

(00001001 compiler-role-from-d4-bootstrap-bits
  (00001000 (seed bits law)
    (00000111
      ((compiler-bits-equal seed bits (compiler-d4-law-first-child law))
       (00000001 lambda-form))
      ((compiler-bits-equal seed bits (compiler-d4-law-second-child law))
       (00000001 define-form))
      ((compiler-true seed) ()))))

(00001001 compiler-role-from-d4-bootstrap
  (00001000 (decompose ідентичність law)
    (00000111
      ((00000011
         (compiler-shape-width (decompose ідентичність))
         (compiler-d4-law-width law))
       (compiler-role-from-d4-bootstrap-bits
         ідентичність
         (compiler-shape-bits (decompose ідентичність))
         law))
      ((compiler-true ідентичність) ()))))

; One production role query for the whole current compiler nucleus.  Domain
; width selects which already-ratified structural law is applicable; neither
; the host nor this function infers meaning from an equal packed payload.
(00001001 compiler-lowering-role-from-l1-l5
  (00001000 (decompose ідентичність law)
    (00000111
      ((00000011
         (compiler-shape-width (decompose ідентичність))
         (compiler-law-width law))
       (compiler-lowering-role-from-l1-l5-bits
         ідентичність
         (compiler-shape-bits (decompose ідентичність))
         law))
      ((compiler-true ідентичність) ()))))

(00001001 compiler-lowering-role-from-laws
  (00001000 (decompose ідентичність d3-law d4-law)
    (00000111
      ((00000011
         (compiler-shape-width (decompose ідентичність))
         (compiler-law-width d3-law))
       (compiler-lowering-role-from-l1-l5 decompose ідентичність d3-law))
      ((00000011
         (compiler-shape-width (decompose ідентичність))
         (compiler-d4-law-width d4-law))
       (compiler-role-from-d4-bootstrap decompose ідентичність d4-law))
      ((compiler-true ідентичність) ()))))


; #3810 — production request cutover.
; Role meaning comes only from compiler-role-from-l1-l5 above.  The host may
; transport LAW/proof/provenance values, but it does not select the role.

(00001001 compiler-request-from-role
  (00001000 (seed ідентичність role proof-ref походження)
    (00000111
      
      ((compiler-true seed)
       (00000100
         ідентичність
         (00000100
           role
           (00000100
             proof-ref
             (00000100 походження ()))))))))

(00001001 compiler-request-from-l1-l5
  (00001000 (decompose ідентичність law proof-ref походження)
    (compiler-request-from-role
      ідентичність
      ідентичність
      (compiler-role-from-l1-l5 decompose ідентичність law)
      proof-ref
      походження)))


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

(00001001 compiler-request-from-laws
  (00001000 (decompose ідентичність d3-law d4-law d3-proof d4-proof походження)
    (00000111
      ((00000011
         (compiler-shape-width (decompose ідентичність))
         (compiler-law-width d3-law))
       (compiler-request-from-role
         ідентичність
         ідентичність
         (compiler-lowering-role-from-l1-l5 decompose ідентичність d3-law)
         d3-proof
         походження))
      ((00000011
         (compiler-shape-width (decompose ідентичність))
         (compiler-d4-law-width d4-law))
       (compiler-request-from-role
         ідентичність
         ідентичність
         (compiler-role-from-d4-bootstrap decompose ідентичність d4-law)
         d4-proof
         походження))
      ((compiler-true ідентичність) ()))))

(00001001 compiler-result-ok
  (00001000 (requests)
    (00000100 (compiler-true ()) requests)))

(00001001 compiler-result-fail
  (00001000 ()
    (00000100 (compiler-false ()) ())))

(00001001 compiler-result-success
  (00001000 (result)
    (00000101 result)))

(00001001 compiler-result-requests
  (00001000 (result)
    (00000110 result)))

(00001001 compiler-append
  (00001000 (left right)
    (00000111
      ((00000010 left) right)
      ((compiler-true ())
       (00000100
         (00000101 left)
         (compiler-append (00000110 left) right))))))

(00001001 compiler-merge-results
  (00001000 (left right)
    (00000111
      ((compiler-result-success left)
       (00000111
         ((compiler-result-success right)
          (compiler-result-ok
            (compiler-append
              (compiler-result-requests left)
              (compiler-result-requests right))))
         ((compiler-true ()) (compiler-result-fail))))
      ((compiler-true ()) (compiler-result-fail)))))

(00001001 compiler-request-role
  (00001000 (request)
    (00000101 (00000110 request))))

; Validate source shape only after SENS has already derived the abstract role.
; This is deliberately role -> arity/shape, never domain-bits -> shape.
(00001001 compiler-exactly-one
  (00001000 (arguments)
    (00000111
      ((00000010 arguments) (compiler-false ()))
      ((00000010 (00000110 arguments))
       (00000111
         ((0100 (00000010 (00000110 arguments))) (compiler-true ()))
         ((compiler-true ()) (compiler-false ()))))
      ((compiler-true ()) (compiler-false ())))))

(00001001 compiler-exactly-two
  (00001000 (arguments)
    (00000111
      ((00000010 arguments) (compiler-false ()))
      ((00000010 (00000110 arguments)) (compiler-false ()))
      ((00000010 (00000110 (00000110 arguments)))
       (00000111
         ((0100 (00000010 (00000110 (00000110 arguments)))) (compiler-true ()))
         ((compiler-true ()) (compiler-false ()))))
      ((compiler-true ()) (compiler-false ())))))

; D4 LAMBDA is parameters plus one-or-more body expressions.
; Runtime create_lambda enforces the same minimum arity and preserves every
; body expression, so the compiler shape law must match that variadic body.
(00001001 compiler-at-least-two
  (00001000 (arguments)
    (00000111
      ((00000010 arguments) (compiler-false ()))
      ((00000010 (00000110 arguments)) (compiler-false ()))
      ((compiler-true ()) (compiler-true ())))))

; Exact D3 COND is a non-empty sequence of two-part (test expression) clauses.
(00001001 compiler-cond-clauses-valid
  (00001000 (clauses)
    (00000111
      ((00000010 clauses) (compiler-true ()))
      ((compiler-exactly-two (00000101 clauses))
       (compiler-cond-clauses-valid (00000110 clauses)))
      ((compiler-true ()) (compiler-false ())))))

(00001001 compiler-role-shape-valid
  (00001000 (request arguments)
    (00000111
      ((00000010 request) (compiler-false ()))
      ((00000011 (compiler-request-role request) (00000001 quote-form))
       (compiler-exactly-one arguments))
      ((00000011 (compiler-request-role request) (00000001 atom-predicate))
       (compiler-exactly-one arguments))
      ((00000011 (compiler-request-role request) (00000001 selector-tail))
       (compiler-exactly-one arguments))
      ((00000011 (compiler-request-role request) (00000001 selector-head))
       (compiler-exactly-one arguments))
      ((00000011 (compiler-request-role request) (00000001 atom-equality))
       (compiler-exactly-two arguments))
      ((00000011 (compiler-request-role request) (00000001 pair-construct))
       (compiler-exactly-two arguments))
      ((00000011 (compiler-request-role request) (00000001 lambda-form))
       (compiler-at-least-two arguments))
      ((00000011 (compiler-request-role request) (00000001 define-form))
       (compiler-exactly-two arguments))
      ((00000011 (compiler-request-role request) (00000001 cond-form))
       (00000111
         ((00000010 arguments) (compiler-false ()))
         ((compiler-true ()) (compiler-cond-clauses-valid arguments))))
      ((compiler-true ()) (compiler-false ())))))

; Program traversal policy is semantic and therefore SENS-owned.
; QUOTE payload is data.  LAMBDA parameters and DEFINE name are data.
; Other admitted forms recursively compile every argument position.
(00001001 compiler-domain-children
  (00001000 (request arguments)
    (00000111
      ((00000010 request) ())
      ((00000011 (compiler-request-role request) (00000001 quote-form)) ())
      ((00000011 (compiler-request-role request) (00000001 lambda-form))
       (00000110 arguments))
      ((00000011 (compiler-request-role request) (00000001 define-form))
       (00000110 arguments))
      ((compiler-true ()) arguments))))

(00001001 compiler-domain-result
  (00001000
    (request arguments child-result)
    (00000111
      ((00000010 request) (compiler-result-fail))
      ((compiler-role-shape-valid request arguments)
       (00000111
         ((compiler-result-success child-result)
          (compiler-result-ok
            (00000100
              request
              (compiler-result-requests child-result))))
         ((compiler-true ()) (compiler-result-fail))))
      ((compiler-true ()) (compiler-result-fail)))))

(00001001 compiler-program-list
  (00001000
    (shape-or-empty decompose nodes d3-law d4-law d3-proof d4-proof походження)
    (00000111
      ((00000010 nodes) (compiler-result-ok ()))
      ((compiler-true ())
       (compiler-merge-results
         (compiler-program-node
           shape-or-empty
           decompose
           (00000101 nodes)
           d3-law
           d4-law
           d3-proof
           d4-proof
           походження)
         (compiler-program-list
           shape-or-empty
           decompose
           (00000110 nodes)
           d3-law
           d4-law
           d3-proof
           d4-proof
           походження))))))

(00001001 compiler-program-node
  (00001000
    (shape-or-empty decompose node d3-law d4-law d3-proof d4-proof походження)
    (00000111
      ((00000010 node) (compiler-result-ok ()))
      ((00000010 (shape-or-empty (00000101 node)))
       (compiler-program-list
         shape-or-empty
         decompose
         node
         d3-law
         d4-law
         d3-proof
         d4-proof
         походження))
      ((compiler-true ())
       (compiler-domain-result
         (compiler-request-from-laws
           decompose
           (00000101 node)
           d3-law
           d4-law
           d3-proof
           d4-proof
           походження)
         (00000110 node)
         (compiler-program-list
           shape-or-empty
           decompose
           (compiler-domain-children
             (compiler-request-from-laws
               decompose
               (00000101 node)
               d3-law
               d4-law
               d3-proof
               d4-proof
               походження)
             (00000110 node))
           d3-law
           d4-law
           d3-proof
           d4-proof
           походження))))))

(00001001 compiler-compile-program
  (00001000
    (shape-or-empty decompose program d3-law d4-law d3-proof d4-proof походження)
    (compiler-program-list
      shape-or-empty
      decompose
      program
      d3-law
      d4-law
      d3-proof
      d4-proof
      походження)))


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
(00001001 compiler-artifact-field
  (00001000 (name value)
    (00000100 name (00000100 value ()))))

(00001001 compiler-artifact-from-result
  (00001000
    (digest program-wire-sha256 artifact-provenance result)
    (00000111
      ((compiler-result-success result)
       (00000100
         (00000001 compiler-compilation-artifact/1)
         (00000100
           (compiler-artifact-field
             (00000001 artifact-kind)
             (00000001 whole-program))
           (00000100
             (compiler-artifact-field
               (00000001 program-wire-sha256)
               program-wire-sha256)
             (00000100
               (compiler-artifact-field
                 (00000001 semantic-requests-sha256)
                 (digest (compiler-result-requests result)))
               (00000100
                 (compiler-artifact-field
                   (00000001 authority-provenance)
                   artifact-provenance)
                 (00000100
                   (compiler-artifact-field
                     (00000001 semantic-requests)
                     (compiler-result-requests result))
                   (00000100
                     (compiler-artifact-field
                       (00000001 required-capabilities)
                       ())
                     (00000100
                       (compiler-artifact-field
                         (00000001 artifact-status)
                         (00000001 canonical-backend-neutral))
                       ())))))))))
      ((compiler-true ())
       (00000100
         (00000001 compiler-compilation-error/1)
         (00000100
           (compiler-artifact-field
             (00000001 program-wire-sha256)
             program-wire-sha256)
           (00000100
             (compiler-artifact-field
               (00000001 error)
               (00000001 compiler-program-rejected))
             ())))))))

(00001001 compiler-compile-program-artifact
  (00001000
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