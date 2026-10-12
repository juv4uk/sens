; UTF-8 encoding and decoding semantics owned by Lisp.
; Семантика кодування й декодування UTF-8, якою володіє Lisp.
;
; Decoder input is a proper list of exact byte integers 0..255 and returns:
;   (decoded (codepoint ...))
; or
;   (rejected invalid-byte)
;   (rejected invalid-utf8)
;
; Encoder input is a runtime String and returns its exact UTF-8 bytes as a
; proper list of integers 0..255. Unicode sequence validation and both
; byte<->scalar interpretations stay here in Lisp. The runtime exposes only
; the minimal scalar/string bridges `codepoint->string` and
; `string->codepoint`; neither bridge knows UTF-8.

(def utf8-continuation-byte?
  (lambda (b)
    (and (>= b 128) (<= b 191))))

(def utf8-byte?
  (lambda (b)
    (and (= b b)
         (>= b 0)
         (<= b 255)
         (= (mod b 1) 0))))

(def utf8-all-bytes?
  (lambda (bytes)
    (cond
      ((atom bytes) (eq bytes (quote ())))
      ((not (utf8-byte? (car bytes))) ())
      (t (utf8-all-bytes? (cdr bytes))))))

(def utf8-decode-onto
  (lambda (bytes out)
    (cond
      ((atom bytes) (list (quote decoded) (reverse out)))
      (t
       (let* ((b1 (car bytes))
              (r1 (cdr bytes)))
         (cond
           ; ASCII
           ((<= b1 127)
            (utf8-decode-onto r1 (cons b1 out)))

           ; 2-byte sequence: C2..DF 80..BF
           ((and (>= b1 194) (<= b1 223))
            (cond
              ((atom r1) (list (quote rejected) (quote invalid-utf8)))
              (t
               (let ((b2 (car r1)))
                 (cond
                   ((not (utf8-continuation-byte? b2))
                    (list (quote rejected) (quote invalid-utf8)))
                   (t
                    (utf8-decode-onto
                      (cdr r1)
                      (cons (+ (* (- b1 192) 64)
                               (- b2 128))
                            out))))))))

           ; 3-byte sequence with overlong/surrogate exclusions.
           ((and (>= b1 224) (<= b1 239))
            (cond
              ((or (atom r1) (atom (cdr r1)))
               (list (quote rejected) (quote invalid-utf8)))
              (t
               (let* ((b2 (car r1))
                      (r2 (cdr r1))
                      (b3 (car r2))
                      (second-ok
                        (cond
                          ((= b1 224) (and (>= b2 160) (<= b2 191)))
                          ((= b1 237) (and (>= b2 128) (<= b2 159)))
                          (t (utf8-continuation-byte? b2)))))
                 (cond
                   ((not (and second-ok (utf8-continuation-byte? b3)))
                    (list (quote rejected) (quote invalid-utf8)))
                   (t
                    (utf8-decode-onto
                      (cdr r2)
                      (cons (+ (* (- b1 224) 4096)
                               (* (- b2 128) 64)
                               (- b3 128))
                            out))))))))

           ; 4-byte sequence, restricted to Unicode scalar range <= 10FFFF.
           ((and (>= b1 240) (<= b1 244))
            (cond
              ((or (atom r1) (atom (cdr r1)) (atom (cdr (cdr r1))))
               (list (quote rejected) (quote invalid-utf8)))
              (t
               (let* ((b2 (car r1))
                      (r2 (cdr r1))
                      (b3 (car r2))
                      (r3 (cdr r2))
                      (b4 (car r3))
                      (second-ok
                        (cond
                          ((= b1 240) (and (>= b2 144) (<= b2 191)))
                          ((= b1 244) (and (>= b2 128) (<= b2 143)))
                          (t (utf8-continuation-byte? b2)))))
                 (cond
                   ((not (and second-ok
                              (utf8-continuation-byte? b3)
                              (utf8-continuation-byte? b4)))
                    (list (quote rejected) (quote invalid-utf8)))
                   (t
                    (utf8-decode-onto
                      (cdr r3)
                      (cons (+ (* (- b1 240) 262144)
                               (* (- b2 128) 4096)
                               (* (- b3 128) 64)
                               (- b4 128))
                            out))))))))

           (t (list (quote rejected) (quote invalid-utf8)))))))))

(def utf8-decode
  (lambda (bytes)
    (cond
      ((not (utf8-all-bytes? bytes))
       (list (quote rejected) (quote invalid-byte)))
      (t (utf8-decode-onto bytes (quote ()))))))

(def utf8-valid?
  (lambda (bytes)
    (eq (car (utf8-decode bytes)) (quote decoded))))

