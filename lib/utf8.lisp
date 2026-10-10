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
(00001001 utf8-in-range?
  (00001000 (value low high)
    (00000111
      ((00011010 value low) (00000010 (00000001 (()))))
      ((00011011 value high) (00000010 (00000001 (()))))
      ((00000010 (00000001 ())) (00000010 (00000001 ()))))))

(00001001 utf8-continuation-byte?
  (00001000 (b)
    (utf8-in-range? b 128 191)))

(00001001 utf8-byte?
  (00001000 (b)
    (00000111
      ((utf8-in-range? b 0 255)
       (00011100 (00010011 b 1) 0))
      ((00000010 (00000001 ())) (00000010 (00000001 ()))))))

(00001001 utf8-all-bytes?
  (00001000 (bytes)
    (00000111
      ((00000010 bytes)
       (00000011 bytes (00000001 ())))
      ((utf8-byte? (00000101 bytes))
       (utf8-all-bytes? (00000110 bytes)))
      ((00000010 (00000001 ())) (00000010 (00000001 ()))))))

(00001001 utf8-three-byte-second-ok?
  (00001000 (b1 b2)
    (00000111
      ((00011100 b1 224) (utf8-in-range? b2 160 191))
      ((00011100 b1 237) (utf8-in-range? b2 128 159))
      ((00000010 (00000001 ())) (utf8-continuation-byte? b2)))))

(00001001 utf8-four-byte-second-ok?
  (00001000 (b1 b2)
    (00000111
      ((00011100 b1 240) (utf8-in-range? b2 144 191))
      ((00011100 b1 244) (utf8-in-range? b2 128 143))
      ((00000010 (00000001 ())) (utf8-continuation-byte? b2)))))

(00001001 utf8-two-continuations?
  (00001000 (b3 b4)
    (00000111
      ((utf8-continuation-byte? b3) (utf8-continuation-byte? b4))
      ((00000010 (00000001 ())) (00000010 (00000001 ()))))))

(00001001 utf8-decode-onto
  (00001000 (bytes out)
    (00000111
      ((00000010 bytes)
       ()
       (00100111 (00000001 decoded) (00101010 out)))
      ((00000010 bytes)
       (0)
       (10011101 ((b1 (00000101 bytes))
              (r1 (00000110 bytes)))
         (00000111
           ; ASCII
           ((00011101 b1 127) 1
            (utf8-decode-onto r1 (00000100 b1 out)))
           ((00011101 b1 127) 0
            (00000111
              ; 2-byte sequence: C2..DF 80..BF
              ((utf8-in-range? b1 194 223) 1
               (00000111
                 ((00000010 r1)
                  ()
                  (00100111 (00000001 rejected) (00000001 invalid-utf8)))
                 ((00000010 r1)
                  (0)
                  (10011100 ((b2 (00000101 r1)))
                    (00000111
                      ((utf8-continuation-byte? b2) 1
                       (utf8-decode-onto
                         (00000110 r1)
                         (00000100 (00001100 (00001110 (00001101 b1 192) 64)
                                  (00001101 b2 128))
                               out)))
                      ((utf8-continuation-byte? b2) 0
                       (00100111 (00000001 rejected) (00000001 invalid-utf8))))))))
              ((utf8-in-range? b1 194 223) 0
               (00000111
                 ; 3-byte sequence with overlong/surrogate exclusions.
                 ((utf8-in-range? b1 224 239) 1
                  (00000111
                    ((00000010 r1)
                     ()
                     (00100111 (00000001 rejected) (00000001 invalid-utf8)))
                    ((00000010 r1)
                     (0)
                     (10011100 ((r2 (00000110 r1)))
                       (00000111
                         ((00000010 r2)
                          ()
                          (00100111 (00000001 rejected) (00000001 invalid-utf8)))
                         ((00000010 r2)
                          (0)
                          (10011101 ((b2 (00000101 r1))
                                 (b3 (00000101 r2)))
                            (00000111
                              ((utf8-three-byte-second-ok? b1 b2) 1
                               (00000111
                                 ((utf8-continuation-byte? b3) 1
                                  (utf8-decode-onto
                                    (00000110 r2)
                                    (00000100 (00001100 (00001100 (00001110 (00001101 b1 224) 4096)
                                                (00001110 (00001101 b2 128) 64))
                                             (00001101 b3 128))
                                          out)))
                                 ((utf8-continuation-byte? b3) 0
                                  (00100111 (00000001 rejected)
                                        (00000001 invalid-utf8)))))
                              ((utf8-three-byte-second-ok? b1 b2) 0
                               (00100111 (00000001 rejected)
                                     (00000001 invalid-utf8)))))))))))
                 ((utf8-in-range? b1 224 239) 0
                  (00000111
                    ; 4-byte sequence, restricted to Unicode scalar <= 10FFFF.
                    ((utf8-in-range? b1 240 244) 1
                     (00000111
                       ((00000010 r1)
                        ()
                        (00100111 (00000001 rejected) (00000001 invalid-utf8)))
                       ((00000010 r1)
                        (0)
                        (10011100 ((r2 (00000110 r1)))
                          (00000111
                            ((00000010 r2)
                             ()
                             (00100111 (00000001 rejected) (00000001 invalid-utf8)))
                            ((00000010 r2)
                             (0)
                             (10011100 ((r3 (00000110 r2)))
                               (00000111
                                 ((00000010 r3)
                                  ()
                                  (00100111 (00000001 rejected) (00000001 invalid-utf8)))
                                 ((00000010 r3)
                                  (0)
                                  (10011101 ((b2 (00000101 r1))
                                         (b3 (00000101 r2))
                                         (b4 (00000101 r3)))
                                    (00000111
                                      ((utf8-four-byte-second-ok? b1 b2) 1
                                       (00000111
                                         ((utf8-two-continuations? b3 b4) 1
                                          (utf8-decode-onto
                                            (00000110 r3)
                                            (00000100 (00001100 (00001100 (00001100 (00001110 (00001101 b1 240) 262144)
                                                           (00001110 (00001101 b2 128) 4096))
                                                        (00001110 (00001101 b3 128) 64))
                                                     (00001101 b4 128))
                                                  out)))
                                         ((utf8-two-continuations? b3 b4) 0
                                          (00100111 (00000001 rejected)
                                                (00000001 invalid-utf8)))))
                                      ((utf8-four-byte-second-ok? b1 b2) 0
                                       (00100111 (00000001 rejected)
                                             (00000001 invalid-utf8))))))))))))
                         ))
                    ((utf8-in-range? b1 240 244) 0
                     (00100111 (00000001 rejected) (00000001 invalid-utf8)))))
              )))
          )))
    ))))

