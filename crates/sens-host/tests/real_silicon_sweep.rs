#![cfg(all(target_os = "linux", target_arch = "x86_64"))]

use sens::{eval_program, load_core_library, Session};
use sens_host::install;
use std::env;
use std::fs;
use std::path::PathBuf;

#[derive(Debug)]
struct SiliconRow<'a> {
    id: &'a str,
    families: &'a str,
    expression: &'a str,
    expected: &'a str,
    observed: String,
}

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

fn eval_value(source: &str, session: &mut Session) -> String {
    eval_program(source, session)
        .unwrap_or_else(|error| panic!("real-silicon expression failed: {source}: {error}"))
        .value
        .to_string()
}

fn cpuinfo_field(name: &str) -> String {
    let cpuinfo = fs::read_to_string("/proc/cpuinfo")
        .expect("owner real-silicon lane requires readable /proc/cpuinfo");
    cpuinfo
        .lines()
        .filter_map(|line| line.split_once(':'))
        .find_map(|(key, value)| (key.trim() == name).then(|| value.trim().to_owned()))
        .unwrap_or_else(|| format!("missing-{name}"))
}

fn json_escape(value: &str) -> String {
    let mut out = String::with_capacity(value.len());
    for ch in value.chars() {
        match ch {
            '\\' => out.push_str("\\\\"),
            '"' => out.push_str("\\\""),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if c.is_control() => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out
}

fn write_artifact(cpu_model: &str, cpu_flags: &str, rows: &[SiliconRow<'_>]) {
    let sha = env::var("GITHUB_SHA").unwrap_or_else(|_| "local".to_owned());
    let path = env::var("SENS_REAL_SILICON_ARTIFACT")
        .map(PathBuf::from)
        .unwrap_or_else(|_| repo_root().join("target/real-silicon-sweep.json"));

    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent)
            .unwrap_or_else(|error| panic!("cannot create {}: {error}", parent.display()));
    }

    let mut json = String::new();
    json.push_str("{\n");
    json.push_str("  \"schema\": \"sens-real-silicon-sweep-v1\",\n");
    json.push_str(&format!("  \"sens_commit\": \"{}\",\n", json_escape(&sha)));
    json.push_str("  \"target\": \"x86_64-linux-owner-self-hosted\",\n");
    json.push_str(&format!(
        "  \"cpu_model\": \"{}\",\n",
        json_escape(cpu_model)
    ));
    json.push_str(&format!(
        "  \"cpu_flags\": \"{}\",\n",
        json_escape(cpu_flags)
    ));
    json.push_str("  \"classification\": \"execute-safe\",\n");
    json.push_str(
        "  \"admission_boundary\": \"lib/machine/admission/x86-64.lisp:x86-call-admitted-u64\",\n",
    );
    json.push_str(
        "  \"independent_decode_evidence\": \"crates/sens/tests/x86_64_lisp_encoder.rs\",\n",
    );
    json.push_str(
        "  \"negative_control\": \"UD2 rejected as unadmitted before host execution\",\n",
    );
    json.push_str("  \"rows\": [\n");

    for (index, row) in rows.iter().enumerate() {
        json.push_str("    {");
        json.push_str(&format!(
            "\"id\":\"{}\",\"families\":\"{}\",\"expression\":\"{}\",\"expected\":\"{}\",\"observed\":\"{}\",\"status\":\"pass\"",
            json_escape(row.id),
            json_escape(row.families),
            json_escape(row.expression),
            json_escape(row.expected),
            json_escape(&row.observed),
        ));
        json.push('}');
        if index + 1 != rows.len() {
            json.push(',');
        }
        json.push('\n');
    }

    json.push_str("  ]\n}\n");
    fs::write(&path, json)
        .unwrap_or_else(|error| panic!("cannot write {}: {error}", path.display()));

    println!("real-silicon artifact: {}", path.display());
}

#[test]
fn owner_i5_6400_executes_admitted_safe_slices_and_emits_evidence() {
    install();

    let cpu_model = cpuinfo_field("model name");
    let cpu_flags = cpuinfo_field("flags");
    assert!(
        cpu_model.to_ascii_lowercase().contains("i5-6400"),
        "this P0 witness must run on the owner Intel Core i5-6400, got: {cpu_model}"
    );

    let mut session = Session::default();
    load_core_library(&mut session).expect("core must bootstrap before real-silicon witness");
    load_lisp_file("lib/machine/layout/pair-x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/encoding/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/admission/x86-64.lisp", &mut session);
    load_lisp_file("lib/machine/lowering/semantic-x86-64.lisp", &mut session);

    let cases = [
        (
            "mov-imm-ret",
            "MOV r64,imm64 + RET",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 42) (ret))) 0)",
            "42",
        ),
        (
            "mov-reg-ret",
            "MOV r64,imm64 + MOV r64,r64 + RET",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rcx 73) (mov-r64-r64 rax rcx) (ret))) 0)",
            "73",
        ),
        (
            "add-reg",
            "MOV + ADD r64,r64 + RET",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 10) (mov-r64-imm64 rcx 3) (add-r64-r64 rax rcx) (ret))) 0)",
            "13",
        ),
        (
            "sub-reg",
            "MOV + SUB r64,r64 + RET",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 10) (mov-r64-imm64 rcx 3) (sub-r64-r64 rax rcx) (ret))) 0)",
            "7",
        ),
        (
            "and-reg",
            "MOV + AND r64,r64 + RET",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 10) (mov-r64-imm64 rcx 12) (and-r64-r64 rax rcx) (ret))) 0)",
            "8",
        ),
        (
            "or-reg",
            "MOV + OR r64,r64 + RET",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 10) (mov-r64-imm64 rcx 12) (or-r64-r64 rax rcx) (ret))) 0)",
            "14",
        ),
        (
            "xor-reg",
            "MOV + XOR r64,r64 + RET",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 10) (mov-r64-imm64 rcx 12) (xor-r64-r64 rax rcx) (ret))) 0)",
            "6",
        ),
        (
            "inc-reg",
            "MOV + INC r64 + RET",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 41) (inc-r64 rax) (ret))) 0)",
            "42",
        ),
        (
            "dec-reg",
            "MOV + DEC r64 + RET",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 43) (dec-r64 rax) (ret))) 0)",
            "42",
        ),
        (
            "not-reg-masked",
            "MOV + NOT r64 + AND mask + RET",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 0) (not-r64 rax) (mov-r64-imm64 rcx 255) (and-r64-r64 rax rcx) (ret))) 0)",
            "255",
        ),
        (
            "neg-reg-balanced",
            "MOV + NEG r64 + ADD balance + RET",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 5) (neg-r64 rax) (mov-r64-imm64 rcx 5) (add-r64-r64 rax rcx) (ret))) 0)",
            "0",
        ),
        (
            "shl-imm",
            "MOV + SHL r64,imm8 + RET",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 3) (shl-r64-imm8 rax 4) (ret))) 0)",
            "48",
        ),
        (
            "shr-imm",
            "MOV + SHR r64,imm8 + RET",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 128) (shr-r64-imm8 rax 3) (ret))) 0)",
            "16",
        ),
        (
            "sar-imm-signed",
            "MOV + NEG + SAR r64,imm8 + NEG + RET",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 16) (neg-r64 rax) (sar-r64-imm8 rax 2) (neg-r64 rax) (ret))) 0)",
            "4",
        ),
        (
            "rol-imm",
            "MOV + ROL r64,imm8 + RET",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 1) (rol-r64-imm8 rax 8) (ret))) 0)",
            "256",
        ),
        (
            "ror-imm",
            "MOV + ROR r64,imm8 + RET",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 256) (ror-r64-imm8 rax 8) (ret))) 0)",
            "1",
        ),
        (
            "bswap-reg",
            "MOV + BSWAP r64 + SHR normalize + RET",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 1) (bswap-r64 rax) (shr-r64-imm8 rax 56) (ret))) 0)",
            "1",
        ),
        (
            "xchg-reg",
            "MOV pair + XCHG r64,r64 + RET",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 11) (mov-r64-imm64 rcx 29) (xchg-r64-r64 rax rcx) (ret))) 0)",
            "29",
        ),
        (
            "setz-movzx",
            "MOV pair + CMP + SETZ r8 + MOVZX r64,r8 + RET",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 5) (mov-r64-imm64 rcx 5) (cmp-r64-r64 rax rcx) (setz-r8 rax) (movzx-r64-r8 rax rax) (ret))) 0)",
            "1",
        ),
        (
            "cmp-jnz-equal",
            "MOV + CMP + JNZ rel8 + RET",
            "(x86-call-admitted-u64 (x86-lower-eq-cond-u64-forms 5 5 111 222) 0)",
            "111",
        ),
        (
            "cmp-jnz-distinct",
            "MOV + CMP + JNZ rel8 + RET",
            "(x86-call-admitted-u64 (x86-lower-eq-cond-u64-forms 5 6 111 222) 0)",
            "222",
        ),
        (
            "pair-store-load-car",
            "bounded STORE pair + LOAD head + RET",
            "(x86-call-admitted-u64 (x86-lower-cons-car-u64-forms 2 3) x86-pair-cell-bytes)",
            "2",
        ),
        (
            "pair-store-load-cdr",
            "bounded STORE pair + LOAD tail + RET",
            "(x86-call-admitted-u64 (x86-lower-cons-cdr-u64-forms 2 3) x86-pair-cell-bytes)",
            "3",
        ),
    ];

    let mut rows = Vec::with_capacity(cases.len());
    for (id, families, expression, expected) in cases {
        let observed = eval_value(expression, &mut session);
        assert_eq!(
            observed, expected,
            "owner silicon mismatch for {id}: expected {expected}, observed {observed}"
        );
        rows.push(SiliconRow {
            id,
            families,
            expression,
            expected,
            observed,
        });
    }

    let rejected = eval_value(
        "(x86-call-admitted-u64 (quote ((ud2))) 0)",
        &mut session,
    );
    assert_eq!(
        rejected,
        "(rejected unadmitted-machine-form (ud2))",
        "unsafe/unadmitted control must fail closed before host execution"
    );

    write_artifact(&cpu_model, &cpu_flags, &rows);
}
