use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::PathBuf;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

/// A bare SENS token `00001100` as a number; rows are keyed by code. A quoted
/// `"00001100"` is text describing a code, not the code, and is rejected.
fn sens_code(token: &str) -> Option<u32> {
    if token.starts_with('"') {
        return None;
    }
    let code = token.trim_end_matches(')');
    (code.len() == 8 && code.bytes().all(|b| b == b'0' || b == b'1'))
        .then(|| u32::from_str_radix(code, 2).ok())
        .flatten()
}

fn numeric_row_id_list(source: &str) -> Vec<u32> {
    source
        .lines()
        .filter_map(|line| {
            let line = line.trim_start();
            let rest = line.strip_prefix('(')?;
            let token = rest.split_whitespace().next()?;
            sens_code(token)
        })
        .collect()
}

/// Function-table identities that carry at least one surface; the 256-row
/// table also lists every unused code with only `()` surfaces.
fn named_function_table_ids(source: &str) -> Vec<u32> {
    source
        .lines()
        .filter(|line| !line.contains("(ук ()) (укр ()) (en ()) (sa ()) (sym ())"))
        .flat_map(numeric_row_id_list)
        .collect()
}

fn function_table_ukr_ids(source: &str) -> BTreeMap<String, u32> {
    let mut by_name = BTreeMap::new();
    for line in source.lines() {
        let Some(rest) = line.trim_start().strip_prefix('(') else {
            continue;
        };
        let Some((key, _)) = rest.split_once(char::is_whitespace) else {
            continue;
        };
        let Some(id) = sens_code(key) else {
            continue;
        };
        let Some(surface_tail) = line.split_once("(укр ").map(|(_, tail)| tail) else {
            continue;
        };
        let surface = if surface_tail.starts_with("()") {
            "()"
        } else {
            surface_tail
                .split_whitespace()
                .next()
                .unwrap_or_default()
                .trim_end_matches(')')
        };
        if surface == "()" {
            continue;
        }
        let name = surface
            .strip_prefix('"')
            .and_then(|value| value.strip_suffix('"'))
            .unwrap_or(surface);
        assert!(
            by_name.insert(name.to_string(), id).is_none(),
            "function table must not assign one full Ukrainian surface to multiple identities: {name}"
        );
    }
    by_name
}

#[derive(Debug)]
struct UkrCandidateRow {
    id: u32,
    ukr: String,
}

fn ukr_candidate_rows(source: &str, ids_by_ukr: &BTreeMap<String, u32>) -> Vec<UkrCandidateRow> {
    let mut rows = Vec::new();
    for line in source.lines() {
        let line = line.trim_start();
        let Some(rest) = line.strip_prefix('(') else {
            continue;
        };
        let Some((key, _)) = rest.split_once(char::is_whitespace) else {
            continue;
        };
        // (domain identity or full projection "current UK" "full ukr" status)
        let fields: Vec<_> = line.split('"').collect();
        let Some(ukr) = fields.get(3).copied() else {
            continue;
        };
        let id = sens_code(key).unwrap_or_else(|| {
            *ids_by_ukr.get(ukr).unwrap_or_else(|| {
                panic!("profile full Ukrainian name has no function identity: {ukr}")
            })
        });
        rows.push(UkrCandidateRow {
            id,
            ukr: ukr.to_string(),
        });
    }
    rows
}

fn ukr_aliases(source: &str) -> BTreeMap<u32, u32> {
    let mut aliases = BTreeMap::new();
    for line in source.lines() {
        let line = line.trim_start();
        let Some(rest) = line.strip_prefix("(аліас ") else {
            continue;
        };
        let mut fields = rest.trim_end_matches(')').split_whitespace();
        let from = fields
            .next()
            .and_then(sens_code)
            .expect("ukr alias source must be a SENS code");
        let to = fields
            .next()
            .and_then(sens_code)
            .expect("ukr alias target must be a SENS code");
        assert!(
            fields.next().is_none(),
            "ukr alias rows must have exactly source and target IDs"
        );
        assert!(
            aliases.insert(from, to).is_none(),
            "ukr alias source {from} must be declared only once"
        );
    }
    aliases
}

