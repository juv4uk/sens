//! Run the SENS-written whole-program compiler on canonical SW\x01 input.
//!
//! Host work is deliberately limited to:
//! - reading exact input bytes;
//! - decoding/re-encoding the existing syntax-wire codec;
//! - attaching source revision + raw wire digest provenance;
//! - encoding the SENS-produced artifact into canonical evidence bytes.
//!
//! Traversal, role selection, source-shape policy and artifact composition execute
//! in lib/compiler-nucleus.lisp. This adapter has no identity -> role table.

use sens::{
    compiler_evidence_canonical_bytes, compiler_evidence_from_canonical_bytes,
    compiler_program_artifact_from_sens, sha256_source, wire_decode_program, wire_encode_program,
    lowered_program_to_exact_data, Value,
};
use std::fs::{self, OpenOptions};
use std::io::{self, Write};
use std::path::{Path, PathBuf};
use std::process::Command;

const MAX_INPUT_BYTES: u64 = 64 * 1024 * 1024;

#[derive(Debug, Clone)]
pub struct RunOptions {
    pub input: PathBuf,
    pub output: Option<PathBuf>,
}

fn sha256_hex(bytes: &[u8]) -> String {
    sha256_source(bytes)
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect()
}

fn current_revision(repo_root: &str) -> Result<String, String> {
    let output = Command::new("git")
        .arg("-C")
        .arg(repo_root)
        .args(["rev-parse", "HEAD"])
        .output()
        .map_err(|error| format!("cannot resolve pinned SENS revision: {error}"))?;
    if !output.status.success() {
        return Err("cannot resolve pinned SENS revision: git rev-parse HEAD failed".into());
    }
    let revision = String::from_utf8(output.stdout)
        .map_err(|_| "git revision is not UTF-8".to_string())?
        .trim()
        .to_string();
    if revision.len() != 40
        || !revision
            .bytes()
            .all(|byte| byte.is_ascii_digit() || matches!(byte, b'a'..=b'f'))
    {
        return Err("SENS revision must be a full lowercase 40-character SHA".into());
    }
    Ok(revision)
}

fn artifact_schema(value: &Value) -> Result<&str, String> {
    let Value::Pair(head, _) = value else {
        return Err("SENS compiler returned a non-list artifact".into());
    };
    let Value::Symbol(schema) = head.as_ref() else {
        return Err("SENS compiler artifact must start with a schema symbol".into());
    };
    match schema.as_ref() {
        "compiler-compilation-artifact/1" | "compiler-compilation-error/1" => {
            Ok(schema.as_ref())
        }
        other => Err(format!("SENS compiler returned unknown artifact schema: {other}")),
    }
}

