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
(0011 utf8-in-range?
  (0010 (value low high)
    (011
      ((01110 value low) 1 0)
      ((01110 value low) 0
       (011
         ((not-greaterp? value high) 1 1)
         ((not-greaterp? value high) 0 0))))))

(0011 utf8-continuation-byte?
  (0010 (b)
    (011
      ((utf8-in-range? b 128 191) 1 1)
      ((utf8-in-range? b 128 191) 0 0))))

(0011 utf8-byte?
  (0010 (b)
    (011
      ((utf8-in-range? b 0 255) 1
       (011
         ((equalp? (mod b 1) 0) 1 1)
         ((equalp? (mod b 1) 0) 0 0)))
      ((utf8-in-range? b 0 255) 0 0))))

(0011 utf8-all-bytes?
  (0010 (bytes)
    (011
      ((010 bytes)
       ()
       (011
         ((111 bytes (001 ())) (1) 1)
         ((111 bytes (001 ())) (0) 0)))
      ((010 bytes)
       (0)
       (011
         ((utf8-byte? (101 bytes)) 1
          (utf8-all-bytes? (110 bytes)))
         ((utf8-byte? (101 bytes)) 0 0))))))

(0011 utf8-three-byte-second-ok?
  (0010 (b1 b2)
    (011
      ((equalp? b1 224) 1
       (utf8-in-range? b2 160 191))
      ((equalp? b1 224) 0
       (011
         ((equalp? b1 237) 1
          (utf8-in-range? b2 128 159))
         ((equalp? b1 237) 0
          (utf8-continuation-byte? b2)))))))

(0011 utf8-four-byte-second-ok?
  (0010 (b1 b2)
    (011
      ((equalp? b1 240) 1
       (utf8-in-range? b2 144 191))
      ((equalp? b1 240) 0
       (011
         ((equalp? b1 244) 1
          (utf8-in-range? b2 128 143))
         ((equalp? b1 244) 0
          (utf8-continuation-byte? b2)))))))

(0011 utf8-two-continuations?
  (0010 (b3 b4)
    (011
      ((utf8-continuation-byte? b3) 1
       (011
         ((utf8-continuation-byte? b4) 1 1)
         ((utf8-continuation-byte? b4) 0 0)))
      ((utf8-continuation-byte? b3) 0 0))))

(0011 utf8-decode-onto
  (0010 (bytes out)
    (011
      ((010 bytes)
       ()
       (list (001 decoded) (reverse out)))
      ((010 bytes)
       (0)
       (let* ((b1 (101 bytes))
              (r1 (110 bytes)))
         (011
           ; ASCII
           ((not-greaterp? b1 127) 1
            (utf8-decode-onto r1 (100 b1 out)))
           ((not-greaterp? b1 127) 0
            (011
              ; 2-byte sequence: C2..DF 80..BF
              ((utf8-in-range? b1 194 223) 1
               (011
                 ((010 r1)
                  ()
                  (list (001 rejected) (001 invalid-utf8)))
                 ((010 r1)
                  (0)
                  (let ((b2 (101 r1)))
                    (011
                      ((utf8-continuation-byte? b2) 1
                       (utf8-decode-onto
                         (110 r1)
                         (100 (01010 (10010 (01011 b1 192) 64)
                                  (01011 b2 128))
                               out)))
                      ((utf8-continuation-byte? b2) 0
                       (list (001 rejected) (001 invalid-utf8))))))))
              ((utf8-in-range? b1 194 223) 0
               (011
                 ; 3-byte sequence with overlong/surrogate exclusions.
                 ((utf8-in-range? b1 224 239) 1
                  (011
                    ((010 r1)
                     ()
                     (list (001 rejected) (001 invalid-utf8)))
                    ((010 r1)
                     (0)
                     (let ((r2 (110 r1)))
                       (011
                         ((010 r2)
                          ()
                          (list (001 rejected) (001 invalid-utf8)))
                         ((010 r2)
                          (0)
                          (let* ((b2 (101 r1))
                                 (b3 (101 r2)))
                            (011
                              ((utf8-three-byte-second-ok? b1 b2) 1
                               (011
                                 ((utf8-continuation-byte? b3) 1
                                  (utf8-decode-onto
                                    (110 r2)
                                    (100 (01010 (01010 (10010 (01011 b1 224) 4096)
                                                (10010 (01011 b2 128) 64))
                                             (01011 b3 128))
                                          out)))
                                 ((utf8-continuation-byte? b3) 0
                                  (list (001 rejected)
                                        (001 invalid-utf8)))))
                              ((utf8-three-byte-second-ok? b1 b2) 0
                               (list (001 rejected)
                                     (001 invalid-utf8)))))))))))
                 ((utf8-in-range? b1 224 239) 0
                  (011
                    ; 4-byte sequence, restricted to Unicode scalar <= 10FFFF.
                    ((utf8-in-range? b1 240 244) 1
                     (011
                       ((010 r1)
                        ()
                        (list (001 rejected) (001 invalid-utf8)))
                       ((010 r1)
                        (0)
                        (let ((r2 (110 r1)))
                          (011
                            ((010 r2)
                             ()
                             (list (001 rejected) (001 invalid-utf8)))
                            ((010 r2)
                             (0)
                             (let ((r3 (110 r2)))
                               (011
                                 ((010 r3)
                                  ()
                                  (list (001 rejected) (001 invalid-utf8)))
                                 ((010 r3)
                                  (0)
                                  (let* ((b2 (101 r1))
                                         (b3 (101 r2))
                                         (b4 (101 r3)))
                                    (011
                                      ((utf8-four-byte-second-ok? b1 b2) 1
                                       (011
                                         ((utf8-two-continuations? b3 b4) 1
                                          (utf8-decode-onto
                                            (110 r3)
                                            (100 (01010 (01010 (01010 (10010 (01011 b1 240) 262144)
                                                           (10010 (01011 b2 128) 4096))
                                                        (10010 (01011 b3 128) 64))
                                                     (01011 b4 128))
                                                  out)))
                                         ((utf8-two-continuations? b3 b4) 0
                                          (list (001 rejected)
                                                (001 invalid-utf8)))))
                                      ((utf8-four-byte-second-ok? b1 b2) 0
                                       (list (001 rejected)
                                             (001 invalid-utf8))))))))))))
                         ))
                    ((utf8-in-range? b1 240 244) 0
                     (list (001 rejected) (001 invalid-utf8)))))
              )))
          )))
    ))))

