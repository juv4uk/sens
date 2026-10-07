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
    classification: &'a str,
    feature_gate: &'a str,
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

fn cpu_has_flag(flags: &str, flag: &str) -> bool {
    flags.split_whitespace().any(|candidate| candidate == flag)
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
    json.push_str("  \"classification_policy\": \"per-row\",\n");
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
            "\"id\":\"{}\",\"families\":\"{}\",\"expression\":\"{}\",\"expected\":\"{}\",\"observed\":\"{}\",\"classification\":\"{}\",\"feature_gate\":\"{}\",\"status\":\"pass\"",
            json_escape(row.id),
            json_escape(row.families),
            json_escape(row.expression),
            json_escape(row.expected),
            json_escape(&row.observed),
            json_escape(row.classification),
            json_escape(row.feature_gate),
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
fn owner_i5_6400_executes_admitted_safe_sweep_and_emits_evidence() {
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
        (
            "push-pop-roundtrip",
            "balanced PUSH/POP r64",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 37) (push-r64 rax) (mov-r64-imm64 rax 0) (pop-r64 rax) (ret))) 0)",
            "37",
        ),
        (
            "inc-reg",
            "INC r64",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 41) (inc-r64 rax) (ret))) 0)",
            "42",
        ),
        (
            "dec-reg",
            "DEC r64",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 43) (dec-r64 rax) (ret))) 0)",
            "42",
        ),
        (
            "not-reg-normalized",
            "NOT r64 + bounded mask",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 0) (not-r64 rax) (mov-r64-imm64 rcx 255) (and-r64-r64 rax rcx) (ret))) 0)",
            "255",
        ),
        (
            "neg-reg-normalized",
            "NEG r64 + bounded compensation",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 7) (neg-r64 rax) (mov-r64-imm64 rcx 7) (add-r64-r64 rax rcx) (ret))) 0)",
            "0",
        ),
        (
            "shl-reg-imm8",
            "SHL r64,imm8",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 3) (shl-r64-imm8 rax 4) (ret))) 0)",
            "48",
        ),
        (
            "shr-reg-imm8",
            "SHR r64,imm8",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 128) (shr-r64-imm8 rax 3) (ret))) 0)",
            "16",
        ),
        (
            "sar-reg-imm8-signed",
            "NEG + SAR r64,imm8 + NEG normalization",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 16) (neg-r64 rax) (sar-r64-imm8 rax 2) (neg-r64 rax) (ret))) 0)",
            "4",
        ),
        (
            "test-jnz-zero",
            "TEST r64,r64 + JNZ rel8 zero path",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 0) (test-r64-r64 rax rax) (jnz-rel8 11) (mov-r64-imm64 rax 111) (ret) (mov-r64-imm64 rax 222) (ret))) 0)",
            "111",
        ),
        (
            "test-jnz-nonzero",
            "TEST r64,r64 + JNZ rel8 nonzero path",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 1) (test-r64-r64 rax rax) (jnz-rel8 11) (mov-r64-imm64 rax 111) (ret) (mov-r64-imm64 rax 222) (ret))) 0)",
            "222",
        ),
        (
            "imul-reg",
            "IMUL r64,r64",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 6) (mov-r64-imm64 rcx 7) (imul-r64-r64 rax rcx) (ret))) 0)",
            "42",
        ),
        (
            "cmove-equal",
            "CMP + CMOVE r64,r64",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 5) (mov-r64-imm64 rcx 5) (mov-r64-imm64 rdx 42) (cmp-r64-r64 rax rcx) (cmove-r64-r64 rax rdx) (ret))) 0)",
            "42",
        ),
        (
            "cmovne-distinct",
            "CMP + CMOVNE r64,r64",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 5) (mov-r64-imm64 rcx 6) (mov-r64-imm64 rdx 43) (cmp-r64-r64 rax rcx) (cmovne-r64-r64 rax rdx) (ret))) 0)",
            "43",
        ),
        (
            "sete-movzx",
            "CMP + SETE r8 + MOVZX r64,r8",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 9) (mov-r64-imm64 rcx 9) (cmp-r64-r64 rax rcx) (sete-r8 al) (movzx-r64-r8 rax al) (ret))) 0)",
            "1",
        ),
        (
            "lea-arena-disp8",
            "LEA r64,[arena+disp8] normalized to displacement",
            "(x86-call-admitted-u64 (quote ((lea-r64-mem-disp8 rax rdi 8) (mov-r64-r64 rcx rdi) (sub-r64-r64 rax rcx) (ret))) 16)",
            "8",
        ),
        (
            "xchg-reg",
            "XCHG r64,r64",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 11) (mov-r64-imm64 rcx 22) (xchg-r64-r64 rax rcx) (ret))) 0)",
            "22",
        ),
        (
            "bsf-reg",
            "BSF r64,r64 nonzero source",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rcx 8) (bsf-r64-r64 rax rcx) (ret))) 0)",
            "3",
        ),
        (
            "bsr-reg",
            "BSR r64,r64 nonzero source",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rcx 8) (bsr-r64-r64 rax rcx) (ret))) 0)",
            "3",
        ),
        (
            "rol-reg-imm8",
            "ROL r64,imm8",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 1) (rol-r64-imm8 rax 4) (ret))) 0)",
            "16",
        ),
        (
            "ror-reg-imm8",
            "ROR r64,imm8",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 16) (ror-r64-imm8 rax 4) (ret))) 0)",
            "1",
        ),
        (
            "bswap-reg-normalized",
            "BSWAP r64 + SHR normalization",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 16909060) (bswap-r64 rax) (shr-r64-imm8 rax 32) (ret))) 0)",
            "67305985",
        ),
        (
            "nop-preserves",
            "NOP",
            "(x86-call-admitted-u64 (quote ((mov-r64-imm64 rax 42) (nop) (ret))) 0)",
            "42",
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
            classification: "execute-safe",
            feature_gate: "none",
        });
    }

    for (id, family, flag, expression) in [
        (
            "rdrand-status",
            "RDRAND r64 + SETC + MOVZX",
            "rdrand",
            "(x86-call-admitted-u64 (quote ((rdrand-r64 rax) (setc-r8 al) (movzx-r64-r8 rax al) (ret))) 0)",
        ),
        (
            "rdseed-status",
            "RDSEED r64 + SETC + MOVZX",
            "rdseed",
            "(x86-call-admitted-u64 (quote ((rdseed-r64 rax) (setc-r8 al) (movzx-r64-r8 rax al) (ret))) 0)",
        ),
    ] {
        assert!(
            cpu_has_flag(&cpu_flags, flag),
            "owner i5-6400 real-silicon lane requires CPU feature {flag} before executing {id}"
        );
        let observed = eval_value(expression, &mut session);
        assert!(
            observed == "0" || observed == "1",
            "{id} must expose only the architectural CF status bit 0|1, observed {observed}"
        );
        rows.push(SiliconRow {
            id,
            families: family,
            expression,
            expected: "status-bit 0|1",
            observed,
            classification: "platform-gated",
            feature_gate: flag,
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
