//! Durable candidate intake for the WSM Guard reference bureau.
//! Довговічний прийом кандидатів до довідкового бюро WSM Guard.
//!
//! This tool never writes to the curated WSM directory itself. `propose`
//! appends a bounded, provenance-bearing candidate record; `promote`/`reject`
//! append a review verdict for an existing candidate, identified by its
//! (topic, recorded-at-unix) pair. Writing the actual `(reference ...)` entry
//! into `*guard-reference-directory*` after a `promoted` verdict stays a
//! separate, manual editorial act — this tool only makes a candidate's review
//! status durable and visible, so `list --pending` can show what still has no
//! verdict instead of every candidate looking permanently unreviewed.

use std::fs::OpenOptions;
use std::io::Write;
use std::path::PathBuf;
use std::time::{SystemTime, UNIX_EPOCH};

const MAX_FIELD_BYTES: usize = 64 * 1024;

#[derive(Debug, PartialEq)]
struct Candidate {
    topic: String,
    question: String,
    answer: String,
    source: String,
    route: String,
    evidence: String,
}

fn sexpr_string(value: &str) -> String {
    let mut out = String::with_capacity(value.len() + 2);
    out.push('"');
    for ch in value.chars() {
        match ch {
            '\\' => out.push_str("\\\\"),
            '"' => out.push_str("\\\""),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            other => out.push(other),
        }
    }
    out.push('"');
    out
}

fn validate(candidate: &Candidate) -> Result<(), String> {
    for (name, value) in [
        ("topic", &candidate.topic),
        ("question", &candidate.question),
        ("answer", &candidate.answer),
        ("source", &candidate.source),
        ("evidence", &candidate.evidence),
    ] {
        if value.trim().is_empty() {
            return Err(format!("{name} must not be empty"));
        }
        if value.len() > MAX_FIELD_BYTES {
            return Err(format!("{name} exceeds {MAX_FIELD_BYTES} bytes"));
        }
    }
    if !matches!(
        candidate.route.as_str(),
        "ask-agent" | "ask-owner" | "research-web"
    ) {
        return Err("route must be ask-agent, ask-owner, or research-web".into());
    }
    Ok(())
}

fn render(candidate: &Candidate, recorded_at: u64) -> String {
    format!(
        "(reference-candidate (schema guard-reference-candidate/1) (status pending-review) (recorded-at-unix {recorded_at}) (route {}) (topic {}) (question {}) (answer {}) (source {}) (evidence {}))",
        candidate.route,
        sexpr_string(&candidate.topic),
        sexpr_string(&candidate.question),
        sexpr_string(&candidate.answer),
        sexpr_string(&candidate.source),
        sexpr_string(&candidate.evidence),
    )
}

fn field(args: &[String], name: &str) -> Result<String, String> {
    let position = args
        .iter()
        .position(|arg| arg == name)
        .ok_or_else(|| format!("missing {name}"))?;
    args.get(position + 1)
        .cloned()
        .ok_or_else(|| format!("missing value after {name}"))
}

struct Review {
    topic: String,
    recorded_at_unix: u64,
    status: &'static str,
    reviewer: String,
    note: String,
}

fn validate_review(review: &Review) -> Result<(), String> {
    for (name, value) in [
        ("topic", &review.topic),
        ("reviewer", &review.reviewer),
    ] {
        if value.trim().is_empty() {
            return Err(format!("{name} must not be empty"));
        }
        if value.len() > MAX_FIELD_BYTES {
            return Err(format!("{name} exceeds {MAX_FIELD_BYTES} bytes"));
        }
    }
    if review.status == "rejected" && review.note.trim().is_empty() {
        return Err("reject requires a non-empty --note reason".into());
    }
    if review.note.len() > MAX_FIELD_BYTES {
        return Err(format!("note exceeds {MAX_FIELD_BYTES} bytes"));
    }
    Ok(())
}

fn render_review(review: &Review, reviewed_at: u64) -> String {
    format!(
        "(reference-candidate-review (schema guard-reference-candidate-review/1) (topic {}) (recorded-at-unix {}) (status {}) (reviewed-at-unix {reviewed_at}) (reviewer {}) (note {}))",
        sexpr_string(&review.topic),
        review.recorded_at_unix,
        review.status,
        sexpr_string(&review.reviewer),
        sexpr_string(&review.note),
    )
}

