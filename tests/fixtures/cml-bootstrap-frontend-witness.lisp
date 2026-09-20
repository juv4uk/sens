; Lisp-owned compiler bootstrap witness for juv4uk/cml#153.
; The frontend source is authoritative for this bounded compiler mechanism.
; Consumers compare against this data; they do not re-implement the lowering law.

(cml-bootstrap-witness/0
  ((source . "(+ 1 2)")
   (form . (+ 1 2))
   (expected-envelope
     . (cml-ir-bootstrap-v0
         (prim + (literal 1) (literal 2))))
   (unsupported
     . (((form . (- 1 2))
         (expected-envelope . (compiler-frontend-rejection unsupported-form)))
        ((form . (+ 1))
         (expected-envelope . (compiler-frontend-rejection arity)))))
   (authority . lib/compiler/cml-bootstrap.lisp)
   (consumer . juv4uk/cml#153)))
