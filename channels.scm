;; Чинний pin SENS, оновлення 2026-10-25: Rust/Cargo 1.99.0 через Guix.
;; Guix 3a0d265 узгоджений із Nonguix caa8c0b у перевіреному локальному
;; профілі. Англомовний запис 2026-08-12 нижче — історія попереднього pin.
;; Ecosystem-wide Guix channel pin (my-lisp, cml, fpga-lisp, my-idea).
;;
;; Reproduces the exact Guix revision this ecosystem's toolchain was last
;; verified against — not just the package versions `manifest.scm` names,
;; but the derivations that build them. Use it with `guix time-machine`
;; when a result needs to be reproducible independent of whatever Guix
;; revision happens to be pulled on a given machine on a given day:
;;
;;   guix time-machine -C channels.scm -- shell -m manifest.scm -- cargo test
;;
;; Update this file deliberately (after a `guix pull` that's been verified
;; to still build all four repos' manifests), not automatically on every
;; pull — it is itself a pinned fact, the same way Cargo.lock or a
;; `tested-*-sha` field in compatibility.my is.
;;
;; Last verified: 2026-08-12, my-lisp session, after `guix pull` landed
;; rust 1.93.0 and `cargo build --workspace` / `cargo test --workspace`
;; both passed clean in this repo under it.

(list
      ;; Rust 1.99 через уже використовуваний локально канал Guix Rustup.
      ;; Zig закріплено окремо в manifest.scm; канали мають сумісні ревізії.
      (channel
        (name 'rustup)
        (url "https://codeberg.org/declantsien/guix-rustup")
        (commit "a13fe8b6f533abb9ba43dfc3697c49bb5942d3b6")
        (introduction
          (make-channel-introduction
            "325d3e2859d482c16da21eb07f2c6ff9c6c72a80"
            (openpgp-fingerprint
              "F695 F39E C625 E081 33B5 759F 0FC6 8703 75EF E2F5"))))
      (channel
        (name 'nonguix)
        (url "https://gitlab.com/nonguix/nonguix")
        (commit "caa8c0b4646b993537be13c9bc819b3df68ab9b2")
        (introduction
          (make-channel-introduction
            "897c1a470da759236cc11798f4e0a5f7d4d59fbc"
            (openpgp-fingerprint
              "2A39 3FFF 68F4 EF7A 3D29 12AF 6F51 20A0 22FB B2D5"))))
      (channel
        (name (quote guix))
        (url "https://git.guix.gnu.org/guix.git")
        (branch "master")
        (commit
          "3a0d265d403ff13c1082d07b8f0205771ac412b9")
        (introduction
         (make-channel-introduction
          "9edb3f66fd807b096b48283debdcddccfea34bad"
          (openpgp-fingerprint
           "BBB0 2DDF 2CEA F6A8 0D1D  E643 A2A0 6DF2 A33A 54FA")))))
