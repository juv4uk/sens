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

(0011 compiler-authority-find
  (0010 (ідентичність rows)
    (110
      ((0101 rows) ())
      ((101 ідентичність (100 (100 rows))) (100 rows))
      ((compiler-true ідентичність)
       (compiler-authority-find ідентичність (011 rows))))))

(0011 compiler-nucleus
  (0010 (ідентичність authority)
    (compiler-authority-find ідентичність authority)))


; Representation-only bootstrap seam for #3808.
; DECOMPOSE is an explicitly supplied first-class mechanism.  The language
; chooses when to invoke it; the host function may reveal only exact width/bits
; and has no identity->meaning authority.
(0011 compiler-domain-shape
  (0010 (decompose ідентичність)
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

(0011 compiler-true
  (0010 (seed)
    (010 seed)))

(0011 compiler-false
  (0010 (seed)
    (010 (111 seed ()))))

(0011 compiler-bits-equal
  (0010 (seed left right)
    (110
      ((010 left) (010 right))
      ((010 right) (compiler-false seed))
      ((101 (100 left) (100 right))
       (compiler-bits-equal seed (011 left) (011 right)))
      ((compiler-true seed) (compiler-false seed)))))

(0011 compiler-bit-xor
  (0010 (seed left right)
    (110
      ((101 left right) (compiler-false seed))
      ((compiler-true seed) (compiler-true seed)))))

(0011 compiler-xor-bits
  (0010 (seed left right)
    (110
      ((010 left)
       (110
         ((010 right) ())
         ((compiler-true seed) ())))
      ((010 right) ())
      ((compiler-true seed)
       (111
         (compiler-bit-xor seed (100 left) (100 right))
         (compiler-xor-bits seed (011 left) (011 right)))))))

(0011 compiler-shape-width
  (0010 (shape)
    (100 shape)))

(0011 compiler-shape-bits
  (0010 (shape)
    (100 (011 shape))))

(0011 compiler-law-width
  (0010 (law)
    (100 law)))

(0011 compiler-law-empty-bits
  (0010 (law)
    (100 (011 law))))

(0011 compiler-law-xor-mask
  (0010 (law)
    (100 (011 (011 law)))))

(0011 compiler-law-l5-spine
  (0010 (law)
    (100 (011 (011 (011 law))))))

(0011 compiler-law-l5-atom-bits
  (0010 (law)
    (100 (011 (compiler-law-l5-spine law)))))

(0011 compiler-law-l5-head-bits
  (0010 (law)
    (100 (011 (011 (compiler-law-l5-spine law))))))

(0011 compiler-law-l5-cond-bits
  (0010 (law)
    (100 (011 (011 (011 (compiler-law-l5-spine law)))))))

; Full D3 compiler closure is derived only from the ratified L1/L4/L5
; structure.  The three spine roles are read by ordered position; their duals
; are obtained with the one L4 XOR law.  No raw D3 coordinate is embedded here.
(0011 compiler-role-from-l1-l5-bits
  (0010 (seed bits law)
    (110
      ((compiler-bits-equal seed bits (compiler-law-l5-head-bits law))
       (001 selector-head))
      ((compiler-bits-equal
         seed bits
         (compiler-xor-bits
           seed
           (compiler-law-l5-head-bits law)
           (compiler-law-xor-mask law)))
       (001 selector-tail))
      ((compiler-bits-equal
         seed bits
         (compiler-xor-bits
           seed
           (compiler-law-empty-bits law)
           (compiler-law-xor-mask law)))
       (001 pair-construct))
      ((compiler-true seed) ()))))

; Full D3 lowering closure for self-hosting.  It deliberately has a separate
; name so the already-merged three-role execution API remains stable.
(0011 compiler-lowering-role-from-l1-l5-bits
  (0010 (seed bits law)
    (110
      ((compiler-bits-equal
         seed bits
         (compiler-xor-bits
           seed
           (compiler-law-l5-cond-bits law)
           (compiler-law-xor-mask law)))
       (001 quote-form))
      ((compiler-bits-equal seed bits (compiler-law-l5-atom-bits law))
       (001 atom-predicate))
      ((compiler-bits-equal
         seed bits
         (compiler-xor-bits
           seed
           (compiler-law-l5-head-bits law)
           (compiler-law-xor-mask law)))
       (001 selector-tail))
      ((compiler-bits-equal seed bits (compiler-law-l5-head-bits law))
       (001 selector-head))
      ((compiler-bits-equal
         seed bits
         (compiler-xor-bits
           seed
           (compiler-law-l5-atom-bits law)
           (compiler-law-xor-mask law)))
       (001 atom-equality))
      ((compiler-bits-equal seed bits (compiler-law-l5-cond-bits law))
       (001 cond-form))
      ((compiler-bits-equal
         seed bits
         (compiler-xor-bits
           seed
           (compiler-law-empty-bits law)
           (compiler-law-xor-mask law)))
       (001 pair-construct))
      ((compiler-true seed) ()))))

(0011 compiler-role-from-l1-l5
  (0010 (decompose ідентичність law)
    (110
      ((101
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
(0011 compiler-d4-law-width
  (0010 (law)
    (100 law)))

(0011 compiler-d4-law-children
  (0010 (law)
    (100 (011 (011 law)))))

(0011 compiler-d4-law-first-child
  (0010 (law)
    (100 (compiler-d4-law-children law))))

(0011 compiler-d4-law-second-child
  (0010 (law)
    (100 (011 (compiler-d4-law-children law)))))

(0011 compiler-role-from-d4-bootstrap-bits
  (0010 (seed bits law)
    (110
      ((compiler-bits-equal seed bits (compiler-d4-law-first-child law))
       (001 lambda-form))
      ((compiler-bits-equal seed bits (compiler-d4-law-second-child law))
       (001 define-form))
      ((compiler-true seed) ()))))

(0011 compiler-role-from-d4-bootstrap
  (0010 (decompose ідентичність law)
    (110
      ((101
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
(0011 compiler-lowering-role-from-l1-l5
  (0010 (decompose ідентичність law)
    (110
      ((101
         (compiler-shape-width (decompose ідентичність))
         (compiler-law-width law))
       (compiler-lowering-role-from-l1-l5-bits
         ідентичність
         (compiler-shape-bits (decompose ідентичність))
         law))
      ((compiler-true ідентичність) ()))))

(0011 compiler-lowering-role-from-laws
  (0010 (decompose ідентичність d3-law d4-law)
    (110
      ((101
         (compiler-shape-width (decompose ідентичність))
         (compiler-law-width d3-law))
       (compiler-lowering-role-from-l1-l5 decompose ідентичність d3-law))
      ((101
         (compiler-shape-width (decompose ідентичність))
         (compiler-d4-law-width d4-law))
       (compiler-role-from-d4-bootstrap decompose ідентичність d4-law))
      ((compiler-true ідентичність) ()))))


; #3810 — production request cutover.
; Role meaning comes only from compiler-role-from-l1-l5 above.  The host may
; transport LAW/proof/provenance values, but it does not select the role.

(0011 compiler-request-from-role
  (0010 (seed ідентичність role proof-ref походження)
    (110
      ((101 role ()) ())
      ((compiler-true seed)
       (111
         ідентичність
         (111
           role
           (111
             proof-ref
             (111 походження ()))))))))

(0011 compiler-request-from-l1-l5
  (0010 (decompose ідентичність law proof-ref походження)
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

(0011 compiler-request-from-laws
  (0010 (decompose ідентичність d3-law d4-law d3-proof d4-proof походження)
    (110
      ((101
         (compiler-shape-width (decompose ідентичність))
         (compiler-law-width d3-law))
       (compiler-request-from-role
         ідентичність
         ідентичність
         (compiler-lowering-role-from-l1-l5 decompose ідентичність d3-law)
         d3-proof
         походження))
      ((101
         (compiler-shape-width (decompose ідентичність))
         (compiler-d4-law-width d4-law))
       (compiler-request-from-role
         ідентичність
         ідентичність
         (compiler-role-from-d4-bootstrap decompose ідентичність d4-law)
         d4-proof
         походження))
      ((compiler-true ідентичність) ()))))

(0011 compiler-result-ok
  (0010 (requests)
    (111 (compiler-true ()) requests)))

(0011 compiler-result-fail
  (0010 ()
    (111 (compiler-false ()) ())))

(0011 compiler-result-success
  (0010 (result)
    (100 result)))

(0011 compiler-result-requests
  (0010 (result)
    (011 result)))

(0011 compiler-append
  (0010 (left right)
    (110
      ((010 left) right)
      ((compiler-true ())
       (111
         (100 left)
         (compiler-append (011 left) right))))))

(0011 compiler-merge-results
  (0010 (left right)
    (110
      ((compiler-result-success left)
       (110
         ((compiler-result-success right)
          (compiler-result-ok
            (compiler-append
              (compiler-result-requests left)
              (compiler-result-requests right))))
         ((compiler-true ()) (compiler-result-fail))))
      ((compiler-true ()) (compiler-result-fail)))))

(0011 compiler-request-role
  (0010 (request)
    (100 (011 request))))

; Validate source shape only after SENS has already derived the abstract role.
; This is deliberately role -> arity/shape, never domain-bits -> shape.
(0011 compiler-exactly-one
  (0010 (arguments)
    (110
      ((010 arguments) (compiler-false ()))
      ((010 (011 arguments))
       (110
         ((101 (011 arguments) ()) (compiler-true ()))
         ((compiler-true ()) (compiler-false ()))))
      ((compiler-true ()) (compiler-false ())))))

(0011 compiler-exactly-two
  (0010 (arguments)
    (110
      ((010 arguments) (compiler-false ()))
      ((010 (011 arguments)) (compiler-false ()))
      ((010 (011 (011 arguments)))
       (110
         ((101 (011 (011 arguments)) ()) (compiler-true ()))
         ((compiler-true ()) (compiler-false ()))))
      ((compiler-true ()) (compiler-false ())))))

; D4 LAMBDA is parameters plus one-or-more body expressions.
; Runtime create_lambda enforces the same minimum arity and preserves every
; body expression, so the compiler shape law must match that variadic body.
(0011 compiler-at-least-two
  (0010 (arguments)
    (110
      ((010 arguments) (compiler-false ()))
      ((010 (011 arguments)) (compiler-false ()))
      ((compiler-true ()) (compiler-true ())))))

; Exact D3 COND is a non-empty sequence of two-part (test expression) clauses.
(0011 compiler-cond-clauses-valid
  (0010 (clauses)
    (110
      ((010 clauses) (compiler-true ()))
      ((compiler-exactly-two (100 clauses))
       (compiler-cond-clauses-valid (011 clauses)))
      ((compiler-true ()) (compiler-false ())))))

(0011 compiler-role-shape-valid
  (0010 (request arguments)
    (110
      ((010 request) (compiler-false ()))
      ((101 (compiler-request-role request) (001 quote-form))
       (compiler-exactly-one arguments))
      ((101 (compiler-request-role request) (001 atom-predicate))
       (compiler-exactly-one arguments))
      ((101 (compiler-request-role request) (001 selector-tail))
       (compiler-exactly-one arguments))
      ((101 (compiler-request-role request) (001 selector-head))
       (compiler-exactly-one arguments))
      ((101 (compiler-request-role request) (001 atom-equality))
       (compiler-exactly-two arguments))
      ((101 (compiler-request-role request) (001 pair-construct))
       (compiler-exactly-two arguments))
      ((101 (compiler-request-role request) (001 lambda-form))
       (compiler-at-least-two arguments))
      ((101 (compiler-request-role request) (001 define-form))
       (compiler-exactly-two arguments))
      ((101 (compiler-request-role request) (001 cond-form))
       (110
         ((010 arguments) (compiler-false ()))
         ((compiler-true ()) (compiler-cond-clauses-valid arguments))))
      ((compiler-true ()) (compiler-false ())))))

; Program traversal policy is semantic and therefore SENS-owned.
; QUOTE payload is data.  LAMBDA parameters and DEFINE name are data.
; Other admitted forms recursively compile every argument position.
(0011 compiler-domain-children
  (0010 (request arguments)
    (110
      ((010 request) ())
      ((101 (compiler-request-role request) (001 quote-form)) ())
      ((101 (compiler-request-role request) (001 lambda-form))
       (011 arguments))
      ((101 (compiler-request-role request) (001 define-form))
       (011 arguments))
      ((compiler-true ()) arguments))))

(0011 compiler-domain-result
  (0010
    (request arguments child-result)
    (110
      ((010 request) (compiler-result-fail))
      ((compiler-role-shape-valid request arguments)
       (110
         ((compiler-result-success child-result)
          (compiler-result-ok
            (111
              request
              (compiler-result-requests child-result))))
         ((compiler-true ()) (compiler-result-fail))))
      ((compiler-true ()) (compiler-result-fail)))))

(0011 compiler-program-list
  (0010
    (shape-or-empty decompose nodes d3-law d4-law d3-proof d4-proof походження)
    (110
      ((010 nodes) (compiler-result-ok ()))
      ((compiler-true ())
       (compiler-merge-results
         (compiler-program-node
           shape-or-empty
           decompose
           (100 nodes)
           d3-law
           d4-law
           d3-proof
           d4-proof
           походження)
         (compiler-program-list
           shape-or-empty
           decompose
           (011 nodes)
           d3-law
           d4-law
           d3-proof
           d4-proof
           походження))))))

(0011 compiler-program-node
  (0010
    (shape-or-empty decompose node d3-law d4-law d3-proof d4-proof походження)
    (110
      ((010 node) (compiler-result-ok ()))
      ((010 (shape-or-empty (100 node)))
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
           (100 node)
           d3-law
           d4-law
           d3-proof
           d4-proof
           походження)
         (011 node)
         (compiler-program-list
           shape-or-empty
           decompose
           (compiler-domain-children
             (compiler-request-from-laws
               decompose
               (100 node)
               d3-law
               d4-law
               d3-proof
               d4-proof
               походження)
             (011 node))
           d3-law
           d4-law
           d3-proof
           d4-proof
           походження))))))

(0011 compiler-compile-program
  (0010
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
(0011 compiler-artifact-field
  (0010 (name value)
    (111 name (111 value ()))))

(0011 compiler-artifact-from-result
  (0010
    (digest program-wire-sha256 artifact-provenance result)
    (110
      ((compiler-result-success result)
       (111
         (001 compiler-compilation-artifact/1)
         (111
           (compiler-artifact-field
             (001 artifact-kind)
             (001 whole-program))
           (111
             (compiler-artifact-field
               (001 program-wire-sha256)
               program-wire-sha256)
             (111
               (compiler-artifact-field
                 (001 semantic-requests-sha256)
                 (digest (compiler-result-requests result)))
               (111
                 (compiler-artifact-field
                   (001 authority-provenance)
                   artifact-provenance)
                 (111
                   (compiler-artifact-field
                     (001 semantic-requests)
                     (compiler-result-requests result))
                   (111
                     (compiler-artifact-field
                       (001 required-capabilities)
                       ())
                     (111
                       (compiler-artifact-field
                         (001 artifact-status)
                         (001 canonical-backend-neutral))
                       ())))))))))
      ((compiler-true ())
       (111
         (001 compiler-compilation-error/1)
         (111
           (compiler-artifact-field
             (001 program-wire-sha256)
             program-wire-sha256)
           (111
             (compiler-artifact-field
               (001 error)
               (001 compiler-program-rejected))
             ())))))))

(0011 compiler-compile-program-artifact
  (0010
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
