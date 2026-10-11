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
    (110
      ((11010 value low)  0)
      ((0100 (11010 value low))
       (110
         ((110100 value high)  1)
         ((0100 (110100 value high)) 0))))))

(0011 utf8-continuation-byte?
  (0010 (b)
    (110
      ((utf8-in-range? b 128 191)  1)
      ((0100 (utf8-in-range? b 128 191)) 0))))

(0011 utf8-byte?
  (0010 (b)
    (110
      ((utf8-in-range? b 0 255) 
       (110
         ((11110111 (00101100 b 1) 0)  1)
         ((0100 (11110111 (00101100 b 1) 0)) 0)))
      ((0100 (utf8-in-range? b 0 255)) 0))))

(0011 utf8-all-bytes?
  (0010 (bytes)
    (110
      ((0100 (010 bytes))
       (110
         ((101 bytes (001 ()))  1)
         ((0100 (101 bytes (001 ()))) 0)))
      ((0100 (010 bytes))
       (110
         ((utf8-byte? (100 bytes)) 
          (utf8-all-bytes? (011 bytes)))
         ((0100 (utf8-byte? (100 bytes))) 0))))))

(0011 utf8-three-byte-second-ok?
  (0010 (b1 b2)
    (110
      ((11110111 b1 224) 
       (utf8-in-range? b2 160 191))
      ((0100 (11110111 b1 224))
       (110
         ((11110111 b1 237) 
          (utf8-in-range? b2 128 159))
         ((0100 (11110111 b1 237))
          (utf8-continuation-byte? b2)))))))

(0011 utf8-four-byte-second-ok?
  (0010 (b1 b2)
    (110
      ((11110111 b1 240) 
       (utf8-in-range? b2 144 191))
      ((0100 (11110111 b1 240))
       (110
         ((11110111 b1 244) 
          (utf8-in-range? b2 128 143))
         ((0100 (11110111 b1 244))
          (utf8-continuation-byte? b2)))))))

(0011 utf8-two-continuations?
  (0010 (b3 b4)
    (110
      ((utf8-continuation-byte? b3) 
       (110
         ((utf8-continuation-byte? b4)  1)
         ((0100 (utf8-continuation-byte? b4)) 0)))
      ((0100 (utf8-continuation-byte? b3)) 0))))

(0011 utf8-decode-onto
  (0010 (bytes out)
    (110
      ((0100 (010 bytes))
       (1110 (001 decoded) (10100 out)))
      ((0100 (010 bytes))
       (001001 ((b1 (100 bytes))
              (r1 (011 bytes)))
         (110
           ; ASCII
           ((110100 b1 127) 
            (utf8-decode-onto r1 (111 b1 out)))
           ((0100 (110100 b1 127))
            (110
              ; 2-byte sequence: C2..DF 80..BF
              ((utf8-in-range? b1 194 223) 
               (110
                 ((0100 (010 r1))
                  (1110 (001 rejected) (001 invalid-utf8)))
                 ((0100 (010 r1))
                  (001000 ((b2 (100 r1)))
                    (110
                      ((utf8-continuation-byte? b2) 
                       (utf8-decode-onto
                         (011 r1)
                         (111 (01010 (10110 (01011 b1 192) 64)
                                  (01011 b2 128))
                               out)))
                      ((0100 (utf8-continuation-byte? b2))
                       (1110 (001 rejected) (001 invalid-utf8))))))))
              ((0100 (utf8-in-range? b1 194 223))
               (110
                 ; 3-byte sequence with overlong/surrogate exclusions.
                 ((utf8-in-range? b1 224 239) 
                  (110
                    ((0100 (010 r1))
                     (1110 (001 rejected) (001 invalid-utf8)))
                    ((0100 (010 r1))
                     (001000 ((r2 (011 r1)))
                       (110
                         ((0100 (010 r2))
                          (1110 (001 rejected) (001 invalid-utf8)))
                         ((0100 (010 r2))
                          (001001 ((b2 (100 r1))
                                 (b3 (100 r2)))
                            (110
                              ((utf8-three-byte-second-ok? b1 b2) 
                               (110
                                 ((utf8-continuation-byte? b3) 
                                  (utf8-decode-onto
                                    (011 r2)
                                    (111 (01010 (01010 (10110 (01011 b1 224) 4096)
                                                (10110 (01011 b2 128) 64))
                                             (01011 b3 128))
                                          out)))
                                 ((0100 (utf8-continuation-byte? b3))
                                  (1110 (001 rejected)
                                        (001 invalid-utf8)))))
                              ((0100 (utf8-three-byte-second-ok? b1 b2))
                               (1110 (001 rejected)
                                     (001 invalid-utf8)))))))))))
                 ((0100 (utf8-in-range? b1 224 239))
                  (110
                    ; 4-byte sequence, restricted to Unicode scalar <= 10FFFF.
                    ((utf8-in-range? b1 240 244) 
                     (110
                       ((0100 (010 r1))
                        (1110 (001 rejected) (001 invalid-utf8)))
                       ((0100 (010 r1))
                        (001000 ((r2 (011 r1)))
                          (110
                            ((0100 (010 r2))
                             (1110 (001 rejected) (001 invalid-utf8)))
                            ((0100 (010 r2))
                             (001000 ((r3 (011 r2)))
                               (110
                                 ((0100 (010 r3))
                                  (1110 (001 rejected) (001 invalid-utf8)))
                                 ((0100 (010 r3))
                                  (001001 ((b2 (100 r1))
                                         (b3 (100 r2))
                                         (b4 (100 r3)))
                                    (110
                                      ((utf8-four-byte-second-ok? b1 b2) 
                                       (110
                                         ((utf8-two-continuations? b3 b4) 
                                          (utf8-decode-onto
                                            (011 r3)
                                            (111 (01010 (01010 (01010 (10110 (01011 b1 240) 262144)
                                                           (10110 (01011 b2 128) 4096))
                                                        (10110 (01011 b3 128) 64))
                                                     (01011 b4 128))
                                                  out)))
                                         ((0100 (utf8-two-continuations? b3 b4))
                                          (1110 (001 rejected)
                                                (001 invalid-utf8)))))
                                      ((0100 (utf8-four-byte-second-ok? b1 b2))
                                       (1110 (001 rejected)
                                             (001 invalid-utf8))))))))))))
                         ))
                    ((0100 (utf8-in-range? b1 240 244))
                     (1110 (001 rejected) (001 invalid-utf8)))))
              )))
          )))
    ))))