/// Extracts one `(name "quoted value")` field's inner text from a rendered
/// record line. This is a bounded scan for this tool's own fixed output
/// shape, not a general S-expression reader.
fn extract_quoted_field(line: &str, name: &str) -> Option<String> {
    let marker = format!("({name} \"");
    let start = line.find(&marker)? + marker.len();
    let rest = &line[start..];
    let mut out = String::new();
    let mut chars = rest.chars();
    while let Some(ch) = chars.next() {
        match ch {
            '\\' => match chars.next()? {
                'n' => out.push('\n'),
                'r' => out.push('\r'),
                't' => out.push('\t'),
                other => out.push(other),
            },
            '"' => return Some(out),
            other => out.push(other),
        }
    }
    None
}

fn extract_bare_field(line: &str, name: &str) -> Option<String> {
    let marker = format!("({name} ");
    let start = line.find(&marker)? + marker.len();
    let rest = &line[start..];
    let end = rest.find(')')?;
    Some(rest[..end].to_string())
}

fn review_key(line: &str) -> Option<(String, u64)> {
    let topic = extract_quoted_field(line, "topic")?;
    let recorded_at_unix = extract_bare_field(line, "recorded-at-unix")?
        .parse::<u64>()
        .ok()?;
    Some((topic, recorded_at_unix))
}

fn propose(args: &[String]) -> Result<(), String> {
    let inbox = PathBuf::from(field(args, "--inbox")?);
    if !inbox.is_absolute() {
        return Err("--inbox must be an absolute path".into());
    }
    let candidate = Candidate {
        topic: field(args, "--topic")?,
        question: field(args, "--question")?,
        answer: field(args, "--answer")?,
        source: field(args, "--source")?,
        route: field(args, "--route")?,
        evidence: field(args, "--evidence")?,
    };
    validate(&candidate)?;
    let recorded_at = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|error| error.to_string())?
        .as_secs();
    let mut file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&inbox)
        .map_err(|error| format!("cannot open {}: {error}", inbox.display()))?;
    writeln!(file, "{}", render(&candidate, recorded_at)).map_err(|error| error.to_string())?;
    file.sync_data().map_err(|error| error.to_string())?;
    println!("recorded pending-review candidate in {}", inbox.display());
    Ok(())
}

fn review(args: &[String], status: &'static str) -> Result<(), String> {
    let inbox = PathBuf::from(field(args, "--inbox")?);
    if !inbox.is_absolute() {
        return Err("--inbox must be an absolute path".into());
    }
    let review = Review {
        topic: field(args, "--topic")?,
        recorded_at_unix: field(args, "--recorded-at-unix")?
            .parse::<u64>()
            .map_err(|_| "--recorded-at-unix must be a non-negative integer".to_string())?,
        status,
        reviewer: field(args, "--reviewer")?,
        note: field(args, "--note").unwrap_or_default(),
    };
    validate_review(&review)?;
    if !std::fs::read_to_string(&inbox)
        .map_err(|error| format!("cannot open {}: {error}", inbox.display()))?
        .lines()
        .any(|line| review_key(line) == Some((review.topic.clone(), review.recorded_at_unix)))
    {
        return Err(format!(
            "no candidate with topic {:?} and --recorded-at-unix {} found in {}",
            review.topic,
            review.recorded_at_unix,
            inbox.display()
        ));
    }
    let reviewed_at = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|error| error.to_string())?
        .as_secs();
    let mut file = OpenOptions::new()
        .append(true)
        .open(&inbox)
        .map_err(|error| format!("cannot open {}: {error}", inbox.display()))?;
    writeln!(file, "{}", render_review(&review, reviewed_at)).map_err(|error| error.to_string())?;
    file.sync_data().map_err(|error| error.to_string())?;
    println!("recorded {status} verdict in {}", inbox.display());
    Ok(())
}

fn list_lines(text: &str, pending_only: bool) -> Vec<String> {
    let lines: Vec<&str> = text
        .lines()
        .filter(|line| !line.trim().is_empty() && !line.trim_start().starts_with(';'))
        .collect();
    let decided: std::collections::HashSet<(String, u64)> = lines
        .iter()
        .filter(|line| line.contains("(reference-candidate-review "))
        .filter_map(|line| review_key(line))
        .collect();
    lines
        .into_iter()
        .filter(|line| {
            if !pending_only {
                return true;
            }
            if !line.contains("(reference-candidate ") {
                return false;
            }
            !matches!(review_key(line), Some(key) if decided.contains(&key))
        })
        .map(str::to_string)
        .collect()
}

fn list(args: &[String]) -> Result<(), String> {
    let inbox = PathBuf::from(field(args, "--inbox")?);
    let pending_only = args.iter().any(|arg| arg == "--pending");
    let text = std::fs::read_to_string(&inbox)
        .map_err(|error| format!("cannot open {}: {error}", inbox.display()))?;
    for line in list_lines(&text, pending_only) {
        println!("{line}");
    }
    Ok(())
}

