use std::collections::{BTreeMap, BTreeSet};

const INVENTORY: &str = include_str!("../../../tests/data/macro-generated-heads-1485.tsv");
const REGISTRY: &str = include_str!("../../../lib/surface/semantic-registry.lisp");
const CORE: &str = include_str!("../../../lib/core.lisp");
const CORE4: &str = include_str!("../../../lib/core4.lisp");

#[derive(Debug, Clone, Eq, Ord, PartialEq, PartialOrd)]
struct Row {
    path: String,
    line: usize,
    surface: String,
    exact_sens: String,
    class: String,
}

fn inventory_rows() -> Vec<Row> {
    INVENTORY
        .lines()
        .filter(|line| !line.trim().is_empty() && !line.starts_with('#'))
        .map(|line| {
            let parts: Vec<_> = line.split('\t').collect();
            assert_eq!(parts.len(), 5, "bad #1485 inventory row: {line}");
            Row {
                path: parts[0].to_string(),
                line: parts[1].parse().expect("line must be decimal"),
                surface: parts[2].to_string(),
                exact_sens: parts[3].to_string(),
                class: parts[4].to_string(),
            }
        })
        .collect()
}

fn admitted_surface_bits() -> BTreeMap<String, String> {
    let mut out = BTreeMap::new();
    for line in REGISTRY.lines() {
        let trimmed = line.trim_start();
        if !trimmed.starts_with('(') || trimmed.len() < 10 {
            continue;
        }
        let bits = &trimmed[1..9];
        if bits.len() != 8 || !bits.bytes().all(|b| b == b'0' || b == b'1') {
            continue;
        }
        for namespace in ["en", "ук", "укр", "sa", "sym"] {
            let needle = format!("({namespace} ");
            let Some(start) = trimmed.find(&needle) else {
                continue;
            };
            let rest = &trimmed[start + needle.len()..];
            let Some(end) = rest.find(')') else {
                continue;
            };
            let value = rest[..end].trim();
            if !value.is_empty()
                && value != "()"
                && !value.contains(char::is_whitespace)
                && !value.contains('(')
            {
                out.insert(value.to_string(), bits.to_string());
            }
        }
    }
    out
}

fn quoted_admitted_single_atoms(path: &str, source: &str) -> BTreeSet<Row> {
    let admitted = admitted_surface_bits();
    let mut out = BTreeSet::new();
    let needle = "(00000001 ";
    let mut offset = 0;
    while let Some(relative) = source[offset..].find(needle) {
        let start = offset + relative;
        let value_start = start + needle.len();
        let Some(relative_end) = source[value_start..].find(')') else {
            break;
        };
        let value_end = value_start + relative_end;
        let value = source[value_start..value_end].trim();
        if !value.is_empty()
            && !value.contains(char::is_whitespace)
            && !value.contains('(')
            && !value.bytes().all(|b| b == b'0' || b == b'1')
        {
            if let Some(bits) = admitted.get(value) {
                let line = source[..start].bytes().filter(|b| *b == b'\n').count() + 1;
                out.insert(Row {
                    path: path.to_string(),
                    line,
                    surface: value.to_string(),
                    exact_sens: bits.clone(),
                    class: String::new(),
                });
            }
        }
        offset = value_end + 1;
    }
    out
}

fn discovered_rows_without_class() -> BTreeSet<Row> {
    let mut rows = quoted_admitted_single_atoms("lib/core.lisp", CORE);
    rows.extend(quoted_admitted_single_atoms("lib/core4.lisp", CORE4));
    rows
}

#[test]
fn inventory_covers_every_quoted_admitted_single_atom_in_core_and_core4() {
    let inventoried: BTreeSet<_> = inventory_rows()
        .into_iter()
        .map(|mut row| {
            row.class.clear();
            row
        })
        .collect();
    assert_eq!(
        discovered_rows_without_class(),
        inventoried,
        "#1485 inventory must change whenever quoted admitted single-atom values change"
    );
}

#[test]
fn inventory_has_only_explicit_data_or_code_template_classes() {
    let rows = inventory_rows();
    assert_eq!(rows.len(), 16, "current audit is exactly eight rows per core profile");
    for row in &rows {
        assert!(
            matches!(row.class.as_str(), "ordinary-data" | "code-template-operator"),
            "unclassified #1485 row: {row:?}"
        );
    }

    let ordinary: Vec<_> = rows.iter().filter(|row| row.class == "ordinary-data").collect();
    assert_eq!(ordinary.len(), 2);
    assert!(ordinary.iter().all(|row| row.surface == "binary"));
    assert!(ordinary.iter().all(|row| row.exact_sens == "10101001"));
}

#[test]
fn code_template_operator_rows_name_the_exact_registry_function() {
    let admitted = admitted_surface_bits();
    for row in inventory_rows()
        .into_iter()
        .filter(|row| row.class == "code-template-operator")
    {
        assert_eq!(
            admitted.get(&row.surface),
            Some(&row.exact_sens),
            "inventory exact SENS must be derived from the current registry: {row:?}"
        );
    }
}

#[test]
#[ignore = "RED witness for #1485: unignore when production macro/code templates emit exact SENS"]
fn code_template_operators_never_reintroduce_surface_heads() {
    let offenders: Vec<_> = inventory_rows()
        .into_iter()
        .filter(|row| row.class == "code-template-operator")
        .filter(|row| {
            let source = match row.path.as_str() {
                "lib/core.lisp" => CORE,
                "lib/core4.lisp" => CORE4,
                other => panic!("unexpected inventory path: {other}"),
            };
            source
                .lines()
                .nth(row.line - 1)
                .is_some_and(|line| line.contains(&format!("(00000001 {})", row.surface)))
        })
        .collect();

    assert!(
        offenders.is_empty(),
        "#1485 RED: code-producing templates still quote human surface heads: {offenders:#?}"
    );
}
