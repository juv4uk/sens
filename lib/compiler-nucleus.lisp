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

(визначити знайти-авторитет-компілятора
  (функція (ідентичність рядки-для-пошуку-авторитету)
    (за-умовою
      ((атом? рядки-для-пошуку-авторитету) ())
      ((тотожне? ідентичність (перше (перше рядки-для-пошуку-авторитету))) (перше рядки-для-пошуку-авторитету))
      (так (знайти-авторитет-компілятора ідентичність (решта рядки-для-пошуку-авторитету))))))

(визначити compiler-nucleus
  (функція (ідентичність authority)
    (знайти-авторитет-компілятора ідентичність authority)))


; Representation-only bootstrap seam for #3808.
; DECOMPOSE is an explicitly supplied first-class mechanism.  The language
; chooses when to invoke it; the host function may reveal only exact width/bits
; and has no identity->meaning authority.
(визначити compiler-domain-shape
  (функція (розкласти ідентичність)
    (розкласти ідентичність)))


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

(визначити істина-компілятора
  (функція (насіння-локального-компілятора)
    (атом? насіння-локального-компілятора)))

(визначити хиба-компілятора
  (функція (насіння-локального-компілятора)
    ні))

; Exact proper-list end is NIL, not every atom. Derive the observation
; from the admitted D3 ATOM + atom-only D3 EQ laws. N0's compiler ISA
; does not claim a D4 NULL lowering role or invent a callable bridge.
(визначити compiler-list-end?
  (функція (значення)
    (за-умовою
      ((атом? значення) (тотожне? значення (як-є ())))
      (так (хиба-компілятора ())))))

; A verified bit sequence is a proper list of D1 atoms. To test the
; empty-list terminator, use the ratified ATOM predicate, not EQ over a
; non-atomic pair: exact D3 EQ admits two ATOMS, not a list-versus-NIL.
(визначити бітові-послідовності-однакові?
  (функція (насіння-локального-компілятора послідовність-бітів-зліва послідовність-бітів-справа)
    (за-умовою
      ((атом? послідовність-бітів-зліва) (атом? послідовність-бітів-справа))
      ((атом? послідовність-бітів-справа) (хиба-компілятора насіння-локального-компілятора))
      ((тотожне? (перше послідовність-бітів-зліва) (перше послідовність-бітів-справа))
       (бітові-послідовності-однакові? насіння-локального-компілятора (решта послідовність-бітів-зліва) (решта послідовність-бітів-справа)))
      ((істина-компілятора насіння-локального-компілятора) (хиба-компілятора насіння-локального-компілятора)))))

(визначити виключне-або-одного-біту-компілятора
  (функція (насіння-локального-компілятора біт-зліва-компілятора біт-справа-компілятора)
    (за-умовою
      (біт-зліва-компілятора
       (за-умовою
         (біт-справа-компілятора (хиба-компілятора насіння-локального-компілятора))
         ((істина-компілятора насіння-локального-компілятора) (істина-компілятора насіння-локального-компілятора))))
      ((істина-компілятора насіння-локального-компілятора)
       (за-умовою
         (біт-справа-компілятора (істина-компілятора насіння-локального-компілятора))
         ((істина-компілятора насіння-локального-компілятора) (хиба-компілятора насіння-локального-компілятора)))))))

(визначити виключне-або-бітових-послідовностей-компілятора
  (функція (насіння-локального-компілятора послідовність-бітів-зліва послідовність-бітів-справа)
    (за-умовою
      ((атом? послідовність-бітів-зліва) ())
      ((атом? послідовність-бітів-справа) ())
      ((істина-компілятора насіння-локального-компілятора)
       (сполучити
         (виключне-або-одного-біту-компілятора насіння-локального-компілятора (перше послідовність-бітів-зліва) (перше послідовність-бітів-справа))
         (виключне-або-бітових-послідовностей-компілятора насіння-локального-компілятора (решта послідовність-бітів-зліва) (решта послідовність-бітів-справа)))))))

