use std::path::PathBuf;
use std::fs;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

#[test]
fn cons_pair_layout_is_machine_readable_before_native_lowering() {
    let path = repo_root().join("memory-layout-contract.lisp");
    let source = fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("{} must exist: {error}", path.display()));

    for required in [
        "(cons . ((storage . heap)",
        "(pointer-bits . 48)",
        "(cell-size-bytes . 16)",
        "(car-offset-bytes . 0)",
        "(cdr-offset-bytes . 8)",
        "(field-width-bits . 64)",
    ] {
        assert!(
            source.contains(required),
            "pair representation contract must state {required} before CAR/CDR/CONS native lowering"
        );
    }
}