/// Compile one exact canonical syntax-wire stream through the executable SENS
/// compiler. Ok((bytes, true)) means accepted; Ok((bytes, false)) means SENS
/// emitted a canonical semantic-rejection artifact which must not execute.
fn compile_sw1_bytes(input: &[u8], sens_revision: &str) -> Result<(Vec<u8>, bool), String> {
    if input.is_empty() {
        return Err("SW1 compiler input is empty".into());
    }
    if input.len() as u64 > MAX_INPUT_BYTES {
        return Err(format!(
            "SW1 compiler input exceeds the {}-byte resource cap",
            MAX_INPUT_BYTES
        ));
    }

    let expressions = wire_decode_program(input)
        .map_err(|error| format!("canonical sens-syntax-wire/1 decode failed: {error}"))?;

    // Decode acceptance alone is not treated as proof of canonicality. The
    // exact wire must survive a decode/encode round-trip byte-for-byte.
    let reencoded = wire_encode_program(&expressions);
    if reencoded.as_slice() != input {
        return Err("SW1 input is valid-looking but not byte-canonical".into());
    }

    // Representation conversion only: exact DomainIdentity, pair/list shape,
    // symbols and strings survive. Legacy Sid/Call or resolved Locals are
    // rejected by the converter before the SENS compiler is invoked.
    let program = lowered_program_to_exact_data(&expressions)
        .map_err(|error| format!("SW1 program-data conversion failed closed: {error}"))?;
    let wire_digest = sha256_hex(input);

    // This is the language compiler entry point. Do not replace it with a Rust
    // walk over expressions or per-node host identity->role lookups.
    let artifact = compiler_program_artifact_from_sens(program, &wire_digest, sens_revision)
        .map_err(|error| format!("SENS compiler invocation failed: {error}"))?;
    let schema = artifact_schema(&artifact)?;
    let accepted = schema == "compiler-compilation-artifact/1";
    let canonical_bytes = compiler_evidence_canonical_bytes(&artifact)
        .map_err(|error| format!("cannot encode SENS artifact as canonical evidence bytes: {error}"))?;

    // Defend the producer boundary as well: the exact bytes we emit must decode
    // and re-encode identically through the existing canonical evidence codec.
    let decoded = compiler_evidence_from_canonical_bytes(&canonical_bytes)
        .map_err(|error| format!("emitted artifact failed canonical evidence decode: {error}"))?;
    let reencoded_artifact = compiler_evidence_canonical_bytes(&decoded)
        .map_err(|error| format!("emitted artifact failed canonical evidence re-encode: {error}"))?;
    if reencoded_artifact != canonical_bytes {
        return Err("emitted compiler artifact is not byte-canonical".into());
    }
    if artifact_schema(&decoded)? != schema {
        return Err("compiler artifact schema changed across canonical byte round-trip".into());
    }

    Ok((canonical_bytes, accepted))
}

fn write_output(output: Option<&Path>, bytes: &[u8]) -> Result<(), String> {
    match output {
        Some(path) => {
            // Evidence artifacts are immutable by default; refuse to clobber an
            // earlier run. Use a new path for a new result.
            let mut file = OpenOptions::new()
                .write(true)
                .create_new(true)
                .open(path)
                .map_err(|error| {
                    format!(
                        "cannot create output {} without overwriting existing data: {error}",
                        path.display()
                    )
                })?;
            file.write_all(bytes)
                .map_err(|error| format!("cannot write output {}: {error}", path.display()))?;
            file.sync_all()
                .map_err(|error| format!("cannot sync output {}: {error}", path.display()))?;
            Ok(())
        }
        None => io::stdout()
            .lock()
            .write_all(bytes)
            .map_err(|error| format!("cannot write artifact bytes to stdout: {error}")),
    }
}

pub fn run(repo_root: &str, options: RunOptions) -> Result<bool, String> {
    let metadata = fs::metadata(&options.input)
        .map_err(|error| format!("cannot stat SW1 input {}: {error}", options.input.display()))?;
    if !metadata.is_file() {
        return Err(format!("SW1 input is not a regular file: {}", options.input.display()));
    }
    if metadata.len() > MAX_INPUT_BYTES {
        return Err(format!(
            "SW1 input exceeds the {}-byte resource cap",
            MAX_INPUT_BYTES
        ));
    }
    let input = fs::read(&options.input)
        .map_err(|error| format!("cannot read SW1 input {}: {error}", options.input.display()))?;
    let revision = current_revision(repo_root)?;
    let (artifact, accepted) = compile_sw1_bytes(&input, &revision)?;
    write_output(options.output.as_deref(), &artifact)?;

    if !accepted {
        eprintln!("SENS compiler rejected the program; canonical compiler-compilation-error/1 artifact emitted");
    }
    Ok(accepted)
}

#[cfg(test)]
mod tests {
    use super::*;
    use sens::{
        parse_mixed_exact_domain, lower_program, verify_compiler_program_artifact_from_sens,
        CoreD8, Bit8, DomainIdentity, Expr, ExprKind, Span, CompilerLoweringRole,
    };
    use std::rc::Rc;

    const NUCLEUS: &str = include_str!("../../../lib/compiler-nucleus.lisp");