; Keep text materialization in tail position. The previous direct recursion
; accumulated one host evaluator frame per Unicode scalar while waiting to
; string-append on unwind; ordinary network payloads could therefore exhaust
; the smaller stacks of worker threads even though byte validation itself was
; tail-recursive.
(def unicode-scalars->string-onto
  (lambda (scalars out)
    (cond
      ((atom scalars) out)
      (t
       (unicode-scalars->string-onto
         (cdr scalars)
         (string-append out (codepoint->string (car scalars))))))))

(def unicode-scalars->string
  (lambda (scalars)
    (unicode-scalars->string-onto scalars "")))

(def utf8-decode-string
  (lambda (bytes)
    (let ((decoded (utf8-decode bytes)))
      (cond
        ((eq (car decoded) (quote decoded))
         (list (quote decoded)
               (unicode-scalars->string (car (cdr decoded)))))
        (t decoded)))))

; Encode one runtime String by observing one Unicode scalar at a time. The
; accumulator is kept in reverse byte order so the recursive call remains in
; tail position and one final reverse restores wire order.
(def utf8-encode-string-onto
  (lambda (text out)
    (cond
      ((string-empty? text) (reverse out))
      (t
       (let* ((character (string-first text))
              (rest (string-rest text))
              (scalar (string->codepoint character)))
         (cond
           ((<= scalar 127)
            (utf8-encode-string-onto rest (cons scalar out)))
           ((<= scalar 2047)
            (utf8-encode-string-onto
              rest
              (cons (+ 128 (mod scalar 64))
                    (cons (+ 192 (quotient scalar 64)) out))))
           ((<= scalar 65535)
            (utf8-encode-string-onto
              rest
              (cons (+ 128 (mod scalar 64))
                    (cons (+ 128 (mod (quotient scalar 64) 64))
                          (cons (+ 224 (quotient scalar 4096)) out)))))
           (t
            (utf8-encode-string-onto
              rest
              (cons (+ 128 (mod scalar 64))
                    (cons (+ 128 (mod (quotient scalar 64) 64))
                          (cons (+ 128 (mod (quotient scalar 4096) 64))
                                (cons (+ 240 (quotient scalar 262144)) out))))))))))))

(def utf8-encode-string
  (lambda (text)
    (utf8-encode-string-onto text (quote ()))))

; #362 — single-pass semantic decoder. Every byte-domain check happens in
; Lisp while the same traversal interprets UTF-8. Once a malformed UTF-8
; prefix is observed, keep scanning only for byte-domain violations so the
; historical global precedence remains exact: any invalid byte anywhere wins
; over invalid-utf8.
(def utf8-fused-invalid-rest
  (lambda (bytes)
    (cond
      ((atom bytes) (structural-kind empty-list)
       (list (quote rejected) (quote invalid-utf8)))
      ((atom bytes) (structural-kind atom)
       (list (quote rejected) (quote invalid-byte)))
      ((atom bytes) (structural-kind pair)
       (let ((b (car bytes)))
         (cond
           ((equal? (utf8-byte? b) 1) (structural-relation same)
            (utf8-fused-invalid-rest (cdr bytes)))
           ((equal? (utf8-byte? b) 1) (structural-relation distinct)
            (list (quote rejected) (quote invalid-byte)))))))))

