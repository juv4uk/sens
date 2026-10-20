;; Real Guix package definition for swarm-node -- GUIX-WITNESS-01 step 1.
;;
;; swarm-node was chosen as the first real package (over the full my-lisp
;; workspace) specifically because its own Cargo.toml declares zero
;; dependencies -- the smallest possible real case, and a fast build even
;; under --no-substitutes --rounds=2, which matters because this file was
;; written under AGENT-RESOURCE-POLICY.md's "machine already busy, defer"
;; rule (load average 4.01, 201Mi free RAM at write time, 2026-08-26) --
;; the definition itself costs no CPU, an actual `guix build` run does and
;; is deliberately deferred, not run here.
;;
;; Usage once evaluated:
;;   guix time-machine -C ../../channels.scm -- \
;;     build -f package.scm --no-substitutes --rounds=2
;; (channels.scm sits two directories up, at the my-lisp repo root --
;; verify it's still current before relying on it; last verified date is
;; recorded in that file itself, not duplicated here.)

(use-modules (guix packages)
             (guix build-system cargo)
             (guix licenses)
             (guix gexp))

;; Note (added after the first dry-run, 2026-08-26): the original draft
;; imported (gnu packages crates-io) for no actual reason -- #:cargo-inputs
;; is empty, matching Cargo.toml's own empty [dependencies] -- and that
;; module failed to resolve on this machine's Guix installation ("no code
;; for module"). Removed rather than left in as dead, untested code.

(package
  (name "swarm-node")
  (version "0.1.0")
  (source (local-file "." "swarm-node-checkout"
                       #:recursive? #t
                       #:select? (lambda (file stat)
                                   (not (string-contains file "/target/")))))
  (build-system cargo-build-system)
  (arguments
   (list #:install-source? #f
         ;; No crates.io dependencies to vendor -- Cargo.toml's own
         ;; [dependencies] section is empty, confirmed by direct read
         ;; 2026-08-26. If a future dependency is added, its #:cargo-inputs
         ;; must be added here too, or the build will fail cleanly (not
         ;; silently) since cargo-build-system vendors explicitly.
         #:cargo-inputs '()))
  (home-page "https://github.com/juv4uk/sens")
  (synopsis "P2P coordination-plane node for the SENS ecosystem")
  (description
   "swarm-node is a dependency-free Rust binary implementing gossip-based
peer discovery, anti-entropy event-log synchronization, and quorum-voted
task claiming for agents coordinating across SENS ecosystem repositories.
See docs/swarm-mesh-v2.md in the SENS repository for the protocol.")
  (license expat))
