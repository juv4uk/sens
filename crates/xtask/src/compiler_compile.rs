//! Виконання SENS-компілятора зі SW1 або фізичного T5M через Zig.
//!
//! Host work is deliberately limited to:
//! - validating and round-tripping the selected wire/codec representation;
//! - порівняння Lisp, фізичного T5M і похідного бітового перегляду;
//! - attaching SENS revision and canonical program-wire digest provenance;
//! - encoding the SENS-produced artifact into canonical evidence bytes.
//!
//! Traversal, role selection, source-shape policy and artifact composition execute
//! in lib/compiler-nucleus.lisp. This adapter has no identity -> role table.

use sens::{
    compiler_evidence_canonical_bytes, compiler_evidence_from_canonical_bytes,
    compiler_program_artifact_from_sens, lower_program, lowered_program_to_exact_data,
    parse_canonical_binary, parse_mixed_exact_domain, sha256_source,
    verify_compiler_program_artifact_from_sens, wire_decode_program, wire_encode_program, Value,
};
use sens_cli::zig_transport::{decode_t5m_exact_words, encode_t5m_exact_words};
use std::fs::{self, OpenOptions};
use std::io::{self, Write};
use std::path::{Path, PathBuf};
use std::process::Command;

const MAX_INPUT_BYTES: u64 = 64 * 1024 * 1024;

// The recursive compiler is written and executed in SENS. Give its host
// entrypoints a bounded dedicated stack without copying the SW1/T5M input.
// Only the canonical artifact bytes and acceptance bit cross the thread
// boundary; SENS Value (Rc-backed) never becomes Send or an authority table.
const SENS_COMPILER_STACK_BYTES: usize = 64 * 1024 * 1024;

fn on_compiler_stack<T: Send>(operation: impl FnOnce() -> T + Send) -> Result<T, String> {
    std::thread::scope(|scope| {
        let worker = std::thread::Builder::new()
            .name("sens-compiler-transport".to_owned())
            .stack_size(SENS_COMPILER_STACK_BYTES)
            .spawn_scoped(scope, operation)
            .map_err(|error| format!("cannot start SENS compiler worker: {error}"))?;
        worker
            .join()
            .map_err(|_| "SENS compiler worker panicked".to_owned())
    })
}

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
    let Value::Pair(node) = value else {
        return Err("SENS compiler returned a non-list artifact".into());
    };
    let Value::Symbol(schema) = &node.head else {
        return Err("SENS compiler artifact must start with a schema symbol".into());
    };
    match schema.as_ref() {
        "compiler-compilation-artifact-1" | "compiler-compilation-error-1" => Ok(schema.as_ref()),
        other => Err(format!(
            "SENS compiler returned unknown artifact schema: {other}"
        )),
    }
}

/// Keep artifact construction and canonical evidence verification shared by
/// the explicit SW1 bootstrap route and the physical-T5M triplet route.
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
    let accepted = schema == "compiler-compilation-artifact-1";
    let canonical_bytes = compiler_evidence_canonical_bytes(&artifact).map_err(|error| {
        format!("cannot encode SENS artifact as canonical evidence bytes: {error}")
    })?;

    // Defend the producer boundary as well: the exact bytes we emit must decode
    // and re-encode identically through the existing canonical evidence codec.
    let decoded = compiler_evidence_from_canonical_bytes(&canonical_bytes)
        .map_err(|error| format!("emitted artifact failed canonical evidence decode: {error}"))?;
    let reencoded_artifact = compiler_evidence_canonical_bytes(&decoded).map_err(|error| {
        format!("emitted artifact failed canonical evidence re-encode: {error}")
    })?;
    if reencoded_artifact != canonical_bytes {
        return Err("emitted compiler artifact is not byte-canonical".into());
    }
    if artifact_schema(&decoded)? != schema {
        return Err("compiler artifact schema changed across canonical byte round-trip".into());
    }
    if accepted {
        verify_compiler_program_artifact_from_sens(&decoded, program_wire_sha256, sens_revision)
            .map_err(|error| {
                format!("SENS compiler artifact failed current-authority verification: {error}")
            })?;
    }

    Ok((canonical_bytes, accepted))
}

