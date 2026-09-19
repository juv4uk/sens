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

; Internal UTF-8 range decisions are exact-Q values, never generic truth.
(def utf8-in-range?
  (lambda (value low high)
    (cond
      ((< value low) 1 0)
      ((< value low) 0
       (cond
         ((<= value high) 1 1)
         ((<= value high) 0 0))))))

(def utf8-continuation-byte?
  (lambda (b)
    (cond
      ((utf8-in-range? b 128 191) 1 1)
      ((utf8-in-range? b 128 191) 0 0))))

(def utf8-byte?
  (lambda (b)
    (cond
      ((utf8-in-range? b 0 255) 1
       (cond
         ((= (mod b 1) 0) 1 1)
         ((= (mod b 1) 0) 0 0)))
      ((utf8-in-range? b 0 255) 0 0))))

(def utf8-all-bytes?
  (lambda (bytes)
    (cond
      ((atom bytes)
       (structural-kind empty-list)
       (cond
         ((eq bytes (quote ())) (identity-relation same) 1)
         ((eq bytes (quote ())) (identity-relation distinct) 0)))
      ((atom bytes)
       (structural-kind pair)
       (cond
         ((utf8-byte? (car bytes)) 1
          (utf8-all-bytes? (cdr bytes)))
         ((utf8-byte? (car bytes)) 0 0))))))

(def utf8-three-byte-second-ok?
  (lambda (b1 b2)
    (cond
      ((= b1 224) 1
       (utf8-in-range? b2 160 191))
      ((= b1 224) 0
       (cond
         ((= b1 237) 1
          (utf8-in-range? b2 128 159))
         ((= b1 237) 0
          (utf8-continuation-byte? b2)))))))

(def utf8-four-byte-second-ok?
  (lambda (b1 b2)
    (cond
      ((= b1 240) 1
       (utf8-in-range? b2 144 191))
      ((= b1 240) 0
       (cond
         ((= b1 244) 1
          (utf8-in-range? b2 128 143))
         ((= b1 244) 0
          (utf8-continuation-byte? b2)))))))

(def utf8-two-continuations?
  (lambda (b3 b4)
    (cond
      ((utf8-continuation-byte? b3) 1
       (cond
         ((utf8-continuation-byte? b4) 1 1)
         ((utf8-continuation-byte? b4) 0 0)))
      ((utf8-continuation-byte? b3) 0 0))))

