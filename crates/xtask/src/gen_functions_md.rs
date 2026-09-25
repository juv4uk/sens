//! `cargo xtask gen-functions-md` — regenerate the small set of
//! `docs/FUNCTIONS.md` library sections that are mechanically derivable
//! from `(def ...)` forms in their source file, so they can never drift
//! the way `documentation_contract.rs`'s
//! `tracked_function_reference_tracks_live_library_definitions` test used
//! to merely detect after the fact.
//!
//! This intentionally covers only the same 5 files that test covered
//! (`result-status.lisp`, `narrate.lisp`, `translation.lisp`, `quantity.lisp`,
//! `si.lisp`) — regenerating the *entire* FUNCTIONS.md (builtins table,
//! all library sections, prose) from scratch is a larger project-owned
//! generator rewrite (in the spirit of `scripts/generate-function-table.lisp`
//! replacing the retired Python generator) that is out of scope for this
//! pass. That is left as a follow-up; see TEST-ARCHITECTURE-1 step 4 notes.
//!
//! Регенерує лише ту невелику підмножину секцій `docs/FUNCTIONS.md`, яку
//! можна механічно вивести з форм `(def ...)` у вихідному файлі. Повний
//! переписувач FUNCTIONS.md лишається окремим завданням на майбутнє.

use std::fs;

const TRACKED_FILES: &[&str] = &[
    "result-status.lisp",
    "narrate.lisp",
    "translation.lisp",
    "quantity.lisp",
    "si.lisp",
];

fn defined_names(source: &str) -> Vec<&str> {
    source
        .lines()
        .filter_map(|line| {
            let trimmed = line.trim_start();
            let rest = trimmed.strip_prefix("(def ")?;
            rest.split_whitespace().next()
        })
        .collect()
}

pub fn run() -> Result<(), String> {
    let reference_path = "docs/FUNCTIONS.md";
    let mut reference = fs::read_to_string(reference_path)
        .map_err(|error| format!("cannot read {reference_path}: {error}"))?;

    for file in TRACKED_FILES {
        let lib_path = format!("lib/{file}");
        let source = fs::read_to_string(&lib_path)
            .map_err(|error| format!("cannot read {lib_path}: {error}"))?;
        let names = defined_names(&source);

        let marker = format!("### {file} (");
        let start = reference
            .find(&marker)
            .ok_or_else(|| format!("FUNCTIONS.md is missing section for {file}"))?;
        let tail_start = start;
        let after_marker = start + marker.len();
        let end = reference[after_marker..]
            .find("\n### ")
            .map(|offset| after_marker + offset)
            .unwrap_or(reference.len());

        let names_line = names
            .iter()
            .map(|name| format!("`{name}`"))
            .collect::<Vec<_>>()
            .join(", ");
        let new_section = format!(
            "### {file} ({})\n\n{names_line}\n",
            names.len()
        );

        reference.replace_range(tail_start..end, &new_section);
    }

    fs::write(reference_path, reference)
        .map_err(|error| format!("cannot write {reference_path}: {error}"))?;
    println!("gen-functions-md: refreshed sections for {TRACKED_FILES:?}");
    Ok(())
}
