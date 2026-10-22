//! Guard Reference Schema Quality Gate / Гарантна перевірка якості схеми довідника.
//!
//! Fail-closed validation of guard-reference.lisp:
//! - Duplicate topics
//! - Missing authority files
//! - Empty authority/verify
//! - Unreviewed inbox entries (pending-review)

use sens::{parse_mixed_exact_domain_guard_reference_source, Expr, ExprKind};
use std::collections::HashSet;
use std::fs;
use std::path::{Path, PathBuf};

const MAX_TOPIC_LENGTH: usize = 64;

#[derive(Debug, Clone)]
struct TopicEntry {
    topic: String,
    summary: String,
    authority: Vec<String>,
    how_to: Vec<String>,
    verify: Vec<String>,
    lifecycle: String,
    provenance: String,
    unknown_route: String,
}

#[derive(Debug)]
struct ValidationResult {
    errors: Vec<String>,
    warnings: Vec<String>,
}

impl ValidationResult {
    fn new() -> Self {
        Self {
            errors: Vec::new(),
            warnings: Vec::new(),
        }
    }
    fn add_error(&mut self, msg: String) {
        self.errors.push(msg);
    }
    fn add_warning(&mut self, msg: String) {
        self.warnings.push(msg);
    }
    fn has_errors(&self) -> bool {
        !self.errors.is_empty()
    }
    fn print(&self) {
        for w in &self.warnings {
            eprintln!("WARN: {}", w);
        }
        for e in &self.errors {
            eprintln!("ERROR: {}", e);
        }
    }
}

/// Механічна перевірка точної доменної тотожності каталогу Guard.
/// D4:0011 і D3:001 задає SENS, Rust лише перевіряє збереження ширини AST.
fn check_directory_domain(expressions: &[Expr]) -> Result<(), String> {
    // Обидва каталоги мають самостійно точні D4/D3 координати.
    // Жоден історичний восьмибітний заголовок не отримує цього допуску.
    for name in ["*guard-reference-directory*", "*guard-script-directory*"] {
        let mut found = false;
        for expression in expressions {
            let ExprKind::List(items) = &expression.kind else {
                continue;
            };
            if !matches!(
                items.get(1),
                Some(Expr { kind: ExprKind::Symbol(symbol), .. })
                    if symbol.as_ref() == name
            ) {
                continue;
            }
            found = true;
            if !matches!(
                items.first(),
                Some(Expr { kind: ExprKind::DomainIdentity(id), .. })
                    if id.width() == 4 && id.packed_bits() == 0b0011
            ) {
                return Err(format!(
                    "{name} requires exact D4:0011 DEFINE; W8 is not D4"
                ));
            }
            let Some(Expr {
                kind: ExprKind::List(quoted),
                ..
            }) = items.get(2)
            else {
                return Err(format!("{name} requires an exact D3:001 quoted directory"));
            };
            if quoted.len() != 2
                || !matches!(
                    quoted.first(),
                    Some(Expr { kind: ExprKind::DomainIdentity(id), .. })
                        if id.width() == 3 && id.packed_bits() == 0b001
                )
            {
                return Err(format!("{name} requires exact D3:001 QUOTE; W8 is not D3"));
            }
        }
        if !found {
            return Err(format!("missing exact-domain directory definition: {name}"));
        }
    }
    Ok(())
}

