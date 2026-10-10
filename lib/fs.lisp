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
(00001001 read-file
  (00001000 (path)
    (10011100 ((decoded (read-file-utf8-raw path)))
      (00000111
        ((00000011 (00000101 decoded) (00000001 decoded))
         (00101111 decoded))
        ((00000010 (00000001 ()))
         decoded)))))

; Historical `write-file` returns the text it was given after a successful
; write; encoding policy belongs to Lisp, the host only persists bytes.
(00001001 write-file
  (00001000 (path text)
    (00101111 (00100111 (write-file-bytes path (utf8-encode-string text)) text))))
 
; Stable surface peers are projected by load_fs_library after the public
; file closures exist. Avoid the retired per-file post-core materializer.
