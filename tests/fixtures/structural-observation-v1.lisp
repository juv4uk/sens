; #218 — executable target for PRIM_ATOM / PRIM_EQ domain-owned results.
; Expected outcomes are Lisp-owned semantic data.
;
; #217 now provides a canonical explicit-result dispatch path, so structural
; domain-result rows are active again. Historical two-part cond remains only a
; migration compatibility path while bootstrap/library callers are converted.

((expr . "(00000010 (quote ()))")
 (expected . "(structural-kind empty-list)")
 (active . t)
 (identity . "0002")
 (case . canon-zero))

((expr . "(00000010 (quote radio))")
 (expected . "(structural-kind atom)")
 (active . t)
 (identity . "0002")
 (case . non-pair-atom))

((expr . "(00000010 (quote (radio antenna)))")
 (expected . "(structural-kind pair)")
 (active . t)
 (identity . "0002")
 (case . pair))

((expr . "(00000011 (quote radio) (quote radio))")
 (expected . "(identity-relation same)")
 (active . t)
 (identity . "0003")
 (case . same-atom))

((expr . "(00000011 (quote radio) (quote antenna))")
 (expected . "(identity-relation distinct)")
 (active . t)
 (identity . "0003")
 (case . distinct-atoms))

((expr . "(00000011 (quote (radio)) (quote (radio)))")
 (error . "Type")
 (active . t)
 (identity . "0003")
 (case . outside-atom-domain))

; Vector values are atoms at the PRIM_EQ boundary (only Pair is outside the
; atom domain). Their recursive Value equality therefore belongs to the same
; Lisp-owned identity-relation contract, not to Rust-authored t/() assertions.
((expr . "(00000011 (vector 1 2 3) (vector 1 2 3))")
 (expected . "(identity-relation same)")
 (active . t)
 (identity . "0003")
 (case . vector-same-structure))

((expr . "(def v (vector 1 2)) (00000011 v v)")
 (expected . "(identity-relation same)")
 (active . t)
 (identity . "0003")
 (case . vector-same-object))

((expr . "(00000011 (vector 1 2) (vector 1 9))")
 (expected . "(identity-relation distinct)")
 (active . t)
 (identity . "0003")
 (case . vector-distinct-element))

((expr . "(00000011 (vector 1 2) (vector 1))")
 (expected . "(identity-relation distinct)")
 (active . t)
 (identity . "0003")
 (case . vector-distinct-length))

((expr . "(00000011 (vector) (vector))")
 (expected . "(identity-relation same)")
 (active . t)
 (identity . "0003")
 (case . empty-vectors-same))

((expr . "(00000011 (vector (list 1 2)) (vector (list 1 2)))")
 (expected . "(identity-relation same)")
 (active . t)
 (identity . "0003")
 (case . vector-nested-structure-same))

; Typed numeric buffers are also atoms at the PRIM_EQ boundary. Their
; representation-specific equality is mechanism, but the meaning of the
; observation is still the Lisp-owned identity-relation algebra.
((expr . "(00000011 (i32-buffer 1 2) (i32-buffer 1 2))")
 (expected . "(identity-relation same)")
 (active . t)
 (identity . "0003")
 (case . numeric-buffer-i32-same-values))

((expr . "(00000011 (i32-buffer 1) (f32-buffer 1))")
 (expected . "(identity-relation distinct)")
 (active . t)
 (identity . "0003")
 (case . numeric-buffer-distinct-types))

; F32 buffer equality is bitwise at the mechanism boundary. Signed zeroes have
; different binary32 encodings, so EQ reports the ordinary explicit distinct
; identity relation rather than a truth sentinel.
((expr . "(00000011 #f32(-0.0) #f32(0.0))")
 (expected . "(identity-relation distinct)")
 (active . t)
 (identity . "0003")
 (case . numeric-buffer-f32-signed-zero-distinct))


; #218 regression: equal? must distinguish equal atomic values from distinct atoms.
(def equal-atomic-structural-witness
  (lambda ()
    (cond
      ((equal? (quote radio) (quote radio)) (structural-relation same)
       (quote (equal-atomic-structural-witness (status pass))))
      ((equal? (quote radio) (quote antenna)) (structural-relation distinct)
       (quote (equal-atomic-structural-witness (status pass)))))))

(equal-atomic-structural-witness)
