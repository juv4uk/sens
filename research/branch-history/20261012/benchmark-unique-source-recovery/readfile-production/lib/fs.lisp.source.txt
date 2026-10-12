; File text policy owned by Lisp.
; Політика текстового читання/запису файлів, якою володіє Lisp.
;
; Host capabilities `read-file-bytes` and `write-file-bytes` expose only raw
; byte mechanism (with allowlist enforcement already applied at that
; boundary); this layer owns UTF-8 decoding/encoding and the public meanings
; of `read-file` and `write-file`, mirroring the split already established
; for `process-run` (lib/process.lisp) and `tcp-read`/`tcp-write` (lib/tcp.lisp).
; Load `lib/utf8.lisp` before this file.

; Historical `read-file` returns the decoded text directly. `read-file-bytes`
; constructively returns a proper list of exact u8 values, so this specific
; filesystem composition can enter the existing Lisp-owned UTF-8 sequence
; decoder directly instead of re-running the generic `utf8-all-bytes?` domain
; proof. Public `utf8-decode` remains unchanged for arbitrary Lisp lists.
; Invalid UTF-8 still returns the same explicit rejection value because
; sequence validity and byte->scalar interpretation remain in
; `utf8-decode-onto`.
(def read-file
  (lambda (path)
    (let ((decoded
            (utf8-decode-onto
              (read-file-bytes path)
              (quote ()))))
      (cond
        ((eq (car decoded) (quote decoded))
         (unicode-scalars->string (second decoded)))
        (t decoded)))))

; Historical `write-file` returns the text it was given after a successful
; write; encoding policy belongs to Lisp, the host only persists bytes.
(def write-file
  (lambda (path text)
    (second (list (write-file-bytes path (utf8-encode-string text)) text))))