;; Базове dev-середовище SENS. Evidence-grade запуск: ./guix/run dev -- <команда>
;; gcc-toolchain оголошений явно, щоб --pure не успадковував linker з host PATH.
;; Rust-пакет оголошує LD_LIBRARY_PATH для запуску Cargo build-script у --pure.
(use-modules (guix profiles) (gnu packages))

(define sens-rust-toolchain
  (primitive-load
   (string-append (dirname (current-filename))
                  "/packaging/guix/rust-toolchain.scm")))

(define sens-sccache
  (primitive-load
   (string-append (dirname (current-filename))
                  "/packaging/guix/sccache.scm")))

(concatenate-manifests
 (list
  (packages->manifest (list sens-rust-toolchain sens-sccache))
  (specifications->manifest
   (quote ("zig@0.16.0"
         "gcc-toolchain"
         "bash"
         "coreutils"
         "diffutils"
         "findutils"
         "gawk"
         "grep"
         "nss-certs"
         "git"
         "python@3.12"
         "node"
         "lua@5.4"
         "sed"
         "racket")))))