; Exact selectors: D4:1001 CADR, D5:10011 CADDR.
; D6 is ratified but these longer selectors lack executable admission;
; compose admitted D5 and D3 instead. No D7 text/data aliases.
(визначити compiler-shape-width
  (функція (форма)
    (перше форма)))

(визначити compiler-shape-bits
  (функція (форма)
    (перше (решта форма))))

(визначити compiler-law-width
  (функція (закон)
    (перше закон)))

(визначити compiler-law-empty-bits
  (функція (закон)
    (перше (решта закон))))

(визначити compiler-law-xor-mask
  (функція (закон)
    (перше (решта (решта закон)))))

(визначити остов-закону-л5-компілятора
  (функція (закон-остова-л5-компілятора)
    (перше (решта (решта (решта закон-остова-л5-компілятора))))))

(визначити біти-атома-остова-л5-компілятора
  (функція (закон-бітів-атома-л5-компілятора)
    (перше (решта (остов-закону-л5-компілятора закон-бітів-атома-л5-компілятора)))))

(визначити біти-голови-остова-л5-компілятора
  (функція (закон-бітів-голови-л5-компілятора)
    (перше (решта (решта (остов-закону-л5-компілятора закон-бітів-голови-л5-компілятора))))))

(визначити біти-умови-остова-л5-компілятора
  (функція (закон-бітів-умови-л5-компілятора)
    (перше (решта (решта (решта (остов-закону-л5-компілятора закон-бітів-умови-л5-компілятора)))))))

; Full D3 compiler closure is derived only from the ratified L1/L4/L5
; structure.  The three spine roles are read by ordered position; their duals
; are obtained with the one L4 XOR law.  No raw D3 coordinate is embedded here.
(визначити compiler-role-from-l1-l5-bits
  (функція (seed bits law)
    (за-умовою
      ((бітові-послідовності-однакові? seed bits (біти-голови-остова-л5-компілятора law))
       (як-є selector-head))
      ((бітові-послідовності-однакові?
         seed bits
         (виключне-або-бітових-послідовностей-компілятора
           seed
           (біти-голови-остова-л5-компілятора law)
           (compiler-law-xor-mask law)))
       (як-є selector-tail))
      ((бітові-послідовності-однакові?
         seed bits
         (виключне-або-бітових-послідовностей-компілятора
           seed
           (compiler-law-empty-bits law)
           (compiler-law-xor-mask law)))
       (як-є pair-construct))
      ((істина-компілятора seed) ()))))

; Full D3 lowering closure for self-hosting.  It deliberately has a separate
; name so the already-merged three-role execution API remains stable.
(визначити compiler-lowering-role-from-l1-l5-bits
  (функція (seed bits law)
    (за-умовою
      ((бітові-послідовності-однакові?
         seed bits
         (виключне-або-бітових-послідовностей-компілятора
           seed
           (біти-умови-остова-л5-компілятора law)
           (compiler-law-xor-mask law)))
       (як-є quote-form))
      ((бітові-послідовності-однакові? seed bits (біти-атома-остова-л5-компілятора law))
       (як-є atom-predicate))
      ((бітові-послідовності-однакові?
         seed bits
         (виключне-або-бітових-послідовностей-компілятора
           seed
           (біти-голови-остова-л5-компілятора law)
           (compiler-law-xor-mask law)))
       (як-є selector-tail))
      ((бітові-послідовності-однакові? seed bits (біти-голови-остова-л5-компілятора law))
       (як-є selector-head))
      ((бітові-послідовності-однакові?
         seed bits
         (виключне-або-бітових-послідовностей-компілятора
           seed
           (біти-атома-остова-л5-компілятора law)
           (compiler-law-xor-mask law)))
       (як-є atom-equality))
      ((бітові-послідовності-однакові? seed bits (біти-умови-остова-л5-компілятора law))
       (як-є cond-form))
      ((бітові-послідовності-однакові?
         seed bits
         (виключне-або-бітових-послідовностей-компілятора
           seed
           (compiler-law-empty-bits law)
           (compiler-law-xor-mask law)))
       (як-є pair-construct))
      ((істина-компілятора seed) ()))))

