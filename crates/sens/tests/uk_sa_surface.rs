//! Surviving, non-redundant UK/SA surface tests.
//!
//! TEST-ARCHITECTURE-1 step 3 removed most of this file's per-operator
//! tests: each was a single hardcoded example of "does this UK/SA name
//! resolve to the same runtime value as its EN counterpart", a mutation
//! `uk_surface_equivalence.rs`'s registry-driven sweep already kills
//! generically for every stable EN/UK pair. What remains here either (a)
//! exercises syntax forms the identity-based sweep can't check (quote/cond
//! aren't first-class values), (b) exercises names/mechanisms the sweep
//! does not cover (aliases absent from the registry, or SA identity, which
//! has no EN-comparison sweep), or (c) is the acceptance-program runner
//! pattern the owner explicitly wants kept.
//!
//! Removed and why (surviving test that kills the same mutation):
//! - uk_atom_predicates_correctly, uk_eq_compares_identity,
//!   uk_cons_car_cdr_roundtrip, uk_abs_works, uk_min_max_work,
//!   uk_mod_quotient_work, uk_not_works, uk_equal_works,
//!   uk_symbol_predicate_works, uk_string_predicate_works,
//!   uk_list_length_append_reverse, uk_ordinals_work, uk_map_works,
//!   uk_filter_works, uk_reduce_works, uk_string_operations,
//!   uk_and_en_produce_same_result -> all stable EN/UK pairs, killed by
//!   `uk_surface_equivalence.rs::every_stable_uk_surface_entry_resolves_to_its_declared_operation`.
//! - uk_subtraction_works, uk_multiplication_works, uk_division_works,
//!   3 of 5 assertions in uk_comparisons_work (менше?/більше?/рівне?)
//!   -> `runtime_peer_operators.rs::stable_operator_peers_exist_before_human_surface_libraries_load`
//!   (same IDs 1001/1002/1003/1014/1015/1016, behaviorally checked there).
//! - uk_addition_works, uk_and_sa_produce_same_result (додати/+/yoga, ID
//!   0104) -> `rivnopravnist_mov.rs::додавання_відділяє_людські_мови_від_спільного_двійкового_коду`.
//! - sa_arithmetic_works, sa_comparisons_work, sa_and_en_produce_same_result
//!   -> `runtime_peer_operators.rs` CASES already behaviorally check every
//!   one of those SA spellings (viyoga/guṇana/haraṇa/hīna?/adhika?/sama?)
//!   against their UK/symbolic peers.

use sens::{
    Session, eval_parsed_expressions, eval_program, load_core_library, lower_program,
    parse_mixed_exact_domain,
};

fn load_surface_prerequisites(session: &mut Session) {
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
        eval_program(source, session).expect("surface prerequisite should load");
    }
}

/// Load core library + Ukrainian surface, return a fresh session.
fn uk_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core bootstrap");
    load_surface_prerequisites(&mut session);
    eval_program(include_str!("../../../lib/surface/uk.lisp"), &mut session)
        .expect("Ukrainian surface should load");
    session
}

/// Load core library + Sanskrit surface, return a fresh session.
fn sa_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core bootstrap");
    load_surface_prerequisites(&mut session);
    // Canon 0+7 names are resolved by their stable identities. The separate
    // `sa.lisp` candidate alias inventory is not itself a fully executable
    // program and must not be treated as one by this runtime test.
    session
}

// ── Syntax forms: not first-class values, so the identity-based
//    registry sweep in uk_surface_equivalence.rs can't check them. ──

#[test]
fn uk_quote_returns_form_unevaluated() {
    let mut s = uk_session();
    let r = eval_program("(як-є (+ 1 2))", &mut s).expect("eval");
    assert_eq!(r.value.to_string(), "(+ 1 2)");
}

#[test]
fn uk_cond_branches_correctly() {
    let mut s = uk_session();
    let r = eval_program(
        r#"(за-умовою
             ((тотожне? 1 1) (як-є так))
             ((тотожне? 1 1) (як-є ні)))"#,
        &mut s,
    )
    .expect("eval");
    assert_eq!(r.value.to_string(), "так");
}

// ── Comparison aliases not covered elsewhere: не-більше?/не-менше? have
//    no spelled-out EN name in the registry (EN column is "missing"), so
//    they fall outside both the equivalence sweep and runtime_peer_operators'
//    CASES table. менше?/більше?/рівне? are covered by
//    runtime_peer_operators.rs and were dropped from this test. ──