fn usage() {
    eprintln!(
        "guard-reference propose --inbox ABS --topic T --question Q --answer A --source S --route ask-agent|ask-owner|research-web --evidence E\n\
         guard-reference promote --inbox ABS --topic T --recorded-at-unix N --reviewer R [--note TEXT]\n\
         guard-reference reject --inbox ABS --topic T --recorded-at-unix N --reviewer R --note TEXT\n\
         guard-reference list --inbox ABS [--pending]"
    );
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let result = match args.first().map(String::as_str) {
        Some("propose") => propose(&args[1..]),
        Some("promote") => review(&args[1..], "promoted"),
        Some("reject") => review(&args[1..], "rejected"),
        Some("list") => list(&args[1..]),
        _ => {
            usage();
            Err("expected propose, promote, reject, or list".into())
        }
    };
    if let Err(error) = result {
        eprintln!("guard-reference: {error}");
        std::process::exit(2);
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn candidate(route: &str) -> Candidate {
        Candidate {
            topic: "guix".into(),
            question: "How do I build a relocatable pack?".into(),
            answer: "Use the reviewed Guix workflow.".into(),
            source: "agent:sakshi".into(),
            route: route.into(),
            evidence: "docs/VIVEKA-FINDINGS-2026-08-24.md#5".into(),
        }
    }

    #[test]
    fn renders_data_without_evaluating_or_losing_provenance() {
        let record = render(&candidate("ask-agent"), 42);
        assert!(record.starts_with("(reference-candidate"));
        assert!(record.contains("(status pending-review)"));
        assert!(record.contains("(recorded-at-unix 42)"));
        assert!(record.contains("(route ask-agent)"));
        assert!(record.contains("(source \"agent:sakshi\")"));
    }

    #[test]
    fn accepts_only_the_three_unknown_routes() {
        assert!(validate(&candidate("ask-agent")).is_ok());
        assert!(validate(&candidate("ask-owner")).is_ok());
        assert!(validate(&candidate("research-web")).is_ok());
        assert!(validate(&candidate("guess")).is_err());
    }

    #[test]
    fn escapes_candidate_text_as_data() {
        assert_eq!(sexpr_string("a\n\"b\"\\c"), "\"a\\n\\\"b\\\"\\\\c\"");
    }

    fn review(status: &'static str, note: &str) -> Review {
        Review {
            topic: "guix".into(),
            recorded_at_unix: 42,
            status,
            reviewer: "agent:ganaka".into(),
            note: note.into(),
        }
    }

    #[test]
    fn renders_a_review_verdict_keyed_by_topic_and_recorded_at() {
        let record = render_review(&review("promoted", "matches lib/guard.lisp shape"), 99);
        assert!(record.starts_with("(reference-candidate-review"));
        assert!(record.contains("(topic \"guix\")"));
        assert!(record.contains("(recorded-at-unix 42)"));
        assert!(record.contains("(status promoted)"));
        assert!(record.contains("(reviewed-at-unix 99)"));
        assert!(record.contains("(reviewer \"agent:ganaka\")"));
    }

    #[test]
    fn reject_requires_a_reason_but_promote_does_not() {
        assert!(validate_review(&review("rejected", "")).is_err());
        assert!(validate_review(&review("rejected", "no evidence")).is_ok());
        assert!(validate_review(&review("promoted", "")).is_ok());
    }

    #[test]
    fn extracts_topic_and_recorded_at_from_a_rendered_candidate_line() {
        let candidate = candidate("ask-agent");
        let line = render(&candidate, 42);
        assert_eq!(review_key(&line), Some(("guix".to_string(), 42)));
    }

    #[test]
    fn review_key_ignores_the_reviewed_at_timestamp() {
        let line = render_review(&review("promoted", "ok"), 12345);
        assert_eq!(review_key(&line), Some(("guix".to_string(), 42)));
    }

    #[test]
    fn list_pending_hides_a_candidate_once_any_review_verdict_names_it() {
        let reviewed = render(&candidate("ask-agent"), 42);
        let still_pending = render(
            &Candidate {
                topic: "other".into(),
                ..candidate("ask-agent")
            },
            43,
        );
        let verdict = render_review(&review("rejected", "stale"), 99);
        let text = format!("{reviewed}\n{still_pending}\n{verdict}\n");

        let all = list_lines(&text, false);
        assert_eq!(all.len(), 3, "unfiltered list keeps candidates and verdicts");

        let pending = list_lines(&text, true);
        assert_eq!(pending, vec![still_pending]);
    }
}
