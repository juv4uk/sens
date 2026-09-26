use std::collections::HashSet;
use std::fs;
use std::path::{Path, PathBuf};

fn repo_root() -> PathBuf {
    Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("../..")
        .canonicalize()
        .expect("repository root")
}

fn inventory_source() -> String {
    fs::read_to_string(repo_root().join("knowledge/canon-authority-inventory.lisp"))
        .expect("canon authority inventory must be readable")
}

fn authority_rows(source: &str) -> Vec<&str> {
    source
        .lines()
        .map(str::trim)
        .filter(|line| line.starts_with("(authority "))
        .collect()
}

fn quoted_field<'a>(row: &'a str, field: &str) -> &'a str {
    let marker = format!("({field} \"");
    let start = row
        .find(&marker)
        .unwrap_or_else(|| panic!("missing {field:?} in inventory row: {row}"))
        + marker.len();
    let tail = &row[start..];
    let end = tail
        .find('"')
        .unwrap_or_else(|| panic!("unterminated {field:?} in inventory row: {row}"));
    &tail[..end]
}

fn atom_field<'a>(row: &'a str, field: &str) -> &'a str {
    let marker = format!("({field} ");
    let start = row
        .find(&marker)
        .unwrap_or_else(|| panic!("missing {field:?} in inventory row: {row}"))
        + marker.len();
    let tail = &row[start..];
    let end = tail
        .find(')')
        .unwrap_or_else(|| panic!("unterminated {field:?} in inventory row: {row}"));
    &tail[..end]
}

#[test]
fn inventory_is_structured_complete_data_not_a_second_semantic_table() {
    let source = inventory_source();
    assert!(source.contains("(schema canon-authority-inventory/1)"));
    assert!(source.contains("(authority-root \"lib/surface/semantic-registry.lisp\")"));

    let rows = authority_rows(&source);
    assert!(rows.len() >= 25, "expected a broad #1060 baseline, got {}", rows.len());

    let allowed_classes: HashSet<&str> = [
        "canon-function-table-authority",
        "generated-mechanical-projection",
        "executor-local-mechanism-detail",
        "compatibility-historical-fixture",
        "forbidden-duplicate-semantic-authority",
        // Метадані за кодом (вид, механізм особливої форми, арність,
        // сигнатура) — мовою, поруч із таблицею; не влада над ідентичністю.
        "function-table-metadata",
    ]
    .into_iter()
    .collect();

    let mut seen_paths = HashSet::new();
    let mut root_claims = Vec::new();

    for row in rows {
        let path = quoted_field(row, "path");
        assert!(seen_paths.insert(path), "duplicate inventory path: {path}");
        assert!(
            repo_root().join(path).exists(),
            "inventory path does not exist: {path}"
        );

        for required in ["mapping", "class", "provenance", "consumers", "retirement", "note"] {
            assert!(
                row.contains(&format!("({required} ")),
                "inventory row is missing {required}: {row}"
            );
        }

        let class = atom_field(row, "class");
        assert!(
            allowed_classes.contains(class),
            "unknown/unclassified authority class {class:?} in row: {row}"
        );

        if class == "canon-function-table-authority" {
            root_claims.push(path);
        }

        if class == "forbidden-duplicate-semantic-authority" {
            assert!(
                !row.contains("(retirement ())"),
                "forbidden duplicate authority must have an explicit retirement issue: {row}"
            );
        }
    }

    assert_eq!(
        root_claims,
        vec!["lib/surface/semantic-registry.lisp"],
        "only the existing Canon/function-table registry may claim semantic identity authority"
    );
}

#[test]
fn every_known_active_sid_mapping_hotspot_has_an_inventory_classification() {
    let source = inventory_source();
    let inventoried: HashSet<&str> = authority_rows(&source)
        .into_iter()
        .map(|row| quoted_field(row, "path"))
        .collect();

    // Baseline discovered in #1060. #1049 may turn this curated list into a
    // broader structural guard; for now a new/renamed hotspot must update the
    // inventory deliberately rather than silently disappearing from the audit.
    let required = [
        "lib/surface/semantic-registry.lisp",
        "crates/sens/src/semantic_registry_generated.rs",
        "crates/sens/src/semantic_registry.rs",
        "crates/sens/src/eval/canon.rs",
        "lib/surface/function-signatures.lisp",
        "crates/sens/src/eval/necessary_forms_generated.rs",
        "crates/sens/src/eval/necessary_forms.rs",
        "crates/sens/src/ir.rs",
        "crates/sens/src/language_items.rs",
        "crates/sens-cli/src/bin/cml-export.rs",
        "mylisp-cml-export.lisp",
        "lib/machine/lowering/semantic-x86-64.lisp",
        "lib/machine/dispatch/native-first.lisp",
        "crates/wsm-kernel-c-abi/src/lib.rs",
        "crates/wsm-kernel-host/src/lib.rs",
        "crates/wsm-common-lisp-kernel/src/lib.rs",
        "crates/wsm-prolog-kernel/src/lib.rs",
        "crates/wsm-clips-kernel/src/lib.rs",
        "crates/wsm-datalog-kernel/src/lib.rs",
        "crates/wsm-native-result-types/src/lib.rs",
    ];

    for path in required {
        assert!(
            inventoried.contains(path),
            "known active SID mapping/mechanism hotspot is unclassified: {path}"
        );
    }
}

#[test]
fn generated_projections_name_their_real_source_instead_of_claiming_authority() {
    let source = inventory_source();
    let rows = authority_rows(&source);

    for path in [
        "crates/sens/src/semantic_registry_generated.rs",
        "crates/sens/src/semantic_registry.rs",
        "crates/sens/src/eval/necessary_forms_generated.rs",
        "mylisp-cml-export.lisp",
        "lib/generated/function-table.lisp",
    ] {
        let row = rows
            .iter()
            .copied()
            .find(|row| quoted_field(row, "path") == path)
            .unwrap_or_else(|| panic!("missing generated/projection row: {path}"));
        assert_eq!(
            atom_field(row, "class"),
            "generated-mechanical-projection",
            "{path} must be classified as a projection, never authority"
        );
        let provenance = quoted_field(row, "provenance");
        assert!(
            !provenance.trim().is_empty() && provenance != "unknown",
            "{path} must name its actual provenance source"
        );
    }
}