(визначити compiler-role-from-l1-l5
  (функція (decompose ідентичність law)
    (за-умовою
      ((тотожне?
         (compiler-shape-width (decompose ідентичність))
         (compiler-law-width law))
       (compiler-role-from-l1-l5-bits
         ідентичність
         (compiler-shape-bits (decompose ідентичність))
         law))
      ((істина-компілятора ідентичність) ()))))


; #3824 — D4 bootstrap-role derivation from the ordered owner-ratified fibre.
; D4-LAW is transported as:
;   (domain-width parent-bits ordered-children)
; where ordered-children is the exact two-child fibre generated from #3272.
; The structure carries no role names.  SENS assigns the first/second
; irreducible bootstrap child to LambdaForm/DefineForm respectively.
; Bootstrap uses exact D3 CAR/CDR compositions for selector access;
; canonical D4:1001 CADR and D5:10011 CADDR keep their separate identities.
; The compiler's present lowering law does not yet admit D5 calls.
; The domain width remains part of the callable identity; no D6/D7 alias.
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
      ((бітові-послідовності-однакові? seed bits (compiler-d4-law-first-child law))
       (як-є lambda-form))
      ((бітові-послідовності-однакові? seed bits (compiler-d4-law-second-child law))
       (як-є define-form))
      ((істина-компілятора seed) ()))))

(визначити compiler-role-from-d4-bootstrap
  (функція (decompose ідентичність law)
    (за-умовою
      ((тотожне?
         (compiler-shape-width (decompose ідентичність))
         (compiler-d4-law-width law))
       (compiler-role-from-d4-bootstrap-bits
         ідентичність
         (compiler-shape-bits (decompose ідентичність))
         law))
      ((істина-компілятора ідентичність) ()))))

; One production role query for the whole current compiler nucleus.  Domain
; width selects which already-ratified structural law is applicable; neither
; the host nor this function infers meaning from an equal packed payload.
(визначити compiler-lowering-role-from-l1-l5
  (функція (decompose ідентичність law)
    (за-умовою
      ((тотожне?
         (compiler-shape-width (decompose ідентичність))
         (compiler-law-width law))
       (compiler-lowering-role-from-l1-l5-bits
         ідентичність
         (compiler-shape-bits (decompose ідентичність))
         law))
      ((істина-компілятора ідентичність) ()))))

(визначити compiler-lowering-role-from-laws
  (функція (decompose ідентичність d3-law d4-law)
    (за-умовою
      ((тотожне?
         (compiler-shape-width (decompose ідентичність))
         (compiler-law-width d3-law))
       (compiler-lowering-role-from-l1-l5 decompose ідентичність d3-law))
      ((тотожне?
         (compiler-shape-width (decompose ідентичність))
         (compiler-d4-law-width d4-law))
       (compiler-role-from-d4-bootstrap decompose ідентичність d4-law))
      ((істина-компілятора ідентичність) ()))))


; #3810 — production request cutover.
; Role meaning comes only from compiler-role-from-l1-l5 above.  The host may
; transport LAW/proof/provenance values, but it does not select the role.

; Empty role means the law did not admit this identity. Do not emit a
; malformed request carrying (), especially for a wrong-width domain.
; Empty role is NIL, which is itself an atom in this language. Test
; exact equality with () before emitting a compiler request.
(визначити compiler-request-from-role
  (функція (seed ідентичність role proof-ref походження)
    (за-умовою
      ((тотожне? role ()) ())
      ((істина-компілятора seed)
       (сполучити
         ідентичність
         (сполучити
           role
           (сполучити
             proof-ref
             (сполучити походження ()))))))))

