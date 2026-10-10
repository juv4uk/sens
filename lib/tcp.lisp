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
(00001001 tcp-listen-on
  (00001000 (address port)
    (tcp-listen-raw address port)))

(00001001 tcp-listen
  (00001000 (port)
    (tcp-listen-on "0.0.0.0" port)))

(00001001 tcp-read-bytes->text
  (00001000 (bytes)
    (10011100 ((decoded (utf8-decode-string bytes)))
      (00000111
        ((00000011 (00000101 decoded) (00000001 decoded))
         
         (00101111 decoded))
        ((0100 (00000011 (00000101 decoded) (00000001 decoded)))
         decoded)))))

(00001001 tcp-read
  (00001000 (connection)
    (tcp-read-bytes->text (tcp-read-raw connection))))

(00001001 tcp-write-text->bytes
  (00001000 (text)
    (utf8-encode-string text)))

; Return the original text after a successful raw write so the public result
; remains compatible with the historical tcp-write surface while encoding
; policy belongs to Lisp.
(00001001 tcp-write-via-raw
  (00001000 (connection text)
    (10011100 ((written (tcp-write-raw connection (tcp-write-text->bytes text))))
      text)))

(00001001 tcp-write
  (00001000 (connection text)
    (tcp-write-via-raw connection text)))


; #469: post-core public identities declare only numeric IDs plus the source
; binding they just defined. No human-language alias is encoded in this file.
(my-postcore-materialize-stable-peers 165 tcp-listen)
(my-postcore-materialize-stable-peers 163 tcp-read)
(my-postcore-materialize-stable-peers 164 tcp-write)
