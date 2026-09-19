; File text policy owned by Lisp.
; Політика текстового читання/запису файлів, якою володіє Lisp.
;
; Host capabilities `read-file-bytes` and `write-file-bytes` expose only raw
; byte mechanism (with allowlist enforcement already applied at that
; boundary); this layer owns UTF-8 decoding/encoding and the public meanings
; of `read-file` and `write-file`, mirroring the split already established
; for `process-run` (lib/process.lisp) and `tcp-read`/`tcp-write` (lib/tcp.lisp).
; Load `lib/utf8.lisp` before this file.

; Historical `read-file` returns the decoded text directly. Invalid UTF-8 is
; no longer a raw Rust IO error: it returns the same explicit rejection value
; `utf8-decode-string` already produces for process/TCP bytes.
(def read-file
  (lambda (path)
    (let ((decoded (utf8-decode-string (read-file-bytes path))))
      (cond
        ((eq (car decoded) (quote decoded)) (second decoded))
        (t decoded)))))

; Historical `write-file` returns the text it was given after a successful
; write; encoding policy belongs to Lisp, the host only persists bytes.
(def write-file
  (lambda (path text)
    (second (list (write-file-bytes path (utf8-encode-string text)) text))))

; #469: post-core public identities declare only numeric IDs plus the source
; binding they just defined. No human-language alias is encoded in this file.
(my-postcore-materialize-stable-peers 166 read-file)
(my-postcore-materialize-stable-peers 167 write-file)