(def utf8-decode-onto
  (lambda (bytes out)
    (cond
      ((atom bytes)
       (structural-kind empty-list)
       (list (quote decoded) (reverse out)))
      ((atom bytes)
       (structural-kind pair)
       (let* ((b1 (car bytes))
              (r1 (cdr bytes)))
         (cond
           ; ASCII
           ((<= b1 127) 1
            (utf8-decode-onto r1 (cons b1 out)))
           ((<= b1 127) 0
            (cond
              ; 2-byte sequence: C2..DF 80..BF
              ((utf8-in-range? b1 194 223) 1
               (cond
                 ((atom r1)
                  (structural-kind empty-list)
                  (list (quote rejected) (quote invalid-utf8)))
                 ((atom r1)
                  (structural-kind pair)
                  (let ((b2 (car r1)))
                    (cond
                      ((utf8-continuation-byte? b2) 1
                       (utf8-decode-onto
                         (cdr r1)
                         (cons (+ (* (- b1 192) 64)
                                  (- b2 128))
                               out)))
                      ((utf8-continuation-byte? b2) 0
                       (list (quote rejected) (quote invalid-utf8)))))))
              ((utf8-in-range? b1 194 223) 0
               (cond
                 ; 3-byte sequence with overlong/surrogate exclusions.
                 ((utf8-in-range? b1 224 239) 1
                  (cond
                    ((atom r1)
                     (structural-kind empty-list)
                     (list (quote rejected) (quote invalid-utf8)))
                    ((atom r1)
                     (structural-kind pair)
                     (let ((r2 (cdr r1)))
                       (cond
                         ((atom r2)
                          (structural-kind empty-list)
                          (list (quote rejected) (quote invalid-utf8)))
                         ((atom r2)
                          (structural-kind pair)
                          (let* ((b2 (car r1))
                                 (b3 (car r2)))
                            (cond
                              ((utf8-three-byte-second-ok? b1 b2) 1
                               (cond
                                 ((utf8-continuation-byte? b3) 1
                                  (utf8-decode-onto
                                    (cdr r2)
                                    (cons (+ (* (- b1 224) 4096)
                                             (* (- b2 128) 64)
                                             (- b3 128))
                                          out)))
                                 ((utf8-continuation-byte? b3) 0
                                  (list (quote rejected)
                                        (quote invalid-utf8)))))
                              ((utf8-three-byte-second-ok? b1 b2) 0
                               (list (quote rejected)
                                     (quote invalid-utf8))))))))))
                 ((utf8-in-range? b1 224 239) 0
                  (cond
                    ; 4-byte sequence, restricted to Unicode scalar <= 10FFFF.
                    ((utf8-in-range? b1 240 244) 1
                     (cond
                       ((atom r1)
                        (structural-kind empty-list)
                        (list (quote rejected) (quote invalid-utf8)))
                       ((atom r1)
                        (structural-kind pair)
                        (let ((r2 (cdr r1)))
                          (cond
                            ((atom r2)
                             (structural-kind empty-list)
                             (list (quote rejected) (quote invalid-utf8)))
                            ((atom r2)
                             (structural-kind pair)
                             (let ((r3 (cdr r2)))
                               (cond
                                 ((atom r3)
                                  (structural-kind empty-list)
                                  (list (quote rejected) (quote invalid-utf8)))
                                 ((atom r3)
                                  (structural-kind pair)
                                  (let* ((b2 (car r1))
                                         (b3 (car r2))
                                         (b4 (car r3)))
                                    (cond
                                      ((utf8-four-byte-second-ok? b1 b2) 1
                                       (cond
                                         ((utf8-two-continuations? b3 b4) 1
                                          (utf8-decode-onto
                                            (cdr r3)
                                            (cons (+ (* (- b1 240) 262144)
                                                     (* (- b2 128) 4096)
                                                     (* (- b3 128) 64)
                                                     (- b4 128))
                                                  out)))
                                         ((utf8-two-continuations? b3 b4) 0
                                          (list (quote rejected)
                                                (quote invalid-utf8)))))
                                      ((utf8-four-byte-second-ok? b1 b2) 0
                                       (list (quote rejected)
                                             (quote invalid-utf8))))))))))))
                         ))
                       ))
                    ((utf8-in-range? b1 240 244) 0
                     (list (quote rejected) (quote invalid-utf8)))))
              )))
          )))
    ))))

(def utf8-decode
  (lambda (bytes)
    (cond
      ((utf8-all-bytes? bytes) 1
       (utf8-decode-onto bytes (quote ())))
      ((utf8-all-bytes? bytes) 0
       (list (quote rejected) (quote invalid-byte))))))

(def utf8-valid?
  (lambda (bytes)
    (eq (car (utf8-decode bytes)) (quote decoded))))

; Keep text materialization in tail position.
(def unicode-scalars->string-onto
  (lambda (scalars out)
    (cond
      ((atom scalars)
       (structural-kind empty-list)
       out)
      ((atom scalars)
       (structural-kind pair)
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
         (identity-relation same)
         (list (quote decoded)
               (unicode-scalars->string (car (cdr decoded)))))
        ((eq (car decoded) (quote decoded))
         (identity-relation distinct)
         decoded)))))

(def utf8-encode-string-onto
  (lambda (text out)
    (cond
      ((string-empty? text)
       (identity-relation same)
       (reverse out))
      ((string-empty? text)
       (identity-relation distinct)
       (let* ((character (string-first text))
              (rest (string-rest text))
              (scalar (string->codepoint character)))
         (cond
           ((<= scalar 127) 1
            (utf8-encode-string-onto rest (cons scalar out)))
           ((<= scalar 127) 0
            (cond
              ((<= scalar 2047) 1
               (utf8-encode-string-onto
                 rest
                 (cons (+ 128 (mod scalar 64))
                       (cons (+ 192 (quotient scalar 64)) out))))
              ((<= scalar 2047) 0
               (cond
                 ((<= scalar 65535) 1
                  (utf8-encode-string-onto
                    rest
                    (cons (+ 128 (mod scalar 64))
                          (cons (+ 128 (mod (quotient scalar 64) 64))
                                (cons (+ 224 (quotient scalar 4096))
                                      out)))))
                 ((<= scalar 65535) 0
                  (utf8-encode-string-onto
                    rest
                    (cons (+ 128 (mod scalar 64))
                          (cons (+ 128 (mod (quotient scalar 64) 64))
                                (cons (+ 128 (mod (quotient scalar 4096) 64))
                                      (cons (+ 240 (quotient scalar 262144))
                                            out)))))))))))))))

(def utf8-encode-string
  (lambda (text)
    (utf8-encode-string-onto text (quote ())))))
