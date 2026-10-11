//! Run the SENS-written whole-program compiler from canonical SW1 or physical T5.
//!
//! Host work is deliberately limited to:
//! - validating and round-tripping the selected wire/codec representation;
//! - comparing same-stem source, physical T5 and visible-view projections;
//! - attaching SENS revision and canonical program-wire digest provenance;
//! - encoding the SENS-produced artifact into canonical evidence bytes.
//!
//! Traversal, role selection, source-shape policy and artifact composition execute
//! in lib/compiler-nucleus.lisp. This adapter has no identity -> role table.

use sens::{
    compiler_evidence_canonical_bytes, compiler_evidence_from_canonical_bytes,
    compiler_program_artifact_from_sens, encode_binary_projection_ternary, lower_program,
    lowered_program_to_exact_data, open_ternary_program, parse_canonical_binary,
    parse_mixed_exact_domain, sha256_source, verify_compiler_program_artifact_from_sens,
    wire_decode_program, wire_encode_program, Value,
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

/// Keep artifact construction and canonical evidence verification shared by
/// the explicit SW1 bootstrap route and the physical-T5 triplet route.
fn compile_program_data(
    program: Value,
    program_wire_sha256: &str,
    sens_revision: &str,
) -> Result<(Vec<u8>, bool), String> {
    // This is the language compiler entry point. Do not replace it with a Rust
    // walk over expressions or per-node host identity->role lookups.
    let artifact = compiler_program_artifact_from_sens(program, program_wire_sha256, sens_revision)
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
    if accepted {
        verify_compiler_program_artifact_from_sens(
            &decoded,
            program_wire_sha256,
            sens_revision,
        )
        .map_err(|error| {
            format!("SENS compiler artifact failed current-authority verification: {error}")
        })?;
    }

    Ok((canonical_bytes, accepted))
}

/// Compile one three-file source projection: same-stem SENS source, physical
/// T5 and extensionless exact-width binary view. The T5 reader owns word
/// decoding and D2 syntax; all projections must agree after SENS lowering.
fn compile_t5_triplet_bytes(
    lisp_source: &[u8],
    physical_t5: &[u8],
    visible_view: &[u8],
    sens_revision: &str,
) -> Result<(Vec<u8>, bool), String> {
    for (name, bytes) in [
        ("Lisp source", lisp_source),
        ("physical T5", physical_t5),
        ("visible word view", visible_view),
    ] {
        if bytes.is_empty() {
            return Err(format!("{name} input is empty"));
        }
        if bytes.len() as u64 > MAX_INPUT_BYTES {
            return Err(format!("{name} input exceeds the {}-byte resource cap", MAX_INPUT_BYTES));
        }
    }

    let visible = open_ternary_program(physical_t5)
        .map_err(|error| format!("canonical physical T5 open failed: {error:?}"))?;
    // The Rust renderer returns the spaced words without a newline, while the
    // on-disk view contract requires exactly one final LF.
    let mut canonical_view = visible.as_bytes().to_vec();
    canonical_view.push(b'\n');
    if visible_view != canonical_view.as_slice() {
        return Err("triplet view does not byte-match the canonical T5 decoder output plus one LF".into());
    }
    let reencoded_t5 = encode_binary_projection_ternary(&visible)
        .map_err(|error| format!("canonical T5 re-encode failed: {error:?}"))?;
    if reencoded_t5.as_slice() != physical_t5 {
        return Err("physical T5 is not byte-canonical after decode/encode".into());
    }

    let source = std::str::from_utf8(lisp_source)
        .map_err(|_| "triplet Lisp source is not UTF-8".to_string())?;
    let source_parsed = parse_mixed_exact_domain(source)
        .map_err(|error| format!("SENS source parse failed: {error}"))?;
    let source_lowered = lower_program(&source_parsed);
    let source_identity_wire = wire_encode_program(&source_lowered);

    let binary_parsed = parse_canonical_binary(&visible)
        .map_err(|error| format!("canonical exact-domain view parse failed: {error}"))?;
    let binary_lowered = lower_program(&binary_parsed);
    let binary_identity_wire = wire_encode_program(&binary_lowered);
    if source_identity_wire != binary_identity_wire {
        return Err("SENS source and physical-T5 view disagree after exact-domain lowering".into());
    }

    let program = lowered_program_to_exact_data(&binary_lowered)
        .map_err(|error| format!("T5 program-data conversion failed closed: {error}"))?;
    // The artifact contract names this field program_wire_sha256. Derive it
    // from the canonical SW1 encoding of the typed program; physical T5 bytes
    // already passed their own byte-roundtrip gate above.
    let canonical_program_wire = wire_encode_program(&binary_lowered);
    let program_wire_digest = sha256_hex(&canonical_program_wire);
    compile_program_data(program, &program_wire_digest, sens_revision)
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
        .ok_or_else(|| "canonical sens-syntax-wire/1 decode failed: invalid physical wire".to_string())?;

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
    compile_program_data(program, &wire_digest, sens_revision)
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

fn read_triplet_member(path: &Path, role: &str) -> Result<Vec<u8>, String> {
    let absolute = if path.is_absolute() {
        path.to_path_buf()
    } else {
        std::env::current_dir()
            .map_err(|error| format!("cannot resolve current directory for {role}: {error}"))?
            .join(path)
    };
    let mut cursor = PathBuf::new();
    for component in absolute.components() {
        cursor.push(component.as_os_str());
        let metadata = fs::symlink_metadata(&cursor)
            .map_err(|error| format!("cannot inspect {role} path component {}: {error}", cursor.display()))?;
        if metadata.file_type().is_symlink() {
            return Err(format!("{role} path contains a symlink: {}", cursor.display()));
        }
    }

    let metadata = fs::symlink_metadata(&absolute)
        .map_err(|error| format!("cannot inspect {role} {}: {error}", absolute.display()))?;
    if !metadata.is_file() {
        return Err(format!("{role} must be a regular file: {}", absolute.display()));
    }
    if metadata.len() > MAX_INPUT_BYTES {
        return Err(format!(
            "{role} exceeds the {}-byte resource cap: {}",
            MAX_INPUT_BYTES,
            absolute.display()
        ));
    }
    fs::read(&absolute)
        .map_err(|error| format!("cannot read {role} {}: {error}", absolute.display()))
}

/// Run the physical T5 route from an explicit .sens path, requiring same-stem
/// .lisp and extensionless-view siblings. No format sniffing or fallback occurs.
pub fn run_triplet(
    repo_root: &str,
    sens_path: &Path,
    output: Option<&Path>,
) -> Result<bool, String> {
    if sens_path.extension().and_then(|extension| extension.to_str()) != Some("sens") {
        return Err(format!("--triplet requires a physical .sens path: {}", sens_path.display()));
    }
    let lisp_path = sens_path.with_extension("lisp");
    let view_path = sens_path.with_extension("");
    let lisp = read_triplet_member(&lisp_path, "triplet Lisp source")?;
    let physical = read_triplet_member(sens_path, "triplet physical T5")?;
    let view = read_triplet_member(&view_path, "triplet visible view")?;
    let revision = current_revision(repo_root)?;
    let (artifact, accepted) = compile_t5_triplet_bytes(&lisp, &physical, &view, &revision)?;
    write_output(output, &artifact)?;
    if !accepted {
        eprintln!("SENS compiler rejected the triplet program; canonical compiler-compilation-error/1 artifact emitted");
    }
    Ok(accepted)
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
        encode_binary_projection_ternary, parse_mixed_exact_domain, lower_program,
        verify_compiler_program_artifact_from_sens, CoreD8, Bit8, DomainIdentity, Expr,
        ExprKind, Span, CompilerLoweringRole,
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
    fn canonical_t5_triplet_compiles_only_when_all_three_projections_match() {
        let source = "(як-є ())\n".as_bytes();
        let view = b"10 001 00 000 01\n";
        let physical = encode_binary_projection_ternary(
            std::str::from_utf8(view).expect("ASCII canonical view"),
        ).expect("existing SENS T5 codec");

        let revision = "0123456789abcdef0123456789abcdef01234567";
        let (bytes, accepted) = compile_t5_triplet_bytes(
            source, &physical, view, revision,
        ).expect("three matching projections compile through SENS");
        assert!(accepted);
        let artifact = compiler_evidence_from_canonical_bytes(&bytes)
            .expect("canonical compiler evidence");
        assert_eq!(artifact_schema(&artifact).unwrap(), "compiler-compilation-artifact/1");
        let parsed_view = parse_canonical_binary(
            std::str::from_utf8(view).expect("ASCII canonical view"),
        ).expect("parse compiled view");
        let lowered_view = lower_program(&parsed_view);
        let canonical_wire = wire_encode_program(&lowered_view);
        verify_compiler_program_artifact_from_sens(
            &artifact,
            &sha256_hex(&canonical_wire),
            revision,
        ).expect("artifact provenance is pinned to canonical program wire, not mislabeled T5 bytes");

        assert!(compile_t5_triplet_bytes(
            source, &physical, b"10 100 00 000 01\n", revision,
        ).is_err(), "a mismatched extensionless view must block");
        assert!(compile_t5_triplet_bytes(
            source, &physical, b"10 001 00 000 01", revision,
        ).is_err(), "the canonical extensionless view requires exactly one trailing LF");
        assert!(compile_t5_triplet_bytes(
            "(інакше ())\n".as_bytes(), &physical, view, revision,
        ).is_err(), "a source that lowers to a different exact program must block");
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
        for phrase in forbidden {
            assert!(
                !source.contains(phrase),
                "host adapter contains a forbidden semantic shortcut: {phrase}"
            );
        }
    }
}
