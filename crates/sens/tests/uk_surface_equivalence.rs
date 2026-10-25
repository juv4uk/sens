//! Registry-driven UK/EN surface equivalence sweep.
//!
//! Data source: `lib/surface/semantic-registry.lisp`, the byte-SID surface
//! authority (see `semantic_registry.rs` for the runtime parser this test
//! mirrors). This file used to read the legacy EN-shaped
//! `lib/surface/uk-sa-coverage.wsm`, which `rivnopravnist_mov.rs` and
//! `runtime_peer_operators.rs` already assert is no longer executable
//! authority (TEST-ARCHITECTURE-1 step 2 migration, 2026-09-12).

use sens::syntax::ExprKind;
use sens::{eval_program, load_core_library, lower_program, parse, Session};

fn registry_rows() -> Vec<(String, Vec<Surface>)> {
    sens::semantic_registry_export::admitted_semantic_ids()
        .into_iter()
        .map(|semantic_id| {
            let id = sens::semantic_registry_export::semantic_id_bits(semantic_id);
            let surfaces =
                sens::semantic_registry_export::admitted_surfaces_for_semantic_id(semantic_id)
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
    surfaces
        .iter()
        .find(|surface| surface.namespace == namespace)
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

        let lower_surface = |surface: &str| {
            let source = format!("({surface})");
            let parsed = parse(&source).expect("admitted surface call must parse");
            let lowered = lower_program(&parsed);
            assert_eq!(lowered.len(), 1);
            lowered.into_iter().next().unwrap().kind
        };

        let english_kind = lower_surface(english);
        let ukrainian_kind = lower_surface(ukrainian);

        match (&english_kind, &ukrainian_kind) {
            (
                ExprKind::DomainCall(english_domain, _),
                ExprKind::DomainCall(ukrainian_domain, _),
            ) => assert_eq!(
                english_domain, ukrainian_domain,
                "EN/UK surfaces must lower to one exact domain identity: {english} / {ukrainian}"
            ),
            (ExprKind::Call(english_sens, _), ExprKind::Call(ukrainian_sens, _)) => {
                assert_eq!(
                    english_sens, ukrainian_sens,
                    "legacy EN/UK surfaces must lower to one compatibility identity: {english} / {ukrainian}"
                );
                assert_eq!(
                    *english_sens, declared,
                    "unmigrated compatibility surface must retain its declared legacy identity: {english}"
                );
            }
            (ExprKind::Call(english_sens, _), ExprKind::DomainCall(_, _)) => {
                assert_eq!(
                    *english_sens, declared,
                    "English compatibility projection must retain its declared legacy identity while UK migrates: {english}"
                );
            }
            (ExprKind::DomainCall(_, _), ExprKind::Call(_, _)) => panic!(
                "canonical migration must not regress UK back to the legacy path: \
                 {english} -> {english_kind:?}; {ukrainian} -> {ukrainian_kind:?}"
            ),
            _ => panic!(
                "EN/UK surface pair has an unsupported lowering split: \
                 {english} -> {english_kind:?}; {ukrainian} -> {ukrainian_kind:?}"
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
fn чинний_d8_round_не_є_історичним_sid8_invoke() {
    // У ратифікованому D8:10101000 мешкає ROUND, а не історичний
    // Function8:10101000 INVOKE. Однакові 8 біт не означають один закон.
    let table = include_str!("../../../lib/domains/d8.lisp");
    let actual = table.lines()
        .find(|line| line.starts_with("  (10101000 "))
        .expect("збережено ратифікований D8:10101000");
    assert!(actual.contains("(укр округлити-до-найближчого)"));
    assert!(actual.contains("(en round)"));
    assert!(!actual.contains("invoke"), "D8 не може успадкувати SID8");

    let decoded = sens::parse_exact_domain_source("10101000")
        .expect("точний D8 reader");
    assert!(matches!(
        &decoded[0].kind,
        ExprKind::DomainIdentity(sens::DomainIdentity::D8(word))
            if word.word().packed_bits() == 0b10101000
    ));

    // Історична поверхня не отримує чинної DomainCall лише тому,
    // що її колишній байт збігається з новою D8 координатою.
    for surface in ["invoke", "викликати"] {
        let lowered = lower_program(
            &parse(&format!("({surface})")).expect("історичне ім'я читається як текст")
        );
        assert!(
            !matches!(
                &lowered[0].kind,
                ExprKind::DomainCall(identity, _) if
                    (identity.width(), identity.packed_bits()) == (8, 0b10101000)
            ),
            "історичне INVOKE не може підмінити сучасний D8 ROUND"
        );
    }
}
