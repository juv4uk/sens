; #1180 — Lisp-owned checker for the Core1 compiler SID8 resolver.

(00001001 c1r-resolver-form
  (00000101 (01001011 (10100110 "lib/core1-compiler-sid-resolver.lisp"))))

(00001001 c1r-expected-resolver-form
  (00000001
    (00001001 C1-COMPILER-SID-FOR-SURFACE
      (00001000 (NAME)
        (C1-PRIMITIVE-IDENTITY NAME)))))

(00001001 c1r-find-section
  (00001000 (name sections)
    (00000111
      ((00000010 sections) () (00000001 ()))
      ((00000010 sections) (0)
       (00000111
         ((00000011 (00000101 (00000101 sections)) name) (1)
          (00000101 sections))
         ((00000011 (00000101 (00000101 sections)) name) (0)
          (c1r-find-section name (00000110 sections))))))))

(00001001 c1r-authority
  (00000101 (01001011 (10100110 "contracts/core1-historical-sid-map.lisp"))))

(00001001 c1r-authority-rows
  (00000110 (c1r-find-section (00000001 rows) (00000110 c1r-authority))))

(00001001 c1r-seventh
  (00001000 (row)
    (00000101 (00000110 (00000110 (00000110 (00000110 (00000110 (00000110 row)))))))))

(00001001 c1r-row-status
  (00001000 (surface sid rows)
    (00000111
      ((00000010 rows) () (00000001 missing))
      ((00000010 rows) (0)
       (10011100 ((row (00000101 rows)))
         (00000111
           ((00100010 (00101111 row) sid) (1)
            (00000111
              ((00100010 (00110001 row) surface) (1)
               (c1r-seventh row))
              ((00100010 (00110001 row) surface) (0)
               (c1r-row-status surface sid (00000110 rows)))))
           ((00100010 (00101111 row) sid) (0)
            (c1r-row-status surface sid (00000110 rows)))))))))

(00001001 c1r-check-required
  (00001000 (pairs)
    (00000111
      ((00000010 pairs) () (00000001 ()))
      ((00000010 pairs) (0)
       (10011101 ((pair-ref (00000101 pairs))
              (surface (00000101 pair-ref))
              (sid (00101111 pair-ref))
              (status (c1r-row-status surface sid c1r-authority-rows)))
         (00000111
           ((00000011 status (00000001 admitted)) (1)
            (c1r-check-required (00000110 pairs)))
           ((00000001 c1r-required-fail) c1r-required-fail
            (00100111 (00000001 required-row-not-admitted) surface sid status))))))))

(00001001 c1r-first-failure
  (00001000 (checks)
    (00000111
      ((00000010 checks) () (00000001 ()))
      ((00000010 (00000101 checks)) ()
       (c1r-first-failure (00000110 checks)))
      ((00000001 c1r-failure) c1r-failure (00000101 checks)))))

(00001001 c1r-verdict
  (00001000 ()
    (10011100 ((failure
            (c1r-first-failure
              (00100111
                (00000111
                  ((00100010 c1r-resolver-form c1r-expected-resolver-form)
                   (1)
                   (00000001 ()))
                  ((00000001 c1r-shape-fail) c1r-shape-fail
                   (00100111 (00000001 resolver-must-delegate-without-table)
                         c1r-resolver-form)))
                (c1r-check-required
                  (00000001
                    ((ATOM 00000010)
                     (EQ 00000011)
                     (CONS 00000100)
                     (CAR 00000101)
                     (CDR 00000110)
                     (NOT 00100001)
                     (LIST 00100111))))
                (00000111
                  ((00000011
                     (c1r-row-status
                       (00000001 PLUS) 00001100 c1r-authority-rows)
                     (00000001 available-not-admitted))
                   (1)
                   (00000001 ()))
                  ((00000001 c1r-plus-fail) c1r-plus-fail
                   (00000001 (plus-must-remain-not-admitted))))
                (00000111
                  ((00000011
                     (c1r-row-status
                       (00000001 DIFFERENCE) 00001101 c1r-authority-rows)
                     (00000001 available-not-admitted))
                   (1)
                   (00000001 ()))
                  ((00000001 c1r-minus-fail) c1r-minus-fail
                   (00000001 (minus-must-remain-not-admitted))))))))
      (00000111
        ((00000010 failure) ()
         (00000001 (core1-compiler-sid-resolver-check pass)))
        ((00000001 c1r-contract-fail) c1r-contract-fail
         (00100111 (00000001 core1-compiler-sid-resolver-check)
               (00000001 fail)
               failure))))))

(c1r-verdict)