(def utf8-decode-fused-onto
  (lambda (bytes out)
    (cond
      ((atom bytes) (structural-kind empty-list)
       (list (quote decoded) (reverse out)))
      ((atom bytes) (structural-kind atom)
       (list (quote rejected) (quote invalid-byte)))
      ((atom bytes) (structural-kind pair)
       (let* ((b1 (car bytes))
              (r1 (cdr bytes)))
         (cond
           ((equal? (utf8-byte? b1) 1) (structural-relation distinct)
            (list (quote rejected) (quote invalid-byte)))

           ; ASCII
           ((<= b1 127) 1
            (utf8-decode-fused-onto r1 (cons b1 out)))

           ; 2-byte sequence: C2..DF 80..BF
           ((* (>= b1 194) (<= b1 223)) 1
            (cond
              ((atom r1) (structural-kind empty-list)
               (list (quote rejected) (quote invalid-utf8)))
              ((atom r1) (structural-kind atom)
               (list (quote rejected) (quote invalid-byte)))
              ((atom r1) (structural-kind pair)
               (let* ((b2 (car r1))
                      (r2 (cdr r1)))
                 (cond
                   ((equal? (utf8-byte? b2) 1) (structural-relation distinct)
                    (list (quote rejected) (quote invalid-byte)))
                   ((* (>= b2 128) (<= b2 191)) 1
                    (utf8-decode-fused-onto
                      r2
                      (cons (+ (* (- b1 192) 64)
                               (- b2 128))
                            out)))
                   ((* (>= b2 128) (<= b2 191)) 0
                    (utf8-fused-invalid-rest r2)))))))

           ; 3-byte sequence with overlong/surrogate exclusions.
           ((* (>= b1 224) (<= b1 239)) 1
            (cond
              ((atom r1) (structural-kind empty-list)
               (list (quote rejected) (quote invalid-utf8)))
              ((atom r1) (structural-kind atom)
               (list (quote rejected) (quote invalid-byte)))
              ((atom r1) (structural-kind pair)
               (let* ((b2 (car r1))
                      (r2 (cdr r1)))
                 (cond
                   ((equal? (utf8-byte? b2) 1) (structural-relation distinct)
                    (list (quote rejected) (quote invalid-byte)))
                   ((atom r2) (structural-kind empty-list)
                    (list (quote rejected) (quote invalid-utf8)))
                   ((atom r2) (structural-kind atom)
                    (list (quote rejected) (quote invalid-byte)))
                   ((atom r2) (structural-kind pair)
                    (let* ((b3 (car r2))
                           (r3 (cdr r2))
                           (second-ok
                             (cond
                               ((= b1 224) 1
                                (* (>= b2 160) (<= b2 191)))
                               ((= b1 237) 1
                                (* (>= b2 128) (<= b2 159)))
                               ((= b1 b1) 1
                                (* (>= b2 128) (<= b2 191))))))
                      (cond
                        ((equal? (utf8-byte? b3) 1)
                         (structural-relation distinct)
                         (list (quote rejected) (quote invalid-byte)))
                        ((* second-ok
                            (* (>= b3 128) (<= b3 191))) 1
                         (utf8-decode-fused-onto
                           r3
                           (cons (+ (* (- b1 224) 4096)
                                    (* (- b2 128) 64)
                                    (- b3 128))
                                 out)))
                        ((* second-ok
                            (* (>= b3 128) (<= b3 191))) 0
                         (utf8-fused-invalid-rest r3))))))))))

           ; 4-byte sequence, restricted to Unicode scalar range <= 10FFFF.
           ((* (>= b1 240) (<= b1 244)) 1
            (cond
              ((atom r1) (structural-kind empty-list)
               (list (quote rejected) (quote invalid-utf8)))
              ((atom r1) (structural-kind atom)
               (list (quote rejected) (quote invalid-byte)))
              ((atom r1) (structural-kind pair)
               (let* ((b2 (car r1))
                      (r2 (cdr r1)))
                 (cond
                   ((equal? (utf8-byte? b2) 1) (structural-relation distinct)
                    (list (quote rejected) (quote invalid-byte)))
                   ((atom r2) (structural-kind empty-list)
                    (list (quote rejected) (quote invalid-utf8)))
                   ((atom r2) (structural-kind atom)
                    (list (quote rejected) (quote invalid-byte)))
                   ((atom r2) (structural-kind pair)
                    (let* ((b3 (car r2))
                           (r3 (cdr r2)))
                      (cond
                        ((equal? (utf8-byte? b3) 1)
                         (structural-relation distinct)
                         (list (quote rejected) (quote invalid-byte)))
                        ((atom r3) (structural-kind empty-list)
                         (list (quote rejected) (quote invalid-utf8)))
                        ((atom r3) (structural-kind atom)
                         (list (quote rejected) (quote invalid-byte)))
                        ((atom r3) (structural-kind pair)
                         (let* ((b4 (car r3))
                                (r4 (cdr r3))
                                (second-ok
                                  (cond
                                    ((= b1 240) 1
                                     (* (>= b2 144) (<= b2 191)))
                                    ((= b1 244) 1
                                     (* (>= b2 128) (<= b2 143)))
                                    ((= b1 b1) 1
                                     (* (>= b2 128) (<= b2 191))))))
                           (cond
                             ((equal? (utf8-byte? b4) 1)
                              (structural-relation distinct)
                              (list (quote rejected) (quote invalid-byte)))
                             ((* second-ok
                                 (* (>= b3 128) (<= b3 191))
                                 (* (>= b4 128) (<= b4 191))) 1
                              (utf8-decode-fused-onto
                                r4
                                (cons (+ (* (- b1 240) 262144)
                                         (* (- b2 128) 4096)
                                         (* (- b3 128) 64)
                                         (- b4 128))
                                      out)))
                             ((* second-ok
                                 (* (>= b3 128) (<= b3 191))
                                 (* (>= b4 128) (<= b4 191))) 0
                              (utf8-fused-invalid-rest r4)))))))))))))

           ; b1 is a byte, but not a valid UTF-8 leading byte.
           ((= b1 b1) 1
            (utf8-fused-invalid-rest r1))))))))

(def utf8-decode-fused
  (lambda (bytes)
    (utf8-decode-fused-onto bytes (quote ()))))