fn parse_guard_reference(file_path: &Path) -> Result<Vec<TopicEntry>, String> {
    let content = fs::read_to_string(file_path)
        .map_err(|e| format!("cannot read {}: {}", file_path.display(), e))?;

    // Спільний path-bound exact-domain reader; без байтових припущень.
    let parsed =
        parse_mixed_exact_domain_guard_reference_source("knowledge/guard-reference.lisp", &content)
            .map_err(|error| {
                format!(
                    "cannot parse {}: {}",
                    file_path.display(),
                    error.render(&content)
                )
            })?;
    check_directory_domain(&parsed)
        .map_err(|reason| format!("invalid exact-domain {}: {reason}", file_path.display()))?;

    // The catalogue is intentionally formatted one field per line. Parsing
    // those records line-by-line keeps this quality gate independent of the
    // full evaluator while preserving quoted summaries and list fields.
    let mut entries = Vec::new();
    let mut current: Option<TopicEntry> = None;
    for line in content.lines().map(str::trim) {
        if line.contains("(reference") {
            if let Some(previous) = current.take() {
                if !previous.topic.is_empty() {
                    entries.push(previous);
                }
            }
            current = Some(TopicEntry {
                topic: String::new(),
                summary: String::new(),
                authority: Vec::new(),
                how_to: Vec::new(),
                verify: Vec::new(),
                lifecycle: String::new(),
                provenance: String::new(),
                unknown_route: String::new(),
            });
            continue;
        }
        let Some(entry) = current.as_mut() else {
            continue;
        };
        if line == ")" || line == "))" {
            if !entry.topic.is_empty() {
                entries.push(current.take().unwrap());
            }
            continue;
        }
        for (field, target) in [
            ("topic", 0),
            ("summary", 1),
            ("lifecycle", 2),
            ("provenance", 3),
            ("unknown-route", 4),
        ] {
            let prefix = format!("({field} ");
            if let Some(value) = line.strip_prefix(&prefix) {
                let value = value.trim_end_matches(')').trim_matches('"').to_string();
                match target {
                    0 => entry.topic = value,
                    1 => entry.summary = value,
                    2 => entry.lifecycle = value,
                    3 => entry.provenance = value,
                    _ => entry.unknown_route = value,
                }
            }
        }
        for (field, target) in [("authority", 0), ("how-to", 1), ("verify", 2)] {
            let prefix = format!("({field} (");
            if let Some(value) = line.strip_prefix(&prefix) {
                let values = value
                    .trim_end_matches(')')
                    .trim_end_matches(')')
                    .split_whitespace()
                    .map(|v| v.trim_matches('"').to_string());
                match target {
                    0 => entry.authority.extend(values),
                    1 => entry.how_to.extend(values),
                    _ => entry.verify.extend(values),
                }
            }
        }
    }
    if let Some(entry) = current {
        if !entry.topic.is_empty() {
            entries.push(entry);
        }
    }

    if entries.is_empty() {
        return Err("no reference entries found".into());
    }
    Ok(entries)
}

fn validate_entries(entries: &[TopicEntry], repo_root: &Path) -> ValidationResult {
    let mut result = ValidationResult::new();
    let mut seen_topics = HashSet::new();

    for entry in entries {
        if entry.topic.is_empty() {
            result.add_error("topic must not be empty".into());
        } else if entry.topic.len() > MAX_TOPIC_LENGTH {
            result.add_error(format!(
                "topic '{}' exceeds {} chars",
                entry.topic, MAX_TOPIC_LENGTH
            ));
        }
        if !seen_topics.insert(entry.topic.clone()) {
            result.add_error(format!("duplicate topic: {}", entry.topic));
        }
        if entry.summary.trim().is_empty() {
            result.add_error(format!(
                "topic '{}': summary must not be empty",
                entry.topic
            ));
        }
        if entry.authority.is_empty() {
            result.add_error(format!(
                "topic '{}': authority must not be empty",
                entry.topic
            ));
        } else {
            for auth in &entry.authority {
                // Cross-repository authorities (../...) are resolved by the
                // ecosystem Guard workflow, not by this repository-local CI.
                if auth.starts_with("../") {
                    continue;
                }
                let path = repo_root.join(auth);
                if !path.exists() {
                    result.add_error(format!(
                        "topic '{}': authority file not found: {} (checked: {})",
                        entry.topic,
                        auth,
                        path.display()
                    ));
                }
            }
        }
        if entry.verify.is_empty() {
            result.add_error(format!("topic '{}': verify must not be empty", entry.topic));
        }
        if entry.lifecycle.is_empty() {
            result.add_error(format!(
                "topic '{}': lifecycle must not be empty",
                entry.topic
            ));
        }
        if entry.provenance.is_empty() {
            result.add_error(format!(
                "topic '{}': provenance must not be empty",
                entry.topic
            ));
        }
        if entry.unknown_route.is_empty() {
            result.add_error(format!(
                "topic '{}': unknown-route must not be empty",
                entry.topic
            ));
        } else if !matches!(
            entry.unknown_route.as_str(),
            "ask-agent" | "ask-owner" | "research-web"
        ) {
            result.add_error(format!(
                "topic '{}': unknown-route must be ask-agent|ask-owner|research-web, got '{}'",
                entry.topic, entry.unknown_route
            ));
        }
    }

    result
}