#[test]
fn ukrainian_staging_profile_covers_every_function_table_identity() {
    let root = repo_root();
    let function_table = fs::read_to_string(root.join("lib/generated/function-table.lisp"))
        .expect("generated function table must be readable");
    let profile = fs::read_to_string(root.join("lib/surface/український-профіль-джерела.lisp"))
        .expect("Ukrainian staging profile must be readable");

    let expected_rows = named_function_table_ids(&function_table);
    let ids_by_ukr = function_table_ukr_ids(&function_table);
    let actual_rows = ukr_candidate_rows(&profile, &ids_by_ukr);
    let expected: BTreeSet<u32> = expected_rows.iter().copied().collect();
    let actual: BTreeSet<u32> = actual_rows.iter().map(|row| row.id).collect();

    assert_eq!(
        expected_rows.len(),
        expected.len(),
        "function table must not contain duplicate semantic identity rows"
    );
    assert_eq!(
        actual_rows.len(),
        actual.len(),
        "Ukrainian staging must contain exactly one row per semantic identity"
    );
    assert_eq!(
        actual, expected,
        "Ukrainian staging must cover each current function-table identity via its exact domain key or full ukr projection"
    );
}

#[test]
fn ukr_candidate_collisions_require_explicit_alias_targets() {
    let root = repo_root();
    let profile = fs::read_to_string(root.join("lib/surface/український-профіль-джерела.lisp"))
        .expect("Ukrainian staging profile must be readable");

    let function_table = fs::read_to_string(root.join("lib/generated/function-table.lisp"))
        .expect("generated function table must be readable");
    let rows = ukr_candidate_rows(&profile, &function_table_ukr_ids(&function_table));
    let unique_ids: BTreeSet<u32> = rows.iter().map(|row| row.id).collect();
    assert_eq!(
        rows.len(),
        unique_ids.len(),
        "each staging row resolves to one identity"
    );

    let by_id: BTreeMap<u32, &UkrCandidateRow> = rows.iter().map(|row| (row.id, row)).collect();
    let aliases = ukr_aliases(&profile);

    for (&source_id, &target_id) in &aliases {
        let source = by_id
            .get(&source_id)
            .copied()
            .unwrap_or_else(|| panic!("ukr alias source {source_id} is not a staging identity"));
        let target = by_id
            .get(&target_id)
            .copied()
            .unwrap_or_else(|| panic!("ukr alias target {target_id} is not a staging identity"));
        assert!(
            !aliases.contains_key(&target_id),
            "ukr alias {source_id} -> {target_id} must point directly to a canonical owner"
        );
        assert_eq!(
            source.ukr.as_str(),
            target.ukr.as_str(),
            "ukr alias {source_id} -> {target_id} must preserve the owner's candidate spelling"
        );
    }

    let mut owners: BTreeMap<&str, Vec<&UkrCandidateRow>> = BTreeMap::new();
    for row in &rows {
        owners.entry(row.ukr.as_str()).or_default().push(row);
    }

    for (name, group) in owners {
        if name == "—" || group.len() == 1 {
            continue;
        }

        let canonical: Vec<_> = group
            .iter()
            .copied()
            .filter(|row| !aliases.contains_key(&row.id))
            .collect();
        assert_eq!(
            canonical.len(),
            1,
            "duplicate ukr candidate {name:?} must have exactly one canonical owner; rows: {:?}",
            group.iter().map(|row| row.id).collect::<Vec<_>>()
        );

        let owner_id = canonical[0].id;
        for row in group {
            if row.id == owner_id {
                continue;
            }
            assert_eq!(
                aliases.get(&row.id).copied(),
                Some(owner_id),
                "duplicate ukr candidate {name:?} on row {} must explicitly alias canonical owner {}",
                row.id,
                owner_id
            );
        }
    }
}