(визначити compiler-request-from-l1-l5
  (функція (decompose ідентичність law proof-ref походження)
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

(визначити compiler-request-from-laws
  (функція (decompose ідентичність d3-law d4-law d3-proof d4-proof походження)
    (за-умовою
      ((тотожне?
         (compiler-shape-width (decompose ідентичність))
         (compiler-law-width d3-law))
       (compiler-request-from-role
         ідентичність
         ідентичність
         (compiler-lowering-role-from-l1-l5 decompose ідентичність d3-law)
         d3-proof
         походження))
      ((тотожне?
         (compiler-shape-width (decompose ідентичність))
         (compiler-d4-law-width d4-law))
       (compiler-request-from-role
         ідентичність
         ідентичність
         (compiler-role-from-d4-bootstrap decompose ідентичність d4-law)
         d4-proof
         походження))
      ((істина-компілятора ідентичність) ()))))

(визначити compiler-result-ok
  (функція (requests)
    (сполучити (істина-компілятора ()) requests)))

(визначити compiler-result-fail
  (функція ()
    (сполучити (хиба-компілятора ()) ())))

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
      ((істина-компілятора ())
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
         ((істина-компілятора ()) (compiler-result-fail))))
      ((істина-компілятора ()) (compiler-result-fail)))))

(визначити compiler-request-role
  (функція (request)
    (перше (решта request))))

; Validate source shape only after SENS has already derived the abstract role.
; This is deliberately role -> arity/shape, never domain-bits -> shape.
; Arguments are proper SENS compiler-program-data lists.  Exact cardinality
; must be tested using the D3 ATOM predicate on the tail, not a D4
; operator applied to an already-computed D1 predicate bit.
(визначити compiler-exactly-one
  (функція (arguments)
    (за-умовою
      ((атом? arguments) (хиба-компілятора ()))
      ((compiler-list-end? (решта arguments)) (істина-компілятора ()))
      ((істина-компілятора ()) (хиба-компілятора ())))))

(визначити compiler-exactly-two
  (функція (arguments)
    (за-умовою
      ((атом? arguments) (хиба-компілятора ()))
      ((атом? (решта arguments)) (хиба-компілятора ()))
      ((compiler-list-end? (решта (решта arguments))) (істина-компілятора ()))
      ((істина-компілятора ()) (хиба-компілятора ())))))

; Proper variadic tails: only the exact EMPTY terminates a list.
; D3 ATOM detects a malformed nonempty atom; EQ sees EMPTY only after ATOM.
; The already-admitted compiler-list-end? owns that distinction in SENS.
(визначити compiler-proper-tail?
  (функція (tail)
    (за-умовою
      ((compiler-list-end? tail) (істина-компілятора ()))
      ((атом? tail) (хиба-компілятора ()))
      (так (compiler-proper-tail? (решта tail))))))

; D4 LAMBDA is parameters plus one-or-more body expressions.
; Both mandatory argument cells must be pairs, and all remaining cells must
; form a proper list; nested data elements may themselves be dotted pairs.
(визначити compiler-at-least-two
  (функція (arguments)
    (за-умовою
      ((атом? arguments) (хиба-компілятора ()))
      ((атом? (решта arguments)) (хиба-компілятора ()))
      (так (compiler-proper-tail? (решта (решта arguments)))))))

; Exact D3 COND is a non-empty sequence of two-part (test expression) clauses.
(визначити compiler-cond-clauses-valid
  (функція (clauses)
    (за-умовою
      ((compiler-list-end? clauses) (істина-компілятора ()))
      ((атом? clauses) (хиба-компілятора ()))
      ((compiler-exactly-two (перше clauses))
       (compiler-cond-clauses-valid (решта clauses)))
      ((істина-компілятора ()) (хиба-компілятора ())))))

(визначити compiler-role-shape-valid
  (функція (request arguments)
    (за-умовою
      ((атом? request) (хиба-компілятора ()))
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
         ((атом? arguments) (хиба-компілятора ()))
         ((істина-компілятора ()) (compiler-cond-clauses-valid arguments))))
      ((істина-компілятора ()) (хиба-компілятора ())))))

