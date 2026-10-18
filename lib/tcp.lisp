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
  (функція (address port)
    (tcp-listen-raw address port)))

(визначити tcp-listen
  (функція (port)
    (протокол-передавання-слухати-на "0.0.0.0" port)))

(визначити tcp-read-bytes->text
  (функція (bytes)
    ((функція (decoded)
       (за-умовою
         ((тотожне? (перше decoded) (як-є decoded))
          (друге decoded))
         (так
          decoded)))
     (кодування-юнікод-8-декодувати-рядок bytes))))

(визначити tcp-read
  (функція (connection)
    (протокол-передавання-читати-байти-текст (tcp-read-raw connection))))

(визначити tcp-write-text->bytes
  (функція (text)
    (кодування-юнікод-8-кодувати-рядок text)))

; Return the original text after a successful raw write so the public result
; remains compatible with the historical tcp-write surface while encoding
; policy belongs to Lisp.
(визначити tcp-write-via-raw
  (функція (connection text)
    ((функція (written) text)
     (tcp-write-raw connection (протокол-передавання-записати-текст-байти text)))))

(визначити tcp-write
  (функція (connection text)
    (протокол-передавання-записати-через-сирий connection text)))

; Stable surface peers are projected by load_tcp_library after the TCP
; closures exist. Avoid the retired per-file post-core materializer.

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити протокол-передавання-слухати-на tcp-listen-on)
(визначити протокол-передавання-читати-байти-текст tcp-read-bytes->text)
(визначити протокол-передавання-записати-текст-байти tcp-write-text->bytes)
(визначити протокол-передавання-записати-через-сирий tcp-write-via-raw)
(визначити кодування-юнікод-8-декодувати-рядок utf8-decode-string)
(визначити кодування-юнікод-8-кодувати-рядок utf8-encode-string)
