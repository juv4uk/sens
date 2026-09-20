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

fn semantic_id_list(source: &str) -> Vec<String> {
    source
        .lines()
        .filter_map(|line| {
            let line = line.trim_start();
            let rest = line.strip_prefix('(')?;
            let token = rest.split_whitespace().next()?.trim_matches('"');
            if token.len() == 8 && token.bytes().all(|byte| matches!(byte, b'0' | b'1')) {
                Some(token.to_string())
            } else {
                None
            }
        })
        .collect()
}

fn semantic_ids(source: &str) -> BTreeSet<String> {
    semantic_id_list(source).into_iter().collect()
}

#[derive(Debug)]
struct UkrCandidateRow {
    id: String,
    ukr: String,
}

fn ukr_candidate_rows(source: &str) -> Vec<UkrCandidateRow> {
    source
        .lines()
        .filter_map(|line| {
            let line = line.trim_start();
            let rest = line.strip_prefix('(')?;
            let token = rest.split_whitespace().next()?.trim_matches('"');
            if token.len() != 8 || !token.bytes().all(|byte| matches!(byte, b'0' | b'1')) {
                return None;
            }
            let id = token.to_string();

            let mut quoted = line.split('"');
            quoted.next()?;
            quoted.next()?; // current UK surface, or —
            quoted.next()?;
            let ukr = quoted.next()?.to_string();

            Some(UkrCandidateRow { id, ukr })
        })
        .collect()
}

fn ukr_aliases(source: &str) -> BTreeMap<String, String> {
    let mut aliases = BTreeMap::new();
    for line in source.lines() {
        let line = line.trim_start();
        let Some(rest) = line.strip_prefix("(аліас ") else {
            continue;
        };
        let mut fields = rest.trim_end_matches(')').split_whitespace();
        let from = fields
            .next()
            .map(|field| field.trim_matches('"').to_string())
            .expect("ukr alias source must be a semantic ID");
        let to = fields
            .next()
            .map(|field| field.trim_matches('"').to_string())
            .expect("ukr alias target must be a semantic ID");
        assert!(
            fields.next().is_none(),
            "ukr alias rows must have exactly source and target IDs"
        );
        assert!(
            from.len() == 8 && from.bytes().all(|byte| matches!(byte, b'0' | b'1')),
            "ukr alias source must be an 8-bit semantic ID: {from}"
        );
        assert!(
            to.len() == 8 && to.bytes().all(|byte| matches!(byte, b'0' | b'1')),
            "ukr alias target must be an 8-bit semantic ID: {to}"
        );
        assert!(
            aliases.insert(from.clone(), to).is_none(),
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
fn ukrainian_staging_profile_covers_every_registry_callable_identity() {
    let root = repo_root();
    let registry = fs::read_to_string(root.join("lib/surface/semantic-registry.lisp"))
        .expect("semantic registry must be readable");
    let profile = fs::read_to_string(root.join("lib/surface/український-профіль-джерела.lisp"))
        .expect("Ukrainian staging profile must be readable");

    let expected_rows = semantic_id_list(&registry)
        .into_iter()
        .filter(|id| id != "00000000")
        .collect::<Vec<_>>();
    let actual_rows = semantic_id_list(&profile);
    let expected = expected_rows.iter().cloned().collect::<BTreeSet<_>>();
    let actual = semantic_ids(&profile);

    assert_eq!(
        expected_rows.len(),
        expected.len(),
        "semantic registry must not contain duplicate callable identity rows"
    );
    assert_eq!(
        actual_rows.len(),
        actual.len(),
        "Ukrainian staging must contain exactly one row per callable semantic identity"
    );
    assert_eq!(
        actual, expected,
        "Ukrainian staging must explicitly cover every Canon/function-table callable identity, including compatibility-only rows"
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
        167,
        "coherence audit must inspect every Ukrainian staging candidate"
    );

    let by_id: BTreeMap<String, &UkrCandidateRow> =
        rows.iter().map(|row| (row.id.clone(), row)).collect();
    let aliases = ukr_aliases(&profile);

    for (source_id, target_id) in &aliases {
        let source = by_id
            .get(source_id)
            .copied()
            .unwrap_or_else(|| panic!("ukr alias source {source_id} is not a staging identity"));
        let target = by_id
            .get(target_id)
            .copied()
            .unwrap_or_else(|| panic!("ukr alias target {target_id} is not a staging identity"));
        assert!(
            !aliases.contains_key(target_id),
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
                aliases.get(&row.id),
                Some(&owner_id),
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
