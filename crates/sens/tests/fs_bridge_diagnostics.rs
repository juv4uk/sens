//! Path-pinned witness for Lisp-owned filesystem adapter semantics.
//! This narrows full store failures to package lookup or lambda binding.
use sens::{eval_program, eval_pinned_legacy_core_source, eval_pinned_reasoning_source, Session};

fn session() -> Session {
    let mut s = Session::default();
    eval_pinned_legacy_core_source("lib/core.lisp", include_str!("../../../lib/core.lisp"), &mut s).unwrap();
    for (path, source) in [
        ("lib/unify.lisp", include_str!("../../../lib/unify.lisp")),
        ("lib/reason.lisp", include_str!("../../../lib/reason.lisp")),
        ("lib/forward.lisp", include_str!("../../../lib/forward.lisp")),
        ("lib/knowledge.lisp", include_str!("../../../lib/knowledge.lisp")),
        ("lib/persistent-map.lisp", include_str!("../../../lib/persistent-map.lisp")),
        ("lib/world.lisp", include_str!("../../../lib/world.lisp")),
        ("lib/content-store.lisp", include_str!("../../../lib/content-store.lisp")),
        ("lib/lisp-fs.lisp", include_str!("../../../lib/lisp-fs.lisp")),
    ] {
        eval_pinned_reasoning_source(path, source, &mut s)
            .unwrap_or_else(|e| panic!("bootstrap {path}: {e:?}"));
    }
    s
}

fn observe(s: &mut Session, source: &str) -> String {
    eval_program(source, s)
        .unwrap_or_else(|e| panic!("filesystem witness {source}: {e:?}"))
        .value.to_string()
}

#[test]
fn journal_event_fields_are_retrieved_from_a_real_alist() {
    let mut s = session();
    for (field, expected) in [("format","wsm-fs-event"), ("op","future-op")] {
        let source = format!("(fs-package-field (quote {field}) (fs-journal-event (quote future-op) (quote ())))");
        assert_eq!(observe(&mut s, &source), expected, "assoc field {field}");
    }
    assert_eq!(
        observe(&mut s, "(fs-package-field (quote missing) (fs-journal-event (quote future-op) (quote ())))"),
        "()",
        "unknown envelope keys remain absent, never synthesized"
    );
}

#[test]
fn root_envelope_accepts_its_own_schema_without_object_only_fields() {
    let mut session = session();
    assert_eq!(
        observe(&mut session, "(car (fs-root-package-decision (fs-root-package (fs-empty))))"),
        "accepted",
        "root metadata consists of format/version/revision/bindings/objects, not an address/value pair"
    );
    assert_eq!(
        observe(&mut session, "(fs-package-field (quote address) (fs-root-package (fs-empty)))"),
        "()",
        "the absent object address remains absent in a root envelope"
    );
}

#[test]
fn empty_object_store_uses_an_admitted_two_argument_lisp_closure() {
    let mut s = session();
    assert_eq!(
        observe(&mut s, "(fs-build-object-store (quote ()) (empty-content-store))"),
        "(accepted ())",
        "nested reconstruction must not shadow the two-argument closure"
    );
}

#[test]
fn derived_macro_binds_list_values_as_one_variable() {
    let mut s = session();
    assert_eq!(
        observe(&mut s, "(нехай-похідне ((x (list 4 5))) (car x))"),
        "4"
    );
    assert_eq!(
        observe(&mut s, "(нехай-похідне ((x (fs-build-object-store (quote ()) (empty-content-store)))) (car x))"),
        "accepted"
    );
}
