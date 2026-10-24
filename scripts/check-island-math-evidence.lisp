; #990 — fail-closed validation for mechanism evidence.
; Evidence may only attach to an existing Canon/function-table SID and to an
; executor route already admitted by #1046 mechanism metadata. This checker does
; not define operation names, meaning, law, domain, or semantic equivalence.

(визначити registry
  (перше (читати-всі (читати-файл "lib/surface/semantic-registry.lisp"))))

(визначити mechanisms
  (перше (читати-всі (читати-файл "lib/function-table-mechanisms.lisp"))))

(визначити evidence
  (перше (читати-всі (читати-файл "lib/island-math-evidence.lisp"))))

(визначити registry-rows registry)

(визначити evidence-sid-bits
  (функція (sid)
    (за-умовою
      ((рядок? sid) sid)
      (1 (значення-у-текст sid)))))

(визначити find-section
  (функція (name sections)
    (за-умовою
      ((тотожне? sections (як-є ())) (як-є ()))
      ((тотожне? (атом? sections) 0) (за-умовою
         ((тотожне? (перше (перше sections)) name) (перше sections))
         ((тотожне? (тотожне? (перше (перше sections)) name) 0) (find-section name (решта sections))))))))

(визначити mechanism-rows
  (решта (find-section (як-є rows) mechanisms)))

(визначити evidence-rows
  (решта (find-section (як-є rows) evidence)))

(визначити registry-has-sid?
  (функція (sid rows)
    (за-умовою
      ((тотожне? rows (як-є ())) (як-є no))
      ((тотожне? (атом? rows) 0) (за-умовою
         ((однакові? sid (перше (перше rows))) (як-є yes))
         ((тотожне? (однакові? sid (перше (перше rows))) 0) (registry-has-sid? sid (решта rows))))))))

(визначити mechanism-has-route?
  (функція (sid executor rows)
    (за-умовою
      ((тотожне? rows (як-є ())) (як-є no))
      ((тотожне? (атом? rows) 0) (нехай ((row (перше rows)))
         (за-умовою
           ((однакові? (evidence-sid-bits sid) (evidence-sid-bits (перше row))) (за-умовою
              ((тотожне? executor (друге row)) (як-є yes))
              ((тотожне? (тотожне? executor (друге row)) 0) (mechanism-has-route? sid executor (решта rows)))))
           ((тотожне? (однакові? (evidence-sid-bits sid) (evidence-sid-bits (перше row))) 0) (mechanism-has-route? sid executor (решта rows)))))))))

(визначити evidence-has-route?
  (функція (sid executor rows)
    (за-умовою
      ((тотожне? rows (як-є ())) (як-є no))
      ((тотожне? (атом? rows) 0) (нехай ((row (перше rows)))
         (за-умовою
           ((однакові? sid (перше row)) (за-умовою
              ((тотожне? executor (друге row)) (як-є yes))
              ((тотожне? (тотожне? executor (друге row)) 0) (evidence-has-route? sid executor (решта rows)))))
           ((тотожне? (однакові? sid (перше row)) 0) (evidence-has-route? sid executor (решта rows)))))))))

(визначити admitted-executor?
  (функція (executor)
    (за-умовою
      ((тотожне? executor (як-є common-lisp)) (як-є yes))
      ((тотожне? executor (як-є prolog)) (як-є yes))
      ((тотожне? executor (як-є clips)) (як-є yes))
      ((тотожне? executor (як-є datalog)) (як-є yes))
      (1 (як-є no)))))

(визначити admitted-status?
  (функція (status)
    (за-умовою
      ((тотожне? status (як-є execution-witness)) (як-є yes))
      (1 (як-є no)))))

(визначити forbidden-semantic-symbol?
  (функція (value)
    (за-умовою
      ((тотожне? value (як-є ())) (як-є no))
      ((тотожне? (атом? value) 0) (як-є no))
      ((атом? value) (за-умовою
         ((тотожне? value (як-є operation)) (як-є yes))
         ((тотожне? value (як-є meaning)) (як-є yes))
         ((тотожне? value (як-є law)) (як-є yes))
         ((тотожне? value (як-є domain)) (як-є yes))
         ((тотожне? value (як-є operand-domain)) (як-є yes))
         ((тотожне? value (як-є result-domain)) (як-є yes))
         (1 (як-є no)))))))

