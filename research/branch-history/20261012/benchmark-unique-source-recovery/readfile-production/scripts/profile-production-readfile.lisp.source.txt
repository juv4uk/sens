; Verification-only #362 microscope. Never production authority.
; Measures the actual public `read-file` path from the stacked production
; candidate, then parses the same semantic-registry workload used by #379,
; #394 and #397.

(def production-readfile-profile-path "lib/surface/semantic-registry.lisp")

(def production-readfile-profile-start (mono-ns))
(def production-readfile-profile-text
  (read-file production-readfile-profile-path))
(def production-readfile-profile-after-read-file (mono-ns))

(def production-readfile-profile-root
  (car (read-all production-readfile-profile-text)))
(def production-readfile-profile-after-read-all (mono-ns))

(print
  (list
    (quote eco-lisp-script-perf/production-readfile)
    (list (quote read-file-ns)
          (- production-readfile-profile-after-read-file
             production-readfile-profile-start))
    (list (quote read-all-ns)
          (- production-readfile-profile-after-read-all
             production-readfile-profile-after-read-file))
    (list (quote total-ns)
          (- production-readfile-profile-after-read-all
             production-readfile-profile-start))
    (list (quote root) production-readfile-profile-root)))