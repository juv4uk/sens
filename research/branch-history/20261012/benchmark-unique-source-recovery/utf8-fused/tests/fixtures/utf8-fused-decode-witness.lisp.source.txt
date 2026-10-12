; #362 — RED/preservation witness for a Lisp-owned fused UTF-8 decoder.
; The proposed entry point must preserve the current public result domain:
;   (decoded (...)) | (rejected invalid-byte) | (rejected invalid-utf8)
; including the non-obvious global precedence of invalid-byte over an earlier
; malformed UTF-8 prefix.  Rust/host code owns none of these expectations.

(load "lib/core.lisp")
(load "lib/utf8.lisp")

(def utf8-fused-expect
  (lambda (law bytes expected)
    (let ((actual (utf8-decode-fused bytes)))
      (cond
        ((equal? actual expected) (structural-relation same)
         (quote ()))
        ((equal? actual expected) (structural-relation distinct)
         (list
           (quote utf8-fused-decode-witness)
           (quote (status fail))
           (list (quote law) law)
           (list (quote expected) expected)
           (list (quote actual) actual)))))))

(def utf8-fused-check-failures
  (lambda (checks)
    (cond
      ((atom checks) (structural-kind empty-list)
       (quote (utf8-fused-decode-witness (status pass))))
      ((atom checks) (structural-kind pair)
       (let ((failure (car checks)))
         (cond
           ((equal? failure (quote ())) (structural-relation same)
            (utf8-fused-check-failures (cdr checks)))
           ((equal? failure (quote ())) (structural-relation distinct)
            failure)))))))

(def utf8-fused-decode-check
  (lambda ()
    (utf8-fused-check-failures
      (list
        (utf8-fused-expect
          (quote ascii)
          (quote (65 66 67))
          (quote (decoded (65 66 67))))
        (utf8-fused-expect
          (quote multibyte-2-3-4)
          (quote (194 162 226 130 172 240 159 152 128))
          (quote (decoded (162 8364 128512))))
        (utf8-fused-expect
          (quote invalid-byte-high)
          (quote (65 256 66))
          (quote (rejected invalid-byte)))
        (utf8-fused-expect
          (quote invalid-byte-low)
          (quote (65 -1 66))
          (quote (rejected invalid-byte)))
        (utf8-fused-expect
          (quote bad-continuation)
          (quote (226 65 172))
          (quote (rejected invalid-utf8)))
        (utf8-fused-expect
          (quote truncated-three-byte)
          (quote (226 130))
          (quote (rejected invalid-utf8)))
        (utf8-fused-expect
          (quote truncated-four-byte)
          (quote (240 159 152))
          (quote (rejected invalid-utf8)))
        (utf8-fused-expect
          (quote overlong-two-byte)
          (quote (192 128))
          (quote (rejected invalid-utf8)))
        (utf8-fused-expect
          (quote overlong-three-byte)
          (quote (224 128 128))
          (quote (rejected invalid-utf8)))
        (utf8-fused-expect
          (quote surrogate-range)
          (quote (237 160 128))
          (quote (rejected invalid-utf8)))
        (utf8-fused-expect
          (quote above-unicode-range)
          (quote (244 144 128 128))
          (quote (rejected invalid-utf8)))
        (utf8-fused-expect
          (quote invalid-byte-precedes-earlier-invalid-utf8)
          (quote (192 128 256))
          (quote (rejected invalid-byte)))))))

(utf8-fused-decode-check)
