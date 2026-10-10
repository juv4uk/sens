//! Repository-wide invariant for every FASL consumer, including WASM.
//! A committed core4.lisp.fasl must be bound to the exact current lib/core4.lisp
//! source. The native CLI already falls back when this is false; consumers
//! that embed only the snapshot must never be allowed to build from a green
//! repository with a stale snapshot in the first place.

#[test]
fn committed_core_fasl_matches_current_core_source() {
    let fasl = include_bytes!("../../../lib/core4.lisp.fasl");
    let (snapshot_expressions, embedded_hash) = sens::fasl_decode_program(fasl)
        .expect("committed lib/core4.lisp.fasl must decode");
    let current_source = sens::CORE_LIBRARY_SOURCE;
    let current_hash = sens::sha256_source(current_source.as_bytes());

    assert_eq!(
        embedded_hash, current_hash,
        "lib/core4.lisp.fasl is stale; regenerate it from the current lib/core4.lisp"
    );

    let current_expressions =
        sens::parse_mixed_exact_domain_core_source("lib/core4.lisp", current_source)
            .expect("Core4 source must parse through the path-bound exact-domain reader");
    assert_eq!(
        snapshot_expressions, current_expressions,
        "Core4 FASL must preserve exact-domain parser output, not an ordinary-parse AST; regenerate with gen-fasl"
    );
}
