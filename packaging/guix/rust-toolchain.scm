;; Rust 1.99.0 як пакет Guix із офіційних binary-компонентів Rust.
;; Канал guix-rustup a13fe8b6 знає метадані лише до 1.93.1. Назви нижче
;; взято з офіційного channel-rust-1.99.0.toml; порядок старих індексів
;; збережено. Ці додаткові компоненти/цілі не входять у наш мінімальний профіль.
(use-modules (rustup build toolchain)
             (rustup build manifest)
             (guix packages)
             (guix build-system gnu)
             (guix search-paths)
             (guix utils)
             (rnrs enums))

(let ((manifest-module (resolve-module '(rustup build manifest))))
  (for-each
   (lambda (binding extra)
     (let ((old (module-ref manifest-module binding)))
       (module-set! manifest-module binding
                    (make-enumeration (append (enum-set->list old) extra)))))
   '(%toolchain-components %rustc-target-triplets)
   '((enzyme offload)
     (x86_64-unknown-linux-gnumsan x86_64-unknown-linux-gnutsan))))

;; cargo/rustc/rust-std беруться з minimal; документацію не завантажуємо.
(let ((toolchain (rustup "1.99.0" #:profile 'minimal #:components '(rustfmt clippy))))
  (package
    (inherit toolchain)
    ;; Спостережений дефект пакування: успадкована Guix-фаза
    ;; install-license-files падає з match-error #f, не доходячи до Cargo.
    ;; Причину всередині самої фази не стверджуємо. Це технічний дефект,
    ;; не зміна семантики SENS і не новий release-gate. Видаляємо лише цю фазу.
    (arguments
     (substitute-keyword-arguments (package-arguments toolchain)
       ((#:phases phases)
        `(modify-phases ,phases
           (delete 'install-license-files)))))
    ;; Upstream rustc створює build-script без Guix rpath. Динамічний
    ;; libgcc береться виключно з lib поточного Guix-профілю.
    (native-search-paths
     (cons (search-path-specification
            (variable "LD_LIBRARY_PATH")
            (files '("lib")))
           (package-native-search-paths toolchain)))))
