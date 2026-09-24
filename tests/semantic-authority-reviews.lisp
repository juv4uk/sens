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

; #992 CLIPS native result observation: reviewed mechanism-only adapter.
(review "crates/wsm-clips-kernel/src/lib.rs" "2ea4eb418c1ac76820145236773caa212a72e39f3d27211bf5608278437a5a0e" issue-992 clips-result-observation-mechanism)
(review "crates/wsm-clips-kernel/tests/c_abi_semantic_witness.rs" "9498c9ab5018b9d0270c72d3906d2f202053a489f4ac4128c3859c2cd33019f0" issue-992 clips-result-observation-witness)

; #1169 CLIPS SID8 boundary: reviewed removal of operator-text semantic dispatch.
; Host code only removes a text-based execution path; it does not map native
; operators/names to SID. Raw Eval remains diagnostic-only outside semantic exchange.
(review "crates/wsm-clips-kernel/src/lib.rs" "e240e4402db8ec44859e1055ccf2cb3e30757517344fa7ea611beeb1c8e34b56" issue-1169 clips-text-dispatch-removal-mechanism)
(review "crates/wsm-clips-kernel/tests/c_abi_semantic_witness.rs" "b701171e34685d0aa9753d836052d5bc2c2c5c33a238852f36570e4d9f602104" issue-1169 clips-text-dispatch-removal-witness)

; #1133 Core2 runtime profile: reviewed profile-selection mechanism and observer witness.
(review "crates/my-lisp/src/environment.rs" "9477dfa4f673a1e490d13d7d9512c919ddbfb18f65028402e0af14702037460d" issue-1133 core2-session-cond-mode)
(review "crates/my-lisp/src/eval/special_forms/core.rs" "96c35aaae7bb11c53138bbc080590c86daad2ea3fe4ae2555106e0b356ef8024" issue-1133 core2-cond-dispatch-mechanism)
(review "crates/my-lisp/src/lib.rs" "a4a37a9e086222440ac438b6c20590f573337037c1063e638b57c1ef0a9b5651" issue-1133 core2-loader-mechanism)
(review "crates/my-lisp/tests/core2_runtime_profile.rs" "718d19aa7681fc60aa90d7846548c727c9ea33feb0aa021555b978babd74c211" issue-1133 core2-runtime-observer)

; #1173 SID8 identity-field migration: reviewed observer-only test updates.
(review "crates/my-lisp/tests/witness_authority.rs" "bc5d4b359a169a5edc1cf3e2d0fb90e3bd7daa87e2d7e4d335ab467f9c76d492" issue-1173 sid8-identity-field-observer)
(review "crates/my-lisp/tests/semantic_coordinate_join.rs" "02cf206794a877fa894b8baf21c2b3a7ff8d97908b8896648005de30b69586a8" issue-1173 sid8-identity-field-observer)
(review "crates/my-lisp/tests/semantic_coordinate_join_2.rs" "ff0709c7ddf2dcd31be16e6ecf2572d154a51e36512f86910ee5338c09276aeb" issue-1173 sid8-identity-field-observer)
(review "crates/my-lisp/tests/semantic_coordinate_matrix_845.rs" "510f3c0ede3407dbc502815db845efdb1a90f7e4e5d5259123851c0d5cd03541" issue-1173 sid8-identity-field-observer)
;
; #1001 Datalog direct-SID8 arithmetic: reviewed mechanism-only host mapping.
; Exact SID8 chooses bounded native integer machinery; payload carries arguments
; only. These host files may execute an already-owned SID but cannot mint or
; reinterpret semantic identity.
(review "crates/wsm-datalog-kernel/src/arithmetic.rs" "79f10471d3b80f988496bb41b1a406a5b20788d386bfa710d0918eebbba8fbf2" issue-1001 datalog-direct-sid8-arithmetic-mechanism)
(review "crates/wsm-datalog-kernel/src/lib.rs" "e5c29f665637b802df1b1f8eb7283ab21ce5b0690690e831c7d4afa1ee2acabd" issue-1001 datalog-direct-sid8-abi-mechanism)
(review "crates/wsm-datalog-kernel/tests/arithmetic_execution_1001.rs" "91bbd2992e344bcae083d38edd96de30fa0b523c4376c8a430c1fc2f661d93ca" issue-1001 datalog-direct-sid8-observer)

; #1217 Common Lisp + semantic ABI: reviewed exact-SID8 mechanism binding.
; Raw CommonLispKernel::evaluate remains diagnostic/native; the shared semantic
; ABI binds SID 00001100 to bounded addition and accepts arguments only.
(review "crates/wsm-common-lisp-kernel/src/lib.rs" "d1c04c59757776a059981110a6622a1923ecf9b0be70b784448a3407f4e6f6f0" issue-1217 common-lisp-direct-sid8-add-mechanism)
