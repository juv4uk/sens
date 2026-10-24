;; Rust 1.99.0 як пакет Guix із офіційних binary-компонентів Rust.
;; Канал guix-rustup a13fe8b6 знає метадані лише до 1.93.1. Назви нижче
;; взято з офіційного channel-rust-1.99.0.toml; порядок старих індексів
;; збережено. Ці додаткові компоненти/цілі не входять у наш мінімальний профіль.
(use-modules (rustup build toolchain)
             (rustup build manifest)
             (guix packages)
             (guix search-paths)
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
    ;; Upstream rustc створює build-script без Guix rpath. Динамічний
    ;; libgcc береться виключно з lib поточного Guix-профілю.
    (native-search-paths
     (cons (search-path-specification
            (variable "LD_LIBRARY_PATH")
            (files '("lib")))
           (package-native-search-paths toolchain)))))
