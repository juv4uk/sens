//! Machine-readable export of the SENS-owned compiler semantic request.
//!
//! This module is transport only. Role meaning comes from
//! `compiler_lowering_role_from_sens`; this exporter never derives a role from
//! raw coordinates itself.

use sens::{
    compiler_semantic_input_from_sens_with_sources, parse_binary_source_words, sha256_source,
    Bija3, BinarySourceWord, CompilerLanguageSources, CompilerLoweringRole,
    CompilerSemanticInput, CoreD4, CoreDomainIdentity,
};
use std::path::Path;

struct CompilerSources {
    nucleus: String,
    corpus: String,
    contract: String,
    d3_projection: String,
    d3_authority: String,
    d4_projection: String,
    d4_authority: String,
}

impl CompilerSources {
    fn semantic_inputs(&self) -> CompilerLanguageSources<'_> {
        CompilerLanguageSources {
            compiler_nucleus: &self.nucleus,
            language_contract: &self.contract,
            d3_projection: &self.d3_projection,
            d3_authority: &self.d3_authority,
            d4_projection: &self.d4_projection,
            d4_authority: &self.d4_authority,
        }
    }
}

fn compiler_sources() -> Result<CompilerSources, String> {
    fn source(bytes: Result<Vec<u8>, String>, name: &str) -> Result<String, String> {
        String::from_utf8(bytes?).map_err(|error| format!("{name} source is not UTF-8: {error}"))
    }
    Ok(CompilerSources {
        nucleus: source(
            sens_cli::zig_transport::compiler_nucleus_source_bytes(),
            "compiler nucleus",
        )?,
        corpus: source(
            sens_cli::zig_transport::compiler_identity_corpus_bytes(),
            "compiler identity corpus",
        )?,
        contract: source(
            sens_cli::zig_transport::compiler_language_contract_bytes(),
            "language contract",
        )?,
        d3_projection: source(
            sens_cli::zig_transport::compiler_d3_projection_bytes(),
            "D3 compiler projection",
        )?,
        d3_authority: source(
            sens_cli::zig_transport::compiler_d3_authority_bytes(),
            "D3 compiler authority",
        )?,
        d4_projection: source(
            sens_cli::zig_transport::compiler_d4_projection_bytes(),
            "D4 compiler projection",
        )?,
        d4_authority: source(
            sens_cli::zig_transport::compiler_d4_authority_bytes(),
            "D4 compiler authority",
        )?,
    })
}

fn compiler_semantic_input(
    identity: CoreDomainIdentity,
    sources: &CompilerSources,
) -> Result<Option<CompilerSemanticInput>, String> {
    compiler_semantic_input_from_sens_with_sources(identity, &sources.semantic_inputs())
        .map_err(|error| error.to_string())
}

#[derive(Debug, Clone)]
pub struct ExportOptions {
    pub fixture: Option<String>,
    pub artifact: bool,
}

fn sha256_hex(bytes: &[u8]) -> String {
    sha256_source(bytes)
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect()
}

fn current_commit(repo_root: &Path) -> Result<String, String> {
    let output = std::process::Command::new("git")
        .arg("-C")
        .arg(repo_root)
        .args(["rev-parse", "HEAD"])
        .output()
        .map_err(|e| format!("cannot resolve SENS source revision: {e}"))?;
    if !output.status.success() {
        return Err("cannot resolve SENS source revision: git rev-parse HEAD failed".into());
    }
    let commit = String::from_utf8(output.stdout)
        .map_err(|_| "git revision is not UTF-8".to_string())?
        .trim()
        .to_string();
    if commit.len() != 40 || !commit.bytes().all(|b| b.is_ascii_hexdigit()) {
        return Err("git revision is not a full 40-character SHA".into());
    }
    Ok(commit)
}

fn role_name(role: CompilerLoweringRole) -> &'static str {
    match role {
        CompilerLoweringRole::QuoteForm => "quote-form",
        CompilerLoweringRole::AtomPredicate => "atom-predicate",
        CompilerLoweringRole::SelectorTail => "selector-tail",
        CompilerLoweringRole::SelectorHead => "selector-head",
        CompilerLoweringRole::AtomEquality => "atom-equality",
        CompilerLoweringRole::CondForm => "cond-form",
        CompilerLoweringRole::PairConstruct => "pair-construct",
        CompilerLoweringRole::LambdaForm => "lambda-form",
        CompilerLoweringRole::DefineForm => "define-form",
    }
}