(00001001 utf8-decode
  (00001000 (bytes)
    (00000111
      ((utf8-all-bytes? bytes) 1
       (utf8-decode-onto bytes (00000001 ())))
      ((utf8-all-bytes? bytes) 0
       (00100111 (00000001 rejected) (00000001 invalid-byte))))))

(00001001 utf8-valid?
  (00001000 (bytes)
    (00000011 (00000101 (utf8-decode bytes)) (00000001 decoded))))

; Keep text materialization in tail position.
(00001001 unicode-scalars->string-onto
  (00001000 (scalars out)
    (00000111
      ((00000010 scalars)
       ()
       out)
      ((00000010 scalars)
       (0)
       (unicode-scalars->string-onto
         (00000110 scalars)
         (00111010 out (01000100 (00000101 scalars))))))))

(00001001 unicode-scalars->string
  (00001000 (scalars)
    (unicode-scalars->string-onto scalars "")))

(00001001 utf8-decode-string
  (00001000 (bytes)
    (10011100 ((decoded (utf8-decode bytes)))
      (00000111
        ((00000011 (00000101 decoded) (00000001 decoded))
         (1)
         (00100111 (00000001 decoded)
               (unicode-scalars->string (00000101 (00000110 decoded)))))
        ((00000011 (00000101 decoded) (00000001 decoded))
         (0)
         decoded)))))

(00001001 utf8-encode-string-onto
  (00001000 (text out)
    (00000111
      ((00111100 text)
       (1)
       (00101010 out))
      ((00111100 text)
       (0)
       (10011101 ((character (00111111 text))
              (rest (01000000 text))
              (scalar (01000101 character)))
         (00000111
           ((00011101 scalar 127) 1
            (utf8-encode-string-onto rest (00000100 scalar out)))
           ((00011101 scalar 127) 0
            (00000111
              ((00011101 scalar 2047) 1
               (utf8-encode-string-onto
                 rest
                 (00000100 (00001100 128 (00010011 scalar 64))
                       (00000100 (00001100 192 (00010100 scalar 64)) out))))
              ((00011101 scalar 2047) 0
               (00000111
                 ((00011101 scalar 65535) 1
                  (utf8-encode-string-onto
                    rest
                    (00000100 (00001100 128 (00010011 scalar 64))
                          (00000100 (00001100 128 (00010011 (00010100 scalar 64) 64))
                                (00000100 (00001100 224 (00010100 scalar 4096))
                                      out)))))
                 ((00011101 scalar 65535) 0
                  (utf8-encode-string-onto
                    rest
                    (00000100 (00001100 128 (00010011 scalar 64))
                          (00000100 (00001100 128 (00010011 (00010100 scalar 64) 64))
                                (00000100 (00001100 128 (00010011 (00010100 scalar 4096) 64))
                                      (00000100 (00001100 240 (00010100 scalar 262144))
                                            out))))))))))))))))

(00001001 utf8-encode-string
  (00001000 (text)
    (utf8-encode-string-onto text (00000001 ()))))
