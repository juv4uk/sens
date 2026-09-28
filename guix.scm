(use-modules (guix packages)
             (guix gexp)
             (guix build-system gnu)
             ((guix licenses) #:prefix license:)
             (gnu packages rust))

(define (source-filter file stat)
  ;; Package identity depends only on compilable sources/resources, not docs,
  ;; CI logs or evidence. Directories stay traversable; individual files are
  ;; admitted by the explicit compile-time closure below.
  (let ((name (basename file)))
    (or (eq? (stat:type stat) 'directory)
        (member name '("Cargo.toml" "Cargo.lock" "LICENSE"
                       "language-contract.lisp" "config.toml"
                       "islands-manifest-v1.json"))
        (string-contains file "/crates/")
        (string-contains file "/vendor/")
        (string-contains file "/lib/")
        (string-contains file "/.cargo/"))))

(package
  (name "sens")
  (version "0.41.0")
  (source (local-file "." "sens-source" #:recursive? #t #:select? source-filter))
  (build-system gnu-build-system)
  (arguments
   `(#:phases
     (modify-phases %standard-phases
       (delete 'configure)
       (replace 'build
         (lambda _
           ;; Cargo читає vendored crates із .cargo/config.toml; мережа не потрібна.
           (setenv "RUSTFLAGS" "-C linker=gcc")
           (invoke "cargo" "build" "--release" "--offline"
                   "-p" "sens-cli" "--bin" "sens" "--bin" "my-lisp"
                   "-p" "swarm-node" "--bin" "swarm-node")))
       (replace 'check (lambda _ #t))
       (replace 'install
         (lambda* (#:key outputs #:allow-other-keys)
           (let* ((out (assoc-ref outputs "out"))
                  (bin (string-append out "/bin")))
             (install-file "target/release/sens" bin)
             ;; Compatibility surface: не вилучати без окремого рішення контракту.
             (install-file "target/release/my-lisp" bin)
             (install-file "target/release/swarm-node" bin)))))))
  (native-inputs
   `(("rust" ,rust)
     ("cargo" ,rust "cargo")))
  (synopsis "SENS runtime, CLI and swarm coordination node")
  (description
   "Hermetic Guix build of the SENS CLI together with its compatibility CLI
and the swarm-node coordination executable.  Semantic authority remains in
SENS sources; this package only defines a reproducible execution substrate.")
  (home-page "https://github.com/juv4uk/sens")
  (license license:expat))
