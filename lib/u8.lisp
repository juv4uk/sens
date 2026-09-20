; Lisp-owned fixed-width byte domain.
; The width-8 Binary value is the language's u8 value: no second U8 storage type exists.
; u8 is represented by the native 8-bit Binary value already understood by the reader.
; There is no second hidden decimal or host-byte representation.
;
; Rust owns only representation mechanisms used below:
; - recognize/materialize width-8 Binary;
; - explicitly observe a u8 as an ordinary integer;
; - explicitly materialize a u8 from an ordinary exact integer.
; Bitwise, ordering, shift and arithmetic laws are Lisp code in this file.
;
; Laws:
; - integer<->u8 conversion is explicit;
; - u8? is true exactly for width-8 Binary values;
; - u8-add rejects overflow through integer->u8's 0..255 gate;
; - u8-sub rejects underflow through the same gate;
; - shifts accept exact integer counts 0..7 and reject other counts;
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

(def u8=
  (lambda (left right)
    (= (u8->integer left) (u8->integer right))))

(def u8<
  (lambda (left right)
    (< (u8->integer left) (u8->integer right))))

; Fold exactly eight low-order bits. combine receives only 0/1 integers.
(def u8-bit-fold
  (lambda (left right place remaining acc combine)
    (cond
      ((= remaining 0) 1 acc)
      ((= remaining 0) 0
       (let* ((left-bit (mod left 2))
              (right-bit (mod right 2))
              (result-bit (combine left-bit right-bit)))
         (u8-bit-fold
           (quotient left 2)
           (quotient right 2)
           (* place 2)
           (- remaining 1)
           (+ acc (* result-bit place))
           combine))))))

(def u8-and
  (lambda (left right)
    (integer->u8
      (u8-bit-fold
        (u8->integer left)
        (u8->integer right)
        1
        8
        0
        (lambda (left-bit right-bit)
          (* left-bit right-bit))))))

(def u8-or
  (lambda (left right)
    (integer->u8
      (u8-bit-fold
        (u8->integer left)
        (u8->integer right)
        1
        8
        0
        (lambda (left-bit right-bit)
          (- (+ left-bit right-bit) (* left-bit right-bit)))))))

(def u8-xor
  (lambda (left right)
    (integer->u8
      (u8-bit-fold
        (u8->integer left)
        (u8->integer right)
        1
        8
        0
        (lambda (left-bit right-bit)
          (mod (+ left-bit right-bit) 2))))))

(def u8-not
  (lambda (value)
    (integer->u8 (- 255 (u8->integer value)))))

(def u8-power-of-two
  (lambda (count)
    (cond
      ((= count 0) 1 1)
      ((< count 0) 1 (/ 1 0))
      ((< 0 count) 1 (* 2 (u8-power-of-two (- count 1)))))))

(def u8-shift-factor
  (lambda (count)
    (cond
      ((< count 0) 1 (/ 1 0))
      ((< 7 count) 1 (/ 1 0))
      ((< count 8) 1 (u8-power-of-two count)))))

(def u8-shl
  (lambda (value count)
    (integer->u8
      (mod
        (* (u8->integer value) (u8-shift-factor count))
        256))))

(def u8-shr
  (lambda (value count)
    (integer->u8
      (quotient
        (u8->integer value)
        (u8-shift-factor count)))))

(def u8-add
  (lambda (left right)
    (integer->u8
      (+ (u8->integer left) (u8->integer right)))))

(def u8-sub
  (lambda (left right)
    (integer->u8
      (- (u8->integer left) (u8->integer right)))))