(0011 utf8-decode
  (0010 (bytes)
    (011
      ((utf8-all-bytes? bytes) 1
       (utf8-decode-onto bytes (001 ())))
      ((utf8-all-bytes? bytes) 0
       (list (001 rejected) (001 invalid-byte))))))

(0011 utf8-valid?
  (0010 (bytes)
    (111 (101 (utf8-decode bytes)) (001 decoded))))

; Keep text materialization in tail position.
(0011 unicode-scalars->string-onto
  (0010 (scalars out)
    (011
      ((010 scalars)
       ()
       out)
      ((010 scalars)
       (0)
       (unicode-scalars->string-onto
         (110 scalars)
         (string-append out (codepoint->string (101 scalars))))))))

(0011 unicode-scalars->string
  (0010 (scalars)
    (unicode-scalars->string-onto scalars "")))

(0011 utf8-decode-string
  (0010 (bytes)
    (let ((decoded (utf8-decode bytes)))
      (011
        ((111 (101 decoded) (001 decoded))
         (1)
         (list (001 decoded)
               (unicode-scalars->string (101 (110 decoded)))))
        ((111 (101 decoded) (001 decoded))
         (0)
         decoded)))))

(0011 utf8-encode-string-onto
  (0010 (text out)
    (011
      ((string-empty? text)
       (1)
       (reverse out))
      ((string-empty? text)
       (0)
       (let* ((character (string-first text))
              (rest (string-rest text))
              (scalar (string->codepoint character)))
         (011
           ((not-greaterp? scalar 127) 1
            (utf8-encode-string-onto rest (100 scalar out)))
           ((not-greaterp? scalar 127) 0
            (011
              ((not-greaterp? scalar 2047) 1
               (utf8-encode-string-onto
                 rest
                 (100 (01010 128 (mod scalar 64))
                       (100 (01010 192 (quotient scalar 64)) out))))
              ((not-greaterp? scalar 2047) 0
               (011
                 ((not-greaterp? scalar 65535) 1
                  (utf8-encode-string-onto
                    rest
                    (100 (01010 128 (mod scalar 64))
                          (100 (01010 128 (mod (quotient scalar 64) 64))
                                (100 (01010 224 (quotient scalar 4096))
                                      out)))))
                 ((not-greaterp? scalar 65535) 0
                  (utf8-encode-string-onto
                    rest
                    (100 (01010 128 (mod scalar 64))
                          (100 (01010 128 (mod (quotient scalar 64) 64))
                                (100 (01010 128 (mod (quotient scalar 4096) 64))
                                      (100 (01010 240 (quotient scalar 262144))
                                            out))))))))))))))))

(0011 utf8-encode-string
  (0010 (text)
    (utf8-encode-string-onto text (001 ()))))
