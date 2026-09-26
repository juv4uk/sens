//! #1417 — canonical Core4 bootstrap must not pre-bind lexical SENS
//! placeholders that block later language-owned peer materialization.

use sens::{load_core_library, load_process_library, semantic_registry_export, Session, Value};

#[test]
fn core4_bootstrap_leaves_postcore_peer_unbound_until_real_closure_exists() {
    let mut session = Session::default();

    load_core_library(&mut session).expect("Core4 bootstrap");

    let process_run =
        semantic_registry_export::semantic_id_for_admitted_surface("process-run")
            .expect("process-run stays admitted by the registry");
    assert_eq!(
        semantic_registry_export::semantic_id_for_admitted_surface("запустити-процес"),
        Some(process_run)
    );

    assert!(
        session.environment.get("process-run").is_none(),
        "post-core source surface must not be pre-bound before lib/process.lisp"
    );
    assert!(
        session.environment.get("запустити-процес").is_none(),
        "stable peer must not be pre-bound before the real language value exists"
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
        "post-core stable surfaces must share the same closure value"
    );
}
