//! Current-side semantic witness for the historical machine-block migration.
//!
//! The physical .sens is the program under test. Historical expectations are
//! read from the independent Python oracle in tests/test_machine_block_historical_oracle.py.
//! No expected machine-block semantics are duplicated in this Rust test.

use sens::{decode_ternary_program, eval_parsed_expressions, eval_program, open_ternary_program, parse_canonical_binary, Session, Value};
use serde_json::{json, Value as JsonValue};
use std::{env, fs, process::Command};

const SOURCE: &str = include_str!("../../../lib/machine/block.lisp");
const T5: &[u8] = include_bytes!("../../../lib/machine/block.sens");
const SOURCE_GIT_BLOB: &str = "200201b741787c4e144ad4194848acf51d7b439e";

fn sha256_hex(bytes: &[u8]) -> String {
    sens::sha256_source(bytes).iter().map(|byte| format!("{byte:02x}")).collect()
}

/// Same owner-reviewed digest law as scripts/sens_t5_codec.py typed_sha256:
/// byte(width) || unsigned packed value encoded in ceil(width / 8) big-endian bytes.
fn typed_sha256(words: &[sens::BinarySourceWord]) -> String {
    let mut typed_bytes = Vec::new();
    for word in words {
        let width = word.width() as usize;
        typed_bytes.push(width as u8);
        let packed = (word.packed_bits() as u16).to_be_bytes();
        let count = (width + 7) / 8;
        typed_bytes.extend_from_slice(&packed[2 - count..]);
    }
    sha256_hex(&typed_bytes)
}

fn json_value(value: &Value) -> JsonValue {
    match value {
        Value::Nil => JsonValue::Array(Vec::new()),
        Value::Symbol(name) => JsonValue::String(name.to_string()),
        Value::String(text) => JsonValue::String(text.to_string()),
        Value::Pair(_, _) => {
            let mut items = Vec::new();
            let mut cursor = value;
            loop {
                match cursor {
                    Value::Pair(head, tail) => {
                        items.push(json_value(head.as_ref()));
                        cursor = tail.as_ref();
                    }
                    Value::Nil => return JsonValue::Array(items),
                    other => {
                        return json!({"improper_pair": json_value(other)});
                    }
                }
            }
        }
        other => JsonValue::String(other.to_string()),
    }
}

fn load_block() -> Session {
    let visible = open_ternary_program(T5).expect("physical T5 must pass current D2 reader");
    let forms = parse_canonical_binary(&visible).expect("physical T5 must parse as current SENS");
    let mut session = Session::default();
    eval_parsed_expressions(&forms, &mut session)
        .expect("physical block definitions must load into observer session");
    session
}

fn observe(session: &mut Session, source: &str) -> JsonValue {
    eval_program(source, session)
        .unwrap_or_else(|error| panic!("current SENS observer call failed: {source}: {error}"))
        .value
        .pipe(|value| json_value(&value))
}

trait Pipe: Sized {
    fn pipe<T>(self, f: impl FnOnce(Self) -> T) -> T { f(self) }
}
impl<T> Pipe for T {}

fn historical_oracle_report() -> serde_json::Value {
    let path = env::temp_dir().join(format!("sens-machine-block-historical-{}.json", std::process::id()));
    let run = Command::new("python3")
        .args(["tests/test_machine_block_historical_oracle.py", "--emit-json", path.to_str().expect("utf-8 temp path")])
        .output()
        .expect("python3 historical oracle must be available");
    assert!(run.status.success(), "historical oracle failed: {}", String::from_utf8_lossy(&run.stderr));
    let report = serde_json::from_slice(&fs::read(&path).expect("historical oracle JSON"))
        .expect("historical oracle emits JSON");
    let _ = fs::remove_file(path);
    report
}

#[test]
fn current_machine_block_matches_historical_oracle() {
    assert_eq!(sens::sha256_source(SOURCE.as_bytes()), "84e1a10f5ed21eaec1c9704e88cbf7ebd49db3b3edf5041c913fa020fe7631de");
    let words = decode_ternary_program(T5).expect("canonical physical T5");
    assert_eq!(words.len(), 273);
    assert_eq!(open_ternary_program(T5).expect("T5 opens"),
        sens::open_ternary_program(T5).expect("stable current opener"));

    let historical = historical_oracle_report();
    assert_eq!(historical["source_git_blob_sha1"], SOURCE_GIT_BLOB);
    assert_eq!(historical["case_count"], 9);
    assert_eq!(historical["status"], "HISTORICAL_SIDE_ONLY");
    assert_eq!(historical["current_sens_semantic_parity"], "NOT_VERIFIED");

    let mut session = load_block();
    let cases = [
        ("empty", "(machine-block-empty)"),
        ("one_nested", "(machine-block-one (quote (mov (r1 r2))))"),
        ("append", "(machine-block-append (quote ((mov (r1 r2)) (branch L1))) (quote ret))"),
        ("concat", "(machine-block-concat (quote ((mov (r1 r2)) (branch L1))) (quote ((label L2))))"),
        ("forms", "(machine-block-forms (quote ((mov (r1 r2)) (branch L1))))"),
        ("identity", "(machine-block (quote ((mov (r1 r2)) (branch L1))))"),
        ("append_empty", "(machine-block-append (quote ()) (quote nop))"),
        ("concat_left_empty", "(machine-block-concat (quote ()) (quote ((mov (r1 r2)) (branch L1))))"),
        ("concat_right_empty", "(machine-block-concat (quote ((mov (r1 r2)) (branch L1))) (quote ()))"),
    ];
    let mut observed = serde_json::Map::new();
    for (name, source) in cases {
        observed.insert(name.to_string(), observe(&mut session, source));
    }
    assert_eq!(JsonValue::Object(observed), historical["cases"]);
}

#[test]
fn block_physical_transport_has_stable_proof_digests() {
    let physical = sha256_hex(T5);
    assert_eq!(physical, "1540c7e9a69c7dcb953713469a2c6ac803ae5aebfc40e2cd1ab529e66f0271");
    let words = decode_ternary_program(T5).expect("canonical physical T5");
    assert_eq!(typed_sha256(&words), "0951a7c253644c5783e7317269e354959817932e2bf9016114760fc76f769922");
}
