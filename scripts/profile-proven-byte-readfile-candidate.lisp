; Verification-only #333 microscope. Never production authority.
; Measures the provenance-specialized read-file candidate on the same
; semantic-registry workload as #379/#394:
;   host-proven exact u8 list -> existing Lisp UTF-8 sequence decoder
;   -> String -> read-all.
;
; `read-file-bytes` materializes std::fs::read Vec<u8> directly as exact Lisp
; numbers 0..255, so this candidate deliberately skips only the redundant
; generic byte-domain pass. UTF-8 sequence interpretation remains in Lisp.

(визначити proven-byte-profile-path "lib/surface/semantic-registry.lisp")

(визначити proven-byte-profile-start (монотонний-наносекунди))
(визначити proven-byte-profile-bytes (read-file-bytes proven-byte-profile-path))
(визначити proven-byte-profile-after-bytes (монотонний-наносекунди))

(визначити proven-byte-profile-decoded
  (utf8-decode-onto proven-byte-profile-bytes (як-є ())))
(визначити proven-byte-profile-after-decode (монотонний-наносекунди))

(визначити proven-byte-profile-text
  (юнікод-скаляри-рядок (second proven-byte-profile-decoded)))
(визначити proven-byte-profile-after-string (монотонний-наносекунди))

(визначити proven-byte-profile-root (перше (читати-всі proven-byte-profile-text)))
(визначити proven-byte-profile-after-read-all (монотонний-наносекунди))

(друкувати
  (список
    (як-є eco-lisp-script-perf/proven-byte-readfile-candidate)
    (список (як-є read-file-bytes-ns)
          (відняти proven-byte-profile-after-bytes proven-byte-profile-start))
    (список (як-є decode-plus-reverse-ns)
          (відняти proven-byte-profile-after-decode proven-byte-profile-after-bytes))
    (список (як-є string-assembly-ns)
          (відняти proven-byte-profile-after-string proven-byte-profile-after-decode))
    (список (як-є read-all-ns)
          (відняти proven-byte-profile-after-read-all proven-byte-profile-after-string))
    (список (як-є total-ns)
          (відняти proven-byte-profile-after-read-all proven-byte-profile-start))
    (список (як-є decode-tag) (перше proven-byte-profile-decoded))
    (список (як-є root) proven-byte-profile-root)))

; opt-in повна укр-поверхня: exact identity = lib/domains/d*.lisp; DEFINE-аліас, без нової диспетчеризації.
(визначити монотонний-наносекунди mono-ns)
(визначити читати-всі read-all)
(визначити юнікод-скаляри-рядок unicode-scalars->string)
