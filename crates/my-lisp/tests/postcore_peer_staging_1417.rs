//! #1417 — canonical Core4 bootstrap must not pre-bind lexical SENS placeholders
//! that block post-core Lisp-owned peer materialization.

use my_lisp::{load_core_library, load_process_library, Session, Value};

#[test]
fn core4_bootstrap_leaves_postcore_peer_unbound_until_real_closure_exists() {
    let mut session = Session::default();

    load_core_library(&mut session).expect("Core4 bootstrap");

    assert!(
        session.environment.get("process-run").is_none(),
        "post-core source surface must not be pre-bound before lib/process.lisp"
    );
    assert!(
        session.environment.get("запустити-процес").is_none(),
        "stable peer must not be pre-bound to a lexical SENS placeholder"
    );

    load_process_library(&mut session).expect("process/TCP language layer");

    let source = session
        .environment
        .get("process-run")
        .expect("process-run closure after process library");
    let peer = session
        .environment
        .get("запустити-процес")
        .expect("stable Ukrainian peer after post-core materialization");

    assert!(matches!(source, Value::Closure(_)));
    assert_eq!(
        source, peer,
        "post-core stable surfaces must share the same closure identity"
    );
}
