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

; UTF-8 predicate verdicts are direct D1 bits: #d1:1 / #d1:0.
; Structural () remains data; byte arithmetic remains in its admitted numeric roles.
(0011 utf8-in-range?
  (0010 (value low high)
    (110
      ((11010 value low)  #d1:0)
      ((0100 (11010 value low))
       (110
         ((0100 (11010 high value))  #d1:1)
         ((0100 (0100 (11010 high value))) #d1:0))))))

(0011 utf8-continuation-byte?
  (0010 (b)
    (110
      ((кодова-одиниця-кодування-юнікод-8-у-допустимому-діапазоні? b 128 191)  так)
      ((хибне? (кодова-одиниця-кодування-юнікод-8-у-допустимому-діапазоні? b 128 191)) ні))))

(0011 utf8-byte?
  (0010 (b)
    (110
      ((кодова-одиниця-кодування-юнікод-8-у-допустимому-діапазоні? b 0 255) 
       (110
         ((101 (00101100 b 1) 0)  #d1:1)
         ((0100 (101 (00101100 b 1) 0)) #d1:0)))
      ((хибне? (кодова-одиниця-кодування-юнікод-8-у-допустимому-діапазоні? b 0 255)) ні))))

(0011 utf8-all-bytes?
  (0010 (bytes)
    (110
      ((010 bytes)
       (110
         ((101 bytes (001 ()))  #d1:1)
         ((0100 (101 bytes (001 ()))) #d1:0)))
      ((0100 (010 bytes))
       (110
         ((це-допустимий-байт-кодування-юнікод-8? (перше bytes)) 
          (усі-елементи-є-байтами-кодування-юнікод-8? (решта bytes)))
         ((хибне? (це-допустимий-байт-кодування-юнікод-8? (перше bytes))) ні))))))

(0011 utf8-three-byte-second-ok?
  (0010 (b1 b2)
    (110
      ((101 b1 224) 
       (кодова-одиниця-кодування-юнікод-8-у-допустимому-діапазоні? b2 160 191))
      ((0100 (101 b1 224))
       (110
         ((101 b1 237) 
          (кодова-одиниця-кодування-юнікод-8-у-допустимому-діапазоні? b2 128 159))
         ((0100 (101 b1 237))
          (це-байт-продовження-кодування-юнікод-8? b2)))))))

(0011 utf8-four-byte-second-ok?
  (0010 (b1 b2)
    (110
      ((101 b1 240) 
       (кодова-одиниця-кодування-юнікод-8-у-допустимому-діапазоні? b2 144 191))
      ((0100 (101 b1 240))
       (110
         ((101 b1 244) 
          (кодова-одиниця-кодування-юнікод-8-у-допустимому-діапазоні? b2 128 143))
         ((0100 (101 b1 244))
          (це-байт-продовження-кодування-юнікод-8? b2)))))))

(0011 utf8-two-continuations?
  (0010 (b3 b4)
    (110
      ((це-байт-продовження-кодування-юнікод-8? b3) 
       (110
         ((це-байт-продовження-кодування-юнікод-8? b4)  так)
         ((хибне? (це-байт-продовження-кодування-юнікод-8? b4)) ні)))
      ((хибне? (це-байт-продовження-кодування-юнікод-8? b3)) ні))))

(0011 utf8-decode-onto
  (0010 (bytes out)
    (110
      ((010 bytes)
       (1110 (001 decoded) (10100 out)))
      ((0100 (010 bytes))
       (001001 ((b1 (100 bytes))
              (r1 (011 bytes)))
         (110
           ; ASCII
           ((0100 (11010 127 b1)) 
            (utf8-decode-onto r1 (111 b1 out)))
           ((0100 (0100 (11010 127 b1)))
            (110
              ; 2-byte sequence: C2..DF 80..BF
              ((кодова-одиниця-кодування-юнікод-8-у-допустимому-діапазоні? b1 194 223) 
               (110
                 ((010 r1)
                  (1110 (001 rejected) (001 invalid-utf8)))
                 ((0100 (010 r1))
                  (001000 ((b2 (100 r1)))
                    (110
                      ((це-байт-продовження-кодування-юнікод-8? b2) 
                       (utf8-decode-onto
                         (011 r1)
                         (111 (01010 (10110 (01011 b1 192) 64)
                                  (01011 b2 128))
                               out)))
                      ((хибне? (це-байт-продовження-кодування-юнікод-8? b2))
                       (1110 (001 rejected) (001 invalid-utf8))))))))
              ((хибне? (кодова-одиниця-кодування-юнікод-8-у-допустимому-діапазоні? b1 194 223))
               (110
                 ; 3-byte sequence with overlong/surrogate exclusions.
                 ((кодова-одиниця-кодування-юнікод-8-у-допустимому-діапазоні? b1 224 239) 
                  (110
                    ((010 r1)
                     (1110 (001 rejected) (001 invalid-utf8)))
                    ((0100 (010 r1))
                     (001000 ((r2 (011 r1)))
                       (110
                         ((010 r2)
                          (1110 (001 rejected) (001 invalid-utf8)))
                         ((0100 (010 r2))
                          (001001 ((b2 (100 r1))
                                 (b3 (100 r2)))
                            (110
                              ((другий-байт-трибайтової-послідовності-кодування-юнікод-8-коректний? b1 b2) 
                               (110
                                 ((це-байт-продовження-кодування-юнікод-8? b3) 
                                  (utf8-decode-onto
                                    (011 r2)
                                    (111 (01010 (01010 (10110 (01011 b1 224) 4096)
                                                (10110 (01011 b2 128) 64))
                                             (01011 b3 128))
                                          out)))
                                 ((хибне? (це-байт-продовження-кодування-юнікод-8? b3))
                                  (1110 (001 rejected)
                                        (001 invalid-utf8)))))
                              ((хибне? (другий-байт-трибайтової-послідовності-кодування-юнікод-8-коректний? b1 b2))
                               (1110 (001 rejected)
                                     (001 invalid-utf8)))))))))))
                 ((хибне? (кодова-одиниця-кодування-юнікод-8-у-допустимому-діапазоні? b1 224 239))
                  (110
                    ; 4-byte sequence, restricted to Unicode scalar <= 10FFFF.
                    ((кодова-одиниця-кодування-юнікод-8-у-допустимому-діапазоні? b1 240 244) 
                     (110
                       ((010 r1)
                        (1110 (001 rejected) (001 invalid-utf8)))
                       ((0100 (010 r1))
                        (001000 ((r2 (011 r1)))
                          (110
                            ((010 r2)
                             (1110 (001 rejected) (001 invalid-utf8)))
                            ((0100 (010 r2))
                             (001000 ((r3 (011 r2)))
                               (110
                                 ((010 r3)
                                  (1110 (001 rejected) (001 invalid-utf8)))
                                 ((0100 (010 r3))
                                  (001001 ((b2 (100 r1))
                                         (b3 (100 r2))
                                         (b4 (100 r3)))
                                    (110
                                      ((другий-байт-чотирибайтової-послідовності-кодування-юнікод-8-коректний? b1 b2) 
                                       (110
                                         ((наявні-два-байти-продовження-кодування-юнікод-8? b3 b4) 
                                          (utf8-decode-onto
                                            (011 r3)
                                            (111 (01010 (01010 (01010 (10110 (01011 b1 240) 262144)
                                                           (10110 (01011 b2 128) 4096))
                                                        (10110 (01011 b3 128) 64))
                                                     (01011 b4 128))
                                                  out)))
                                         ((хибне? (наявні-два-байти-продовження-кодування-юнікод-8? b3 b4))
                                          (1110 (001 rejected)
                                                (001 invalid-utf8)))))
                                      ((хибне? (другий-байт-чотирибайтової-послідовності-кодування-юнікод-8-коректний? b1 b2))
                                       (1110 (001 rejected)
                                             (001 invalid-utf8))))))))))))
                         ))
                    ((хибне? (кодова-одиниця-кодування-юнікод-8-у-допустимому-діапазоні? b1 240 244))
                     (1110 (001 rejected) (001 invalid-utf8)))))
              )))
          )))
    ))))

(0011 utf8-decode
  (0010 (bytes)
    (110
      ((усі-елементи-є-байтами-кодування-юнікод-8? bytes) 
       (utf8-decode-onto bytes (001 ())))
      ((хибне? (усі-елементи-є-байтами-кодування-юнікод-8? bytes))
       (1110 (001 rejected) (001 invalid-byte))))))

(0011 utf8-valid?
  (0010 (bytes)
    (тотожне? (перше (кодування-юнікод-8-декодувати bytes)) (як-є decoded))))

; Keep text materialization in tail position.
(0011 unicode-scalars->string-onto
  (0010 (scalars out)
    (110
      ((010 scalars)
       out)
      ((0100 (010 scalars))
       (unicode-scalars->string-onto
         (011 scalars)
         (110011110 out (00000000 (100 scalars))))))))

(0011 unicode-scalars->string
  (0010 (scalars)
    (unicode-scalars->string-onto scalars "")))

; D6 LET is ratified but this path does not infer executable binding
; from a bare numeric head. Use the admitted D4 LAMBDA application, like TCP.
; Decode once; the original two-branch semantic law remains SENS-owned.
(0011 utf8-decode-string
  (0010 (bytes)
    ((0010 (decoded)
       (110
         ((101 (100 decoded) (001 decoded))
          (1110 (001 decoded)
                (unicode-scalars->string (100 (011 decoded)))))
         ((0100 (101 (100 decoded) (001 decoded)))
          decoded)))
     (кодування-юнікод-8-декодувати bytes))))

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
           ((0100 (11010 127 scalar)) 
            (utf8-encode-string-onto rest (111 scalar out)))
           ((0100 (0100 (11010 127 scalar)))
            (110
              ((0100 (11010 2047 scalar)) 
               (utf8-encode-string-onto
                 rest
                 (111 (01010 128 (00101100 scalar 64))
                       (111 (01010 192 (10111 scalar 64)) out))))
              ((0100 (0100 (11010 2047 scalar)))
               (110
                 ((0100 (11010 65535 scalar)) 
                  (utf8-encode-string-onto
                    rest
                    (111 (01010 128 (00101100 scalar 64))
                          (111 (01010 128 (00101100 (10111 scalar 64) 64))
                                (111 (01010 224 (10111 scalar 4096))
                                      out)))))
                 ((0100 (0100 (11010 65535 scalar)))
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

; D9 ratified UTF-8 Ukrainian projection; existing SENS Lisp codec is owner.
; These names do not assert direct D9 opcode callability.
; D9:000001001
(визначити utf8-декодувати кодування-юнікод-8-декодувати)
; D9:000101011
(0011 utf8-чинний? utf8-valid?)
; D9:000100010
(0011 unicode-скаляри-рядок unicode-scalars->string)
; D9:000001010
(0011 utf8-декодувати-рядок utf8-decode-string)
; D9:000010101
(0011 utf8-кодувати-рядок utf8-encode-string)

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити усі-елементи-є-байтами-кодування-юнікод-8? utf8-all-bytes?)
(визначити це-допустимий-байт-кодування-юнікод-8? utf8-byte?)
(визначити це-байт-продовження-кодування-юнікод-8? utf8-continuation-byte?)
(визначити кодування-юнікод-8-декодувати utf8-decode)
(визначити другий-байт-чотирибайтової-послідовності-кодування-юнікод-8-коректний? utf8-four-byte-second-ok?)
(визначити кодова-одиниця-кодування-юнікод-8-у-допустимому-діапазоні? utf8-in-range?)
(визначити другий-байт-трибайтової-послідовності-кодування-юнікод-8-коректний? utf8-three-byte-second-ok?)
(визначити наявні-два-байти-продовження-кодування-юнікод-8? utf8-two-continuations?)