/// Compile one three-file source projection: same-stem SENS source, physical
/// T5 and extensionless exact-width binary view. The T5 reader owns word
/// decoding and D2 syntax; all projections must agree after SENS lowering.
fn compile_t5m_triplet_bytes(
    lisp_source: &[u8],
    physical_t5m: &[u8],
    visible_view: &[u8],
    sens_revision: &str,
) -> Result<(Vec<u8>, bool), String> {
    on_compiler_stack(|| {
        compile_t5m_triplet_on_worker(lisp_source, physical_t5m, visible_view, sens_revision)
    })?
}

fn compile_t5m_triplet_on_worker(
    lisp_source: &[u8],
    physical_t5m: &[u8],
    visible_view: &[u8],
    sens_revision: &str,
) -> Result<(Vec<u8>, bool), String> {
    for (name, bytes) in [
        ("Lisp source", lisp_source),
        ("physical T5M", physical_t5m),
        ("visible word view", visible_view),
    ] {
        if bytes.is_empty() {
            return Err(format!("{name} input is empty"));
        }
        if bytes.len() as u64 > MAX_INPUT_BYTES {
            return Err(format!(
                "{name} input exceeds the {}-byte resource cap",
                MAX_INPUT_BYTES
            ));
        }
    }

    // Фізичний T5M декодує лише Zig; Rust відображає вже відновлені
    // точні слова для незалежного SENS-парсера й не вводить власний кодек.
    let exact = decode_t5m_exact_words(physical_t5m)
        .map_err(|error| format!("Zig T5M відхилив фізичний носій: {error}"))?;
    let visible = exact
        .iter()
        .map(|word| {
            word.bits
                .iter()
                .map(|bit| char::from(b'0' + *bit))
                .collect::<String>()
        })
        .collect::<Vec<_>>()
        .join(" ");
    let mut canonical_view = visible.as_bytes().to_vec();
    canonical_view.push(b'\n');
    if visible_view != canonical_view.as_slice() {
        return Err("T5M: похідний бітовий перегляд не збігається зі словами Zig".into());
    }
    let reencoded_t5m = encode_t5m_exact_words(&exact)
        .map_err(|error| format!("Zig T5M не відновив фізичний носій: {error}"))?;
    if reencoded_t5m.as_slice() != physical_t5m {
        return Err("T5M: порушено побайтову канонічність кодека".into());
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
        let common_forms = source_lowered.len().min(binary_lowered.len());
        for index in 0..common_forms {
            let source_form = wire_encode_program(std::slice::from_ref(&source_lowered[index]));
            let binary_form = wire_encode_program(std::slice::from_ref(&binary_lowered[index]));
            if source_form != binary_form {
                let first_wire_difference = source_form
                    .iter()
                    .zip(binary_form.iter())
                    .position(|(left, right)| left != right)
                    .unwrap_or(source_form.len().min(binary_form.len()));
                return Err(format!(
                    "SENS source and physical-T5M view disagree after exact-domain lowering at top-level form {index}; first per-form wire difference={first_wire_difference}; source form={:?}; physical-T5M form={:?}",
                    source_lowered[index], binary_lowered[index]
                ));
            }
        }
        if source_lowered.len() != binary_lowered.len() {
            return Err(format!(
                "SENS source and physical-T5M view have different top-level form counts: source={}, physical-T5M={}",
                source_lowered.len(), binary_lowered.len()
            ));
        }
        return Err(format!(
            "SENS source and physical-T5M view differ in whole-program wire (source_bytes={}, physical_T5_bytes={}) although individual top-level forms appear equal",
            source_identity_wire.len(), binary_identity_wire.len()
        ));
    }

    let program = lowered_program_to_exact_data(&binary_lowered)
        .map_err(|error| format!("T5M program-data conversion failed closed: {error}"))?;
    // The artifact contract names this field program_wire_sha256. Derive it
    // from the canonical SW1 encoding of the typed program; physical T5M bytes
    // already passed their own byte-roundtrip gate above.
    let canonical_program_wire = wire_encode_program(&binary_lowered);
    let program_wire_digest = sha256_hex(&canonical_program_wire);
    compile_program_data(program, &program_wire_digest, sens_revision)
}

