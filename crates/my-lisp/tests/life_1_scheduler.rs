use std::fs;
use std::path::PathBuf;

use my_lisp::{eval_program, load_core_library, Session};

fn repo_file(relative: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..").join(relative)
}

#[test]
fn life_1_scheduler_witness_is_lisp_owned() {
    let source = fs::read_to_string(repo_file("tests/fixtures/life-1-scheduler-witness.lisp"))
        .expect("#801 scheduler witness must be readable");
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library");
    let result = eval_program(&source, &mut session).expect("#801 scheduler witness must execute");

    assert_eq!(
        result.value.to_string(),
        "(life-1-scheduler-witness (status pass) (detail deduplicated-activation-and-quiescence))"
    );
}
