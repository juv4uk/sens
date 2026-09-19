use std::collections::HashSet;
use std::path::Path;

#[test]
fn i5_6400_profile_projects_existing_semantic_identities() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let profile_path = root.join("lib/machine/intel-core-i5-6400.lisp");
    let profile = std::fs::read_to_string(&profile_path)
        .unwrap_or_else(|error| panic!("missing i5-6400 machine profile at {profile_path:?}: {error}"));

    my_lisp::parse(&profile).expect("i5-6400 machine profile must be valid my-lisp data");
    assert!(profile.contains("(machine-profile/1"));
    assert!(profile.contains("(cpu intel-core-i5-6400)"));
    assert!(profile.contains("(microarchitecture skylake)"));
    assert!(profile.contains("(isa x86-64)"));

    for (semantic_id, expected_machine_path) in [
        ("00000010", "tag-test"),
        ("00000011", "CMP/SETE"),
        ("00000101", "LOAD-pair-head"),
        ("00000110", "LOAD-pair-tail"),
        ("00001100", "ADD"),
        ("00001101", "SUB/NEG"),
        ("00001110", "IMUL"),
        ("00010011", "IDIV-remainder"),
        ("00010100", "IDIV-quotient"),
        ("00011010", "CMP/SETL"),
        ("00011011", "CMP/SETG"),
        ("00011100", "CMP/SETE"),
        ("01010001", "LOAD-vector-length"),
        ("01010010", "LOAD-vector-element"),
        ("01010011", "STORE-vector-element"),
        ("01010111", "LOAD-buffer-length"),
        ("01011000", "LOAD-buffer-element"),
    ] {
        let row_prefix = format!("(\"{semantic_id}\" ");
        let row = profile
            .lines()
            .map(str::trim_start)
            .find(|line| line.starts_with(&row_prefix))
            .unwrap_or_else(|| panic!("i5-6400 profile missing byte SID {semantic_id}"));
        assert!(
            row.contains(expected_machine_path),
            "byte SID {semantic_id} must advertise {expected_machine_path:?}; row: {row}"
        );
    }
}

#[test]
fn every_i5_6400_row_is_a_unique_existing_semantic_identity() {
    let profile = include_str!("../../../lib/machine/intel-core-i5-6400.lisp");
    let registry = include_str!("../../../lib/surface/semantic-registry.lisp");
    let mut seen = HashSet::new();
    let mut projected = 0usize;

    for line in profile.lines().map(str::trim_start) {
        let Some(rest) = line.strip_prefix("(\"") else {
            continue;
        };
        let Some((id, after_id)) = rest.split_once("\" ") else {
            continue;
        };
        if id.len() != 8 || !id.bytes().all(|byte| matches!(byte, b'0' | b'1')) {
            continue;
        }
        assert!(!after_id.is_empty(), "machine row must continue after SID");

        projected += 1;
        assert!(
            seen.insert(id),
            "i5-6400 projection must not contain duplicate byte SID {id}"
        );
        let registry_prefix = format!("  (\"{id}\" ");
        assert!(
            registry.lines().any(|row| row.starts_with(&registry_prefix)),
            "i5-6400 projection may only reference semantic-registry identities; unknown ID {id}"
        );
    }

    assert!(projected >= 50, "processor profile should cover a meaningful existing subset");
}

#[test]
fn generated_function_table_has_i5_6400_column_without_replacing_semantic_authority() {
    let markdown = include_str!("../../../docs/generated/function-table.md");
    assert!(
        markdown.contains("Intel Core i5-6400 / Skylake"),
        "human function table must expose the requested processor column"
    );
    assert!(
        markdown.contains("| `00001100` | додати | додати | stable | — | yoga | stable | ADD"),
        "byte SID 0104 must show the i5-6400 ADD fast path"
    );
    assert!(
        markdown.contains("| `00000101` | перше | перше | stable | car | ādi | stable | LOAD-pair-head"),
        "Canon CAR identity must show its direct memory-load realization"
    );

    let semantic_table = include_str!("../../../lib/generated/function-table.lisp");
    assert!(
        !semantic_table.contains("intel-core-i5-6400"),
        "processor-specific realization must not contaminate the semantic machine-readable function table"
    );
}

#[test]
fn function_table_generator_with_machine_projection_is_valid_lisp() {
    let source = include_str!("../../../scripts/generate-function-table.lisp");
    my_lisp::parse(source).expect("function-table generator must remain valid my-lisp source");
}