    #[test]
    fn canonical_sw1_runs_through_sens_compiler_and_emits_repeatable_artifact_bytes() {
        let parsed = parse_mixed_exact_domain(NUCLEUS).expect("SENS compiler source parses");
        let lowered = lower_program(&parsed);
        let input = wire_encode_program(&lowered);
        let revision = "0123456789abcdef0123456789abcdef01234567";

        let (first, accepted) =
            compile_sw1_bytes(&input, revision).expect("SENS compiler accepts its own nucleus");
        let (second, accepted_again) =
            compile_sw1_bytes(&input, revision).expect("repeat compile succeeds");
        assert!(accepted && accepted_again);
        assert_eq!(first, second, "same SW1 bytes/provenance must yield exact same artifact bytes");

        let artifact = compiler_evidence_from_canonical_bytes(&first)
            .expect("canonical evidence bytes decode");
        assert_eq!(artifact_schema(&artifact).unwrap(), "compiler-compilation-artifact/1");
        let verified = verify_compiler_program_artifact_from_sens(
            &artifact,
            &sha256_hex(&input),
            revision,
        )
        .expect("artifact verifies against current SENS law/provenance");
        for role in [
            CompilerLoweringRole::QuoteForm,
            CompilerLoweringRole::AtomPredicate,
            CompilerLoweringRole::SelectorTail,
            CompilerLoweringRole::SelectorHead,
            CompilerLoweringRole::AtomEquality,
            CompilerLoweringRole::CondForm,
            CompilerLoweringRole::PairConstruct,
            CompilerLoweringRole::LambdaForm,
            CompilerLoweringRole::DefineForm,
        ] {
            assert!(
                verified.requests.iter().any(|request| request.lowering_role == role),
                "SENS artifact omitted current compiler role {role:?}"
            );
        }
    }

    #[test]
    fn malformed_or_noncanonical_sw1_fails_before_compiler_execution() {
        assert!(compile_sw1_bytes(
            b"not-an-sw1-stream",
            "0123456789abcdef0123456789abcdef01234567"
        ).is_err());

        let empty_program = wire_encode_program(&[]);
        let mut with_trailing_byte = empty_program;
        with_trailing_byte.push(0);
        assert!(compile_sw1_bytes(
            &with_trailing_byte,
            "0123456789abcdef0123456789abcdef01234567"
        ).is_err());
    }

    #[test]
    fn d8_input_emits_semantic_rejection_artifact_not_a_compilable_artifact() {
        let d8: DomainIdentity = CoreD8::from_word(Bit8::new(0b0000_0010).unwrap()).into();
        let node = Expr {
            kind: ExprKind::List(Rc::from(vec![Expr {
                kind: ExprKind::DomainIdentity(d8),
                span: Span::default(),
            }].into_boxed_slice())),
            span: Span::default(),
        };
        let input = wire_encode_program(&[node]);
        let (bytes, accepted) =
            compile_sw1_bytes(&input, "0123456789abcdef0123456789abcdef01234567")
                .expect("semantic rejection is a typed artifact, not a host reinterpretation");
        assert!(!accepted);
        let artifact = compiler_evidence_from_canonical_bytes(&bytes)
            .expect("error artifact is canonical");
        assert_eq!(artifact_schema(&artifact).unwrap(), "compiler-compilation-error/1");
    }

    #[test]
    fn compiler_adapter_contains_no_parallel_role_or_coordinate_table() {
        let source = include_str!("compiler_compile.rs");
        // Construct banned phrases from fragments so this negative guard does
        // not fail merely because the test contains its own search strings.
        let forbidden = [
            concat!("match identity.", "width()"),
            concat!("packed_", "bits()"),
            concat!("selector-", "head"),
            concat!("selector-", "tail"),
            concat!("lambda-", "form"),
            concat!("define-", "form"),
            concat!("compiler_semantic_", "input_from_sens"),
        ];
            assert!(
                !source.contains(forbidden),
                "host adapter contains a forbidden semantic shortcut: {forbidden}"
            );
        }
    }
}
