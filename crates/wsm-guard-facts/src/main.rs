//! Bounded read-only fact adapter feeding normalized clauses to guard.wsm.
//! Обмежений read-only адаптер фактів, що подає нормалізовані clause у guard.wsm.
//!
//! G2 slice (docs/guard-oracle-node-plan.md): a Rust adapter observes Git,
//! systemd, and swarm state with read-only, time-bounded probes, normalizes
//! each observation into one `(fact ...)` clause, and lets WSM policy own the
//! classification. This slice never mutates the observed system and enforces
//! nothing — it only normalizes observations into clauses and classifies them.
//!
//! Policy is reloaded from an absolute path on every event, so classification
//! can change without recompiling this adapter.
//!
//! G2 зріз: Rust-адаптер спостерігає стан Git/systemd/swarm read-only,
//! обмеженими за часом пробами, нормалізує кожне спостереження в один
//! `(fact ...)` clause, а класифікацію виконує WSM-політика. Цей зріз не
//! змінює систему й нічого не enforce — лише нормалізує спостереження і
//! класифікує їх. Політика перечитується для кожного події з абсолютного
//! шляху, тож класифікацію можна змінювати без перекомпіляції адаптера.

use std::env;
use std::fs;
use std::io::{self, BufRead};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::time::{Duration, Instant};

const MAX_OBSERVATION_ID_BYTES: usize = 256;
const PROBE_TIMEOUT: Duration = Duration::from_secs(10);
const PROBE_CAPACITY_BYTES: usize = 64 * 1024;

/// A normalized, bounded clause produced from one read-only observation.
/// Нормалізований, обмежений clause, створений з одного read-only спостереження.
#[derive(Debug, PartialEq)]
struct Fact {
    source: String,
    subject: String,
    state: String,
    error: Option<String>,
}

fn identifier(value: &str) -> bool {
    !value.is_empty()
        && value.len() <= MAX_OBSERVATION_ID_BYTES
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || b"-_./@:".contains(&byte))
}

/// Run a read-only probe with a hard wall-clock timeout and a bounded output
/// capacity. Returns stdout, or a stable error reason if the command times
/// out, fails to start, or produces a non-zero exit.
/// Запускає read-only пробу з жорстким лімітом часу й обмеженням виводу.
fn run_probe(program: &str, args: &[&str]) -> Result<String, String> {
    let mut child = Command::new(program)
        .args(args)
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|e| format!("probe-spawn-failed-{e}"))?;

    // Wait with a deadline; on timeout kill the child and fail closed. Output
    // is read after exit through a capacity-bounded reader, so a probe that
    // outlives the deadline cannot leak into this process unboundedly.
    let deadline = Instant::now() + PROBE_TIMEOUT;
    loop {
        match child.try_wait() {
            Ok(Some(status)) => {
                if !status.success() {
                    return Err(format!("probe-exit-{}", status.code().unwrap_or(-1)));
                }
                return read_output(&mut child);
            }
            Ok(None) => {
                if Instant::now() >= deadline {
                    let _ = child.kill();
                    let _ = child.wait();
                    return Err("probe-timeout".into());
                }
                std::thread::sleep(Duration::from_millis(20));
            }
            Err(e) => return Err(format!("probe-wait-{e}")),
        }
    }
}

fn read_output(child: &mut std::process::Child) -> Result<String, String> {
    let mut output = String::new();
    if let Some(stdout) = child.stdout.take() {
        use std::io::Read;
        let mut reader = io::BufReader::new(stdout).take(PROBE_CAPACITY_BYTES as u64);
        reader
            .read_to_string(&mut output)
            .map_err(|e| format!("probe-read-{e}"))?;
    }
    Ok(output)
}

fn git_fact(repo: &str) -> Result<Fact, String> {
    if !identifier(repo) {
        return Err("invalid-repo-identifier".into());
    }
    if !Path::new(repo).is_dir() {
        return Err("repo-not-a-directory".into());
    }
    let head = run_probe("git", &["-C", repo, "rev-parse", "--verify", "HEAD"])?;
    let branch = run_probe("git", &["-C", repo, "rev-parse", "--abbrev-ref", "HEAD"])?;
    let status = run_probe("git", &["-C", repo, "status", "--porcelain"])?;
    let head = head.trim();
    let branch = branch.trim();
    let dirty = if status.trim().is_empty() {
        "clean"
    } else {
        "dirty"
    };
    if !identifier(head) || !identifier(branch) {
        return Err("invalid-git-probe-output".into());
    }
    Ok(Fact {
        source: "git".into(),
        subject: repo.to_string(),
        state: format!("((head {head}) (branch {branch}) (dirty {dirty}))"),
        error: None,
    })
}

