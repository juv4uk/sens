; Lisp-owned fixed-width byte domain.
; The width-8 Binary value is the language's u8 value: no second U8 storage type exists.
; u8 is represented by the native 8-bit Binary value already understood by the reader.
; There is no second hidden decimal or host-byte representation.
;
; Laws:
; - integer<->u8 conversion is explicit;
; - u8? is true exactly for width-8 Binary values;
; - u8-add rejects overflow;
; - u8-sub rejects underflow;
; - shifts accept counts 0..7 and reject 8 or larger counts;
; - left shift is fixed-width: bits shifted past bit 7 are discarded;
; - printing a u8 is the canonical 8-bit binary spelling.
(def u8?
  (lambda (value)
    (u8-native? value)))

(def binary->u8
  (lambda (value)
    (u8-native-from-binary value)))

(def u8->binary
  (lambda (value)
    (u8-native-to-binary value)))

(def u8->integer
  (lambda (value)
    (u8-native-to-integer value)))

(def integer->u8
  (lambda (value)
    (u8-native-from-integer value)))

(def u8
  (lambda (value)
    (if (u8? value)
        value
        (integer->u8 value))))

(def u8-and
  (lambda (left right)
    (u8-native-and left right)))

(def u8-or
  (lambda (left right)
    (u8-native-or left right)))

(def u8-xor
  (lambda (left right)
    (u8-native-xor left right)))

(def u8-not
  (lambda (value)
    (u8-native-not value)))

(def u8-shl
  (lambda (value count)
    (u8-native-shl value count)))

(def u8-shr
  (lambda (value count)
    (u8-native-shr value count)))

(def u8-add
  (lambda (left right)
    (u8-native-add left right)))

(def u8-sub
  (lambda (left right)
    (u8-native-sub left right)))