/// Compile one exact canonical syntax-wire stream through the executable SENS
/// compiler. Ok((bytes, true)) means accepted; Ok((bytes, false)) means SENS
/// emitted a canonical semantic-rejection artifact which must not execute.
fn compile_sw1_bytes(input: &[u8], sens_revision: &str) -> Result<(Vec<u8>, bool), String> {
    on_compiler_stack(|| compile_sw1_on_worker(input, sens_revision))?
}

fn compile_sw1_on_worker(input: &[u8], sens_revision: &str) -> Result<(Vec<u8>, bool), String> {
    if input.is_empty() {
        return Err("SW1 compiler input is empty".into());
    }
    if input.len() as u64 > MAX_INPUT_BYTES {
        return Err(format!(
            "SW1 compiler input exceeds the {}-byte resource cap",
            MAX_INPUT_BYTES
        ));
    }

    let expressions = wire_decode_program(input).ok_or_else(|| {
        "canonical sens-syntax-wire-1 decode failed: invalid physical wire".to_string()
    })?;

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
        let metadata = fs::symlink_metadata(&cursor).map_err(|error| {
            format!(
                "cannot inspect {role} path component {}: {error}",
                cursor.display()
            )
        })?;
        if metadata.file_type().is_symlink() {
            return Err(format!(
                "{role} path contains a symlink: {}",
                cursor.display()
            ));
        }
    }

    let metadata = fs::symlink_metadata(&absolute)
        .map_err(|error| format!("cannot inspect {role} {}: {error}", absolute.display()))?;
    if !metadata.is_file() {
        return Err(format!(
            "{role} must be a regular file: {}",
            absolute.display()
        ));
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

/// Run the physical T5M route from an explicit .sens path, requiring same-stem
/// .lisp and extensionless-view siblings. No format sniffing or fallback occurs.
pub fn run_triplet(
    repo_root: &str,
    sens_path: &Path,
    output: Option<&Path>,
) -> Result<bool, String> {
    if sens_path
        .extension()
        .and_then(|extension| extension.to_str())
        != Some("sens")
    {
        return Err(format!(
            "--triplet requires a physical .sens path: {}",
            sens_path.display()
        ));
    }
    let lisp_path = sens_path.with_extension("lisp");
    let view_path = sens_path.with_extension("");
    let lisp = read_triplet_member(&lisp_path, "triplet Lisp source")?;
    let physical = read_triplet_member(sens_path, "triplet physical T5M")?;
    let view = read_triplet_member(&view_path, "triplet visible view")?;
    let revision = current_revision(repo_root)?;
    let (artifact, accepted) = compile_t5m_triplet_bytes(&lisp, &physical, &view, &revision)?;
    write_output(output, &artifact)?;
    if !accepted {
        eprintln!("SENS compiler rejected the triplet program; canonical compiler-compilation-error-1 artifact emitted");
    }
    Ok(accepted)
}

pub fn run(repo_root: &str, options: RunOptions) -> Result<bool, String> {
    let metadata = fs::metadata(&options.input)
        .map_err(|error| format!("cannot stat SW1 input {}: {error}", options.input.display()))?;
    if !metadata.is_file() {
        return Err(format!(
            "SW1 input is not a regular file: {}",
            options.input.display()
        ));
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
        eprintln!("SENS compiler rejected the program; canonical compiler-compilation-error-1 artifact emitted");
    }
    Ok(accepted)
}

