; #536 — preserve stable comparison-peer topology before retiring stale Rust
; semantic result oracles from runtime_peer_operators.rs.
;
; This witness owns only runtime peer identity and lexical-shadowing isolation
; for semantic IDs 1014 (<), 1015 (>), and 1016 (=). It deliberately does NOT
; assert mathematical YES/NO values: exact-Q result meaning remains owned by
; contracts/exact-q-binary-contract.lisp and tests/fixtures/exact-q-binary-v1.lisp.
;
; The CLI does not load lib/surface/uk.lisp or lib/surface/sa.lisp before this
; fixture, so these names exist only through the canonical runtime peer binder.

(def runtime-peer-comparison-topology-observations
  (list
    ; Initial stable peer identities.
    (eq менше? hīna?)
    (eq hīna? <)
    (eq більше? adhika?)
    (eq adhika? >)
    (eq рівне? sama?)
    (eq sama? =)

    ; 1014: shadow each spelling independently. The shadow becomes distinct,
    ; while the two untouched peers remain one callable identity.
    (let ((менше? (lambda (a b) (quote shadowed))))
      (list (eq менше? hīna?) (eq hīna? <)))
    (let ((hīna? (lambda (a b) (quote shadowed))))
      (list (eq hīna? менше?) (eq менше? <)))
    (let ((< (lambda (a b) (quote shadowed))))
      (list (eq < менше?) (eq менше? hīna?)))

    ; 1015.
    (let ((більше? (lambda (a b) (quote shadowed))))
      (list (eq більше? adhika?) (eq adhika? >)))
    (let ((adhika? (lambda (a b) (quote shadowed))))
      (list (eq adhika? більше?) (eq більше? >)))
    (let ((> (lambda (a b) (quote shadowed))))
      (list (eq > більше?) (eq більше? adhika?)))

    ; 1016.
    (let ((рівне? (lambda (a b) (quote shadowed))))
      (list (eq рівне? sama?) (eq sama? =)))
    (let ((sama? (lambda (a b) (quote shadowed))))
      (list (eq sama? рівне?) (eq рівне? =)))
    (let ((= (lambda (a b) (quote shadowed))))
      (list (eq = рівне?) (eq рівне? sama?)))))

(def runtime-peer-comparison-topology-expected
  (quote
    (
      (identity-relation same)
      (identity-relation same)
      (identity-relation same)
      (identity-relation same)
      (identity-relation same)
      (identity-relation same)

      ((identity-relation distinct) (identity-relation same))
      ((identity-relation distinct) (identity-relation same))
      ((identity-relation distinct) (identity-relation same))

      ((identity-relation distinct) (identity-relation same))
      ((identity-relation distinct) (identity-relation same))
      ((identity-relation distinct) (identity-relation same))

      ((identity-relation distinct) (identity-relation same))
      ((identity-relation distinct) (identity-relation same))
      ((identity-relation distinct) (identity-relation same))
    )))

(cond
  ((equal?
     runtime-peer-comparison-topology-observations
     runtime-peer-comparison-topology-expected)
   (structural-relation same)
   (quote (runtime-peer-comparison-topology-witness (status pass))))
  ((equal?
     runtime-peer-comparison-topology-observations
     runtime-peer-comparison-topology-expected)
   (structural-relation distinct)
   (list
     (quote runtime-peer-comparison-topology-witness)
     (quote (status fail))
     (list
       (quote actual)
       runtime-peer-comparison-topology-observations)
     (list
       (quote expected)
       runtime-peer-comparison-topology-expected))))
