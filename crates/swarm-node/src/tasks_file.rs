//! Reads the ecosystem's durable `tasks.lisp` format (the same dotted-alist
//! convention `sens`'s `:9999` `sync-tasks`/`sync-milestone` ops read) so
//! `swarm-node` can absorb the same durable plan files as part of the M0.5
//! migration off `:9999` for coordination traffic.

use crate::sexpr::Sexp;

#[derive(Debug, Clone, Default)]
pub struct ParsedTask {
    pub id: String,
    pub priority: f64,
    pub capabilities: Vec<String>,
    pub depends_on: Vec<String>,
    pub done: bool,
    pub description: Option<String>,
    /// Owning repository id, e.g. "cml" (M1.1b provenance). Absent = the
    /// file doesn't declare it; sync-tasks may fill a msg-level default.
    pub origin: Option<String>,
}

/// `(key . value)` pairs written as a 3-element list `[key, ".", value]` —
/// look up `key` in a list of such pairs.
fn dotted_get<'a>(pairs: &'a [Sexp], key: &str) -> Option<&'a Sexp> {
    pairs.iter().find_map(|entry| {
        let Sexp::List(items) = entry else {
            return None;
        };
        match items.as_slice() {
            [Sexp::Atom(k), Sexp::Atom(dot), value] if dot == "." && k == key => Some(value),
            _ => None,
        }
    })
}

fn atoms_of(sexp: &Sexp) -> Vec<String> {
    match sexp {
        Sexp::List(items) => items
            .iter()
            .filter_map(|i| match i {
                Sexp::Atom(s) | Sexp::Str(s) => Some(s.clone()),
                _ => None,
            })
            .collect(),
        _ => Vec::new(),
    }
}

fn atom_text(sexp: &Sexp) -> Option<String> {
    match sexp {
        Sexp::Atom(s) | Sexp::Str(s) => Some(s.clone()),
        _ => None,
    }
}

/// Parse task priority while preserving the historical decimal surface and
/// admitting exact binary integer metadata used by current binary-first tasks.
///
/// A present-but-malformed priority is an error at the call site. Only an
/// absent priority receives the historical default.
fn parse_priority_atom(raw: &str) -> Option<f64> {
    if let Some(bits) = raw.strip_prefix("#b") {
        if bits.is_empty() || !bits.bytes().all(|byte| matches!(byte, b'0' | b'1')) {
            return None;
        }
        return u64::from_str_radix(bits, 2).ok().map(|value| value as f64);
    }
    raw.parse::<f64>().ok()
}

/// A task's `done` value is `t` in two shapes actually used across this
/// ecosystem's `tasks.lisp` files: the bare `(done . t)`, and the
/// evidence-carrying `(done . (t . "who/when/what happened"))` -- the
/// dotted pair's own car is still the atom `t`, its cdr is just a record
/// of proof rather than nothing. Treat both as done; only `(done . ())`
/// (or the field's absence) is not-done.
fn is_done_value(sexp: &Sexp) -> bool {
    if atom_text(sexp).as_deref() == Some("t") {
        return true;
    }
    let Sexp::List(items) = sexp else {
        return false;
    };
    matches!(items.as_slice(), [Sexp::Atom(t), Sexp::Atom(dot), _] if t == "t" && dot == ".")
}

