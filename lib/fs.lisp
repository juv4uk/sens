; File text policy owned by Lisp.
; Політика текстового читання/запису файлів, якою володіє Lisp.
;
; Migrated: two-field COND only; explicit D1 fallbacks #d1:1.
; Reuses utf8-encode-string from lib/utf8.lisp and host mechanisms
; read-file-utf8-raw / write-file-bytes. Width is identity; every bit valued.
;
; Host capabilities expose only raw byte mechanism (allowlist already applied).
; This layer owns UTF-8 decoding/encoding and public meanings of read-file /
; write-file, mirroring process-run (lib/process.lisp) and tcp-read/tcp-write
; (lib/tcp.lisp). Load `lib/utf8.lisp` before this file.
;
; #1228: pure-Lisp byte-by-byte utf8-decode-string over read-file-bytes was too
; slow for multi-kilobyte registry files. read-file-utf8-raw is high-load host
; mechanism only: same two-tag domain (decoded / rejected invalid-utf8) that
; utf8-decode-string defines — language-facing contract unchanged.
; Semantic reference remains lib/utf8.lisp (tests/utf8-fast-path-parity.lisp).

; Historical read-file returns decoded text directly. Invalid UTF-8 returns
; the same explicit rejection utf8-decode-string produces for process/TCP.
(0011 read-file
  (0010 (path)
    (001000 ((decoded (read-file-utf8-raw path)))
      (110
        ((101 (100 decoded) (001 decoded))
         (1001 decoded))
        (#d1:1
         decoded)))))

; Historical write-file returns the text after successful write;
; encoding policy belongs to Lisp, host only persists bytes.
(0011 write-file
  (0010 (path text)
    (1001 (1110 (write-file-bytes path (utf8-encode-string text)) text))))

; Stable surface peers are projected by load_fs_library after the public
; file closures exist. Avoid the retired per-file post-core materializer.
