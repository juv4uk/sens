; SENS-owned D3 EQ/COND law for existing meta-eval lexical dependency helpers.
; Names are source-level bindings in lib/meta-eval.lisp, NOT new domain IDs.
; Positive and mutant invoke same live functions with same data.
; Quote D3:001, Lambda D4:0010, Define D4:0011; result bit is D1.
(110
  ((101 (my-form-references-name? (001 (001 target)) (001 target)) #d1:1)
   (110
     ((101 (my-form-references-name? (001 target) (001 target)) #d1:1)
      (110
        ((101 (my-form-references-name? (001 (0010 (target) target)) (001 target)) #d1:0)
         (110
           ((101 (my-form-references-name? (001 (0010 (other) target)) (001 target)) #d1:1)
            (110
              ((101 (my-form-references-name? (001 (0010 (other) (001 target))) (001 target)) #d1:0)
               (110
                 ((101 (my-lambda-def-references-name? (001 (0011 fn (0010 (target) target))) (001 target)) #d1:0)
                  (110
                    ((101 (my-lambda-def-references-name? (001 (0011 fn (0010 (other) target))) (001 target)) #d1:1)
                     (110
                       ((101 (my-lambda-def-references-name? (001 (0011 fn (0010 (other) (001 target)))) (001 target)) #d1:0)
                        #d1:1)
                       (#d1:1 (#d1:0))))
                    (#d1:1 (#d1:0))))
                 (#d1:1 (#d1:0))))
              (#d1:1 (#d1:0))))
           (#d1:1 (#d1:0))))
        (#d1:1 (#d1:0))))
     (#d1:1 (#d1:0))))
  (#d1:1 (#d1:0)))
