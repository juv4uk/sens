;; CLIPS 6.4.2 for the native-clips islands (wsm-clips-kernel), as a Guix
;; package: the Guix channel has no CLIPS, and distributions rarely ship the
;; exact 6.4.2 C ABI. Same recipe as packaging/install.sh — every core/*.c
;; compiled into libclips.so and the clips CLI.
;;
;;   guix build -f packaging/guix/clips.scm
;;   guix package -p /var/guix/profiles/shared/guix-profile -f packaging/guix/clips.scm
;;
;; The self-hosted runner then uses
;;   WSM_CLIPS_LIBRARY=/var/guix/profiles/shared/guix-profile/lib/libclips.so

(use-modules (guix packages)
             (guix gexp)
             (guix download)
             (guix build-system gnu)
             ((guix licenses) #:prefix license:))

(package
  (name "clips")
  (version "6.4.2")
  (source
   (origin
     (method url-fetch)
     (uri "https://sourceforge.net/projects/clipsrules/files/CLIPS/6.4.2/clips_core_source_642.tar.gz/download")
     (file-name "clips_core_source_642.tar.gz")
     (sha256
      (base32 "0nj521y445sndzp22k99y8473jhbbw4q9mk31prsz73fzjr1x2k0"))))
  (build-system gnu-build-system)
  (arguments
   (list
    #:tests? #f
    #:phases
    #~(modify-phases %standard-phases
        (delete 'configure)
        (replace 'build
          (lambda _
            (with-directory-excursion "core"
              (let ((cflags '("-std=c99" "-O3" "-fPIC" "-fno-strict-aliasing")))
                (apply invoke "gcc" "-shared" "-o" "libclips.so"
                       (append cflags (find-files "." "\\.c$") '("-lm")))
                (apply invoke "gcc" "-o" "clips"
                       (append cflags (find-files "." "\\.c$") '("-lm")))))))
        (replace 'install
          (lambda _
            (let ((lib (string-append #$output "/lib"))
                  (bin (string-append #$output "/bin"))
                  (include (string-append #$output "/include/clips")))
              (install-file "core/libclips.so" lib)
              (install-file "core/clips" bin)
              (for-each (lambda (header) (install-file header include))
                        (find-files "core" "\\.h$"))))))))
  (home-page "https://www.clipsrules.net/")
  (synopsis "C Language Integrated Production System (rule engine)")
  (description
   "CLIPS is a forward-chaining rule-based programming language.  This
package provides the CLIPS 6.4.2 shared library with its C API and the
interactive @command{clips} shell.")
  (license license:public-domain))
