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
  (функція (ідентичність джерело-авторитету)
    (знайти-авторитет-компілятора ідентичність джерело-авторитету)))


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
(визначити компілятор-ширина-форми
  (функція (форма)
    (перше форма)))

(визначити компілятор-біти-форми
  (функція (форма)
    (перше (решта форма))))

(визначити компілятор-ширина-закону
  (функція (закон)
    (перше закон)))

(визначити компілятор-порожні-біти-закону
  (функція (закон)
    (перше (решта закон))))

(визначити компілятор-маска-виключного-або-закону
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
  (функція (початковий-код біти-координати закон-домену)
    (за-умовою
      ((бітові-послідовності-однакові? початковий-код біти-координати (біти-голови-остова-л5-компілятора закон-домену))
       (як-є selector-head))
      ((бітові-послідовності-однакові?
         початковий-код біти-координати
         (виключне-або-бітових-послідовностей-компілятора
           початковий-код
           (біти-голови-остова-л5-компілятора закон-домену)
           (компілятор-маска-виключного-або-закону закон-домену)))
       (як-є selector-tail))
      ((бітові-послідовності-однакові?
         початковий-код біти-координати
         (виключне-або-бітових-послідовностей-компілятора
           початковий-код
           (компілятор-порожні-біти-закону закон-домену)
           (компілятор-маска-виключного-або-закону закон-домену)))
       (як-є pair-construct))
      ((істина-компілятора початковий-код) ()))))

; Full D3 lowering closure for self-hosting.  It deliberately has a separate
; name so the already-merged three-role execution API remains stable.
(визначити compiler-lowering-role-from-l1-l5-bits
  (функція (початковий-код біти-координати закон-домену)
    (за-умовою
      ((бітові-послідовності-однакові?
         початковий-код біти-координати
         (виключне-або-бітових-послідовностей-компілятора
           початковий-код
           (біти-умови-остова-л5-компілятора закон-домену)
           (компілятор-маска-виключного-або-закону закон-домену)))
       (як-є quote-form))
      ((бітові-послідовності-однакові? початковий-код біти-координати (біти-атома-остова-л5-компілятора закон-домену))
       (як-є atom-predicate))
      ((бітові-послідовності-однакові?
         початковий-код біти-координати
         (виключне-або-бітових-послідовностей-компілятора
           початковий-код
           (біти-голови-остова-л5-компілятора закон-домену)
           (компілятор-маска-виключного-або-закону закон-домену)))
       (як-є selector-tail))
      ((бітові-послідовності-однакові? початковий-код біти-координати (біти-голови-остова-л5-компілятора закон-домену))
       (як-є selector-head))
      ((бітові-послідовності-однакові?
         початковий-код біти-координати
         (виключне-або-бітових-послідовностей-компілятора
           початковий-код
           (біти-атома-остова-л5-компілятора закон-домену)
           (компілятор-маска-виключного-або-закону закон-домену)))
       (як-є atom-equality))
      ((бітові-послідовності-однакові? початковий-код біти-координати (біти-умови-остова-л5-компілятора закон-домену))
       (як-є cond-form))
      ((бітові-послідовності-однакові?
         початковий-код біти-координати
         (виключне-або-бітових-послідовностей-компілятора
           початковий-код
           (компілятор-порожні-біти-закону закон-домену)
           (компілятор-маска-виключного-або-закону закон-домену)))
       (як-є pair-construct))
      ((істина-компілятора початковий-код) ()))))