; Program traversal policy is semantic and therefore SENS-owned.
; QUOTE payload is data.  LAMBDA parameters and DEFINE name are data.
; Other admitted forms recursively compile every argument position.
; Exact D3 COND clauses are pairs of source expressions, not
; calls whose head is the D1 predicate. Flatten each admitted pair into
; predicate, result, then the remaining clauses. D3 handles the traversal;
; no new domain coordinate or callable slot is created.
(визначити compiler-cond-child-expressions
  (функція (clauses)
    (за-умовою
      ((атом? clauses) ())
      ((compiler-exactly-two (перше clauses))
       (сполучити
         (перше (перше clauses))
         (сполучити
           (перше (решта (перше clauses)))
           (compiler-cond-child-expressions (решта clauses)))))
      (так ()))))

(визначити compiler-domain-children
  (функція (request arguments)
    (за-умовою
      ((атом? request) ())
      ((тотожне? (compiler-request-role request) (як-є quote-form)) ())
      ((тотожне? (compiler-request-role request) (як-є lambda-form))
       (решта arguments))
      ((тотожне? (compiler-request-role request) (як-є define-form))
       (решта arguments))
      ((тотожне? (compiler-request-role request) (як-є cond-form))
       (compiler-cond-child-expressions arguments))
      ((істина-компілятора ()) arguments))))

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
         ((істина-компілятора ()) (compiler-result-fail))))
      ((істина-компілятора ()) (compiler-result-fail)))))

; Tail-position list traversal keeps stack bounded by expression nesting,
; not by the number of sibling forms. The accumulator stores requests reversed.
; Request selection and failure remain entirely SENS-owned.
(визначити compiler-reverse-onto
  (функція (items accumulator)
    (за-умовою
      ((атом? items) accumulator)
      ((істина-компілятора ())
       (compiler-reverse-onto
         (решта items)
         (сполучити (перше items) accumulator))))))

(визначити compiler-program-list-continue
  (функція
    (shape-or-empty decompose node-result remaining d3-law d4-law d3-proof d4-proof походження accumulator)
    (за-умовою
      ((compiler-result-success node-result)
       (compiler-program-list-acc
         shape-or-empty
         decompose
         remaining
         d3-law
         d4-law
         d3-proof
         d4-proof
         походження
         (compiler-reverse-onto
           (compiler-result-requests node-result)
           accumulator)))
      ((істина-компілятора ()) (compiler-result-fail)))))

(визначити compiler-program-list-acc
  (функція
    (shape-or-empty decompose nodes d3-law d4-law d3-proof d4-proof походження accumulator)
    (за-умовою
      ((compiler-list-end? nodes)
       (compiler-result-ok (compiler-reverse-onto accumulator ())))
      ((атом? nodes) (compiler-result-fail))
      ((істина-компілятора ())
       (compiler-program-list-continue
         shape-or-empty
         decompose
         (compiler-program-node
           shape-or-empty
           decompose
           (перше nodes)
           d3-law
           d4-law
           d3-proof
           d4-proof
           походження)
         (решта nodes)
         d3-law
         d4-law
         d3-proof
         d4-proof
         походження
         accumulator)))))

(визначити compiler-program-list
  (функція
    (shape-or-empty decompose nodes d3-law d4-law d3-proof d4-proof походження)
    (compiler-program-list-acc
      shape-or-empty
      decompose
      nodes
      d3-law
      d4-law
      d3-proof
      d4-proof
      походження
      ())))

(визначити compiler-program-node
  (функція
    (shape-or-empty decompose node d3-law d4-law d3-proof d4-proof походження)
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
         походження))
      ((істина-компілятора ())
       (compiler-domain-result
         (compiler-request-from-laws
           decompose
           (перше node)
           d3-law
           d4-law
           d3-proof
           d4-proof
           походження)
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
               походження)
             (решта node))
           d3-law
           d4-law
           d3-proof
           d4-proof
           походження))))))

(визначити compiler-compile-program
  (функція
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
      ((істина-компілятора ())
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