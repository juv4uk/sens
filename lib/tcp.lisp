; TCP text interpretation and public listen policy owned by Lisp.
; Інтерпретація TCP-тексту й публічна політика listen, якими володіє Lisp.
;
; Migrated: two-field COND only; direct D1:YES fallback #d1:1.
; Reuses utf8-decode-string / utf8-encode-string from lib/utf8.lisp and
; tcp-listen-raw / tcp-read-raw / tcp-write-raw host mechanism.
; Width is identity; every bit of the domain address is valued.
;
; Host capabilities expose mechanism only. This layer owns the historical
; default bind address, UTF-8 decoding/encoding, and public meanings of
; tcp-listen, tcp-read, and tcp-write.
; Load `lib/utf8.lisp` before this file.

; Preserve historical public behavior: listen on all IPv4 interfaces.
; Callers that need an explicit address use tcp-listen-on.
(визначити tcp-listen-on
  (функція (вхідна-адреса мережевий-порт)
    (tcp-listen-raw вхідна-адреса мережевий-порт)))

(визначити tcp-listen
  (функція (мережевий-порт)
    (протокол-передавання-слухати-на "0.0.0.0" мережевий-порт)))

(визначити tcp-read-bytes->text
  (функція (вхідні-байти)
    ((функція (декодований-вміст)
       (за-умовою
         ((тотожне? (перше декодований-вміст) (як-є decoded))
          (друге декодований-вміст))
         (так
          декодований-вміст)))
     (кодування-юнікод-8-декодувати-рядок вхідні-байти))))

(визначити tcp-read
  (функція (мережеве-підключення)
    (протокол-передавання-читати-байти-текст (tcp-read-raw мережеве-підключення))))

(визначити tcp-write-text->bytes
  (функція (вхідний-текст)
    (кодування-юнікод-8-кодувати-рядок вхідний-текст)))

; Return the original text after a successful raw write so the public result
; remains compatible with the historical tcp-write surface while encoding
; policy belongs to Lisp.
(визначити tcp-write-via-raw
  (функція (мережеве-підключення вхідний-текст)
    ((функція (записано-байтів) вхідний-текст)
     (tcp-write-raw мережеве-підключення (протокол-передавання-записати-текст-байти вхідний-текст)))))

(визначити tcp-write
  (функція (мережеве-підключення вхідний-текст)
    (протокол-передавання-записати-через-сирий мережеве-підключення вхідний-текст)))

; Stable surface peers are projected by load_tcp_library after the TCP
; closures exist. Avoid the retired per-file post-core materializer.

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити протокол-передавання-слухати-на tcp-listen-on)
(визначити протокол-передавання-читати-байти-текст tcp-read-bytes->text)
(визначити протокол-передавання-записати-текст-байти tcp-write-text->bytes)
(визначити протокол-передавання-записати-через-сирий tcp-write-via-raw)
(визначити кодування-юнікод-8-декодувати-рядок utf8-decode-string)
(визначити кодування-юнікод-8-кодувати-рядок utf8-encode-string)
