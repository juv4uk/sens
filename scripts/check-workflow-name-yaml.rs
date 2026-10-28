//! Host-only GitHub Actions YAML guard: unquoted ": " after name: is invalid YAML.
//! No SENS semantics, JSON or third-party dependency. Scans every active workflow.
//! Usage: rustc --edition=2021 scripts/check-workflow-name-yaml.rs -o /tmp/workflow-names && /tmp/workflow-names

use std::{fs, path::Path, process::ExitCode};

fn invalid_name_line(line: &str) -> bool {
    let trimmed = line.trim_start();
    if trimmed.starts_with('#') {
        return false;
    }
    let mapping = trimmed.strip_prefix("- ").unwrap_or(trimmed);
    let Some(value) = mapping.strip_prefix("name:") else {
        return false;
    };
    let value = value.trim_start();
    if value.starts_with('"')
        || value.starts_with('\'')
        || value.starts_with('|')
        || value.starts_with('>')
    {
        return false;
    }
    let value = value.split(" #").next().unwrap_or(value);
    value.as_bytes().windows(2).any(|pair| pair == b": ")
}

fn audit(dir: &Path) -> Result<usize, String> {
    let entries = fs::read_dir(dir)
        .map_err(|error| format!("cannot read {}: {error}", dir.display()))?;
    let mut workflows = Vec::new();
    for entry in entries {
        let entry = entry.map_err(|error| format!("cannot enumerate workflows: {error}"))?;
        let path = entry.path();
        if matches!(path.extension().and_then(|e| e.to_str()), Some("yml" | "yaml")) {
            workflows.push(path);
        }
    }
    workflows.sort();
    if workflows.is_empty() {
        return Err("no GitHub Actions workflows: refusing false green".into());
    }
    let mut violations = 0;
    for path in &workflows {
        let source = fs::read_to_string(path)
            .map_err(|error| format!("cannot read {}: {error}", path.display()))?;
        for (index, line) in source.lines().enumerate() {
            if invalid_name_line(line) {
                eprintln!(
                    "WORKFLOW_YAML_INVALID path={} line={} reason=unquoted-colon-space-in-name",
                    path.display(),
                    index + 1,
                );
                violations += 1;
            }
        }
    }
    if violations > 0 {
        Err(format!("{violations} invalid workflow name scalar(s)"))
    } else {
        Ok(workflows.len())
    }
}

fn main() -> ExitCode {
    match audit(Path::new(".github/workflows")) {
        Ok(scanned) => {
            println!("WORKFLOW_YAML_NAME_GUARD=PASS scanned={scanned} scope=unquoted-colon-space");
            ExitCode::SUCCESS
        }
        Err(error) => {
            eprintln!("WORKFLOW_YAML_NAME_GUARD=RED {error}");
            ExitCode::from(1)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::invalid_name_line;

    #[test]
    fn rejects_the_actual_github_actions_incident() {
        assert!(invalid_name_line("name: SENS — three lanes: Rust Zig SENS"));
        assert!(invalid_name_line("  - name: Work: Rust mechanism"));
    }

    #[test]
    fn permits_quoted_names_comments_and_block_scalars() {
        assert!(!invalid_name_line("name: \"SENS: Rust, Zig, SENS\""));
        assert!(!invalid_name_line("  - name: 'Rust: mechanism'"));
        assert!(!invalid_name_line("name: Safe title # comment: explanatory"));
        assert!(!invalid_name_line("name: >"));
        assert!(!invalid_name_line("# name: Broken: commented out"));
    }

    #[test]
    fn ignores_unrelated_yaml_keys_and_run_script_text() {
        assert!(!invalid_name_line("runs-on: ubuntu-latest"));
        assert!(!invalid_name_line("  echo \"notice: text\""));
        assert!(!invalid_name_line("run: |"));
    }
}
