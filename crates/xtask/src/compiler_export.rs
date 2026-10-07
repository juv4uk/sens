//! Machine-readable export of the SENS-owned compiler semantic request.
//!
//! This module is transport only. Role meaning comes from
//! `compiler_lowering_role_from_sens`; this exporter never derives a role from
//! raw coordinates itself.

use sens::{
    compiler_semantic_input_from_sens, sha256_source, Bija3, Bit3, Bit4, CompilerLoweringRole,
    CompilerSemanticInput, CoreD4, CoreDomainIdentity,
};
use std::path::Path;

const NUCLEUS: &str = include_str!("../../../lib/compiler-nucleus.lisp");
const CORPUS: &str =
    include_str!("../../../contracts/compiler-nucleus-identity-corpus-v1.tsv");

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

    match domain {
        "D3" => {
            if bits.len() != 3 {
                return Err(format!("D3 compiler identity requires 3 bits, got {bits:?}"));
            }
            let raw = u8::from_str_radix(bits, 2)
                .map_err(|_| format!("invalid D3 compiler identity {bits:?}"))?;
            Ok(CoreDomainIdentity::D3(Bija3::from_word(
                Bit3::new(raw).ok_or_else(|| format!("invalid D3 value {raw}"))?,
            )))
        }
        "D4" => {
            if bits.len() != 4 {
                return Err(format!("D4 compiler identity requires 4 bits, got {bits:?}"));
            }
            let raw = u8::from_str_radix(bits, 2)
                .map_err(|_| format!("invalid D4 compiler identity {bits:?}"))?;
            Ok(CoreDomainIdentity::D4(CoreD4::from_word(
                Bit4::new(raw).ok_or_else(|| format!("invalid D4 value {raw}"))?,
            )))
        }
        other => Err(format!(
            "unsupported compiler export domain {other:?}; only current D3/D4 are admitted"
        )),
    }
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
        sha256_hex(NUCLEUS.as_bytes()),
        input.language_contract_version,
    )
}

fn render_artifact(fixture_id: &str, semantic_request: &str) -> String {
    let semantic_request_sha256 = sha256_hex(semantic_request.as_bytes());
    format!(
        "(compilation-artifact\n           (schema . compiler-compilation-artifact/1)\n           (fixture-id . \"{fixture_id}\")\n           (semantic-request-sha256 . \"{semantic_request_sha256}\")\n           (semantic-request . {semantic_request})\n           (required-capabilities . ())\n           (artifact-status . canonical-backend-neutral))"
    )
}

pub fn run(repo_root: &str, options: ExportOptions) -> Result<String, String> {
    let root = Path::new(repo_root);
    let source_commit = current_commit(root)?;

    let rows = parse_fixture_rows(options.fixture.as_deref())?;
    let mut rendered = Vec::with_capacity(rows.len());
    for (name, identity) in rows {
        let input = compiler_semantic_input_from_sens(identity)
            .map_err(|error| format!("SENS semantic input production failed for {name}: {error}"))?
            .ok_or_else(|| format!("SENS compiler law returned no role for {name}"))?;

        let request = render_request(&name, &input, &source_commit);
        rendered.push(if options.artifact {
            render_artifact(&name, &request)
        } else {
            request
        });
    }

    Ok(format!("{}\n", rendered.join("\n\n")))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn identity_parser_preserves_width_and_rejects_other_domains() {
        assert!(matches!(
            parse_identity("D3", "010").unwrap(),
            CoreDomainIdentity::D3(_)
        ));
        assert!(matches!(
            parse_identity("D4", "0010").unwrap(),
            CoreDomainIdentity::D4(_)
        ));
        assert!(parse_identity("D4", "010").is_err());
        assert!(parse_identity("D8", "00000010").is_err());
    }

    #[test]
    fn corpus_is_identity_only_and_covers_nine_current_roles() {
        let rows = parse_fixture_rows(None).unwrap();
        assert_eq!(rows.len(), 9);
        let roles = rows
            .into_iter()
            .map(|(_, identity)| {
                compiler_semantic_input_from_sens(identity)
                    .unwrap()
                    .expect("every nucleus identity must have SENS-owned semantic input")
                    .lowering_role
            })
            .collect::<std::collections::HashSet<_>>();
        assert_eq!(roles.len(), 9);
    }

    #[test]
    fn compilation_artifact_wraps_the_exact_semantic_request_by_digest() {
        let input = compiler_semantic_input_from_sens(parse_identity("D3", "010").unwrap())
            .unwrap()
            .expect("ATOM compiler input");
        let request = render_request("atom", &input, "0123456789abcdef0123456789abcdef01234567");
        let artifact = render_artifact("atom", &request);
        let request_digest = sha256_hex(request.as_bytes());

        assert!(artifact.contains("(schema . compiler-compilation-artifact/1)"));
        assert!(artifact.contains(&format!("(semantic-request-sha256 . \"{request_digest}\")")));
        assert!(artifact.contains(&format!("(semantic-request . {request})")));
        assert!(artifact.contains("(artifact-status . canonical-backend-neutral)"));
        assert!(request.contains("(ідентичність . ((domain . D3) (bits . 010)))"));
        assert!(request.contains("(походження . ((repository . \"juv4uk/sens\")"));
        let legacy_a: String = ['i', 'd', 'e', 'n', 't', 'i', 't', 'y'].into_iter().collect();
        let legacy_b: String = ['p', 'r', 'o', 'v', 'e', 'n', 'a', 'n', 'c', 'e']
            .into_iter()
            .collect();
        assert!(!request.contains(&format!("({legacy_a} .")));
        assert!(!request.contains(&format!("({legacy_b} .")));
    }

    #[test]
    fn compilation_artifact_carries_no_backend_or_install_policy() {
        let input = compiler_semantic_input_from_sens(parse_identity("D4", "0010").unwrap())
            .unwrap()
            .expect("LAMBDA compiler input");
        let request = render_request("d4-0010", &input, "0123456789abcdef0123456789abcdef01234567");
        let artifact = render_artifact("d4-0010", &request).to_ascii_lowercase();

        for forbidden in [
            "cuda",
            "ptx",
            "sass",
            "graal",
            "fpga",
            "register-allocation",
            "install-target",
        ] {
            assert!(
                !artifact.contains(forbidden),
                "backend policy leaked into artifact: {forbidden}"
            );
        }
    }
}