(0011 utf8-decode
  (0010 (bytes)
    (110
      ((utf8-all-bytes? bytes) 
       (utf8-decode-onto bytes (001 ())))
      ((0100 (utf8-all-bytes? bytes))
       (1110 (001 rejected) (001 invalid-byte))))))

(0011 utf8-valid?
  (0010 (bytes)
    (101 (100 (utf8-decode bytes)) (001 decoded))))

; Keep text materialization in tail position.
(0011 unicode-scalars->string-onto
  (0010 (scalars out)
    (110
      ((0100 (010 scalars))
       out)
      ((0100 (010 scalars))
       (unicode-scalars->string-onto
         (011 scalars)
         (110011110 out (00000000 (100 scalars))))))))

(0011 unicode-scalars->string
  (0010 (scalars)
    (unicode-scalars->string-onto scalars "")))

(0011 utf8-decode-string
  (0010 (bytes)
    (001000 ((decoded (utf8-decode bytes)))
      (110
        ((101 (100 decoded) (001 decoded))
         
         (1110 (001 decoded)
               (unicode-scalars->string (100 (011 decoded)))))
        ((0100 (101 (100 decoded) (001 decoded)))
         decoded)))))

(0011 utf8-encode-string-onto
  (0010 (text out)
    (110
      ((110011100 text)
       
       (10100 out))
      ((0100 (110011100 text))
       (001001 ((character (110101011 text))
              (rest (110011101 text))
              (scalar (11100000 character)))
         (110
           ((110100 scalar 127) 
            (utf8-encode-string-onto rest (111 scalar out)))
           ((0100 (110100 scalar 127))
            (110
              ((110100 scalar 2047) 
               (utf8-encode-string-onto
                 rest
                 (111 (01010 128 (00101100 scalar 64))
                       (111 (01010 192 (10111 scalar 64)) out))))
              ((0100 (110100 scalar 2047))
               (110
                 ((110100 scalar 65535) 
                  (utf8-encode-string-onto
                    rest
                    (111 (01010 128 (00101100 scalar 64))
                          (111 (01010 128 (00101100 (10111 scalar 64) 64))
                                (111 (01010 224 (10111 scalar 4096))
                                      out)))))
                 ((0100 (110100 scalar 65535))
                  (utf8-encode-string-onto
                    rest
                    (111 (01010 128 (00101100 scalar 64))
                          (111 (01010 128 (00101100 (10111 scalar 64) 64))
                                (111 (01010 128 (00101100 (10111 scalar 4096) 64))
                                      (111 (01010 240 (10111 scalar 262144))
                                            out))))))))))))))))

(0011 utf8-encode-string
  (0010 (text)
    (utf8-encode-string-onto text (001 ()))))
