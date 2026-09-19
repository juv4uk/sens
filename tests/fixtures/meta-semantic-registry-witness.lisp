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

(def registry-native-value
  (lambda (source)
    (eval (read source))))

(def registry-meta-value
  (lambda (source)
    (my-eval (read source) (quote ()))))

(def registry-meta-program-result
  (lambda (source)
    (cdr (my-eval-program (read-all source) (quote ())))))

(def registry-witness-failure
  (lambda (case actual expected)
    (list
      (quote meta-semantic-registry-witness)
      (quote (status fail))
      (list (quote case) case)
      (list (quote actual) actual)
      (list (quote expected) expected))))

(def registry-check-rows
  (lambda (rows)
    (cond
      ((atom rows) (structural-kind empty-list)
       (quote (meta-semantic-registry-witness (status pass))))
      ((atom rows) (structural-kind atom)
       (registry-witness-failure
         (quote malformed-row-tail)
         rows
         (quote ())))
      ((atom rows) (structural-kind pair)
       (let ((row (car rows)))
         (cond
           ((equal? (second row) (third row)) (structural-relation same)
            (registry-check-rows (cdr rows)))
           ((equal? (second row) (third row)) (structural-relation distinct)
            (registry-witness-failure
              (car row)
              (second row)
              (third row)))))))))

(def registry-witness-rows
  (lambda ()
    (list
      ; Generated projection/admission law.
      (list (quote quote-id-en)
            (my-semantic-id-for-surface (quote quote))
            "00000001")
      (list (quote quote-id-uk)
            (my-semantic-id-for-surface (quote як-є))
            "00000001")
      (list (quote lambda-id-en)
            (my-semantic-id-for-surface (quote lambda))
            "00001000")
      (list (quote lambda-id-uk)
            (my-semantic-id-for-surface (quote функція))
            "00001000")
      (list (quote define-id-en)
            (my-semantic-id-for-surface (quote define))
            "00001001")
      (list (quote define-id-uk)
            (my-semantic-id-for-surface (quote визначити))
            "00001001")
      (list (quote def-compat-id)
            (my-semantic-id-for-surface (quote def))
            "00001011")
      (list (quote rupa-id-sa)
            (my-semantic-id-for-surface (quote rūpa))
            "00010000")
      (list (quote unmapped-surface-fails-closed)
            (atom (my-semantic-id-for-surface (quote unmapped-surface)))
            (quote (structural-kind empty-list)))

      ; Canon ATOM peer surfaces: native evaluator.
      (list (quote atom-native-en)
            (registry-native-value "(atom (quote x))")
            (quote (structural-kind atom)))
      (list (quote atom-native-uk)
            (registry-native-value "(атом? (як-є x))")
            (quote (structural-kind atom)))
      (list (quote atom-native-sa)
            (registry-native-value "(aṇu (svarūpa x))")
            (quote (structural-kind atom)))
      (list (quote atom-native-symbolic)
            (registry-native-value "(.? (quote x))")
            (quote (structural-kind atom)))

      ; The same peer surfaces through the metacircular evaluator.
      (list (quote atom-meta-en)
            (registry-meta-value "(atom (quote x))")
            (quote (structural-kind atom)))
      (list (quote atom-meta-uk)
            (registry-meta-value "(атом? (як-є x))")
            (quote (structural-kind atom)))
      (list (quote atom-meta-sa)
            (registry-meta-value "(aṇu (svarūpa x))")
            (quote (structural-kind atom)))
      (list (quote atom-meta-symbolic)
            (registry-meta-value "(.? (quote x))")
            (quote (structural-kind atom)))

      ; Necessary-form routing: native evaluator.
      (list (quote lambda-native-en)
            (registry-native-value "((lambda (x) x) 42)")
            42)
      (list (quote lambda-native-uk)
            (registry-native-value "((функція (x) x) 42)")
            42)
      (list (quote define-native-en)
            (registry-native-value "(define registry-native-en-answer 42)")
            42)
      (list (quote define-native-uk)
            (registry-native-value "(визначити registry-native-uk-answer 42)")
            42)
      (list (quote def-native-compat)
            (registry-native-value "(def registry-native-def-answer 42)")
            42)

      ; The same necessary forms through the metacircular evaluator.
      (list (quote lambda-meta-en)
            (registry-meta-value "((lambda (x) x) 42)")
            42)
      (list (quote lambda-meta-uk)
            (registry-meta-value "((функція (x) x) 42)")
            42)
      (list (quote define-meta-en)
            (registry-meta-program-result "(define registry-meta-en-answer 42)")
            42)
      (list (quote define-meta-uk)
            (registry-meta-program-result "(визначити registry-meta-uk-answer 42)")
            42)
      (list (quote def-meta-compat)
            (registry-meta-program-result "(def registry-meta-def-answer 42)")
            42))))

(registry-check-rows (registry-witness-rows))
