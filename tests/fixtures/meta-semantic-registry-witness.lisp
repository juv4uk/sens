; #305 — semantic-registry meaning is Lisp-owned before the stale Rust oracle
; is retired.  This preserves three laws from meta_eval_semantic_registry.rs:
;   1. admitted surfaces project to their numeric semantic identities and an
;      unadmitted spelling fails closed;
;   2. compatibility ATOM routing stays stable in the metacircular evaluator;
;      exact native D3 predicate results are covered by a separate typed
;      boundary witness whose cases remain Lisp-owned data;
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

(0011 registry-native-value
  (0010 (source)
    (0001 (11101010 source))))

(0011 registry-meta-value
  (0010 (source)
    (my-eval (11101010 source) (001 ()))))

(0011 registry-meta-program-result
  (0010 (source)
    (011 (my-eval-program (110101001 source) (001 ())))))

(0011 registry-witness-failure
  (0010 (case actual expected)
    (1110
      (001 meta-semantic-registry-witness)
      (001 (status fail))
      (1110 (001 case) case)
      (1110 (001 actual) actual)
      (1110 (001 expected) expected))))

(0011 registry-check-rows
  (0010 (rows)
    (110
      ((010 rows) ()
       (001 (meta-semantic-registry-witness (status pass))))
      ((010 rows) (1)
       (registry-witness-failure
         (001 malformed-row-tail)
         rows
         (001 ())))
      ((010 rows) (0)
       (001000 ((row (100 rows)))
         (110
           ((11110111 (1001 row) (10011 row)) (1)
            (registry-check-rows (011 rows)))
           ((11110111 (1001 row) (10011 row)) (0)
            (registry-witness-failure
              (100 row)
              (1001 row)
              (10011 row)))))))))

(0011 registry-witness-rows
  (0010 ()
    (1110
      ; Generated projection/admission law.
      (1110 (001 quote-id-en)
            (my-semantic-id-for-surface (001 quote))
            00000001)
      (1110 (001 quote-id-uk)
            (my-semantic-id-for-surface (001 як-є))
            00000001)
      (1110 (001 lambda-id-en)
            (my-semantic-id-for-surface (001 lambda))
            00001000)
      (1110 (001 lambda-id-uk)
            (my-semantic-id-for-surface (001 функція))
            00001000)
      (1110 (001 define-id-en)
            (my-semantic-id-for-surface (001 define))
            00001001)
      (1110 (001 define-id-uk)
            (my-semantic-id-for-surface (001 визначити))
            00001001)
      (1110 (001 def-compat-id)
            (my-semantic-id-for-surface (001 def))
            00001011)
      (1110 (001 rupa-id-sa)
            (my-semantic-id-for-surface (001 rūpa))
            00010000)
      (1110 (001 unmapped-surface-fails-closed)
            (010 (my-semantic-id-for-surface (001 unmapped-surface)))
            (001 ()))

      ; Historical explicit-byte ATOM remains a compatibility witness.
      ; Current exact-D3 predicate surfaces are verified by the typed,
      ; Lisp-data-owned boundary corpus in witness_authority.rs; this older
      ; meta-registry witness cannot manufacture free-standing D1 literals.
      (1110 (001 atom-native-legacy-byte)
            (registry-native-value "(00000010 (quote x))")
            (001 (1)))

      ; The metacircular evaluator still exercises the compatibility
      ; mechanism in my-apply-primitive. Its D1 cutover remains #2184 follow-up,
      ; so these rows deliberately retain the historical carrier until that
      ; evaluator can consume exact D1 false without generic truth coercion.
      (1110 (001 atom-meta-en)
            (registry-meta-value "(00000010 (quote x))")
            (001 (1)))
      (1110 (001 atom-meta-uk)
            (registry-meta-value "(атом? (як-є x))")
            (001 (1)))
      (1110 (001 atom-meta-sa)
            (registry-meta-value "(aṇu (svarūpa x))")
            (001 (1)))
      (1110 (001 atom-meta-symbolic)
            (registry-meta-value "(.? (quote x))")
            (001 (1)))

      ; Necessary-form routing: native evaluator.
      (1110 (001 lambda-native-en)
            (registry-native-value "((lambda (x) x) 42)")
            42)
      (1110 (001 lambda-native-uk)
            (registry-native-value "((функція (x) x) 42)")
            42)
      (1110 (001 define-native-en)
            (registry-native-value "(define registry-native-en-answer 42)")
            42)
      (1110 (001 define-native-uk)
            (registry-native-value "(визначити registry-native-uk-answer 42)")
            42)
      (1110 (001 def-native-compat)
            (registry-native-value "(def registry-native-def-answer 42)")
            42)

      ; The same necessary forms through the metacircular evaluator.
      (1110 (001 lambda-meta-en)
            (registry-meta-value "((lambda (x) x) 42)")
            42)
      (1110 (001 lambda-meta-uk)
            (registry-meta-value "((функція (x) x) 42)")
            42)
      (1110 (001 define-meta-en)
            (registry-meta-program-result "(define registry-meta-en-answer 42)")
            42)
      (1110 (001 define-meta-uk)
            (registry-meta-program-result "(визначити registry-meta-uk-answer 42)")
            42)
      (1110 (001 def-meta-compat)
            (registry-meta-program-result "(def registry-meta-def-answer 42)")
            42))))

(registry-check-rows (registry-witness-rows))
