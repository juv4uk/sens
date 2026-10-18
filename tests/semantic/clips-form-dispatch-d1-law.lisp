; Source-owned SENS D3 EQ/COND self-verdicts for CLIPS dispatch guards.
; The D9-derived function is invoked by its installed source binding only.
; Structural NIL is still data: EQ(QUOTE ()) observes it as a D1 truth value.
; The fourth form flips exactly one D1 expectation of the first form.
(110
  ((тотожне? (кліпс-форма-клаузи (як-є stray) (як-є ())) (як-є ())) так)
  (#d1:1 (#d1:0)))
(110
  ((тотожне? (кліпс-форма-клаузи (як-є ((nested-head) content)) (як-є ())) (як-є ())) так)
  (#d1:1 (#d1:0)))
(110
  ((тотожне? (кліпс-форма-клаузи (як-є (deffunction square)) (як-є ())) (як-є ())) так)
  (#d1:1 (#d1:0)))
(110
  ((тотожне? (кліпс-форма-клаузи (як-є stray) (як-є ())) (як-є ())) ні)
  (#d1:1 (#d1:0)))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити кліпс-форма-клаузи clips-form->clauses)
