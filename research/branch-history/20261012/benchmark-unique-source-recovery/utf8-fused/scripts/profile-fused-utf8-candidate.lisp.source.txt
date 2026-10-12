; Verification-only #362 microscope. Never production authority.
; Measures the exact candidate path over the same semantic-registry workload
; used by #333/#347/#379: raw bytes -> fused Lisp UTF-8 decode -> String -> read-all.

(def fused-profile-path "lib/surface/semantic-registry.lisp")

(def fused-profile-start (mono-ns))
(def fused-profile-bytes (read-file-bytes fused-profile-path))
(def fused-profile-after-bytes (mono-ns))

(def fused-profile-decoded (utf8-decode-fused fused-profile-bytes))
(def fused-profile-after-decode (mono-ns))

(def fused-profile-text
  (unicode-scalars->string (second fused-profile-decoded)))
(def fused-profile-after-string (mono-ns))

(def fused-profile-root (car (read-all fused-profile-text)))
(def fused-profile-after-read-all (mono-ns))

(print
  (list
    (quote eco-lisp-script-perf/fused-utf8-candidate)
    (list (quote read-file-bytes-ns)
          (- fused-profile-after-bytes fused-profile-start))
    (list (quote fused-decode-ns)
          (- fused-profile-after-decode fused-profile-after-bytes))
    (list (quote string-assembly-ns)
          (- fused-profile-after-string fused-profile-after-decode))
    (list (quote read-all-ns)
          (- fused-profile-after-read-all fused-profile-after-string))
    (list (quote total-ns)
          (- fused-profile-after-read-all fused-profile-start))
    (list (quote decode-tag) (car fused-profile-decoded))
    (list (quote root) fused-profile-root)))
