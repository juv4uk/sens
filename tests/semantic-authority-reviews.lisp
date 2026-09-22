; Explicit semantic-authority reviews.
; Lisp-owned policy data consumed by scripts/semantic-authority-guard.lisp.
;
; Every review is bound to BOTH an exact repository path and the SHA-256 of
; the exact reviewed source text. No prefixes, directories, globs, or
; permanent path exemptions exist. Any later edit changes the digest and
; requires a new explicit review row.
;
; #1098 SID-BINARY-IDENTITY-1 is a reviewed representation migration:
; semantic identity changes from host numeric aliases to opaque exact 8-bit Sid8.

(review "crates/my-lisp/src/eval/builtins.rs" "4ca9b106abd671eccc1abd0c8c9401d219b898c6df72801ab67cb1dea9a0b4f1" issue-1098 sid8-type-migration)
(review "crates/my-lisp/src/eval/canon.rs" "6ba3c72cb8d14552642b8c76dacb680d1c5d2d27712eb498f2454fc32d5f3015" issue-1098 sid8-type-migration)
(review "crates/my-lisp/src/eval/mod.rs" "b82488395827e94ef910ca554962bc9008811d8cae4121dbe6d3533849d7293e" issue-1098 sid8-type-migration)
(review "crates/my-lisp/src/eval/necessary_forms.rs" "6876d0aeec8b7d26b0014a51e194af8cd68ce3bcc84ecaffd974ce27557b55f5" issue-1098 sid8-type-migration)
(review "crates/my-lisp/src/ir.rs" "619143298b56b4788c4c2de1c84023e1cc19449dea8729bdf4e9ccbb07128410" issue-1098 sid8-type-migration)
(review "crates/my-lisp/src/language_items.rs" "f772ebce9c52525c355f944a7472986a70034ae30a70537878444766c02b9f69" issue-1098 sid8-type-migration)
(review "crates/my-lisp/src/lib.rs" "d8cf1aff9c382c98ddae1b8e5e1087135403d91441d1d16c21b32e2e9f570fe4" issue-1098 sid8-projection-boundary)
(review "crates/my-lisp/src/presentation.rs" "436b74f73df5a1c00ee4a35b32ec01aab0441f0fda717ede346bdca3cbdae288" issue-1098 sid8-type-migration)
(review "crates/my-lisp/src/semantic_registry.rs" "9677f513b2fe3ad319f1f371f30c2d4649c4969839de5da852f488426083aec3" issue-1098 sid8-projection-boundary)
(review "crates/my-lisp/src/value.rs" "96d89de14c18dec59101bbcda60ff9f9abbafb9b9e6b2271cea3f318dbaa6179" issue-1098 sid8-type-migration)
(review "crates/my-lisp/tests/machine_capability_axis.rs" "f9c7e69325cc02bcdb4646acd4fa1a15aa49ba0edf52477e529cfdd870e0268e" issue-1098 sid8-witness-migration)
(review "crates/my-lisp/tests/rivnopravnist_mov.rs" "5280e7f47de4ee4bf4d10731e1b0d05a4e2bda78fc6fbc8176596e6a646b05da" issue-1098 sid8-witness-migration)
(review "crates/my-lisp/tests/semantic_coordinate_join.rs" "102a70d74902b90d029a96e1f0d02c81dbd4e7f7afff2298bab303f10e39beba" issue-1098 sid8-witness-migration)
(review "crates/my-lisp/tests/semantic_coordinate_join_2.rs" "49328492430e58e516ce926d77808a111992fdd586356c517c462db7c222baeb" issue-1098 sid8-witness-migration)
(review "crates/my-lisp/tests/semantic_coordinate_law_axis.rs" "b75443a411c225a7075e2c3f2eede1b2f5887c8d94b8a33e6ee0b826544a3c55" issue-1098 sid8-witness-migration)
(review "crates/xtask/src/external_oracle.rs" "9ad5faa5003a3e440ffc1408f4f4e7f4d3985508c34933d0425e796bab4e7f05" issue-1098 sid8-tooling-migration)
(review "crates/my-lisp/tests/peer_surface_identity.rs" "ac66056cda917c2104b4e62d126587a067b9acd6bacff7ad658b3ee905addc8e" issue-1098 sid8-observer-migration)
(review "crates/my-lisp/tests/uk_surface_equivalence.rs" "a726233e46be11fdfaabcb8b84074cfcba8beb919b753334411c2b092a2c1a63" issue-1098 sid8-witness-migration)
(review "crates/my-lisp/tests/rivnopravnist_mov.rs" "40cfe6b0dd9808a31be1f161a5da05982a1b7b15f6b3a5ac5dea063062ae5112" issue-1098 legacy-export-sid8-boundary-witness)

; #1101 SID-RUNTIME-UNIFY-1 removes the duplicate SemanticRef runtime kind.
(review "crates/my-lisp/src/eval/mod.rs" "01c8053accb96d1c91e49073ecf59681df8fe5c86eef7c97b0eddea49a361465" issue-1101 single-sid-runtime)
(review "crates/my-lisp/tests/clock.rs" "035fd471b3b9a1f30fb77d8d92eb84986f2461d9899d7a7b1ffff7ea9ce9d9e2" issue-1101 sid-witness-migration)
(review "crates/my-lisp/tests/timezone_ownership.rs" "72ad98691141e7dbdf496bd300ecb5a3dc26aed7e580a5021643ed256663aa23" issue-1101 sid-witness-migration)
(review "crates/my-lisp/src/presentation.rs" "235c7ff4d8c76fb72c0eaaf5663bf690395f6216c52d625d73f6dc86a521c510" issue-1101 single-sid-presentation-projection)

; #1131 FOUR-CORE-ARCH-1 adds only the mechanical CoreProfile module/export
; boundary to lib.rs. Profile meaning remains in contracts/core-profile-contract.lisp;
; this exact digest review does not permit any later lib.rs edit.
(review "crates/my-lisp/src/lib.rs" "cbfed785afac51fe3ee96c12260039825bc644b8daf0320bce86bca294fa62c9" issue-1131 core-profile-mechanical-boundary)
