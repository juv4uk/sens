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

(list (channel
        (name (quote guix))
        (url "https://git.guix.gnu.org/guix.git")
        (branch "master")
        (commit
          "5375f33fd48ffc3b39ecc1c5993e299258a043d8")
        (introduction
         (make-channel-introduction
          "9edb3f66fd807b096b48283debdcddccfea34bad"
          (openpgp-fingerprint
           "BBB0 2DDF 2CEA F6A8 0D1D  E643 A2A0 6DF2 A33A 54FA")))))
