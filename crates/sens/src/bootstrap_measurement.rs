//! Test-only internal bootstrap decomposition for #3648.
//!
//! This module deliberately lives behind cfg(test) so private bootstrap
//! mechanisms stay private. It is measured by running the already-built
//! lib-test executable directly under Cachegrind.

use super::*;
use std::hint::black_box;

fn root_session() -> Session {
    Session {
        environment: Environment::root(),
    }
}

fn prepare_profile(session: &mut Session) {
    session.environment.select_core_profile(CoreProfile::Core4);
    session
        .environment
        .set_cond_clause_mode(environment::CondClauseMode::CurrentMigration);
}

fn load_first_macro(session: &mut Session) {
    load_macro_library(session).expect("macro library must load");
}

fn decode_current_core() -> Vec<Expr> {
    let (expressions, source_hash) =
        fasl_decode_program(CORE_LIBRARY_FASL).expect("embedded Core FASL must decode");
    assert_eq!(
        source_hash,
        sha256_source(CORE_LIBRARY_SOURCE.as_bytes()),
        "embedded Core FASL must match embedded Core source"
    );
    expressions
}

fn prepare_through_decode() -> (Session, Vec<Expr>) {
    let mut session = root_session();
    prepare_profile(&mut session);
    load_first_macro(&mut session);
    let expressions = decode_current_core();
    (session, expressions)
}

#[test]
#[ignore = "diagnostic benchmark for #3648"]
fn bootstrap_measure_root() {
    black_box(root_session());
}

#[test]
#[ignore = "diagnostic benchmark for #3648"]
fn bootstrap_measure_profile_setup() {
    let mut session = root_session();
    prepare_profile(&mut session);
    black_box(session);
}

#[test]
#[ignore = "diagnostic benchmark for #3648"]
fn bootstrap_measure_macro() {
    let mut session = root_session();
    prepare_profile(&mut session);
    load_first_macro(&mut session);
    black_box(session);
}

#[test]
#[ignore = "diagnostic benchmark for #3648"]
fn bootstrap_measure_decode() {
    let (session, expressions) = prepare_through_decode();
    black_box(session);
    black_box(expressions);
}

#[test]
#[ignore = "diagnostic benchmark for #3648"]
fn bootstrap_measure_eval_decoded_no_peers() {
    let (mut session, expressions) = prepare_through_decode();
    let result =
        eval_parsed_expressions(&expressions, &mut session).expect("decoded Core must evaluate");
    black_box(result);
    black_box(session);
}

#[test]
#[ignore = "diagnostic benchmark for #3648"]
fn bootstrap_measure_eval_decoded_with_peers() {
    let (mut session, expressions) = prepare_through_decode();
    let result =
        eval_parsed_expressions(&expressions, &mut session).expect("decoded Core must evaluate");
    bind_missing_stable_surface_peers(&session.environment);
    black_box(result);
    black_box(session);
}

#[test]
#[ignore = "diagnostic benchmark for #3648"]
fn bootstrap_measure_full_loader() {
    let mut session = root_session();
    let result = load_core_library(&mut session).expect("full Core loader must succeed");
    black_box(result);
    black_box(session);
}