#[test]
fn ukr_candidates_need_no_latin_keyboard_layout() {
    let root = repo_root();
    let profile = fs::read_to_string(root.join("lib/surface/український-профіль-джерела.lisp"))
        .expect("Ukrainian staging profile must be readable");

    let function_table = fs::read_to_string(root.join("lib/generated/function-table.lisp"))
        .expect("generated function table must be readable");
    let offenders = ukr_candidate_rows(&profile, &function_table_ukr_ids(&function_table))
        .into_iter()
        .filter(|row| row.ukr != "—")
        .filter(|row| {
            row.ukr
                .chars()
                .any(|character| character.is_ascii_alphabetic())
        })
        .map(|row| format!("{}:{}", row.id, row.ukr))
        .collect::<Vec<_>>();

    assert!(
        offenders.is_empty(),
        "ukr candidates must be typeable without switching to a Latin keyboard layout; offenders: {}",
        offenders.join(", ")
    );
}

fn projection_token<'a>(line: &'a str, column: &str) -> Option<&'a str> {
    let marker = format!("({column} ");
    let tail = line.split_once(&marker)?.1;
    if tail.starts_with("()") {
        return Some("");
    }
    if let Some(quoted) = tail.strip_prefix('"') {
        let mut escaped = false;
        for (index, character) in quoted.char_indices() {
            if escaped {
                escaped = false;
            } else if character == '\\' {
                escaped = true;
            } else if character == '"' {
                return Some(&quoted[..index]);
            }
        }
        return None;
    }
    Some(tail.split(')').next()?.trim())
}

fn keyboard_projection_findings(source: &str, path: &str) -> Vec<String> {
    let allowed: BTreeSet<char> = "абвгґдеєжзиіїйклмнопрстуфхцчшщьюяАБВГҐДЕЄЖЗИІЇЙКЛМНОПРСТУФХЦЧШЩЬЮЯ0123456789'\\-=./!\"№;%:?*()_+,₴ "
        .chars()
        .collect();
    let mut findings = Vec::new();
    for (line_number, line) in source.lines().enumerate() {
        let Some(rest) = line.trim_start().strip_prefix('(') else {
            continue;
        };
        let Some(bits) = rest.split_whitespace().next() else {
            continue;
        };
        if bits.is_empty() || !bits.bytes().all(|byte| matches!(byte, b'0' | b'1')) {
            continue;
        }
        for column in ["ук", "укр", "sym"] {
            let Some(value) = projection_token(line, column) else {
                findings.push(format!(
                    "{path}:{} {bits} malformed {column} projection",
                    line_number + 1
                ));
                continue;
            };
            for character in value
                .chars()
                .filter(|character| !character.is_control() && !allowed.contains(character))
            {
                findings.push(format!(
                    "{path}:{} D{}:{bits} column={column} U+{:04X} {character:?}",
                    line_number + 1,
                    bits.len(),
                    character as u32
                ));
            }
        }
    }
    findings
}

#[test]
fn domain_uk_ukr_and_sym_projections_use_ukrainian_keyboard_characters() {
    let root = repo_root();
    let mut seen = BTreeSet::new();
    let mut findings = Vec::new();
    for width in 1..=11 {
        let relative = format!("lib/domains/d{width}.lisp");
        let source = fs::read_to_string(root.join(&relative))
            .unwrap_or_else(|error| panic!("{relative} must be readable: {error}"));
        assert!(seen.insert(width), "domain D{width} must be scanned once");
        findings.extend(keyboard_projection_findings(&source, &relative));
    }
    assert_eq!(seen, (1..=11).collect());
    assert!(
        findings.is_empty(),
        "D1–D11 uk/ukr/sym projections contain symbols outside the Ukrainian keyboard:\n{}",
        findings.join("\n")
    );
}

#[test]
fn keyboard_audit_reports_the_exact_projection_cell_and_character() {
    let findings = keyboard_projection_findings(
        "(101 (ук x) (укр а) (san ()) (en ()) (LISP ()) (sym <))\n",
        "lib/domains/d3.lisp",
    );
    assert_eq!(
        findings,
        [
            "lib/domains/d3.lisp:1 D3:101 column=ук U+0078 'x'",
            "lib/domains/d3.lisp:1 D3:101 column=sym U+003C '<'",
        ]
    );
}
