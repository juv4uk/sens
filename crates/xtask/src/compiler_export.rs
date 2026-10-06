//! Machine-readable export of the SENS-owned compiler semantic request.
//!
//! This module is transport only. Role meaning comes from
//! `compiler_lowering_role_from_sens`; this exporter never derives a role from
//! raw coordinates itself.

use sens::{
    compiler_lowering_role_from_sens, sha256_source, Bija3, Bit3, Bit4, CompilerLoweringRole,
    CoreD4, CoreDomainIdentity,
};
use std::path::Path;

const NUCLEUS: &str = include_str!("../../../lib/compiler-nucleus.lisp");
const D3_LAW: &str = include_str!("../../../knowledge/bija3-l1-l5-structure-projection.json");
const D4_LAW: &str =
    include_str!("../../../knowledge/d4-bootstrap-compiler-structure-projection.json");
const D3_CORPUS: &str = include_str!("../../../contracts/compiler-d3-selector-corpus-v1.tsv");

#[derive(Debug, Clone)]
pub struct ExportOptions {
    pub fixture: Option<String>,
}

fn sha256_hex(bytes: &[u8]) -> String {
    sha256_source(bytes)
        .iter()
        .map(|byte| format!("{byte:02x}"))
        .collect()
}

fn quoted_field(source: &str, key: &str) -> Result<String, String> {
    let marker = format!("\"{}\": \"", key);
    let start = source
        .find(&marker)
        .ok_or_else(|| format!("missing generated projection field {key}"))?
        + marker.len();
    let tail = &source[start..];
    let end = tail
        .find('"')
        .ok_or_else(|| format!("unterminated generated projection field {key}"))?;
    Ok(tail[..end].to_string())
}

fn authority_digest() -> Result<String, String> {
    let d3 = quoted_field(D3_LAW, "sha256")?;
    let d4 = quoted_field(D4_LAW, "sha256")?;
    Ok(sha256_hex(format!("{d3}\n{d4}").as_bytes()))
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

fn parse_identity(bits: &str) -> Result<CoreDomainIdentity, String> {
    if bits.len() != 3 || !bits.bytes().all(|b| matches!(b, b'0' | b'1')) {
        return Err(format!("unsupported D3 head bits {bits:?}"));
    }
    let raw = u8::from_str_radix(bits, 2)
        .map_err(|_| format!("invalid D3 head bits {bits:?}"))?;
    Ok(CoreDomainIdentity::D3(Bija3::from_word(
        Bit3::new(raw).ok_or_else(|| format!("invalid D3 value {raw}"))?,
    )))
}

fn parse_fixture_rows(
    fixture: Option<&str>,
) -> Result<Vec<(String, CoreDomainIdentity)>, String> {
    let mut rows = Vec::new();
    for line in CORPUS.lines() {
        let line = line.trim();
        if line.is_empty() || line.starts_with('#') {
            continue;
        }
        let fields: Vec<_> = line.split('\t').collect();
        if fields.len() != 6 {
            return Err(format!(
                "compiler corpus row has {} fields, expected 6: {line}",
                fields.len()
            ));
        }
        let name = fields[0].to_string();
        if let Some(requested) = fixture {
            if requested != name {
                continue;
            }
        }
        rows.push((name, parse_identity(fields[1])?));
    }
    if rows.is_empty() {
        return Err(match fixture {
            Some(name) => format!("compiler corpus fixture not found: {name}"),
            None => "compiler corpus is empty".into(),
        });
    }
    Ok(rows)
}

fn render_request(
    fixture_id: &str,
    identity: CoreDomainIdentity,
    role: CompilerLoweringRole,
    source_commit: &str,
    authority: &str,
) -> String {
    let bits = match identity {
        CoreDomainIdentity::D3(word) => format!("{:03b}", word.word().packed_bits()),
        _ => unreachable!("compiler export corpus is D3-only"),
    };
    format!(
        "(compiler-semantic-request\n           (schema . compiler-semantic-input/1)\n           (fixture-id . \"{fixture_id}\")\n           (identity . ((domain . D3) (bits . {bits})))\n           (law . ((authority-ref . \"knowledge/bija3-l1-l5-structure-projection.json\") (proof-ref . \"contracts/bija3-l1-l5-ratification.lisp\") (semantic-status . current)))\n           (mechanism . ((execution-role . {}) (mechanism-status . unknown) (mechanism-ref . ())))\n           (provenance . ((repository . \"juv4uk/sens\") (revision . \"{source_commit}\") (authority-path . \"knowledge/bija3-l1-l5-structure-projection.json\") (authority-sha256 . \"{authority}\") (compiler-nucleus-sha256 . \"{}\") (contract . 11.6))))",
        role_name(role),
        sha256_hex(NUCLEUS.as_bytes())
    )
}

pub fn run(repo_root: &str, options: ExportOptions) -> Result<String, String> {
    let root = Path::new(repo_root);
    let source_commit = current_commit(root)?;
    let authority = authority_digest()?;

    let rows = parse_fixture_rows(options.fixture.as_deref())?;
    let mut rendered = Vec::with_capacity(rows.len());
    for (name, identity) in rows {
        let role = compiler_lowering_role_from_sens(identity)
            .map_err(|error| format!("SENS role derivation failed for {name}: {error}"))?
            .ok_or_else(|| format!("SENS compiler law returned no role for {name}"))?;

        rendered.push(render_request(
            &name,
            identity,
            role,
            &source_commit,
            &authority,
        ));
    }

    Ok(format!("{}\n", rendered.join("\n\n")))
}