fn validate_inbox(inbox_path: &Path) -> ValidationResult {
    let mut result = ValidationResult::new();
    if !inbox_path.exists() {
        result.add_warning(format!("inbox not found: {}", inbox_path.display()));
        return result;
    }
    let content = fs::read_to_string(inbox_path)
        .map_err(|e| format!("cannot read inbox: {}", e))
        .unwrap_or_default();
    let pending_count = content
        .lines()
        .filter(|l| !l.trim().is_empty() && !l.trim_start().starts_with(';'))
        .filter(|l| l.contains("pending-review"))
        .count();
    if pending_count > 0 {
        result.add_warning(format!(
            "{} unreviewed inbox entries (pending-review)",
            pending_count
        ));
    }
    result
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let check_inbox = args.iter().any(|a| a == "--check-inbox");

    let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let repo_root = manifest_dir.parent().unwrap().parent().unwrap(); // sens/
    let guard_ref_path = repo_root.join("knowledge/guard-reference.lisp");
    let inbox_path = repo_root.join("../../ecosystem/knowledge/guard-reference-inbox.mylog");

    let entries = match parse_guard_reference(&guard_ref_path) {
        Ok(e) => e,
        Err(e) => {
            eprintln!("ERROR: {}", e);
            std::process::exit(2);
        }
    };

    let mut result = validate_entries(&entries, repo_root);

    if check_inbox {
        let inbox_result = validate_inbox(&inbox_path);
        result.errors.extend(inbox_result.errors);
        result.warnings.extend(inbox_result.warnings);
    }

    result.print();

    if result.has_errors() {
        eprintln!(
            "\nSchema validation FAILED ({} errors)",
            result.errors.len()
        );
        std::process::exit(1);
    } else {
        println!("Schema validation PASSED: {} topics checked", entries.len());
        if !result.warnings.is_empty() {
            println!("Warnings: {}", result.warnings.len());
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    fn temp_file(contents: &str, label: &str) -> PathBuf {
        let path = std::env::temp_dir().join(format!(
            "guard-reference-schema-check-{label}-{}",
            std::process::id()
        ));
        fs::write(&path, contents).unwrap();
        path
    }

    fn sample_wsm() -> String {
        r#"(0011 *guard-reference-directory*
  (001
    ((reference
       (topic test-topic)
       (summary "Test summary")
       (authority (file1.md file2.md))
       (how-to (step1 step2))
       (verify (check1 check2))
       (lifecycle current-contract)
       (provenance commit abc123)
       (unknown-route ask-agent)))))
(0011 *guard-script-directory*
  (001
    ((tool (name test-script)))))"#
            .into()
    }

    #[test]
    fn parses_valid_entry() {
        let path = temp_file(&sample_wsm(), "valid");
        let entries = parse_guard_reference(&path).unwrap();
        assert_eq!(entries.len(), 1);
        assert_eq!(entries[0].topic, "test-topic");
        assert_eq!(entries[0].summary, "Test summary");
        assert_eq!(entries[0].lifecycle, "current-contract");
        assert_eq!(entries[0].unknown_route, "ask-agent");
        assert_eq!(entries[0].authority, vec!["file1.md", "file2.md"]);
        assert_eq!(entries[0].how_to, vec!["step1", "step2"]);
        assert_eq!(entries[0].verify, vec!["check1", "check2"]);
        fs::remove_file(path).unwrap();
    }

    #[test]
    fn rejects_historical_w8_quote_with_matching_payload() {
        let source = sample_wsm().replacen("(001\n", "(00000001\n", 1);
        let path = temp_file(&source, "wrong-quote-width");
        let failure = parse_guard_reference(&path).unwrap_err();
        assert!(failure.contains("D3:001 QUOTE"), "{failure}");
        fs::remove_file(path).unwrap();
    }

    #[test]
    fn rejects_historical_w8_define_with_matching_payload() {
        let source = sample_wsm().replacen("(0011 *guard", "(00001001 *guard", 1);
        let path = temp_file(&source, "wrong-define-width");
        let failure = parse_guard_reference(&path).unwrap_err();
        assert!(failure.contains("D4:0011 DEFINE"), "{failure}");
        fs::remove_file(path).unwrap();
    }

    #[test]
    fn rejects_w8_quote_for_script_directory_without_aliasing_d3() {
        let source = sample_wsm().replacen(
            "(0011 *guard-script-directory*\n  (001\n",
            "(0011 *guard-script-directory*\n  (00000001\n",
            1,
        );
        let path = temp_file(&source, "script-w8-quote");
        let failure = parse_guard_reference(&path).unwrap_err();
        assert!(failure.contains("*guard-script-directory*"), "{failure}");
        assert!(failure.contains("D3:001 QUOTE"), "{failure}");
        fs::remove_file(path).unwrap();
    }

    #[test]
    fn rejects_missing_exact_script_directory() {
        let source = sample_wsm()
            .split("\n(0011 *guard-script-directory*")
            .next()
            .unwrap()
            .to_string();
        let path = temp_file(&source, "missing-script-directory");
        let failure = parse_guard_reference(&path).unwrap_err();
        assert!(
            failure.contains("missing exact-domain directory definition"),
            "{failure}"
        );
        assert!(failure.contains("*guard-script-directory*"), "{failure}");
        fs::remove_file(path).unwrap();
    }

    #[test]
    fn catches_duplicate_topic() {
        let content = format!("{}\n{}", sample_wsm(), sample_wsm());
        let path = temp_file(&content, "duplicate");
        let entries = parse_guard_reference(&path).unwrap();
        let repo_root = std::env::current_dir().unwrap();
        let result = validate_entries(&entries, &repo_root);
        assert!(result.has_errors());
        assert!(result.errors.iter().any(|e| e.contains("duplicate topic")));
        fs::remove_file(path).unwrap();
    }

    #[test]
    fn catches_missing_authority() {
        let content = sample_wsm().replace("file1.md file2.md", "nonexistent.md");
        let path = temp_file(&content, "missing-authority");
        let entries = parse_guard_reference(&path).unwrap();
        let repo_root = std::env::current_dir().unwrap();
        let result = validate_entries(&entries, &repo_root);
        assert!(result.has_errors());
        assert!(result
            .errors
            .iter()
            .any(|e| e.contains("authority file not found")));
        fs::remove_file(path).unwrap();
    }

    #[test]
    fn catches_empty_fields() {
        let content = sample_wsm()
            .replace("(summary \"Test summary\")", "(summary \"\")")
            .replace("(lifecycle current-contract)", "(lifecycle \"\")");
        let path = temp_file(&content, "empty-fields");
        let entries = parse_guard_reference(&path).unwrap();
        let repo_root = std::env::current_dir().unwrap();
        let result = validate_entries(&entries, &repo_root);
        assert!(result.has_errors());
        assert!(result
            .errors
            .iter()
            .any(|e| e.contains("summary must not be empty")));
        assert!(result
            .errors
            .iter()
            .any(|e| e.contains("lifecycle must not be empty")));
        fs::remove_file(path).unwrap();
    }

    #[test]
    fn catches_invalid_unknown_route() {
        let content = sample_wsm().replace("(unknown-route ask-agent)", "(unknown-route guess)");
        let path = temp_file(&content, "invalid-route");
        let entries = parse_guard_reference(&path).unwrap();
        let repo_root = std::env::current_dir().unwrap();
        let result = validate_entries(&entries, &repo_root);
        assert!(result.has_errors());
        assert!(result
            .errors
            .iter()
            .any(|e| e.contains("unknown-route must be")));
        fs::remove_file(path).unwrap();
    }

    #[test]
    fn canonical_parse_gate_rejects_unbalanced_paren() {
        let content = format!("{}\n)", sample_wsm());
        let path = temp_file(&content, "unbalanced");
        let err = parse_guard_reference(&path).unwrap_err();
        assert!(err.contains("cannot parse"), "unexpected error: {}", err);
        assert!(
            err.contains("unexpected closing parenthesis"),
            "unexpected error: {}",
            err
        );
        fs::remove_file(path).unwrap();
    }

    #[test]
    fn canonical_parse_gate_accepts_balanced_directory() {
        let path = temp_file(&sample_wsm(), "balanced");
        let entries = parse_guard_reference(&path).unwrap();
        assert_eq!(entries.len(), 1);
        assert_eq!(entries[0].topic, "test-topic");
        fs::remove_file(path).unwrap();
    }
}
