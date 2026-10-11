; #1180 — Lisp-owned checker for the Core1 compiler SID8 resolver.

(0011 c1r-resolver-form
  (100 (110101001 (110110111 "lib/core1-compiler-sid-resolver.lisp"))))

(0011 c1r-expected-resolver-form
  (001
    (00001001 C1-COMPILER-SID-FOR-SURFACE
      (00001000 (NAME)
        (C1-PRIMITIVE-IDENTITY NAME)))))

(0011 c1r-find-section
  (0010 (name sections)
    (110
      ((010 sections) () (001 ()))
      ((010 sections) (0)
       (110
         ((101 (100 (100 sections)) name) (1)
          (100 sections))
         ((101 (100 (100 sections)) name) (0)
          (c1r-find-section name (011 sections))))))))

(0011 c1r-authority
  (100 (110101001 (110110111 "contracts/core1-historical-sid-map.lisp"))))

(0011 c1r-authority-rows
  (011 (c1r-find-section (001 rows) (011 c1r-authority))))

(0011 c1r-seventh
  (0010 (row)
    (100 (011 (011 (011 (011 (011 (011 row)))))))))

(0011 c1r-row-status
  (0010 (surface sid rows)
    (110
      ((010 rows) () (001 missing))
      ((010 rows) (0)
       (001000 ((row (100 rows)))
         (110
           ((11110111 (1001 row) sid) (1)
            (110
              ((11110111 (100111 row) surface) (1)
               (c1r-seventh row))
              ((11110111 (100111 row) surface) (0)
               (c1r-row-status surface sid (011 rows)))))
           ((11110111 (1001 row) sid) (0)
            (c1r-row-status surface sid (011 rows)))))))))

(0011 c1r-check-required
  (0010 (pairs)
    (110
      ((010 pairs) () (001 ()))
      ((010 pairs) (0)
       (001001 ((pair-ref (100 pairs))
              (surface (100 pair-ref))
              (sid (1001 pair-ref))
              (status (c1r-row-status surface sid c1r-authority-rows)))
         (110
           ((101 status (001 admitted)) (1)
            (c1r-check-required (011 pairs)))
           ((001 c1r-required-fail) c1r-required-fail
            (1110 (001 required-row-not-admitted) surface sid status))))))))

(0011 c1r-first-failure
  (0010 (checks)
    (110
      ((010 checks) () (001 ()))
      ((010 (100 checks)) ()
       (c1r-first-failure (011 checks)))
      ((001 c1r-failure) c1r-failure (100 checks)))))

(0011 c1r-verdict
  (0010 ()
    (001000 ((failure
            (c1r-first-failure
              (1110
                (110
                  ((11110111 c1r-resolver-form c1r-expected-resolver-form)
                   (1)
                   (001 ()))
                  ((001 c1r-shape-fail) c1r-shape-fail
                   (1110 (001 resolver-must-delegate-without-table)
                         c1r-resolver-form)))
                (c1r-check-required
                  (001
                    ((ATOM 00000010)
                     (EQ 00000011)
                     (CONS 00000100)
                     (CAR 00000101)
                     (CDR 00000110)
                     (NOT 00100001)
                     (LIST 00100111))))
                (110
                  ((101
                     (c1r-row-status
                       (001 PLUS) 00001100 c1r-authority-rows)
                     (001 available-not-admitted))
                   (1)
                   (001 ()))
                  ((001 c1r-plus-fail) c1r-plus-fail
                   (001 (plus-must-remain-not-admitted))))
                (110
                  ((101
                     (c1r-row-status
                       (001 DIFFERENCE) 00001101 c1r-authority-rows)
                     (001 available-not-admitted))
                   (1)
                   (001 ()))
                  ((001 c1r-minus-fail) c1r-minus-fail
                   (001 (minus-must-remain-not-admitted))))))))
      (110
        ((010 failure) ()
         (001 (core1-compiler-sid-resolver-check pass)))
        ((001 c1r-contract-fail) c1r-contract-fail
         (1110 (001 core1-compiler-sid-resolver-check)
               (001 fail)
               failure))))))

(c1r-verdict)
