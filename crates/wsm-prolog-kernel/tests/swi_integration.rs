use std::path::PathBuf;
use wsm_prolog_kernel::{PrologKernel, PrologQuery};

fn swipl_available() -> bool { PrologKernel::default().version().is_ok() }

fn fixture() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("tests/fixtures/family.pl")
}

#[test]
fn real_swi_zero_one_many_recursive_and_duplicate_answers() {
    if !swipl_available() {
        eprintln!("SKIP: swipl is not installed on this machine");
        return;
    }

    let kernel = PrologKernel::default();

    let zero = kernel.query(fixture(), &PrologQuery::new("parent(nobody, X)", "X")).unwrap();
    assert_eq!(String::from_utf8_lossy(&zero.stdout).trim(), "[]");

    let one = kernel.query(fixture(), &PrologQuery::new("parent(bob, X)", "X")).unwrap();
    assert_eq!(String::from_utf8_lossy(&one.stdout).trim(), "[carol]");

    let many = kernel.query(fixture(), &PrologQuery::new("parent(alice, X)", "X")).unwrap();
    assert_eq!(String::from_utf8_lossy(&many.stdout).trim(), "[bob,dave]");

    let recursive = kernel.query(fixture(), &PrologQuery::new("ancestor(alice, X)", "X")).unwrap();
    assert_eq!(String::from_utf8_lossy(&recursive.stdout).trim(), "[bob,dave,carol]");

    let duplicate = kernel.query(fixture(), &PrologQuery::new("duplicate_path(X)", "X")).unwrap();
    assert_eq!(String::from_utf8_lossy(&duplicate.stdout).trim(), "[alice,alice]");
}