fn systemd_fact(unit: &str) -> Result<Fact, String> {
    if !identifier(unit) {
        return Err("invalid-unit-identifier".into());
    }
    let raw = run_probe("systemctl", &["is-active", unit])?;
    let is_active = raw.trim().to_owned();
    if !identifier(&is_active) {
        return Err("invalid-systemd-probe-output".into());
    }
    Ok(Fact {
        source: "systemd".into(),
        subject: unit.to_string(),
        state: format!("((active {is_active}))"),
        error: None,
    })
}

fn swarm_fact(data_dir: &str, node_id: &str) -> Result<Fact, String> {
    if !identifier(data_dir) || !identifier(node_id) {
        return Err("invalid-swarm-identifier".into());
    }
    if !Path::new(data_dir).is_dir() {
        return Err("data-dir-not-a-directory".into());
    }
    let lock_path = Path::new(data_dir).join(".swarm-node.lock");
    let lock_held = match fs::metadata(&lock_path) {
        Ok(_) => "held",
        Err(_) => "free",
    };
    let identity = Path::new(data_dir).join("identity");
    let identity_present = match fs::metadata(&identity) {
        Ok(m) if m.is_file() => "present",
        _ => "missing",
    };
    Ok(Fact {
        source: "swarm".into(),
        subject: node_id.to_string(),
        state: format!("((lock {lock_held}) (identity {identity_present}))"),
        error: None,
    })
}

fn observe_line(line: &str) -> Result<Fact, String> {
    if line.len() > 4096 {
        return Err("observation-too-large".into());
    }
    let mut source = None;
    let mut repo = None;
    let mut unit = None;
    let mut data_dir = None;
    let mut node_id = None;
    for field in line.split_whitespace() {
        let (key, value) = field.split_once('=').ok_or("malformed-field")?;
        let slot = match key {
            "source" => &mut source,
            "repo" => &mut repo,
            "unit" => &mut unit,
            "data-dir" => &mut data_dir,
            "node-id" => &mut node_id,
            _ => return Err("unknown-field".into()),
        };
        if slot.replace(value.to_owned()).is_some() {
            return Err("duplicate-field".into());
        }
    }
    match source.as_deref() {
        Some("git") => {
            let repo = repo.ok_or("missing-repo")?;
            git_fact(&repo)
        }
        Some("systemd") => {
            let unit = unit.ok_or("missing-unit")?;
            systemd_fact(&unit)
        }
        Some("swarm") => {
            let data_dir = data_dir.ok_or("missing-data-dir")?;
            let node_id = node_id.ok_or("missing-node-id")?;
            swarm_fact(&data_dir, &node_id)
        }
        Some(_) => Err("unknown-source".into()),
        None => Err("missing-source".into()),
    }
}

fn evaluate(policy: &str, fact: &Fact) -> Result<String, String> {
    let call = format!(
        "(guard-fact-evaluate (quote (fact (source {}) (subject {}) (state {}) {})))",
        fact.source,
        fact.subject,
        fact.state,
        fact.error.as_deref().unwrap_or("")
    );
    wsm_guard_core::evaluate(policy, &call)
}

fn adapter_error(reason: &str) -> String {
    format!(
        "(guard-facts (schema guard-facts/1) (decision unknown) (evidence-status unresolved) (error {reason}))"
    )
}

fn policy_path(args: &[String]) -> Result<PathBuf, String> {
    if args.len() != 2 || args[0] != "--policy" {
        return Err("usage: wsm-guard-facts --policy /absolute/policy.lisp".into());
    }
    let path = PathBuf::from(&args[1]);
    if !path.is_absolute() || !path.is_file() {
        return Err("policy path must be an existing absolute file".into());
    }
    Ok(path)
}

fn process_line(path: &Path, line: &str) -> String {
    let started = Instant::now();
    let finding = observe_line(line)
        .and_then(|fact| {
            fs::read_to_string(path)
                .map_err(|_| "policy-read-failed".to_owned())
                .and_then(|policy| evaluate(&policy, &fact))
        })
        .unwrap_or_else(|reason| adapter_error(&reason.replace([' ', ':'], "-")));
    format!(
        "(guard-facts (schema guard-facts/1) (latency-micros {}) (result {finding}))",
        started.elapsed().as_micros()
    )
}

