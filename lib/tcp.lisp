; TCP text interpretation and public listen policy owned by Lisp.
; Інтерпретація TCP-тексту й публічна політика listen, якими володіє Lisp.
;
; Host capabilities `tcp-listen-raw`, `tcp-read-raw`, and `tcp-write-raw`
; expose mechanism only. This layer owns the historical default bind address,
; UTF-8 decoding/encoding, and the public meanings of `tcp-listen`, `tcp-read`,
; and `tcp-write`.
; Load `lib/utf8.lisp` before this file.

; Preserve the historical public behavior explicitly in Lisp: listen on all
; IPv4 interfaces. Callers that need an explicit address can bypass that policy
; through tcp-listen-on without changing the host substrate.
(0011 tcp-listen-on
  (0010 (address port)
    (tcp-listen-raw address port)))

(0011 tcp-listen
  (0010 (port)
    (tcp-listen-on "0.0.0.0" port)))

(0011 tcp-read-bytes->text
  (0010 (bytes)
    (001000 ((decoded (utf8-decode-string bytes)))
      (110
        ((101 (100 decoded) (001 decoded))
         
         (1001 decoded))
        ((010 (001 ()))
         decoded)))))

(0011 tcp-read
  (0010 (connection)
    (tcp-read-bytes->text (tcp-read-raw connection))))

(0011 tcp-write-text->bytes
  (0010 (text)
    (utf8-encode-string text)))

; Return the original text after a successful raw write so the public result
; remains compatible with the historical tcp-write surface while encoding
; policy belongs to Lisp.
(0011 tcp-write-via-raw
  (0010 (connection text)
    (001000 ((written (tcp-write-raw connection (tcp-write-text->bytes text))))
      text)))

(0011 tcp-write
  (0010 (connection text)
    (tcp-write-via-raw connection text)))


; Stable surface peers are projected by load_process_library/load_tcp_library
; after the TCP closures exist. Avoid the retired per-file post-core materializer.
