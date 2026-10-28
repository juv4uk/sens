;; Статичний upstream-binary: не підвантажує host/Guix libc разом.
;; Джерело — офіційний реліз Mozilla sccache для x86_64 Linux/musl.
(use-modules (guix packages)
             (guix download)
             (guix build-system copy)
             (guix licenses))

(let ((version "0.18.0"))
  (package
    (name "sccache")
    (version version)
    (source
     (origin
       (method url-fetch)
       (uri (string-append
             "https://github.com/mozilla/sccache/releases/download/v"
             version "/sccache-v" version "-x86_64-unknown-linux-musl.tar.gz"))
       (sha256
        (base32 "12fcd96wrzh9liyawqlddhhi5lkxcxqfylg3plvk07i3przl9wa5"))))
    (build-system copy-build-system)
    (arguments
     (list
      #:install-plan
      #~'(("sccache" "bin/")
          ("LICENSE" "share/licenses/sccache/"))))
    (home-page "https://github.com/mozilla/sccache")
    (synopsis "Локальне кешування компіляції Rust та C/C++")
    (description
     "sccache кешує результати компіляції на локальному диску. Цей пакунок
містить офіційний статичний x86_64 Linux binary, щоб не змішувати бібліотеки
host-системи з pinned Guix toolchain.")
    (license asl2.0)))
