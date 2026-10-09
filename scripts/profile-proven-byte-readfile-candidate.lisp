; Verification-only #333 microscope. Never production authority.
; Measures the provenance-specialized read-file candidate on the same
; semantic-registry workload as #379/#394:
;   host-proven exact u8 list -> existing Lisp UTF-8 sequence decoder
;   -> String -> read-all.
;
; `read-file-bytes` materializes std::fs::read Vec<u8> directly as exact Lisp
; numbers 0..255, so this candidate deliberately skips only the redundant
; generic byte-domain pass. UTF-8 sequence interpretation remains in Lisp.

(def proven-byte-profile-path "lib/surface/semantic-registry.lisp")

(def proven-byte-profile-start (mono-ns))
(def proven-byte-profile-bytes (read-file-bytes proven-byte-profile-path))
(def proven-byte-profile-after-bytes (mono-ns))

(def proven-byte-profile-decoded
  (utf8-decode-onto proven-byte-profile-bytes (quote ())))
(def proven-byte-profile-after-decode (mono-ns))

(def proven-byte-profile-text
  (unicode-scalars->string (second proven-byte-profile-decoded)))
(def proven-byte-profile-after-string (mono-ns))

(def proven-byte-profile-root (car (read-all proven-byte-profile-text)))
(def proven-byte-profile-after-read-all (mono-ns))

(print
  (list
    (quote eco-lisp-script-perf/proven-byte-readfile-candidate)
    (list (quote read-file-bytes-ns)
          (- proven-byte-profile-after-bytes proven-byte-profile-start))
    (list (quote decode-plus-reverse-ns)
          (- proven-byte-profile-after-decode proven-byte-profile-after-bytes))
    (list (quote string-assembly-ns)
          (- proven-byte-profile-after-string proven-byte-profile-after-decode))
    (list (quote read-all-ns)
          (- proven-byte-profile-after-read-all proven-byte-profile-after-string))
    (list (quote total-ns)
          (- proven-byte-profile-after-read-all proven-byte-profile-start))
    (list (quote decode-tag) (car proven-byte-profile-decoded))
    (list (quote root) proven-byte-profile-root)))
