use sens::{
    eval_program, load_core2_library, load_core_library, Environment, ErrorKind, Session, Value,
};

fn core2_session() -> Session {
    let mut session = Session {
        environment: Environment::root(),
    };
    load_core2_library(&mut session).expect("Core2 library must load");
    session
}

#[test]
fn core2_uses_legacy_two_part_cond_truthiness() {
    let mut session = core2_session();

    let result = eval_program(
        "(cond ((quote ()) (quote no)) ((quote t) (quote yes)))",
        &mut session,
    )
    .expect("Core2 two-part cond");

    assert_eq!(result.value, Value::Symbol("yes".into()));
}

#[test]
fn core2_two_part_cond_short_circuits() {
    let mut session = core2_session();

    let result = eval_program(
        "(cond ((quote t) (quote yes)) ((car (quote ())) (quote unreachable)))",
        &mut session,
    )
    .expect("later clause must remain unevaluated");

    assert_eq!(result.value, Value::Symbol("yes".into()));
}

#[test]
fn core2_exhaustion_returns_nil() {
    let mut session = core2_session();

    let result = eval_program(
        "(cond ((quote ()) (quote no)))",
        &mut session,
    )
    .expect("historical Core2 exhaustion returns nil");

    assert_eq!(result.value, Value::Nil);
}

#[test]
fn core2_rejects_core4_three_part_clause_shape() {
    let mut session = core2_session();

    let error = eval_program(
        "(cond ((quote t) t (quote yes)))",
        &mut session,
    )
    .expect_err("Core2 must not silently import Core4 three-part COND");

    assert_eq!(error.kind, ErrorKind::InvalidForm);
}

#[test]
fn core2_library_projects_structural_results_back_to_t_nil() {
    let mut session = core2_session();

    assert_eq!(
        eval_program("(core2-atom (quote radio))", &mut session)
            .expect("core2 atom symbol")
            .value,
        Value::Symbol("t".into())
    );
    assert_eq!(
        eval_program("(core2-atom (quote (radio antenna)))", &mut session)
            .expect("core2 atom pair")
            .value,
        Value::Nil
    );
    assert_eq!(
        eval_program("(core2-eq (quote radio) (quote radio))", &mut session)
            .expect("core2 eq same")
            .value,
        Value::Symbol("t".into())
    );
    assert_eq!(
        eval_program("(core2-truthy? 0)", &mut session)
            .expect("zero remains truthy in Contract 6")
            .value,
        Value::Symbol("t".into())
    );
}

#[test]
fn loading_core4_after_core2_restores_current_cond_profile() {
    let mut session = core2_session();

    eval_program("(cond ((quote t) t (quote yes)))", &mut session)
        .expect_err("Core2 must reject Core4 three-part COND before profile switch");

    load_core_library(&mut session).expect("Core4 loader must select current COND mode");

    let result = eval_program(
        "(cond ((quote t) t (quote yes)))",
        &mut session,
    )
    .expect("Core4 three-part COND must work after profile switch");

    assert_eq!(result.value, Value::Symbol("yes".into()));
}
