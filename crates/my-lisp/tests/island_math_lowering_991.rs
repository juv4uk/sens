use std::fs;
use std::path::Path;

#[test]
fn shared_math_lowering_contract_is_fail_closed_until_ratified() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let contract = fs::read_to_string(root.join("contracts/island-math-lowering-991.lisp"))
        .expect("read #991 lowering contract");
    let profile = fs::read_to_string(root.join("lib/machine/intel-core-i5-6400.lisp"))
        .expect("read i5-6400 machine profile");

    for required in [
        "(ratification-authority \"#990\")",
        "(ratification-candidate \"#1039\")",
        "(capability-evidence \"#988/#993\")",
        "(execution-evidence \"#992\")",
        "(machine-profile \"lib/machine/intel-core-i5-6400.lisp\")",
        "(lowering-direction semantic-to-machine)",
        "(reverse-authority forbidden)",
        "(semantic-id-from-isa forbidden)",
        "(unratified-operation-policy reject)",
        "(missing-machine-row-policy not-yet-lowered)",
    ] {
        assert!(contract.contains(required), "missing #991 boundary fact: {required}");
    }

    let admitted_candidates = [
        ("00001100", "+"),
        ("00001101", "-"),
        ("00001110", "*"),
        ("00010000", "abs"),
        ("00010001", "min"),
        ("00010010", "max"),
    ];

    for (sid, operation) in admitted_candidates {
        assert!(
            contract.contains(&format!("(semantic-id \"{sid}\")")),
            "missing #1039 candidate SID {sid} ({operation})"
        );
        assert!(
            profile.contains(&format!("(\"{sid}\" ")),
            "candidate SID {sid} ({operation}) has no existing i5-6400 machine-profile row"
        );
    }

    assert_eq!(
        contract.matches("(ratification-status candidate-pending-990-merge)").count(),
        6,
        "all six #1039 candidate rows must remain explicitly pending until #990 lands"
    );
    assert!(
        !contract.contains("(ratification-status ratified)"),
        "#991 must not promote #1039 candidate evidence before #990 lands"
    );

    for excluded_sid in ["00001111", "00010011", "00010100", "00010101"] {
        assert!(
            !contract.contains(&format!("(semantic-id \"{excluded_sid}\")")),
            "non-shared #990 candidate {excluded_sid} must not become a lowering row"
        );
    }
}

#[test]
fn machine_profile_is_projection_not_semantic_authority() {
    let root = Path::new(env!("CARGO_MANIFEST_DIR")).join("../..");
    let profile = fs::read_to_string(root.join("lib/machine/intel-core-i5-6400.lisp"))
        .expect("read i5-6400 machine profile");
    let boundary = fs::read_to_string(root.join("machine-lowering-boundary.lisp"))
        .expect("read machine lowering boundary");

    assert!(profile.contains("This file is NOT a semantic registry"));
    assert!(boundary.contains("(semantic-id-from-isa forbidden)"));
    assert!(boundary.contains("(lowering-direction semantic-to-machine)"));
}