(визначити compiler-role-from-l1-l5
  (функція (розкласти-ідентичність ідентичність закон-домену)
    (за-умовою
      ((тотожне?
         (компілятор-ширина-форми (розкласти-ідентичність ідентичність))
         (компілятор-ширина-закону закон-домену))
       (compiler-role-from-l1-l5-bits
         ідентичність
         (компілятор-біти-форми (розкласти-ідентичність ідентичність))
         закон-домену))
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
  (функція (закон-домену)
    (перше закон-домену)))

(визначити compiler-d4-law-children
  (функція (закон-домену)
    (перше (решта (решта закон-домену)))))

(визначити compiler-d4-law-first-child
  (функція (закон-домену)
    (перше (compiler-d4-law-children закон-домену))))

(визначити compiler-d4-law-second-child
  (функція (закон-домену)
    (перше (решта (compiler-d4-law-children закон-домену)))))

(визначити compiler-role-from-d4-bootstrap-bits
  (функція (початковий-код біти-координати закон-домену)
    (за-умовою
      ((бітові-послідовності-однакові? початковий-код біти-координати (compiler-d4-law-first-child закон-домену))
       (як-є lambda-form))
      ((бітові-послідовності-однакові? початковий-код біти-координати (compiler-d4-law-second-child закон-домену))
       (як-є define-form))
      ((істина-компілятора початковий-код) ()))))

(визначити compiler-role-from-d4-bootstrap
  (функція (розкласти-ідентичність ідентичність закон-домену)
    (за-умовою
      ((тотожне?
         (компілятор-ширина-форми (розкласти-ідентичність ідентичність))
         (compiler-d4-law-width закон-домену))
       (compiler-role-from-d4-bootstrap-bits
         ідентичність
         (компілятор-біти-форми (розкласти-ідентичність ідентичність))
         закон-домену))
      ((істина-компілятора ідентичність) ()))))

; One production role query for the whole current compiler nucleus.  Domain
; width selects which already-ratified structural law is applicable; neither
; the host nor this function infers meaning from an equal packed payload.
(визначити compiler-lowering-role-from-l1-l5
  (функція (розкласти-ідентичність ідентичність закон-домену)
    (за-умовою
      ((тотожне?
         (компілятор-ширина-форми (розкласти-ідентичність ідентичність))
         (компілятор-ширина-закону закон-домену))
       (compiler-lowering-role-from-l1-l5-bits
         ідентичність
         (компілятор-біти-форми (розкласти-ідентичність ідентичність))
         закон-домену))
      ((істина-компілятора ідентичність) ()))))

(визначити compiler-lowering-role-from-laws
  (функція (розкласти-ідентичність ідентичність закон-д3 закон-д4)
    (за-умовою
      ((тотожне?
         (компілятор-ширина-форми (розкласти-ідентичність ідентичність))
         (компілятор-ширина-закону закон-д3))
       (compiler-lowering-role-from-l1-l5 розкласти-ідентичність ідентичність закон-д3))
      ((тотожне?
         (компілятор-ширина-форми (розкласти-ідентичність ідентичність))
         (compiler-d4-law-width закон-д4))
       (compiler-role-from-d4-bootstrap розкласти-ідентичність ідентичність закон-д4))
      ((істина-компілятора ідентичність) ()))))


; #3810 — production request cutover.
; Role meaning comes only from compiler-role-from-l1-l5 above.  The host may
; transport LAW/proof/provenance values, but it does not select the role.

; Empty role means the law did not admit this identity. Do not emit a
; malformed request carrying (), especially for a wrong-width domain.
; Empty role is NIL, which is itself an atom in this language. Test
; exact equality with () before emitting a compiler request.
(визначити compiler-request-from-role
  (функція (початковий-код ідентичність роль-виконання посилання-на-доказ походження)
    (за-умовою
      ((тотожне? роль-виконання ()) ())
      ((істина-компілятора початковий-код)
       (сполучити
         ідентичність
         (сполучити
           роль-виконання
           (сполучити
             посилання-на-доказ
             (сполучити походження ()))))))))

(визначити compiler-request-from-l1-l5
  (функція (розкласти-ідентичність ідентичність закон-домену посилання-на-доказ походження)
    (compiler-request-from-role
      ідентичність
      ідентичність
      (compiler-role-from-l1-l5 розкласти-ідентичність ідентичність закон-домену)
      посилання-на-доказ
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
  (функція (розкласти-ідентичність ідентичність закон-д3 закон-д4 доказ-д3 доказ-д4 походження)
    (за-умовою
      ((тотожне?
         (компілятор-ширина-форми (розкласти-ідентичність ідентичність))
         (компілятор-ширина-закону закон-д3))
       (compiler-request-from-role
         ідентичність
         ідентичність
         (compiler-lowering-role-from-l1-l5 розкласти-ідентичність ідентичність закон-д3)
         доказ-д3
         походження))
      ((тотожне?
         (компілятор-ширина-форми (розкласти-ідентичність ідентичність))
         (compiler-d4-law-width закон-д4))
       (compiler-request-from-role
         ідентичність
         ідентичність
         (compiler-role-from-d4-bootstrap розкласти-ідентичність ідентичність закон-д4)
         доказ-д4
         походження))
      ((істина-компілятора ідентичність) ()))))

(визначити compiler-result-ok
  (функція (запити)
    (сполучити (істина-компілятора ()) запити)))

(визначити compiler-result-fail
  (функція ()
    (сполучити (хиба-компілятора ()) ())))

(визначити compiler-result-success
  (функція (результат)
    (перше результат)))

(визначити compiler-result-requests
  (функція (результат)
    (решта результат)))

(визначити compiler-append
  (функція (лівий правий)
    (за-умовою
      ((атом? лівий) правий)
      ((істина-компілятора ())
       (сполучити
         (перше лівий)
         (compiler-append (решта лівий) правий))))))

(визначити compiler-merge-results
  (функція (лівий правий)
    (за-умовою
      ((compiler-result-success лівий)
       (за-умовою
         ((compiler-result-success правий)
          (compiler-result-ok
            (compiler-append
              (compiler-result-requests лівий)
              (compiler-result-requests правий))))
         ((істина-компілятора ()) (compiler-result-fail))))
      ((істина-компілятора ()) (compiler-result-fail)))))

(визначити compiler-request-role
  (функція (запит)
    (перше (решта запит))))

; Validate source shape only after SENS has already derived the abstract role.
; This is deliberately role -> arity/shape, never domain-bits -> shape.
; Arguments are proper SENS compiler-program-data lists.  Exact cardinality
; must be tested using the D3 ATOM predicate on the tail, not a D4
; operator applied to an already-computed D1 predicate bit.
(визначити compiler-exactly-one
  (функція (аргументи)
    (за-умовою
      ((атом? аргументи) (хиба-компілятора ()))
      ((compiler-list-end? (решта аргументи)) (істина-компілятора ()))
      ((істина-компілятора ()) (хиба-компілятора ())))))

(визначити compiler-exactly-two
  (функція (аргументи)
    (за-умовою
      ((атом? аргументи) (хиба-компілятора ()))
      ((атом? (решта аргументи)) (хиба-компілятора ()))
      ((compiler-list-end? (решта (решта аргументи))) (істина-компілятора ()))
      ((істина-компілятора ()) (хиба-компілятора ())))))

; Proper variadic tails: only the exact EMPTY terminates a list.
; D3 ATOM detects a malformed nonempty atom; EQ sees EMPTY only after ATOM.
; The already-admitted compiler-list-end? owns that distinction in SENS.
(визначити compiler-proper-tail?
  (функція (хвіст)
    (за-умовою
      ((compiler-list-end? хвіст) (істина-компілятора ()))
      ((атом? хвіст) (хиба-компілятора ()))
      (так (compiler-proper-tail? (решта хвіст))))))

; D4 LAMBDA is parameters plus one-or-more body expressions.
; Both mandatory argument cells must be pairs, and all remaining cells must
; form a proper list; nested data elements may themselves be dotted pairs.
(визначити compiler-at-least-two
  (функція (аргументи)
    (за-умовою
      ((атом? аргументи) (хиба-компілятора ()))
      ((атом? (решта аргументи)) (хиба-компілятора ()))
      (так (compiler-proper-tail? (решта (решта аргументи)))))))

; Exact D3 COND is a non-empty sequence of two-part (test expression) clauses.
(визначити compiler-cond-clauses-valid
  (функція (клаузи)
    (за-умовою
      ((compiler-list-end? клаузи) (істина-компілятора ()))
      ((атом? клаузи) (хиба-компілятора ()))
      ((compiler-exactly-two (перше клаузи))
       (compiler-cond-clauses-valid (решта клаузи)))
      ((істина-компілятора ()) (хиба-компілятора ())))))

(визначити compiler-role-shape-valid
  (функція (запит-компіляції аргументи-форми)
    (за-умовою
      ((атом? запит-компіляції) (хиба-компілятора ()))
      ((тотожне? (compiler-request-role запит-компіляції) (як-є quote-form))
       (compiler-exactly-one аргументи-форми))
      ((тотожне? (compiler-request-role запит-компіляції) (як-є atom-predicate))
       (compiler-exactly-one аргументи-форми))
      ((тотожне? (compiler-request-role запит-компіляції) (як-є selector-tail))
       (compiler-exactly-one аргументи-форми))
      ((тотожне? (compiler-request-role запит-компіляції) (як-є selector-head))
       (compiler-exactly-one аргументи-форми))
      ((тотожне? (compiler-request-role запит-компіляції) (як-є atom-equality))
       (compiler-exactly-two аргументи-форми))
      ((тотожне? (compiler-request-role запит-компіляції) (як-є pair-construct))
       (compiler-exactly-two аргументи-форми))
      ((тотожне? (compiler-request-role запит-компіляції) (як-є lambda-form))
       (compiler-at-least-two аргументи-форми))
      ((тотожне? (compiler-request-role запит-компіляції) (як-є define-form))
       (compiler-exactly-two аргументи-форми))
      ((тотожне? (compiler-request-role запит-компіляції) (як-є cond-form))
       (за-умовою
         ((атом? аргументи-форми) (хиба-компілятора ()))
         ((істина-компілятора ()) (compiler-cond-clauses-valid аргументи-форми))))
      ((істина-компілятора ()) (хиба-компілятора ())))))

; Program traversal policy is semantic and therefore SENS-owned.
; QUOTE payload is data.  LAMBDA parameters and DEFINE name are data.
; Other admitted forms recursively compile every argument position.
; Exact D3 COND clauses are pairs of source expressions, not
; calls whose head is the D1 predicate. Flatten each admitted pair into
; predicate, result, then the remaining clauses. D3 handles the traversal;
; no new domain coordinate or callable slot is created.
(визначити компілятор-вирази-гілок-умови
  (функція (гілки-умов)
    (за-умовою
      ((атом? гілки-умов) ())
      ((compiler-exactly-two (перше гілки-умов))
       (сполучити
         (перше (перше гілки-умов))
         (сполучити
           (перше (решта (перше гілки-умов)))
           (компілятор-вирази-гілок-умови (решта гілки-умов)))))
      (так ()))))

(визначити compiler-domain-children
  (функція (запит-компіляції аргументи-форми)
    (за-умовою
      ((атом? запит-компіляції) ())
      ((тотожне? (compiler-request-role запит-компіляції) (як-є quote-form)) ())
      ((тотожне? (compiler-request-role запит-компіляції) (як-є lambda-form))
       (решта аргументи-форми))
      ((тотожне? (compiler-request-role запит-компіляції) (як-є define-form))
       (решта аргументи-форми))
      ((тотожне? (compiler-request-role запит-компіляції) (як-є cond-form))
       (компілятор-вирази-гілок-умови аргументи-форми))
      ((істина-компілятора ()) аргументи-форми))))

(визначити compiler-domain-result
  (функція
    (запит-компіляції аргументи-форми результат-нащадків)
    (за-умовою
      ((атом? запит-компіляції) (compiler-result-fail))
      ((compiler-role-shape-valid запит-компіляції аргументи-форми)
       (за-умовою
         ((compiler-result-success результат-нащадків)
          (compiler-result-ok
            (сполучити
              запит-компіляції
              (compiler-result-requests результат-нащадків))))
         ((істина-компілятора ()) (compiler-result-fail))))
      ((істина-компілятора ()) (compiler-result-fail)))))

; Tail-position list traversal keeps stack bounded by expression nesting,
; not by the number of sibling forms. The accumulator stores requests reversed.
; Request selection and failure remain entirely SENS-owned.
(визначити компілятор-зворот-до
  (функція (елементи накопичувач)
    (за-умовою
      ((атом? елементи) накопичувач)
      ((істина-компілятора ())
       (компілятор-зворот-до
         (решта елементи)
         (сполучити (перше елементи) накопичувач))))))

(визначити компілятор-продовжити-список-програми
  (функція
    (форма-або-порожнє розкласти-ідентичність результат-вузла решта-вузлів закон-д3 закон-д4 доказ-д3 доказ-д4 походження накопичувач)
    (за-умовою
      ((compiler-result-success результат-вузла)
       (компілятор-список-програми-з-накопичувачем
         форма-або-порожнє
         розкласти-ідентичність
         решта-вузлів
         закон-д3
         закон-д4
         доказ-д3
         доказ-д4
         походження
         (компілятор-зворот-до
           (compiler-result-requests результат-вузла)
           накопичувач)))
      ((істина-компілятора ()) (compiler-result-fail)))))

(визначити компілятор-список-програми-з-накопичувачем
  (функція
    (форма-або-порожнє розкласти-ідентичність вузли закон-д3 закон-д4 доказ-д3 доказ-д4 походження накопичувач)
    (за-умовою
      ((compiler-list-end? вузли)
       (compiler-result-ok (компілятор-зворот-до накопичувач ())))
      ((атом? вузли) (compiler-result-fail))
      ((істина-компілятора ())
       (компілятор-продовжити-список-програми
         форма-або-порожнє
         розкласти-ідентичність
         (compiler-program-node
           форма-або-порожнє
           розкласти-ідентичність
           (перше вузли)
           закон-д3
           закон-д4
           доказ-д3
           доказ-д4
           походження)
         (решта вузли)
         закон-д3
         закон-д4
         доказ-д3
         доказ-д4
         походження
         накопичувач)))))

(визначити compiler-program-list
  (функція
    (форма-або-порожнє розкласти-ідентичність вузли закон-д3 закон-д4 доказ-д3 доказ-д4 походження)
    (компілятор-список-програми-з-накопичувачем
      форма-або-порожнє
      розкласти-ідентичність
      вузли
      закон-д3
      закон-д4
      доказ-д3
      доказ-д4
      походження
      ())))

(визначити compiler-program-node
  (функція
    (форма-або-порожнє розкласти-ідентичність вузол закон-д3 закон-д4 доказ-д3 доказ-д4 походження)
    (за-умовою
      ((атом? вузол) (compiler-result-ok ()))
      ((атом? (форма-або-порожнє (перше вузол)))
       (compiler-program-list
         форма-або-порожнє
         розкласти-ідентичність
         вузол
         закон-д3
         закон-д4
         доказ-д3
         доказ-д4
         походження))
      ((істина-компілятора ())
       (compiler-domain-result
         (compiler-request-from-laws
           розкласти-ідентичність
           (перше вузол)
           закон-д3
           закон-д4
           доказ-д3
           доказ-д4
           походження)
         (решта вузол)
         (compiler-program-list
           форма-або-порожнє
           розкласти-ідентичність
           (compiler-domain-children
             (compiler-request-from-laws
               розкласти-ідентичність
               (перше вузол)
               закон-д3
               закон-д4
               доказ-д3
               доказ-д4
               походження)
             (решта вузол))
           закон-д3
           закон-д4
           доказ-д3
           доказ-д4
           походження))))))

(визначити compiler-compile-program
  (функція
    (форма-або-порожнє розкласти-ідентичність програма закон-д3 закон-д4 доказ-д3 доказ-д4 походження)
    (compiler-program-list
      форма-або-порожнє
      розкласти-ідентичність
      програма
      закон-д3
      закон-д4
      доказ-д3
      доказ-д4
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
  (функція (назва-поля значення-поля)
    (сполучити назва-поля (сполучити значення-поля ()))))

(визначити compiler-artifact-from-result
  (функція
    (відбиток ша256-пакованої-програми походження-артефакту результат-компіляції)
    (за-умовою
      ((compiler-result-success результат-компіляції)
       (сполучити
         (як-є compiler-compilation-artifact/1)
         (сполучити
           (compiler-artifact-field
             (як-є artifact-kind)
             (як-є whole-program))
           (сполучити
             (compiler-artifact-field
               (як-є program-wire-sha256)
               ша256-пакованої-програми)
             (сполучити
               (compiler-artifact-field
                 (як-є semantic-requests-sha256)
                 (відбиток (compiler-result-requests результат-компіляції)))
               (сполучити
                 (compiler-artifact-field
                   (як-є authority-provenance)
                   походження-артефакту)
                 (сполучити
                   (compiler-artifact-field
                     (як-є semantic-requests)
                     (compiler-result-requests результат-компіляції))
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
             ша256-пакованої-програми)
           (сполучити
             (compiler-artifact-field
               (як-є error)
               (як-є compiler-program-rejected))
             ())))))))

(визначити compiler-compile-program-artifact
  (функція
    (форма-або-порожнє розкласти-ідентичність відбиток програма закон-д3 закон-д4 доказ-д3 доказ-д4 походження-запиту походження-артефакту ша256-пакованої-програми)
    (compiler-artifact-from-result
      відбиток
      ша256-пакованої-програми
      походження-артефакту
      (compiler-compile-program
        форма-або-порожнє
        розкласти-ідентичність
        програма
        закон-д3
        закон-д4
        доказ-д3
        доказ-д4
        походження-запиту))))