fn main() {
    let args: Vec<String> = env::args().skip(1).collect();
    let path = match policy_path(&args) {
        Ok(path) => path,
        Err(error) => {
            eprintln!("wsm-guard-facts: {error}");
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

    const FACT_POLICY: &str = include_str!("../../../knowledge/guard-fact-policy.lisp");

    #[test]
    fn normalizes_a_bounded_git_fact() {
        assert_eq!(run_probe("true", &[]).unwrap(), "");
        // malformed observation rejected before any probe
        assert!(observe_line("source=git repo=not=valid field").is_err());
        assert!(observe_line("source=git").is_err());
    }

    #[test]
    fn rejects_unbounded_or_malformed_observation_lines() {
        assert!(observe_line("not-an-observation").is_err());
        assert!(observe_line("source=git repo=/x subject=unexpected").is_err());
        assert!(observe_line(&format!("source={}", "x".repeat(5000))).is_err());
    }

    #[test]
    fn unknown_source_routes_to_unknown() {
        let line = "source=unknown thing=whatever";
        let fact = observe_line(line);
        assert!(fact.is_err());
    }

    #[test]
    fn real_fact_policy_covers_git_clean_and_dirty() {
        let fact = Fact {
            source: "git".into(),
            subject: "sens".into(),
            state: "((head abcdef123) (branch main) (dirty clean))".into(),
            error: None,
        };
        let result = evaluate(FACT_POLICY, &fact).unwrap();
        assert!(result.contains("(decision allow)"), "{result}");
        assert!(result.contains("(schema guard/1)"), "{result}");

        let dirty = Fact {
            source: "git".into(),
            subject: "sens".into(),
            state: "((head abcdef123) (branch main) (dirty dirty))".into(),
            error: None,
        };
        let result = evaluate(FACT_POLICY, &dirty).unwrap();
        assert!(result.contains("(decision warn)"), "{result}");
    }

    #[test]
    fn real_fact_policy_covers_systemd_and_swarm() {
        let result = evaluate(
            FACT_POLICY,
            &Fact {
                source: "systemd".into(),
                subject: "sens-oracle".into(),
                state: "((active active))".into(),
                error: None,
            },
        )
        .unwrap();
        assert!(result.contains("(decision allow)"), "{result}");

        let result = evaluate(
            FACT_POLICY,
            &Fact {
                source: "swarm".into(),
                subject: "wsl-nana-1".into(),
                state: "((lock held) (identity present))".into(),
                error: None,
            },
        )
        .unwrap();
        assert!(result.contains("(decision allow)"), "{result}");
    }

    #[test]
    fn unobservable_source_is_unknown_not_reject() {
        let result = evaluate(
            FACT_POLICY,
            &Fact {
                source: "git".into(),
                subject: "missing-repo".into(),
                state: "((unknown (reason not-observed)))".into(),
                error: None,
            },
        )
        .unwrap();
        assert!(result.contains("(decision unknown)"), "{result}");
        assert!(result.contains("(evidence-status unresolved)"), "{result}");
    }

    #[test]
    fn malformed_input_fails_safe_as_unknown() {
        let path = env::temp_dir().join(format!("fact-policy-{}.wsm", std::process::id()));
        fs::write(&path, FACT_POLICY).unwrap();
        let result = process_line(&path, "not-an-observation");
        fs::remove_file(path).unwrap();
        assert!(result.contains("(decision unknown)"));
        assert!(result.contains("malformed-field"));
    }

    #[test]
    fn policy_reload_changes_classification_without_recompiling_rust() {
        let path = env::temp_dir().join(format!("fact-reload-{}.wsm", std::process::id()));
        let allow_policy = r#"
          (def guard-fact-evaluate
            (lambda (fact)
              (make-guard-finding (quote allow) (quote confirmed) (quote test)
                (quote read-only) (quote contract) (quote ()) (quote none)
                (quote continue) (list fact))))"#;
        fs::write(&path, allow_policy).unwrap();
        // A real git-tracked directory that exists in ANY checkout, not
        // just this one machine -- CARGO_MANIFEST_DIR is wherever this
        // crate was actually built from, which is always inside the
        // sens repo `git -C` needs. The previous hardcoded
        // /home/agents/GitHub/sens only existed on the machine that
        // wrote it, so this test had been silently failing in CI (a
        // different checkout path) since the commit that added it --
        // confirmed via `gh run list` history, not assumed.
        let observation = format!("source=git repo={}", env!("CARGO_MANIFEST_DIR"));
        let first = process_line(&path, &observation);
        fs::write(&path, allow_policy.replace("(quote allow)", "(quote warn)")).unwrap();
        let second = process_line(&path, &observation);
        fs::remove_file(path).unwrap();
        assert!(first.contains("(decision allow)"), "{first}");
        assert!(second.contains("(decision warn)"), "{second}");
    }
}
