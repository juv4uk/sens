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
    pub kind: Option<String>,
    /// Normalized target as ((функція NAME) (властивість LAW) (клас-входу CLASS)).
    pub target: Option<Sexp>,
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

/// Convert tasks.lisp's dotted target alist to the swarm wire shape.
/// The parser stays a data reader; semantic registry membership is resolved
/// before defining the task and is never copied into a Rust-side registry.
fn parse_target(value: Option<&Sexp>, task: &str) -> Result<Option<Sexp>, String> {
    let Some(value) = value else { return Ok(None) };
    let Sexp::List(entries) = value else {
        return Err(format!("task `{task}` target must be a dotted alist"));
    };
    let mut normalized = Vec::new();
    for entry in entries {
        let Sexp::List(pair) = entry else {
            return Err(format!("task `{task}` has malformed target field"));
        };
        let [key, dot, value] = pair.as_slice() else {
            return Err(format!("task `{task}` has malformed target field"));
        };
        let Some(key) = atom_text(key) else {
            return Err(format!("task `{task}` target field name must be an atom"));
        };
        if atom_text(dot).as_deref() != Some(".") {
            return Err(format!("task `{task}` target field must use dotted-alist syntax"));
        }
        if !matches!(key.as_str(), "функція" | "властивість" | "клас-входу") {
            return Err(format!("task `{task}` has unknown target field `{key}`"));
        }
        if atom_text(value).is_none() {
            return Err(format!("task `{task}` target value for `{key}` must be one name"));
        }
        normalized.push(Sexp::list(vec![Sexp::atom(key), value.clone()]));
    }
    Ok(Some(Sexp::list(normalized)))
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
        let kind = dotted_get(fields, "вид").and_then(atom_text);
        let target = parse_target(dotted_get(fields, "ціль"), &id)?;
        let origin = dotted_get(fields, "origin").and_then(atom_text);

        parsed.push(ParsedTask {
            id,
            priority,
            capabilities,
            depends_on,
            done,
            description,
            kind,
            target,
            origin,
        });
    }
    Ok(parsed)
}

