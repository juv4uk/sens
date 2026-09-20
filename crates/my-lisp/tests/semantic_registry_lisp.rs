use my_lisp::{eval_program, Session};

#[test]
fn semantic_registry_is_read_and_queried_by_lisp_itself() {
    let mut session = Session::default();

    eval_program(include_str!("../../../lib/core.lisp"), &mut session)
        .expect("core library should load");
    eval_program(
        include_str!("../../../lib/surface/semantic-registry-api.lisp"),
        &mut session,
    )
    .expect("Lisp-owned semantic registry API should load");
    eval_program(
        include_str!("../../../tests/fixtures/semantic-registry-self-hosted-witness.lisp"),
        &mut session,
    )
    .expect("Lisp-owned semantic registry witness should load");

    let result = eval_program(
        "(semantic-registry-self-hosted-witness)",
        &mut session,
    )
    .expect("Lisp-owned semantic registry witness should evaluate")
    .value
    .to_string();

    assert_eq!(
        result,
        r#"((binary 8) 170 "00000001" quote "00000001" "10101000" "00000101" "11111111" () "10101000" (structural-relation same))"#
    );
}
