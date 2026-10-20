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

(визначити runtime-peer-comparison-topology-observations
  (список
    ; Initial stable peer identities.
    (тотожне? менше? hīna?)
    (тотожне? hīna? <)
    (тотожне? більше? adhika?)
    (тотожне? adhika? >)
    (тотожне? рівне? sama?)
    (тотожне? sama? =)

    ; 1014: shadow each spelling independently. The shadow becomes distinct,
    ; while the two untouched peers remain one callable identity.
    (нехай ((менше? (функція (a b) (як-є shadowed))))
      (список (тотожне? менше? hīna?) (тотожне? hīna? <)))
    (нехай ((hīna? (функція (a b) (як-є shadowed))))
      (список (тотожне? hīna? менше?) (тотожне? менше? <)))
    (нехай ((< (функція (a b) (як-є shadowed))))
      (список (тотожне? < менше?) (тотожне? менше? hīna?)))

    ; 1015.
    (нехай ((більше? (функція (a b) (як-є shadowed))))
      (список (тотожне? більше? adhika?) (тотожне? adhika? >)))
    (нехай ((adhika? (функція (a b) (як-є shadowed))))
      (список (тотожне? adhika? більше?) (тотожне? більше? >)))
    (нехай ((> (функція (a b) (як-є shadowed))))
      (список (тотожне? > більше?) (тотожне? більше? adhika?)))

    ; 1016.
    (нехай ((рівне? (функція (a b) (як-є shadowed))))
      (список (тотожне? рівне? sama?) (тотожне? sama? =)))
    (нехай ((sama? (функція (a b) (як-є shadowed))))
      (список (тотожне? sama? рівне?) (тотожне? рівне? =)))
    (нехай ((= (функція (a b) (як-є shadowed))))
      (список (тотожне? = рівне?) (тотожне? рівне? sama?)))))

(визначити runtime-peer-comparison-topology-expected
  (як-є
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

(за-умовою
  ((однакові?
     runtime-peer-comparison-topology-observations
     runtime-peer-comparison-topology-expected)
   (structural-relation same)
   (як-є (runtime-peer-comparison-topology-witness (status pass))))
  ((однакові?
     runtime-peer-comparison-topology-observations
     runtime-peer-comparison-topology-expected)
   (structural-relation distinct)
   (список
     (як-є runtime-peer-comparison-topology-witness)
     (як-є (status fail))
     (список
       (як-є actual)
       runtime-peer-comparison-topology-observations)
     (список
       (як-є expected)
       runtime-peer-comparison-topology-expected))))