fn parse_identity(domain: &str, bits: &str) -> Result<CoreDomainIdentity, String> {
    if !bits.bytes().all(|b| matches!(b, b'0' | b'1')) {
        return Err(format!("invalid compiler identity bits {bits:?}"));
    }

    // Validate width before parsing and retain it in BinarySourceWord.
    // No untyped integer sits between the visible bits and the D3/D4 carrier.
    match (domain, bits.len()) {
        ("D3", 3) | ("D4", 4) => {}
        ("D3", _) => {
            return Err(format!(
                "D3 compiler identity requires 3 bits, got {bits:?}"
            ))
        }
        ("D4", _) => {
            return Err(format!(
                "D4 compiler identity requires 4 bits, got {bits:?}"
            ))
        }
        (other, _) => {
            return Err(format!(
                "unsupported compiler export domain {other:?}; only current D3/D4 are admitted"
            ))
        }
    }

    let tokens = parse_binary_source_words(bits)
        .map_err(|_| format!("invalid compiler identity bits {bits:?}"))?;
    if tokens.len() != 1 {
        return Err(format!(
            "compiler identity must be one exact binary word: {bits:?}"
        ));
    }

    match (domain, tokens[0].word) {
        ("D3", BinarySourceWord::W3(word)) => Ok(CoreDomainIdentity::D3(Bija3::from_word(word))),
        ("D4", BinarySourceWord::W4(word)) => Ok(CoreDomainIdentity::D4(CoreD4::from_word(word))),
        ("D3", _) => Err(format!("D3 source reader lost exact width: {bits:?}")),
        ("D4", _) => Err(format!("D4 source reader lost exact width: {bits:?}")),
        (other, _) => Err(format!("unsupported compiler export domain {other:?}")),
    }
}

fn parse_fixture_rows(
    fixture: Option<&str>,
    corpus: &str,
) -> Result<Vec<(String, CoreDomainIdentity)>, String> {
    let mut rows = Vec::new();
    for line in corpus.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let fields: Vec<_> = line.split('\t').collect();
        if fields.len() != 3 {
            return Err(format!(
                "compiler nucleus corpus row has {} fields, expected 3: {line}",
                fields.len()
            ));
        }

        let name = fields[0].to_string();
        if let Some(requested) = fixture {
            if requested != name {
                continue;
            }
        }
        rows.push((name, parse_identity(fields[1], fields[2])?));
    }

    if rows.is_empty() {
        return Err(match fixture {
            Some(name) => format!("compiler corpus fixture not found: {name}"),
            None => "compiler corpus is empty".into(),
        });
    }
    Ok(rows)
}

fn identity_transport(identity: CoreDomainIdentity) -> (&'static str, String) {
    match identity {
        CoreDomainIdentity::D3(word) => ("D3", format!("{:03b}", word.word().packed_bits())),
        CoreDomainIdentity::D4(word) => ("D4", format!("{:04b}", word.word().packed_bits())),
        _ => unreachable!("compiler export corpus admits only current D3/D4"),
    }
}

fn render_request(
    fixture_id: &str,
    input: &CompilerSemanticInput,
    source_commit: &str,
    nucleus: &str,
) -> String {
    let (domain, bits) = identity_transport(input.identity);
    format!(
        "(compiler-semantic-request\n           (schema . compiler-semantic-input/1)\n           (fixture-id . \"{fixture_id}\")\n           (ідентичність . ((domain . {domain}) (bits . {bits})))\n           (law . ((authority-ref . \"{}\") (proof-ref . \"{}\") (semantic-status . {})))\n           (mechanism . ((execution-role . {}) (mechanism-status . unknown) (mechanism-ref . ())))\n           (походження . ((repository . \"juv4uk/sens\") (revision . \"{source_commit}\") (authority-path . \"{}\") (authority-sha256 . \"{}\") (compiler-nucleus-sha256 . \"{}\") (contract . {}))))",
        input.authority_ref,
        input.proof_ref,
        input.semantic_status,
        role_name(input.lowering_role),
        input.authority_path,
        input.authority_sha256,
        sha256_hex(nucleus.as_bytes()),
        input.language_contract_version,
    )
}

fn render_artifact(fixture_id: &str, semantic_request: &str) -> String {
    let semantic_request_sha256 = sha256_hex(semantic_request.as_bytes());
    format!(
        "(compilation-artifact\n           (schema . compiler-compilation-artifact-1)\n           (fixture-id . \"{fixture_id}\")\n           (semantic-request-sha256 . \"{semantic_request_sha256}\")\n           (semantic-request . {semantic_request})\n           (required-capabilities . ())\n           (artifact-status . canonical-backend-neutral))"
    )
}

pub fn run(repo_root: &str, options: ExportOptions) -> Result<String, String> {
    let root = Path::new(repo_root);
    let source_commit = current_commit(root)?;
    let sources = compiler_sources()?;

    let rows = parse_fixture_rows(options.fixture.as_deref(), &sources.corpus)?;
    let mut rendered = Vec::with_capacity(rows.len());
    for (name, identity) in rows {
        let input = compiler_semantic_input(identity, &sources)
            .map_err(|error| format!("SENS semantic input production failed for {name}: {error}"))?
            .ok_or_else(|| format!("SENS compiler law returned no role for {name}"))?;

        let request = render_request(&name, &input, &source_commit, &sources.nucleus);
        rendered.push(if options.artifact {
            render_artifact(&name, &request)
        } else {
            request
        });
    }

    Ok(format!("{}\n", rendered.join("\n\n")))
}

