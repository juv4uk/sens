use sens::{eval_program, load_core_library, Session};
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
    load_core_library(&mut session).expect("core must bootstrap before machine block round-trip");
    load_lisp_file("lib/machine/block.lisp", &mut session);
    load_lisp_file("lib/machine/encoding/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/operands/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/admission/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/atoms/x86-64.lisp", &mut session);
    session
}

fn eval_value(source: &str, session: &mut Session) -> String {
    eval_program(source, session)
        .unwrap_or_else(|error| panic!("machine expression failed: {source}: {error}"))
        .value
        .to_string()
}

fn parse_byte_list(rendered: &str) -> Vec<u8> {
    rendered
        .trim_start_matches('(')
        .trim_end_matches(')')
        .split_whitespace()
        .map(|token| token.parse().expect("encoded machine byte must fit u8"))
        .collect()
}

fn render_forms(forms: &[String]) -> String {
    format!("({})", forms.join(" "))
}

#[test]
fn composed_machine_block_round_trips_through_independent_decoder() {
    let mut session = machine_session();
    let block = eval_value(
        "(machine-block-append (machine-block-append (machine-block-append (machine-block-one (x86-mov-r64-imm64 (quote rax) 2)) (x86-mov-r64-imm64 (quote rcx) 3)) (x86-add-r64-r64 (quote rax) (quote rcx))) (x86-ret))",
        &mut session,
    );
    let encoded = eval_value(
        &format!("(x86-encode-machine-block (quote {block}))"),
        &mut session,
    );
    let bytes = parse_byte_list(&encoded);

    let decoded = x86_64_block_decoder::decode_machine_block(&bytes)
        .unwrap_or_else(|error| panic!("independent decoder rejected {bytes:?}: {error}"));

    assert_eq!(
        render_forms(&decoded),
        block,
        "decoder must reconstruct the exact Lisp-owned machine forms, not merely accept the byte stream"
    );
}

#[test]
fn independent_decoder_fails_closed_on_truncated_machine_block() {
    let mut session = machine_session();
    let encoded = eval_value(
        "(x86-encode-machine-block (machine-block-one (x86-mov-r64-imm64 (quote rax) 42)))",
        &mut session,
    );
    let mut bytes = parse_byte_list(&encoded);
    bytes.pop();

    assert!(
        x86_64_block_decoder::decode_machine_block(&bytes).is_err(),
        "truncated machine bytes must not be normalized into a different valid form"
    );
}
