//! Minimal event-driven Rust mechanism for WSM Guard policy.
//! Мінімальний event-driven Rust-механізм для політики WSM Guard.
//!
//! Rust validates and frames one bounded event from each stdin line. WSM owns
//! the decision. The policy file is read again for every event, so policy can
//! change without recompiling or restarting this process.

use std::env;
use std::fs;
use std::io::{self, BufRead};
use std::path::{Path, PathBuf};
use std::time::Instant;

const MAX_EVENT_BYTES: usize = 16 * 1024;

#[derive(Debug, PartialEq)]
struct Event {
    kind: String,
    subject: String,
    evidence: String,
}

fn identifier(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= 256
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || b"-_./".contains(&byte))
}

fn parse_event(line: &str) -> Result<Event, String> {
    if line.len() > MAX_EVENT_BYTES {
        return Err("event-too-large".into());
    }
    let mut kind = None;
    let mut subject = None;
    let mut evidence = None;
    for field in line.split_whitespace() {
        let (key, value) = field.split_once('=').ok_or("malformed-field")?;
        if !identifier(value) {
            return Err("invalid-identifier".into());
        }
        let slot = match key {
            "kind" => &mut kind,
            "subject" => &mut subject,
            "evidence" => &mut evidence,
            _ => return Err("unknown-field".into()),
        };
        if slot.replace(value.to_owned()).is_some() {
            return Err("duplicate-field".into());
        }
    }
    Ok(Event {
        kind: kind.ok_or("missing-kind")?,
        subject: subject.ok_or("missing-subject")?,
        evidence: evidence.ok_or("missing-evidence")?,
    })
}

fn evaluate(policy: &str, event: &Event) -> Result<String, String> {
    let call = format!(
        "(guard-evaluate (quote {}) (quote {}) (quote {}))",
        event.kind, event.subject, event.evidence
    );
    wsm_guard_core::evaluate(policy, &call)
}

fn adapter_error(reason: &str) -> String {
    format!(
        "(guard-adapter-result (schema guard-adapter-1) (decision unknown) (evidence-status unresolved) (error {reason}))"
    )
}

fn policy_path(args: &[String]) -> Result<PathBuf, String> {
    if args.len() != 2 || args[0] != "--policy" {
        return Err("usage: wsm-guard-slice --policy /absolute/policy.lisp".into());
    }
    let path = PathBuf::from(&args[1]);
    if !path.is_absolute() || !path.is_file() {
        return Err("policy path must be an existing absolute file".into());
    }
    Ok(path)
}

fn process_line(path: &Path, line: &str) -> String {
    let started = Instant::now();
    let finding = parse_event(line)
        .and_then(|event| {
            fs::read_to_string(path)
                .map_err(|_| "policy-read-failed".to_owned())
                .and_then(|policy| evaluate(&policy, &event))
        })
        .unwrap_or_else(|reason| adapter_error(&reason.replace([' ', ':'], "-")));
    format!(
        "(guard-slice (schema guard-slice-1) (latency-micros {}) (result {finding}))",
        started.elapsed().as_micros()
    )
}

fn main() {
    let args: Vec<String> = env::args().skip(1).collect();
    let path = match policy_path(&args) {
        Ok(path) => path,
        Err(error) => {
            eprintln!("wsm-guard-slice: {error}");
            std::process::exit(2);
        }
    };
    for line in io::stdin().lock().lines() {
        match line {
            Ok(line) if !line.trim().is_empty() => println!("{}", process_line(&path, &line)),
            Ok(_) => {}
            Err(error) => {
                println!("{}", adapter_error(&format!("stdin-{error}")));
                break;
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    const DEFAULT_POLICY: &str = include_str!("../../../knowledge/guard-runtime-policy.lisp");
    const ALLOW_POLICY: &str = r#"
      (визначити guard-evaluate
        (функція (вид суб'єкт докази)
          (створити-захист-висновок (як-є allow) (як-є confirmed) суб'єкт вид
            (як-є test-contract) (як-є ()) (як-є no-impact)
            (як-є no-action) (список докази))))"#;

    #[test]
    fn parses_only_bounded_normalized_events() {
        assert_eq!(
            parse_event("kind=read subject=swarm/tasks evidence=confirmed").unwrap(),
            Event {
                kind: "read".into(),
                subject: "swarm/tasks".into(),
                evidence: "confirmed".into()
            }
        );
        assert!(parse_event("kind=read subject=(evil) evidence=x").is_err());
        assert!(parse_event("kind=read subject=x").is_err());
        assert!(parse_event("kind=read kind=write subject=x evidence=y").is_err());
    }

    #[test]
    fn event_frame_rejects_overlong_duplicate_unknown_and_non_ascii_fields() {
        // Лише Rust-механізм межі вводу; не перевіряємо рішення SENS.
        let oversized = format!(
            "kind=read subject={} evidence=ok",
            "a".repeat(MAX_EVENT_BYTES)
        );
        assert_eq!(parse_event(&oversized), Err("event-too-large".into()));
        assert_eq!(
            parse_event("kind=read subject=docs evidence=ok extra=x"),
            Err("unknown-field".into())
        );
        assert_eq!(
            parse_event("kind=read subject=docs evidence=ok evidence=other"),
            Err("duplicate-field".into())
        );
        assert_eq!(
            parse_event("kind=read subject=ціль evidence=ok"),
            Err("invalid-identifier".into())
        );
    }

    #[test]
    fn real_wsm_policy_returns_structured_decision() {
        let result = evaluate(
            ALLOW_POLICY,
            &Event {
                kind: "read".into(),
                subject: "docs".into(),
                evidence: "confirmed".into(),
            },
        )
        .unwrap();
        assert!(result.contains("(decision allow)"));
        assert!(result.contains("(schema guard-1)"));
    }

    #[test]
    fn default_policy_covers_all_four_decisions() {
        for (kind, evidence, expected) in [
            ("read", "confirmed", "allow"),
            ("write", "partial", "warn"),
            ("destructive", "confirmed", "reject"),
            ("other", "missing", "unknown"),
        ] {
            let result = evaluate(
                DEFAULT_POLICY,
                &Event {
                    kind: kind.into(),
                    subject: "test-subject".into(),
                    evidence: evidence.into(),
                },
            )
            .unwrap();
            assert!(
                result.contains(&format!("(decision {expected})")),
                "{result}"
            );
        }
    }

    #[test]
    fn malformed_input_fails_safe_as_unknown() {
        let path = env::temp_dir().join(format!("guard-policy-{}.wsm", std::process::id()));
        fs::write(&path, ALLOW_POLICY).unwrap();
        let result = process_line(&path, "not-an-event");
        fs::remove_file(path).unwrap();
        assert!(result.contains("(decision unknown)"));
        assert!(result.contains("malformed-field"));
    }

    #[test]
    fn policy_reload_changes_decision_without_recompiling_rust() {
        let path = env::temp_dir().join(format!("guard-reload-{}.wsm", std::process::id()));
        fs::write(&path, ALLOW_POLICY).unwrap();
        let first = process_line(&path, "kind=read subject=docs evidence=confirmed");
        fs::write(&path, ALLOW_POLICY.replace("(quote allow)", "(quote warn)")).unwrap();
        let second = process_line(&path, "kind=read subject=docs evidence=confirmed");
        fs::remove_file(path).unwrap();
        assert!(first.contains("(decision allow)"));
        assert!(second.contains("(decision warn)"));
    }
}
