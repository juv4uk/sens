use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

fn repo_root() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR")).join("../..")
}

fn my_lisp(cwd: &Path) -> Command {
    let mut command = Command::new(env!("CARGO_BIN_EXE_my-lisp"));
    command.current_dir(cwd);
    command
}

fn numeric_row_id_list(source: &str) -> Vec<u32> {
    source
        .lines()
        .filter_map(|line| {
            let line = line.trim_start();
            let rest = line.strip_prefix('(')?;
            let token = rest.split_whitespace().next()?;
            token.parse::<u32>().ok()
        })
        .collect()
}

fn numeric_row_ids(source: &str) -> BTreeSet<u32> {
    numeric_row_id_list(source).into_iter().collect()
}

#[derive(Debug)]
struct UkrCandidateRow {
    id: u32,
    ukr: String,
}

fn ukr_candidate_rows(source: &str) -> Vec<UkrCandidateRow> {
    source
        .lines()
        .filter_map(|line| {
            let line = line.trim_start();
            let rest = line.strip_prefix('(')?;
            let token = rest.split_whitespace().next()?;
            let id = token.parse::<u32>().ok()?;

            let mut quoted = line.split('"');
            quoted.next()?;
            quoted.next()?; // current UK surface, or —
            quoted.next()?;
            let ukr = quoted.next()?.to_string();

            Some(UkrCandidateRow { id, ukr })
        })
        .collect()
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
            .and_then(|field| field.parse::<u32>().ok())
            .expect("ukr alias source must be a numeric semantic ID");
        let to = fields
            .next()
            .and_then(|field| field.parse::<u32>().ok())
            .expect("ukr alias target must be a numeric semantic ID");
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
fn uk_surface_audit_generator_runs_through_real_my_lisp_cli() {
    let root = repo_root();
    let script = root.join("scripts/generate-uk-surface-audit.lisp");
    let output = my_lisp(&root)
        .arg(&script)
        .output()
        .expect("UK surface audit generator should run through the real my-lisp CLI");

    assert!(
        output.status.success(),
        "language-owned UK surface audit generator must run successfully\nstdout:\n{}\nstderr:\n{}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
}

#[test]
fn ukrainian_staging_profile_covers_every_function_table_identity() {
    let root = repo_root();
    let function_table = fs::read_to_string(root.join("lib/generated/function-table.lisp"))
        .expect("generated function table must be readable");
    let profile = fs::read_to_string(root.join("lib/surface/український-профіль-джерела.lisp"))
        .expect("Ukrainian staging profile must be readable");

    let expected_rows = numeric_row_id_list(&function_table);
    let actual_rows = numeric_row_id_list(&profile);
    let expected = numeric_row_ids(&function_table);
    let actual = numeric_row_ids(&profile);

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
        expected_rows.len(),
        169,
        "function table inventory changed; review UK coverage gate"
    );
    assert_eq!(
        actual_rows.len(),
        169,
        "Ukrainian staging row count must stay exactly aligned with the 169-row function table"
    );
    assert_eq!(
        actual, expected,
        "Ukrainian staging must explicitly cover every semantic identity, including compatibility-only rows"
    );
}

#[test]
fn ukr_candidate_collisions_require_explicit_alias_targets() {
    let root = repo_root();
    let profile = fs::read_to_string(root.join("lib/surface/український-профіль-джерела.lisp"))
        .expect("Ukrainian staging profile must be readable");

    let rows = ukr_candidate_rows(&profile);
    assert_eq!(
        rows.len(),
        169,
        "coherence audit must inspect every Ukrainian staging candidate"
    );

    let by_id: BTreeMap<u32, &UkrCandidateRow> =
        rows.iter().map(|row| (row.id, row)).collect();
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

    let offenders = ukr_candidate_rows(&profile)
        .into_iter()
        .filter(|row| row.ukr != "—")
        .filter(|row| row.ukr.chars().any(|character| character.is_ascii_alphabetic()))
        .map(|row| format!("{}:{}", row.id, row.ukr))
        .collect::<Vec<_>>();

    assert!(
        offenders.is_empty(),
        "ukr candidates must be typeable without switching to a Latin keyboard layout; offenders: {}",
        offenders.join(", ")
    );
}
