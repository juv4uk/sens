use my_lisp::{eval_program, load_core_library, load_fs_library, Session};
use my_lisp_host::install;

#[test]
fn semantic_registry_is_read_and_queried_by_lisp_itself() {
    install();
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library should load");
    load_fs_library(&mut session).expect("Lisp-owned file layer should load");
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

    let source = include_str!("../../../lib/surface/semantic-registry.lisp");
    let escaped = source
        .replace('\\', "\\\\")
        .replace('"', "\\"");
    let program = format!("(semantic-registry-self-hosted-witness \"{escaped}\")");
    let result = eval_program(
        &program,
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