/// Parses a whole `tasks.lisp` document: `((kind . tasks-my) (tasks . ((ID .
/// ((priority . N) (capabilities . (a b)) (depends-on . (x y)) (done . t)
/// (description . "..."))) ...)))`. Returns `Err` with a human-readable
/// reason (not a `(line, column)` location — that level of precision was
/// worth building for `:9999`'s interactive `validate-tasks`, not worth
/// duplicating here yet) on structural problems.
pub fn parse_tasks_file(text: &str) -> Result<Vec<ParsedTask>, String> {
    let top = crate::sexpr::parse(text)?;
    let Sexp::List(top_items) = &top else {
        return Err("top-level form must be a list".to_string());
    };
    let tasks_field = dotted_get(top_items, "tasks").ok_or("missing `tasks` field")?;
    let Sexp::List(task_entries) = tasks_field else {
        return Err("`tasks` field must be a list".to_string());
    };

    let mut parsed = Vec::new();
    for entry in task_entries {
        let Sexp::List(items) = entry else {
            return Err(format!("malformed task entry: {}", entry.to_text()));
        };
        let (id_sexp, dot, fields_sexp) = match items.as_slice() {
            [id, dot, fields] => (id, dot, fields),
            _ => return Err(format!("malformed task entry: {}", entry.to_text())),
        };
        if atom_text(dot).as_deref() != Some(".") {
            return Err(format!(
                "malformed task entry (expected `ID . (fields)`): {}",
                entry.to_text()
            ));
        }
        let id = atom_text(id_sexp)
            .ok_or_else(|| format!("task id must be an atom or string: {}", id_sexp.to_text()))?;
        let Sexp::List(fields) = fields_sexp else {
            return Err(format!("task `{id}` fields must be a list"));
        };

        let priority = match dotted_get(fields, "priority").and_then(atom_text) {
            Some(raw) => parse_priority_atom(&raw)
                .ok_or_else(|| format!("task `{id}` has invalid priority `{raw}`"))?,
            None => 1.0,
        };
        let capabilities = dotted_get(fields, "capabilities")
            .map(atoms_of)
            .unwrap_or_default();
        let depends_on = dotted_get(fields, "depends-on")
            .map(atoms_of)
            .unwrap_or_default();
        let done = dotted_get(fields, "done")
            .map(is_done_value)
            .unwrap_or(false);
        let description = dotted_get(fields, "description").and_then(atom_text);
        let origin = dotted_get(fields, "origin").and_then(atom_text);

        parsed.push(ParsedTask {
            id,
            priority,
            capabilities,
            depends_on,
            done,
            description,
            origin,
        });
    }
    Ok(parsed)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_the_ecosystem_tasks_my_shape() {
        let text = r#"
; a comment
((kind . tasks-my)
 (tasks .
  (("SWARM-P2P-CLIENT" . ((priority . 0.9) (capabilities . (lisp docs rust))
                          (done . t)))
   ("SWARM-P2P-HEARTBEAT" . ((priority . 0.7) (capabilities . (lisp docs))
                             (depends-on . ("SWARM-P2P-SYNC")))))))
"#;
        let tasks = parse_tasks_file(text).unwrap();
        assert_eq!(tasks.len(), 2);
        assert_eq!(tasks[0].id, "SWARM-P2P-CLIENT");
        assert_eq!(tasks[0].priority, 0.9);
        assert_eq!(tasks[0].capabilities, vec!["lisp", "docs", "rust"]);
        assert!(tasks[0].done);
        assert_eq!(tasks[1].id, "SWARM-P2P-HEARTBEAT");
        assert_eq!(tasks[1].depends_on, vec!["SWARM-P2P-SYNC"]);
        assert!(!tasks[1].done);
    }

    #[test]
    fn parses_binary_integer_priority_without_silent_fallback() {
        let text = r#"
((kind . tasks-my)
 (tasks .
  (("BINARY-P10" . ((priority . #b1010)))
   ("DECIMAL-P09" . ((priority . 0.9)))
   ("INTEGER-P5" . ((priority . 5))))))
"#;
        let tasks = parse_tasks_file(text).unwrap();
        assert_eq!(tasks[0].priority, 10.0);
        assert_eq!(tasks[1].priority, 0.9);
        assert_eq!(tasks[2].priority, 5.0);
    }

    #[test]
    fn rejects_malformed_binary_priority_instead_of_defaulting_to_one() {
        let text = r#"
((kind . tasks-my)
 (tasks .
  (("BROKEN" . ((priority . #b102))))))
"#;
        let error = parse_tasks_file(text).unwrap_err();
        assert!(error.contains("invalid priority"));
        assert!(error.contains("#b102"));
    }

    #[test]
    fn absent_priority_still_uses_historical_default() {
        let text = r#"
((kind . tasks-my)
 (tasks .
  (("DEFAULT" . ((capabilities . (docs)))))))
"#;
        let tasks = parse_tasks_file(text).unwrap();
        assert_eq!(tasks[0].priority, 1.0);
    }

    #[test]
    fn parses_optional_origin_field() {
        let text = r#"
((kind . tasks-my)
 (tasks .
  (("CML-FOO" . ((priority . 5) (origin . cml) (done . ())))
   ("ORPHAN-TASK" . ((priority . 3))))))
"#;
        let tasks = parse_tasks_file(text).unwrap();
        assert_eq!(tasks[0].origin.as_deref(), Some("cml"));
        assert_eq!(tasks[1].origin, None);
    }

    #[test]
    fn recognizes_done_with_evidence_not_just_bare_t() {
        // (done . (t . "who/when/what happened")) is the predominant shape
        // real completed tasks use across this ecosystem's tasks.lisp files
        // (5 of them in sens's own file alone as of 2026-09-01) -- only
        // the older bare (done . t) had ever been tested here.
        let text = r#"
((kind . tasks-my)
 (tasks .
  (("WITH-EVIDENCE" . ((priority . 1) (done . (t . "nidana 2026-09-01: shipped, see commit db6f666"))))
   ("BARE-DONE" . ((priority . 1) (done . t)))
   ("NOT-DONE" . ((priority . 1) (done . ())))
   ("NO-DONE-FIELD" . ((priority . 1))))))
"#;
        let tasks = parse_tasks_file(text).unwrap();
        assert!(
            tasks[0].done,
            "evidence-carrying done . (t . ...) must count as done"
        );
        assert!(tasks[1].done);
        assert!(!tasks[2].done);
        assert!(!tasks[3].done);
    }
}
