; File text policy owned by Lisp.
; Політика текстового читання/запису файлів, якою володіє Lisp.
;
; Host capabilities `read-file-bytes` and `write-file-bytes` expose only raw
; byte mechanism (with allowlist enforcement already applied at that
; boundary); this layer owns UTF-8 decoding/encoding and the public meanings
; of `read-file` and `write-file`, mirroring the split already established
; for `process-run` (lib/process.lisp) and `tcp-read`/`tcp-write` (lib/tcp.lisp).
; Load `lib/utf8.lisp` before this file.

; #1228: `read-file` on a real multi-kilobyte file drove the pure-Lisp
; byte-by-byte path (`utf8-decode-string` over `read-file-bytes`) to ~47s
; (release) / ~100s (debug) for a single ~20KB registry file — see my-lisp
; issue #333. `read-file-utf8-raw` is a raw host mechanism, high-load
; execution only: it does not decide UTF-8 meaning, it returns the exact
; same two-tag domain (`decoded`/`rejected invalid-utf8`) that
; `utf8-decode-string` already defines, so this rewiring changes no
; language-facing contract. `utf8-decode-string`/`utf8-decode`/
; `utf8-all-bytes?` in lib/utf8.lisp are kept, unchanged, as the semantic
; reference this mechanism is checked against (see
; tests/utf8-fast-path-parity.lisp).
;
; Historical `read-file` returns the decoded text directly. Invalid UTF-8 is
; no longer a raw Rust IO error: it returns the same explicit rejection value
; `utf8-decode-string` already produces for process/TCP bytes.
(0011 read-file
  (0010 (path)
    (let ((decoded (read-file-utf8-raw path)))
      (011
        ((111 (101 decoded) (001 decoded))
         (second decoded))
        ((010 (001 ()))
         decoded)))))

; Historical `write-file` returns the text it was given after a successful
; write; encoding policy belongs to Lisp, the host only persists bytes.
(0011 write-file
  (0010 (path text)
    (second (list (write-file-bytes path (utf8-encode-string text)) text))))
 
; #469: post-core public identities declare only numeric IDs plus the source
; binding they just defined. No human-language alias is encoded in this file.
(my-postcore-materialize-stable-peers 166 read-file)
(my-postcore-materialize-stable-peers 167 write-file)
