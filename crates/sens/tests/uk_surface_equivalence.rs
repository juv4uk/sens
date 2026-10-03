//! Registry-driven UK/EN surface equivalence sweep.
//!
//! Data source: `lib/surface/semantic-registry.lisp`, the byte-SID surface
//! authority (see `semantic_registry.rs` for the runtime parser this test
//! mirrors). This file used to read the legacy EN-shaped
//! `lib/surface/uk-sa-coverage.wsm`, which `rivnopravnist_mov.rs` and
//! `runtime_peer_operators.rs` already assert is no longer executable
//! authority (TEST-ARCHITECTURE-1 step 2 migration, 2026-09-12).

use sens::{eval_program, load_core_library, lower_program, parse, ErrorKind, Session};
use sens::syntax::ExprKind;

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

#[test]
fn every_stable_uk_surface_entry_lowers_to_one_canonical_identity() {
    let pairs = present_en_uk_pairs();
    assert!(
        pairs.len() >= 100,
        "expected a substantial number of present EN/UK pairs, found {}",
        pairs.len()
    );

    // Loading the human projection must still succeed, but its spellings are
    // no longer required to materialize as first-class runtime values.
    let _session = uk_session();

    for (declared_bits, english, ukrainian) in &pairs {
        let declared = sens::semantic_registry_export::semantic_id_for_admitted_surface(english)
            .expect("registry EN surface must resolve");
        let ukrainian_declared =
            sens::semantic_registry_export::semantic_id_for_admitted_surface(ukrainian)
                .expect("registry UK surface must resolve");

        assert_eq!(
            sens::semantic_registry_export::semantic_id_bits(declared),
            *declared_bits,
            "registry row and EN reverse projection drifted for {english}"
        );
        assert_eq!(
            ukrainian_declared, declared,
            "EN/UK surfaces must project to one exact SENS: {english} / {ukrainian}"
        );

        let lower_head = |surface: &str| {
            let source = format!("({surface})");
            let parsed = parse(&source).expect("admitted surface call must parse");
            let lowered = lower_program(&parsed);
            assert_eq!(lowered.len(), 1);
            lowered.into_iter().next().expect("one lowered form").kind
        };

        let english_head = lower_head(english);
        let ukrainian_head = lower_head(ukrainian);

        match (&english_head, &ukrainian_head) {
            (ExprKind::DomainCall(en, _), ExprKind::DomainCall(uk, _)) => {
                assert_eq!(
                    en, uk,
                    "EN/UK migrated surfaces must converge on one exact domain identity: {english} / {ukrainian}"
                );
            }
            (ExprKind::Call(en, _), ExprKind::Call(uk, _)) => {
                assert_eq!(en, uk, "EN/UK compatibility calls must converge");
                assert_eq!(
                    *en, declared,
                    "unmigrated compatibility call must retain declared historical projection"
                );
            }
            (en, uk) => panic!(
                "EN/UK peers must agree on identity class: {english} -> {en:?}, {ukrainian} -> {uk:?}"
            ),
        }
    }
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
fn admitted_invoke_surfaces_lower_to_one_exact_sens_without_bare_value_fallback() {
    let invoke_sens =
        sens::semantic_registry_export::semantic_id_for_admitted_surface("invoke")
            .expect("invoke must be admitted by the single registry");
    let ukrainian_sens =
        sens::semantic_registry_export::semantic_id_for_admitted_surface("викликати")
            .expect("викликати must be admitted by the single registry");
    assert_eq!(invoke_sens, ukrainian_sens);
    assert_eq!(
        sens::semantic_registry_export::semantic_id_bits(invoke_sens),
        "10101000"
    );

    for surface in ["invoke", "викликати"] {
        let parsed = parse(&format!("({surface})")).expect("invoke surface call must parse");
        let lowered = lower_program(&parsed);
        assert_eq!(lowered.len(), 1);
        assert!(matches!(
            &lowered[0].kind,
            ExprKind::Call(sens, _) if *sens == invoke_sens
        ));
    }

    // #1946 / M8 precedent: an admitted function spelling is an input
    // projection in executable head position, not a lexical runtime value.
    let mut session = Session::default();
    load_core_library(&mut session).expect("core bootstrap");
    for surface in ["invoke", "викликати"] {
        let error = eval_program(surface, &mut session)
            .expect_err("bare admitted invoke spelling must not regain name fallback");
        assert_eq!(error.kind, ErrorKind::UnknownSymbol);
    }
}
