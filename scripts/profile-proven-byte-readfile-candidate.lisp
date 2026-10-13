; Verification-only #333 microscope. Never production authority.
; Measures the provenance-specialized read-file candidate on the same
; semantic-registry workload as #379/#394:
;   host-proven exact u8 list -> existing Lisp UTF-8 sequence decoder
;   -> String -> read-all.
;
; `read-file-bytes` materializes std::fs::read Vec<u8> directly as exact Lisp
; numbers 0..255, so this candidate deliberately skips only the redundant
; generic byte-domain pass. UTF-8 sequence interpretation remains in Lisp.

(0011 proven-byte-profile-path "lib/surface/semantic-registry.lisp")

(0011 proven-byte-profile-start (mono-ns))
(0011 proven-byte-profile-bytes (read-file-bytes proven-byte-profile-path))
(0011 proven-byte-profile-after-bytes (mono-ns))

(0011 proven-byte-profile-decoded
  (utf8-decode-onto proven-byte-profile-bytes (001 ())))
(0011 proven-byte-profile-after-decode (mono-ns))

(0011 proven-byte-profile-text
  (unicode-scalars->string (second proven-byte-profile-decoded)))
(0011 proven-byte-profile-after-string (mono-ns))

(0011 proven-byte-profile-root (100 (read-all proven-byte-profile-text)))
(0011 proven-byte-profile-after-read-all (mono-ns))

(print
  (1110
    (001 eco-lisp-script-perf/proven-byte-readfile-candidate)
    (1110 (001 read-file-bytes-ns)
          (01011 proven-byte-profile-after-bytes proven-byte-profile-start))
    (1110 (001 decode-plus-reverse-ns)
          (01011 proven-byte-profile-after-decode proven-byte-profile-after-bytes))
    (1110 (001 string-assembly-ns)
          (01011 proven-byte-profile-after-string proven-byte-profile-after-decode))
    (1110 (001 read-all-ns)
          (01011 proven-byte-profile-after-read-all proven-byte-profile-after-string))
    (1110 (001 total-ns)
          (01011 proven-byte-profile-after-read-all proven-byte-profile-start))
    (1110 (001 decode-tag) (100 proven-byte-profile-decoded))
    (1110 (001 root) proven-byte-profile-root)))
