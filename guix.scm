(use-modules (guix packages)
             (guix gexp)
             (guix build-system gnu)
             ((guix licenses) #:prefix license:)
             (gnu packages rust))

(define (source-filter file stat)
  (let ((name (basename file)))
    (not (or (string=? name "target")
             (string=? name ".git")
             (string=? name ".swarm-node")
             (string=? name ".claude")
             (string=? name ".codex")
             (string=? name ".gemini")))))

(package
  (name "wsm")
  (version "0.1.0")
  (source (local-file "." "wsm-source" #:recursive? #t #:select? source-filter))
  (build-system gnu-build-system)
  (arguments
   `(#:phases
     (modify-phases %standard-phases
       (delete 'configure)
       (replace 'build
         (lambda _
           ;; Ensure gcc and ld are used by rustc
           (setenv "RUSTFLAGS" (string-append "-C linker=gcc"))
           (invoke "cargo" "build" "--release" "--offline" "--workspace")))
       (replace 'check
         (lambda _
           #t))
       (replace 'install
         (lambda* (#:key outputs #:allow-other-keys)
           (let* ((out (assoc-ref outputs "out"))
                  (bin (string-append out "/bin")))
             (install-file "target/release/my-lisp" bin)
             (install-file "target/release/swarm-node" bin)
             #t))))))
  (native-inputs
   `(("rust" ,rust)
     ("cargo" ,rust "cargo")))
  (synopsis "WSM & Swarm Node")
  (description "WSM compiler and Swarm node.")
  (home-page "https://github.com/juv4uk/sens")
  (license license:expat))
