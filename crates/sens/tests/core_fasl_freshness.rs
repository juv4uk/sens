//! Repository-wide invariant for every FASL consumer, including WASM.
//! A committed core.lisp.fasl must be bound to the exact current lib/core.lisp
//! source. The native CLI already falls back when this is false; consumers
//! that embed only the snapshot must never be allowed to build from a green
//! repository with a stale snapshot in the first place.

#[test]
fn committed_core_fasl_matches_current_core_source() {
    let fasl = include_bytes!("../../../lib/core.lisp.fasl");
    let (_, embedded_hash) = sens::fasl_decode_program(fasl)
        .expect("committed lib/core.lisp.fasl must decode");
    let current_hash = sens::sha256_source(sens::CORE_LIBRARY_SOURCE.as_bytes());

    assert_eq!(
        embedded_hash, current_hash,
        "lib/core.lisp.fasl is stale; regenerate it from the current lib/core.lisp"
    );
}
