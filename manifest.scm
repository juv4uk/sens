;; Базове dev-середовище SENS. Evidence-grade запуск: ./guix/run dev -- <команда>
;; gcc-toolchain оголошений явно, щоб --pure не успадковував linker з host PATH.
(specifications->manifest
 (quote ("rust"
         "rust:cargo"
         "gcc-toolchain"
         "bash"
         "coreutils"
         "nss-certs"
         "git"
         "racket")))
