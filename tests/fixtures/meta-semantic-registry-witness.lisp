; #305 — semantic-registry meaning is Lisp-owned before the stale Rust oracle
; is retired.  This preserves three laws from meta_eval_semantic_registry.rs:
;   1. admitted surfaces project to their numeric semantic identities and an
;      unadmitted spelling fails closed;
;   2. peer spellings of Canon ATOM execute as one semantic identity in both
;      the native evaluator and the metacircular evaluator;
;   3. LAMBDA/DEFINE plus compatibility DEF route through their numeric
;      semantic identities in both evaluators.
;
; Rust/shell may observe only the final named pass envelope.  Expected values
; and the comparison logic stay here in Lisp.

; The host helper load_meta_evaluator_library loads this generated projection
; before lib/meta-eval.lisp.  A standalone Lisp witness must make that same
; dependency explicit rather than relying on host bootstrap order.
(load "lib/generated/meta-semantic-registry.lisp")
(load "lib/meta-eval.lisp")

(00001001 registry-native-value
  (00001000 (source)
    (01001101 (01001010 source))))

(00001001 registry-meta-value
  (00001000 (source)
    (my-eval (01001010 source) (00000001 ()))))

(00001001 registry-meta-program-result
  (00001000 (source)
    (00000110 (my-eval-program (01001011 source) (00000001 ())))))

; Independent exact-D1 YES witness. D5:11101 MEMBER is already ratified and
; merged with a canonical D1 result boundary (#3060), so this does not define
; D3 predicate semantics by self-comparison.
(00001001 registry-d1-yes
  (00001000 ()
    (значення-у-списку? (00000001 x) (00000001 (x)))))

(00001001 registry-witness-failure
  (00001000 (case actual expected)
    (00100111
      (00000001 meta-semantic-registry-witness)
      (00000001 (status fail))
      (00100111 (00000001 case) case)
      (00100111 (00000001 actual) actual)
      (00100111 (00000001 expected) expected))))

(00001001 registry-check-rows
  (00001000 (rows)
    (00000111
      ((00000010 rows) ()
       (00000001 (meta-semantic-registry-witness (status pass))))
      ((00000010 rows) (1)
       (registry-witness-failure
         (00000001 malformed-row-tail)
         rows
         (00000001 ())))
      ((00000010 rows) (0)
       (10011100 ((row (00000101 rows)))
         (00000111
           ((00100010 (00101111 row) (00110000 row)) (1)
            (registry-check-rows (00000110 rows)))
           ((00100010 (00101111 row) (00110000 row)) (0)
            (registry-witness-failure
              (00000101 row)
              (00101111 row)
              (00110000 row)))))))))

(00001001 registry-witness-rows
  (00001000 ()
    (00100111
      ; Generated projection/admission law.
      (00100111 (00000001 quote-id-en)
            (my-semantic-id-for-surface (00000001 quote))
            00000001)
      (00100111 (00000001 quote-id-uk)
            (my-semantic-id-for-surface (00000001 як-є))
            00000001)
      (00100111 (00000001 lambda-id-en)
            (my-semantic-id-for-surface (00000001 lambda))
            00001000)
      (00100111 (00000001 lambda-id-uk)
            (my-semantic-id-for-surface (00000001 функція))
            00001000)
      (00100111 (00000001 define-id-en)
            (my-semantic-id-for-surface (00000001 define))
            00001001)
      (00100111 (00000001 define-id-uk)
            (my-semantic-id-for-surface (00000001 визначити))
            00001001)
      (00100111 (00000001 def-compat-id)
            (my-semantic-id-for-surface (00000001 def))
            00001011)
      (00100111 (00000001 rupa-id-sa)
            (my-semantic-id-for-surface (00000001 rūpa))
            00010000)
      (00100111 (00000001 unmapped-surface-fails-closed)
            (00000010 (my-semantic-id-for-surface (00000001 unmapped-surface)))
            (00000001 ()))

      ; Canon ATOM native routes.
      ;
      ; The explicit historical byte remains a compatibility witness and still
      ; exposes its historical one-element answer carrier. Admitted human
      ; surfaces lower to exact D3:010; those results must be exact D1. Their
      ; expected YES is generated independently by ratified D5 MEMBER (#3060).
      (00100111 (00000001 atom-native-legacy-byte)
            (registry-native-value "(00000010 (quote x))")
            (00000001 (1)))
      (00100111 (00000001 atom-native-uk)
            (registry-native-value "(атом? (як-є x))")
            (registry-d1-yes))
      (00100111 (00000001 atom-native-sa)
            (registry-native-value "(aṇu (svarūpa x))")
            (registry-d1-yes))
      (00100111 (00000001 atom-native-symbolic)
            (registry-native-value "(.? (quote x))")
            (registry-d1-yes))

      ; The metacircular evaluator still exercises the explicit compatibility
      ; mechanism in my-apply-primitive. Its D1 cutover remains #2184 follow-up,
      ; so these rows deliberately retain the historical carrier until that
      ; evaluator can consume exact D1 false without generic truth coercion.
      (00100111 (00000001 atom-meta-en)
            (registry-meta-value "(00000010 (quote x))")
            (00000001 (1)))
      (00100111 (00000001 atom-meta-uk)
            (registry-meta-value "(атом? (як-є x))")
            (00000001 (1)))
      (00100111 (00000001 atom-meta-sa)
            (registry-meta-value "(aṇu (svarūpa x))")
            (00000001 (1)))
      (00100111 (00000001 atom-meta-symbolic)
            (registry-meta-value "(.? (quote x))")
            (00000001 (1)))

      ; Necessary-form routing: native evaluator.
      (00100111 (00000001 lambda-native-en)
            (registry-native-value "((lambda (x) x) 42)")
            42)
      (00100111 (00000001 lambda-native-uk)
            (registry-native-value "((функція (x) x) 42)")
            42)
      (00100111 (00000001 define-native-en)
            (registry-native-value "(define registry-native-en-answer 42)")
            42)
      (00100111 (00000001 define-native-uk)
            (registry-native-value "(визначити registry-native-uk-answer 42)")
            42)
      (00100111 (00000001 def-native-compat)
            (registry-native-value "(def registry-native-def-answer 42)")
            42)

      ; The same necessary forms through the metacircular evaluator.
      (00100111 (00000001 lambda-meta-en)
            (registry-meta-value "((lambda (x) x) 42)")
            42)
      (00100111 (00000001 lambda-meta-uk)
            (registry-meta-value "((функція (x) x) 42)")
            42)
      (00100111 (00000001 define-meta-en)
            (registry-meta-program-result "(define registry-meta-en-answer 42)")
            42)
      (00100111 (00000001 define-meta-uk)
            (registry-meta-program-result "(визначити registry-meta-uk-answer 42)")
            42)
      (00100111 (00000001 def-meta-compat)
            (registry-meta-program-result "(def registry-meta-def-answer 42)")
            42))))

(registry-check-rows (registry-witness-rows))
