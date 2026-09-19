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
(def tcp-listen-on
  (lambda (address port)
    (tcp-listen-raw address port)))

(def tcp-listen
  (lambda (port)
    (tcp-listen-on "0.0.0.0" port)))

(def tcp-read-bytes->text
  (lambda (bytes)
    (let ((decoded (utf8-decode-string bytes)))
      (cond
        ((eq (car decoded) (quote decoded))
         (second decoded))
        (t decoded)))))

(def tcp-read
  (lambda (connection)
    (tcp-read-bytes->text (tcp-read-raw connection))))

(def tcp-write-text->bytes
  (lambda (text)
    (utf8-encode-string text)))

; Return the original text after a successful raw write so the public result
; remains compatible with the historical tcp-write surface while encoding
; policy belongs to Lisp.
(def tcp-write-via-raw
  (lambda (connection text)
    (let ((written (tcp-write-raw connection (tcp-write-text->bytes text))))
      text)))

(def tcp-write
  (lambda (connection text)
    (tcp-write-via-raw connection text)))


; #469: post-core public identities declare only numeric IDs plus the source
; binding they just defined. No human-language alias is encoded in this file.
(my-postcore-materialize-stable-peers 165 tcp-listen)
(my-postcore-materialize-stable-peers 163 tcp-read)
(my-postcore-materialize-stable-peers 164 tcp-write)