#[test]
fn uk_le_ge_comparisons_work() {
    let mut s = uk_session();
    assert_eq!(
        eval_program("(не-більше? 2 3)", &mut s)
            .unwrap()
            .value
            .to_string(),
        "1"
    );
    assert_eq!(
        eval_program("(не-менше? 3 3)", &mut s)
            .unwrap()
            .value
            .to_string(),
        "1"
    );
}

// ── The current Ukrainian names are covered here in addition to the
//    registry-driven equivalence sweep. ──

#[test]
fn uk_current_nth_member_names_work() {
    let mut s = uk_session();
    let r = eval_program("(елемент-списку-за-індексом 1 (список 10 20 30))", &mut s).expect("eval");
    assert_eq!(r.value.to_string(), "20");
    let r2 = eval_program("(значення-у-списку? 2 (список 1 2 3))", &mut s).expect("eval");
    assert_eq!(r2.value.to_string(), "1");
}

// ── Sanskrit surface: no SA/EN registry-driven equivalence sweep exists
//    yet (uk_surface_equivalence.rs only compares EN/UK); this checks the
//    stable svarūpa (quote)/ādi (car)/śeṣa (cdr) identities. ──

#[test]
fn sa_canon_works() {
    let mut s = sa_session();
    let r = eval_program("(svarūpa (+ 1 2))", &mut s).expect("eval");
    assert_eq!(r.value.to_string(), "(+ 1 2)");
    let r2 = eval_program("(ādi (saṃyuj 10 20))", &mut s).expect("eval");
    assert_eq!(r2.value.to_string(), "10");
    let r3 = eval_program("(śeṣa (saṃyuj 10 20))", &mut s).expect("eval");
    assert_eq!(r3.value.to_string(), "20");
}

// ── Ukrainian acceptance program: semantic truth lives in the `.my`
//    fixture, Rust just runs it -- a good pattern, not a duplication
//    target. Explicitly kept per the owner's guidance. ──

#[test]
fn uk_acceptance_program_passes() {
    let mut s = uk_session();
    let r = eval_program(
        include_str!("../../../lib/surface/uk-acceptance.lisp"),
        &mut s,
    )
    .expect("Ukrainian acceptance program should evaluate");
    assert_eq!(
        r.value.to_string(),
        "(uk-acceptance (status pass))",
        "acceptance fixture must return its current structured pass witness"
    );
}

/// Виконувана українська програма, не перевірка host-alias.
#[test]
fn peer_identity_acceptance_program_passes() {
    let mut s = uk_session();
    let source = include_str!("../../../lib/surface/peer-identity-acceptance.lisp");
    let parsed = parse_mixed_exact_domain(source)
        .expect("чинний український D1/D24+ читач має приймати програму");
    // Поточні «так»/«ні» — канонічні D1, а не host-змінні.
    let lowered = lower_program(&parsed);
    let r = eval_parsed_expressions(&lowered, &mut s)
        .expect("Ukrainian D1/D3/D24+ acceptance program should evaluate");
    assert_eq!(r.value.to_string(), "успіх");
}

/// Негативний семантичний свідок: змінена очікувана арифметика
/// мусить спричинити іменовану помилку, а не формальний PASS.
#[test]
fn peer_identity_acceptance_wrong_abs_expectation_is_detected() {
    let source = include_str!("../../../lib/surface/peer-identity-acceptance.lisp");
    let correct = "(однакове-число? (модуль (відняти приймання-число-нуль приймання-число-сім)) приймання-число-сім)";
    assert_eq!(source.matches(correct).count(), 1, "втрачено точний свідок");
    let mutant = source.replacen(
        correct,
        "(однакове-число? (модуль (відняти приймання-число-нуль приймання-число-сім)) приймання-число-п'ять)",
        1,
    );
    let mut s = uk_session();
    let parsed = parse_mixed_exact_domain(&mutant)
        .expect("негативний мутант повинен зберігати чинний D1/D24+ синтаксис");
    // Поточні «так»/«ні» — канонічні D1, а не host-змінні.
    let lowered = lower_program(&parsed);
    let r = eval_parsed_expressions(&lowered, &mut s)
        .expect("mutant must execute in actual SENS evaluator");
    assert_eq!(r.value.to_string(), "помилка-модуль");
}
