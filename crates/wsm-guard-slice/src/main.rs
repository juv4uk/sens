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
        "(guard-evaluate (як-є {}) (як-є {}) (як-є {}))",
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

