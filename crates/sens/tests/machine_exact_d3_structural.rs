use sens::{eval_program, load_core_library, lower_program, parse, ExprKind, Session};
use std::fs;
use std::path::PathBuf;

#[path = "support/x86_64_block_decoder.rs"]
mod x86_64_block_decoder;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn load_lisp_file(path: &str, session: &mut Session) {
    let path = repo_root().join(path);
    let source = fs::read_to_string(&path)
        .unwrap_or_else(|error| panic!("{} must exist: {error}", path.display()));
    eval_program(&source, session)
        .unwrap_or_else(|error| panic!("{} must load as ordinary sens: {error}", path.display()));
}

fn machine_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core");
    load_lisp_file("lib/machine/block.lisp", &mut session);
    load_lisp_file("lib/machine/layout/pair-x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/encoding/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/operands/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/admission/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/atoms/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/lowering/semantic-x86-64.lisp", &mut session);
    session
}

fn eval_value(source: &str, session: &mut Session) -> String {
    eval_program(source, session)
        .unwrap_or_else(|error| panic!("{source}: {error}"))
        .value
        .to_string()
}

fn parse_bytes(rendered: &str) -> Vec<u8> {
    rendered
        .trim_start_matches('(')
        .trim_end_matches(')')
        .split_whitespace()
        .filter(|token| !token.is_empty())
        .map(|token| token.parse::<u8>().expect("machine byte"))
        .collect()
}

fn render_decoded(forms: &[x86_64_block_decoder::DecodedMachineForm]) -> String {
    format!(
        "({})",
        forms
            .iter()
            .map(x86_64_block_decoder::DecodedMachineForm::render)
            .collect::<Vec<_>>()
            .join(" ")
    )
}

#[test]
fn current_structural_surfaces_lower_to_exact_d3_identities() {
    for (source, bits) in [
        ("(сполучити 2 3)", 0b111u8),
        ("(перше '(2 . 3))", 0b100),
        ("(решта '(2 . 3))", 0b011),
    ] {
        let parsed = parse(source).unwrap_or_else(|error| panic!("{source}: {error}"));
        let lowered = lower_program(&parsed);
        let ExprKind::DomainCall(identity, _) = lowered[0].kind else {
            panic!("{source} must lower to exact DomainCall");
        };
        assert_eq!(identity.width(), 3, "{source}");
        assert_eq!(identity.packed_bits(), bits, "{source}");
    }
}

#[test]
fn exact_d3_structural_identities_select_existing_bounded_x86_forms() {
    let mut session = machine_session();

    for (identity, expected_forms) in [
        (
            "111",
            "((mov-r64-imm64 rax 2) (mov-mem-disp8-r64 rdi 0 rax) (mov-r64-imm64 rax 3) (mov-mem-disp8-r64 rdi 8 rax))",
        ),
        (
            "100",
            "((mov-r64-imm64 rax 2) (mov-mem-disp8-r64 rdi 0 rax) (mov-r64-imm64 rax 3) (mov-mem-disp8-r64 rdi 8 rax) (mov-r64-mem-disp8 rax rdi 0) (ret))",
        ),
        (
            "011",
            "((mov-r64-imm64 rax 2) (mov-mem-disp8-r64 rdi 0 rax) (mov-r64-imm64 rax 3) (mov-mem-disp8-r64 rdi 8 rax) (mov-r64-mem-disp8 rax rdi 8) (ret))",
        ),
    ] {
        let forms = eval_value(
            &format!("(x86-lower-current-structural-u64-forms {identity} 2 3)"),
            &mut session,
        );
        assert_eq!(forms, expected_forms, "D3:{identity}");

        let encoded = eval_value(
            &format!("(x86-encode-current-structural-u64 {identity} 2 3)"),
            &mut session,
        );
        assert!(
            encoded.starts_with('(') && !encoded.contains("rejected"),
            "D3:{identity} must reach admitted x86 bytes, got {encoded}"
        );

        let bytes = parse_bytes(&encoded);
        let decoded = x86_64_block_decoder::decode_machine_block(&bytes)
            .unwrap_or_else(|error| panic!("D3:{identity} bytes rejected by independent decoder: {error}"));
        assert_eq!(render_decoded(&decoded), forms, "D3:{identity}");
    }
}

#[test]
fn unsupported_exact_domain_identity_fails_closed() {
    let mut session = machine_session();
    let result = eval_value(
        "(x86-encode-current-structural-u64 101 2 3)",
        &mut session,
    );
    assert_eq!(result, "unsupported-current-domain-structural-u64");
}
