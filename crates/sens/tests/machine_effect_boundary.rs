use std::fs;
use std::path::PathBuf;

fn repo_file(path: &str) -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .join(path)
}

fn read(path: &str) -> String {
    fs::read_to_string(repo_file(path))
        .unwrap_or_else(|error| panic!("#4342 requires {path}: {error}"))
}

#[test]
fn machine_effect_layer_is_explicitly_target_neutral_and_nonsemantic() {
    let boundary = read("lib/machine/effect-boundary.lisp");

    for fact in [
        "(role target-neutral-machine-mechanism)",
        "(semantic-authority upstream-only)",
        "(machine-effect-semantic-authority forbidden)",
        "(canonical-machine-effect target-neutral)",
        "(global-machine-opcode-enum forbidden)",
        "(semantic-id-from-machine-effect forbidden)",
        "(semantic-id-from-target-projection forbidden)",
        "(projection-direction machine-effect-to-target)",
        "(reverse-projection-authority forbidden)",
        "(target-projection-admission fail-closed)",
        "(target-projection-rejection named)",
        "(semantic-observable-preserved required)",
        "(diagnostic machine-effect-boundary-violation)",
    ] {
        assert!(boundary.contains(fact), "#4342 boundary missing fact: {fact}");
    }
}

#[test]
fn target_specific_identity_does_not_leak_into_the_effect_contract() {
    let boundary = read("lib/machine/effect-boundary.lisp").to_ascii_lowercase();

    for forbidden in [
        "x86-",
        "rax",
        "rcx",
        "modrm",
        "vex",
        "avx",
        "cuda",
        "ptx",
        "fpga",
    ] {
        assert!(
            !boundary.contains(forbidden),
            "#4342 target-neutral boundary leaked target-specific token: {forbidden}"
        );
    }
}

#[test]
fn lowering_boundary_names_machine_effect_as_a_required_intermediate_stage() {
    let lowering = read("machine-lowering-boundary.lisp");

    for fact in [
        "(canonical-machine-effect-layer lib/machine/effect-boundary.lisp)",
        "(lowering-stage semantic-to-machine-effect required)",
        "(lowering-stage machine-effect-to-target-projection required)",
        "(target-specific-data-before-machine-effect forbidden)",
        "(machine-effect-semantic-authority forbidden)",
    ] {
        assert!(lowering.contains(fact), "#4342 lowering seam missing fact: {fact}");
    }

    assert!(
        lowering.contains("(lowering-direction semantic-to-machine)"),
        "#4342 refines the existing one-way law; it must not delete it"
    );
}