(визначити contains-forbidden-semantic-section?
  (функція (sections)
    (за-умовою
      ((тотожне? sections (як-є ())) (як-є no))
      ((тотожне? (атом? sections) 0) (нехай ((section (перше sections)))
         (за-умовою
           ((тотожне? (атом? section) 0) (за-умовою
              ((тотожне? (forbidden-semantic-symbol? (перше section)) (як-є yes)) (як-є yes))
              (1 (contains-forbidden-semantic-section? (решта sections)))))
           (1 (contains-forbidden-semantic-section? (решта sections)))))))))

(визначити validate-rows
  (функція (rows)
    (за-умовою
      ((тотожне? rows (як-є ())) (як-є (island-math-evidence-ok)))
      ((тотожне? (атом? rows) 0) (нехай-послідовно ((row (перше rows))
              (sid (перше row))
              (executor (друге row))
              (status (третє row))
              (provenance-ref (четверте row)))
         (за-умовою
           ((тотожне? (однакові? (довжина row) 4) 0) (список (як-є island-math-evidence-violation)
                  (як-є invalid-evidence-row-shape) sid))
           ((тотожне? (рядок? provenance-ref) 0) (список (як-є island-math-evidence-violation)
                  (як-є provenance-must-be-string) sid executor))
           ((тотожне? (registry-has-sid? sid registry-rows) (як-є no)) (список (як-є island-math-evidence-violation)
                  (як-є sid-not-in-canon-function-table) sid))
           ((тотожне? (admitted-executor? executor) (як-є no)) (список (як-є island-math-evidence-violation)
                  (як-є unsupported-executor) sid executor))
           ((тотожне? (mechanism-has-route? sid executor mechanism-rows) (як-є no)) (список (як-є island-math-evidence-violation)
                  (як-є executor-route-not-admitted-by-canon-projection) sid executor))
           ((тотожне? (admitted-status? status) (як-є no)) (список (як-є island-math-evidence-violation)
                  (як-є unsupported-status) sid status))
           ((тотожне? (evidence-has-route? sid executor (решта rows)) (як-є yes)) (список (як-є island-math-evidence-violation)
                  (як-є duplicate-executor-evidence) sid executor))
           (1 (validate-rows (решта rows)))))))))

(визначити same-sid?
  (функція (sid rows)
    (за-умовою
      ((тотожне? rows (як-є ())) (як-є yes))
      ((тотожне? (атом? rows) 0) (за-умовою
         ((однакові? sid (перше (перше rows))) (same-sid? sid (решта rows)))
         ((тотожне? (однакові? sid (перше (перше rows))) 0) (як-є no)))))))

(визначити four-island-slice?
  (функція (sid)
    (за-умовою
      ((тотожне? (evidence-has-route? sid (як-є common-lisp) evidence-rows) (як-є no)) (як-є no))
      ((тотожне? (evidence-has-route? sid (як-є prolog) evidence-rows) (як-є no)) (як-є no))
      ((тотожне? (evidence-has-route? sid (як-є clips) evidence-rows) (як-є no)) (як-є no))
      ((тотожне? (evidence-has-route? sid (як-є datalog) evidence-rows) (як-є no)) (як-є no))
      (1 (як-є yes)))))

(визначити row-verdict (validate-rows evidence-rows))

(визначити verdict
  (за-умовою
    ((тотожне? (contains-forbidden-semantic-section? evidence) (як-є yes)) (як-є (island-math-evidence-violation semantic-field-forbidden)))
    ((тотожне? evidence-rows (як-є ())) (як-є (island-math-evidence-violation empty-evidence)))
    ((однакові? row-verdict (як-є (island-math-evidence-ok))) (нехай ((target-sid (перше (перше evidence-rows))))
       (за-умовою
         ((тотожне? (same-sid? target-sid evidence-rows) (як-є no)) (як-є (island-math-evidence-violation first-slice-must-have-one-sid)))
         ((тотожне? (four-island-slice? target-sid) (як-є no)) (як-є (island-math-evidence-violation missing-required-four-island-slice)))
         (1 (як-є (island-math-evidence-ok))))))
    (1 row-verdict)))

(друкувати verdict)
