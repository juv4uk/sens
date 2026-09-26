//! Registry-driven UK/EN surface equivalence sweep.
//!
//! Data source: `lib/surface/semantic-registry.lisp`, the byte-SID surface
//! authority (see `semantic_registry.rs` for the runtime parser this test
//! mirrors, and `peer_surface_identity.rs` for the same pattern applied to
//! one byte SID). This file used to read the legacy EN-shaped
//! `lib/surface/uk-sa-coverage.wsm`, which `rivnopravnist_mov.rs` and
//! `runtime_peer_operators.rs` already assert is no longer executable
//! authority (TEST-ARCHITECTURE-1 step 2 migration, 2026-09-12).

use sens::{eval_program, load_core_library, Session, Value};
use std::rc::Rc;

fn registry_rows() -> Vec<(String, Vec<Surface>)> {
    sens::semantic_registry_export::admitted_semantic_ids()
        .into_iter()
        .map(|semantic_id| {
            let id = sens::semantic_registry_export::semantic_id_bits(semantic_id);
            let surfaces = sens::semantic_registry_export::admitted_surfaces_for_semantic_id(semantic_id)
                .into_iter()
                .map(|row| Surface {
                    namespace: row.namespace.to_owned(),
                    name: Some(row.name.to_owned()),
                })
                .collect();
            (id, surfaces)
        })
        .collect()
}

struct Surface {
    namespace: String,
    name: Option<String>,
}

fn surface<'a>(surfaces: &'a [Surface], namespace: &str) -> Option<&'a Surface> {
    surfaces.iter().find(|surface| surface.namespace == namespace)
}

/// Every byte SID whose EN spelling AND UK spelling are both present.
fn present_en_uk_pairs() -> Vec<(String, String, String)> {
    registry_rows()
        .into_iter()
        .filter_map(|(id, surfaces)| {
            let en = surface(&surfaces, "en")?.name.clone()?;
            let uk = surface(&surfaces, "ук")?.name.clone()?;
            Some((id, en, uk))
        })
        .collect()
}

fn uk_presence_counts() -> (usize, usize, usize) {
    let rows = registry_rows();
    let total = rows.len();
    let mut present = 0;
    let mut empty = 0;
    for (_, surfaces) in &rows {
        match surface(surfaces, "ук").and_then(|s| s.name.as_deref()) {
            Some(_) => present += 1,
            None => empty += 1,
        }
    }
    (total, present, empty)
}

fn uk_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core bootstrap");
    for source in [
        include_str!("../../../lib/unify.lisp"),
        include_str!("../../../lib/reason.lisp"),
        include_str!("../../../lib/forward.lisp"),
        include_str!("../../../lib/knowledge.lisp"),
        include_str!("../../../lib/persistent-map.lisp"),
        include_str!("../../../lib/persistent-vector.lisp"),
        include_str!("../../../lib/time.lisp"),
        include_str!("../../../lib/epistemic.lisp"),
    ] {
        eval_program(source, &mut session).expect("surface prerequisite should load");
    }
    eval_program(include_str!("../../../lib/surface/uk.lisp"), &mut session)
        .expect("Ukrainian surface should load");
    session
}

fn is_same_runtime_value(left: &Value, right: &Value) -> bool {
    match (left, right) {
        // A builtin is an operation handle. Canon EN/UK/SA spellings and
        // ordinary aliases must retain one allocation, not merely similar code.
        (Value::Builtin(left), Value::Builtin(right)) => Rc::ptr_eq(left, right),
        _ => left == right,
    }
}

#[test]
fn every_stable_uk_surface_entry_resolves_to_its_declared_operation() {
    let pairs = present_en_uk_pairs();
    // Floor, not exact count: the registry only grows. An exact hardcoded
    // count here would silently rot every time a new stable pair is added --
    // this just guards against the parse producing an (almost) empty set.
    assert!(
        pairs.len() >= 100,
        "expected a substantial number of present EN/UK pairs, found {}",
        pairs.len()
    );

    let mut session = uk_session();
    // Evaluation-control/necessary forms (quote/cond/lambda/define) are
    // syntax, not first-class values -- Rc-identity comparison is not
    // meaningful for them, so they're verified behaviorally in
    // uk_surface.rs / uk_sa_surface.rs instead of here.
    let syntax = [
        ("quote", "як-є"),
        ("cond", "за-умовою"),
        ("lambda", "функція"),
        ("define", "визначити"),
    ];
    // Host primitives (process, tcp, fs) belong to sens-host substrate,
    // not to the pure language session tested here.
    let host_operations = [
        "process-run",
        "tcp-read",
        "tcp-write",
        "tcp-listen",
        "read-file",
        "write-file",
    ];
    let mut checked_values = 0;

    let mut expected_checked = 0usize;
    for (semantic_id, english, ukrainian) in &pairs {
        if syntax.iter().any(|(en, uk)| en == english && uk == ukrainian)
            || host_operations.iter().any(|name| *name == english)
        {
            continue;
        }
        expected_checked += 1;
        let english_value = eval_program(english, &mut session)
            .unwrap_or_else(|error| {
                panic!("English value is missing: {semantic_id}/{english}: {error}")
            })
            .value;
        let ukrainian_value = eval_program(ukrainian, &mut session)
            .unwrap_or_else(|error| {
                panic!("Ukrainian value is missing: {semantic_id}/{ukrainian}: {error}")
            })
            .value;
        assert!(
            is_same_runtime_value(&english_value, &ukrainian_value),
            "surface changed runtime identity: {semantic_id}/{english} -> {ukrainian}"
        );
        checked_values += 1;
    }

    // Derived, not restated: every pair except the syntax forms and host
    // operations must have been checked above -- catches a silent early
    // `continue`/`break` bug in the loop without hardcoding the pair count twice.
    assert_eq!(checked_values, expected_checked);
}

#[test]
fn ukrainian_surface_status_counts_are_internally_consistent() {
    let (total, present, empty) = uk_presence_counts();
    assert_eq!(
        present + empty,
        total,
        "every registry row's UK slot must be either present or ()"
    );
    assert!(present > 0 && total > 0, "registry must not be empty");
}

// every_stable_ukrainian_name_is_typeable_on_the_ukrainian_layout and
// ukrainian_acceptance_program_code_never_requires_latin_layout were
// keyboard/text-policy lints, relocated to `cargo xtask verify` per
// TEST-ARCHITECTURE-1 step 4 -- see crates/xtask/src/checks.rs.


#[test]
fn admitted_invoke_surfaces_materialize_from_the_single_registry() {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core bootstrap");

    let english = eval_program("invoke", &mut session)
        .expect("registry-admitted invoke surface must resolve")
        .value;
    let ukrainian = eval_program("викликати", &mut session)
        .expect("registry-admitted Ukrainian invoke surface must resolve")
        .value;
    let invoke_sid = sens::semantic_registry_export::semantic_id_for_admitted_surface("invoke")
        .expect("invoke must be admitted by sr/2");
    let ukrainian_sid =
        sens::semantic_registry_export::semantic_id_for_admitted_surface("викликати")
            .expect("викликати must be admitted by sr/2");

    assert_eq!(invoke_sid, ukrainian_sid);
    assert_eq!(english, Value::Sid(invoke_sid));
    assert_eq!(ukrainian, Value::Sid(ukrainian_sid));
    assert_eq!(english, ukrainian);
}
