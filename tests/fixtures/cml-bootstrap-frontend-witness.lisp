; Lisp-owned compiler bootstrap witness for juv4uk/cml#153.
; The frontend source is authoritative for this bounded compiler mechanism.
; Consumers compare against these strings; they do not re-implement the law.

(cml-bootstrap-witness/0
  ((source . "(+ 1 2)")
   (expected-envelope . "(cml-ir-bootstrap-v0 (prim + (literal 1) (literal 2)))")
   (unsupported-form-source . "(- 1 2)")
   (unsupported-form-envelope . "(compiler-frontend-rejection unsupported-form)")
   (arity-source . "(+ 1)")
   (arity-envelope . "(compiler-frontend-rejection arity)")
   (authority . "lib/compiler/cml-bootstrap.lisp")
   (consumer . "juv4uk/cml#153")))
