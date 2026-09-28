; ecosystem-status.my — machine-readable current-state snapshot for the
; four-repository ecosystem (my-lisp, fpga-lisp, cml, my-idea).
;
; Data only, same convention as language-contract.lisp/isa-contract.lisp/
; compatibility.lisp — one flat alist, read via (read-file ...) or (read
; (read-file "ecosystem-status.my")), never loaded as executable source.
; docs/ecosystem-sync.md's prose narrates the same facts for humans;
; this file is the version another session's my-lisp code could actually
; consume (e.g. a future my-idea "System Observatory" panel) without
; scraping Markdown.
;
; Not the contract itself — language-contract.lisp/isa-contract.lisp/
; compatibility.lisp remain authoritative; this file is a snapshot,
; refreshed by hand after each cross-session sync, per
; docs/ecosystem-sync.md's four-point status request.
;
; ecosystem-status.my — машинно-читаний знімок поточного стану
; чотирьох-репозиторної екосистеми. Дані, не код; та сама конвенція, що
; й у language-contract.lisp/isa-contract.lisp/compatibility.lisp.

((kind . ecosystem-status)
 (as-of . "2026-08-12")
 (task-board-note .
  "The `current-task` field per repository below IS the task board — read
   it before starting work so effort isn't duplicated, update your own
   repo's entry (and `as-of`) when your task changes. Not a live feed:
   a snapshot, refreshed by hand, same as the rest of this file. For
   anything time-sensitive faster than a hand-edit, use swarm-node
   (:910x, swarm/1) for coordination. The my-lisp TCP service on :9999 is
   the semantic oracle only (eval/parse/diagnose/contract-version) and
   must not be used as a coordination mailbox.")
 (repositories .
  ((my-lisp .
    ((role . semantic-source-of-truth)
     (language-contract . (1 0))
     (exactness-model . fully-implemented)
     (blocking-others . nil)
     (rust-toolchain-on-this-machine . (guix rust 1 93 0))
     (environment . "WSL2 + Guix, shared profile /var/guix/profiles/shared/guix-profile, per-repo Linux user (wsl -u my-lisp), working dir stays /mnt/c/GitHub/my-lisp — owner-confirmed, not ~/projects or ~/src")
     (channels-scm . "channels.scm at repo root, pins guix commit 5375f33 (verified: cargo build/test --workspace clean under it)")
     (tcp-repl . (flag "--tcp[=PORT]" protocol-flag "--protocol=sexpr"
                   note "each connection gets its own fresh Environment::root() for semantic-oracle eval/parse/diagnose; a connection's def is invisible to every other connection. Coordination is a separate swarm-node :910x/swarm/1 plane and must not be reintroduced here"))
     (open-item . "crates/my-lisp-cli/tests/cli.rs: 4 sexpr_protocol_* tests still #[ignore]d — ConnectionRefused, root cause unknown, confirmed NOT Windows/WSL/DrvFs/libtest-in-general, isolated to that specific test binary (commit 4eb85ce documents what's been ruled out)")
     (current-task . "infra/coordination support (guix toolchain, TCP oracle protocol, channels.scm/evidence schema) — no open product work on the language itself right now")))
   (fpga-lisp .
    ((role . hardware-implementation)
     (isa-contract . (1 0))
     (evidence . "evidence/G5/fpga-lisp/, evidence/G8/fpga-lisp/ in the fpga-lisp repo — see evidence/README.md's protocol; M28-M32 results reported via mailbox as of this writing, not yet filed as evidence/ records")
     (hardware-verified-milestones . (m01 . m32))
     (m28-m29-m30-m31 . "letrec self-recursion (M28), canonical tail-recursive length/length-onto (M29), reverse/reverse-onto — first real CONS-structure result (M30), append built on M30 (M31, commit 4a4f032) — all PASSED on real iverilog, cross-checked against the my-lisp TCP oracle")
     (m32 . "equal? — PASSED on real iverilog first try (commit 4a218fb): (equal? (quote (p . q)) (quote (p . q))) => t via structural, not pointer, equality across two separately-allocated cons cells")
     (open-blocker . nil)
     (isa-representational-gaps . (no-inexact-numbers no-rationals no-string-tag))
     (current-task . "M32 equal? just landed (32/32 milestones); next unclear as of this writing — check mailbox/NOTE-FROM-MY-LISP.md for latest")))
   (cml .
    ((role . aot-compiler)
     (compiler-version . (0 1 0))
     (recursive-def-status . resolved)
     (recursive-def-fix . "compile_cond was using R4 (the ENV register) as a scratch register for its NIL-check, silently clobbering the environment on every cond — fixed commit e73f93a; self-recursive (def count (lambda (n) (cond ((eq n 0) 99) (t (count (+ n -1)))))) now returns 99 on real iverilog")
     (length-e2e . "done — cml evidence/length/{my-lisp/bb6a595,cml/26c1963,fpga-lisp/735e7c4}.my records the same core.my length/length-onto source, oracle expected 3, and fpga-lisp RTL actual 3 via iverilog; RESULT_TAG:0 RESULT_VAL:3")
     (equal-status . merged-fixed-and-verified)
     (defmacro-status . merged-fixed-and-verified)
     (documented-limitations . (no-inexact-numbers no-rationals no-canonical-strings
                                 no-more-than-eight-call-arguments))
     (current-task . "length_e2e evidence reconciled; next cross-repo target is physical execution of the ISA 1.1 tagged register-input frame, with no claim until COM4 evidence exists")))
   (my-idea .
    ((role . observer-and-ide)
     (joined-ecosystem-sync . "2026-08-11")
     ;; updated 2026-08-24: vestigial embedded external/my-lisp submodule
     ;; REMOVED from my-idea (verified: zero build/source references);
     ;; historical risk note below kept for provenance only.
     (depends-on-my-lisp-via . nil)
     (revision-sync-risk . "RESOLVED 2026-08-24: vestigial submodule removed (was pinned 85b53f2, l0.20-era); my-idea consumes nothing from my-lisp build-wise")
     (evidence-matrix-fixture-drill-down . "live, commit 3dc7121 — click a requirement row for source+expected/actual/commit/note per implementation")
     (current-task . "cargo check --workspace was rustc-version-blocked (darling/icu/time/zbus/plist all need >=1.86-1.88), unblocked now that guix rust is 1.93.0 — retry and report")))))
 (open-blockers .
  ((cli-rs-connectionrefused .
    "crates/my-lisp-cli/tests/cli.rs, 4 sexpr_protocol_* tests. Confirmed NOT Windows Firewall/Defender, NOT WSL2/DrvFs-vs-native-fs, NOT cargo test/libtest in general (a minimal standalone repro crate with the identical spawn/banner/retry pattern against the same child binary always succeeds first try, in and out of libtest). Isolated to this one test binary specifically. True root cause still open — see the block comment above the four #[ignore]d tests, commit 4eb85ce.")
   (isa-no-inexact-rational-string .
    "representational gap, not an implementation gap; blocks my-lisp's stated core purpose (exact rational arithmetic) from ever reaching fpga-lisp until isa-contract.my adds tags/encoding for it — needs a representation contract before any RTL/cml lowering work, not an ad-hoc format invented mid-implementation")))
 (next-milestone .
 ((name . heterogeneous-host-staged-fpga-input)
  (status . "complete — physical ISA 1.1 register-input and CPU→CUDA→host-staged-FPGA evidence are pinned in cml/fpga-lisp")
  (goal . "preserve one semantic graph across CPU, CUDA, and FPGA while keeping direct device-to-device transfer explicitly absent")
  (per-repo .
   ((my-lisp . "done — tests/fixtures/conformance.my's tier-1 fixtures already expose the oracle value; no further work needed unless cml/fpga-lisp need a different entry point")
    (cml . "done — typed buffer adapter, explicit graph edge, and CPU→CUDA→host-staged-FPGA live pass are pinned")
    (fpga-lisp . "done — M35 physical register-input and M36 host-staged heterogeneous evidence are pinned")
     (my-idea . "not started — one panel: source -> compiled instructions -> execution -> decoded result -> oracle match, PASS/FAIL")))
   (anti-pattern-to-avoid . "no more NOTE-*.md proliferation or (quote agent) X replied to agent Y' commits — coordinate through this file's current-task fields and normal commits that actually touch code")))
 (how-to-refresh .
  "Before starting new work, read this file's current-task fields. When your own repo's task changes, hand-update your repository's current-task entry and this file's as-of date directly. For live coordination use swarm-node (:910x, swarm/1); never use the my-lisp :9999 semantic oracle as a coordination channel. Don't let this snapshot go stale the way it did between 2026-08-11 and 2026-08-12."))