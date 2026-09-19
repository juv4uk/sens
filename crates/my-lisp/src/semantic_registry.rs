//! Shared projection from the language surface authority to compact byte SIDs.
//!
//! `lib/surface/semantic-registry.lisp` owns human/symbolic spellings. Its sr/2
//! rows carry exactly eight binary digits plus fixed en/uk/ukr/sa/sym slots.
//! A slot contains either one spelling or (); there are no admission statuses.
//! Runtime code stores that identity as one `u8`; the textual bit spelling is
//! provenance/serialization only and is never itself admitted as Lisp surface.
//! Evaluator meaning remains in the modules that interpret each SID.

use std::{collections::HashMap, sync::OnceLock};

const SEMANTIC_REGISTRY: &str = include_str!("../../../lib/surface/semantic-registry.lisp");

pub(crate) type SemanticId = u8;
pub(crate) const EMPTY_LIST_SEMANTIC_ID: SemanticId = 0;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct SemanticSurface {
    namespace: &'static str,
    name: &'static str,
}

#[derive(Debug)]
struct SemanticRow {
    semantic_id: SemanticId,
    surfaces: Vec<SemanticSurface>,
}

fn parse_sid_bits(text: &str) -> Option<SemanticId> {
    if text.len() != 8 || !text.bytes().all(|byte| matches!(byte, b'0' | b'1')) {
        return None;
    }
    u8::from_str_radix(text, 2).ok()
}

pub(crate) fn semantic_id_bits(semantic_id: SemanticId) -> String {
    format!("{semantic_id:08b}")
}

fn surface_groups(line: &'static str) -> Vec<&'static str> {
    let mut groups = Vec::new();
    let mut depth = 0usize;
    let mut start = None;

    for (index, byte) in line.bytes().enumerate() {
        match byte {
            b'(' => {
                depth += 1;
                if depth == 2 {
                    start = Some(index + 1);
                }
            }
            b')' => {
                if depth == 2 {
                    if let Some(group_start) = start.take() {
                        let group = line[group_start..index].trim();
                        if !group.is_empty() {
                            groups.push(group);
                        }
                    }
                }
                depth = depth.saturating_sub(1);
            }
            _ => {}
        }
    }

    groups
}

fn surface_name_token(token: &'static str) -> &'static str {
    token
        .strip_prefix('"')
        .and_then(|value| value.strip_suffix('"'))
        .unwrap_or(token)
}

fn parse_surface_group(group: &'static str) -> Option<SemanticSurface> {
    let fields = group.split_whitespace().collect::<Vec<_>>();
    match fields.as_slice() {
        [_, "()"] => None,
        [namespace, name] => Some(SemanticSurface {
            namespace,
            name: surface_name_token(name),
        }),
        _ => panic!("malformed sr/2 surface group: ({group}); expected (namespace spelling) or (namespace ())"),
    }
}

fn parse_rows(source: &'static str) -> Vec<SemanticRow> {
    source
        .lines()
        .filter_map(|line| {
            let fields = line.split_whitespace().collect::<Vec<_>>();
            let first = fields.first()?;
            let sid_token = first.strip_prefix("(\"")?.strip_suffix('\"')?;
            let semantic_id = parse_sid_bits(sid_token)?;
            let groups = surface_groups(line);

            if semantic_id != EMPTY_LIST_SEMANTIC_ID {
                let namespaces = groups
                    .iter()
                    .filter_map(|group| group.split_whitespace().next())
                    .collect::<Vec<_>>();
                assert_eq!(
                    namespaces,
                    vec!["en", "uk", "ukr", "sa", "sym"],
                    "sr/2 rows must contain exactly en/uk/ukr/sa/sym in fixed order"
                );
            }

            let surfaces = groups
                .into_iter()
                .filter_map(parse_surface_group)
                .collect();

            Some(SemanticRow {
                semantic_id,
                surfaces,
            })
        })
        .collect()
}

fn assert_contiguous_byte_axis(rows: &[SemanticRow]) {
    assert!(!rows.is_empty(), "semantic registry must contain Canon 0");
    assert_eq!(
        rows[0].semantic_id, EMPTY_LIST_SEMANTIC_ID,
        "semantic registry must start at Canon 0 / SID 0"
    );
    for (expected, row) in rows.iter().enumerate() {
        assert_eq!(
            usize::from(row.semantic_id),
            expected,
            "semantic registry byte SIDs must be contiguous and ordered"
        );
    }
    assert!(
        rows.len() <= 256,
        "semantic registry must fit the declared 8-bit SID axis"
    );
}

fn insert_surface_mapping(
    index: &mut HashMap<&'static str, SemanticId>,
    surface: &'static str,
    semantic_id: SemanticId,
) {
    if let Some(previous) = index.insert(surface, semantic_id) {
        if previous != semantic_id {
            panic!(
                "semantic registry surface must be unique: {surface} maps to both {} and {}",
                semantic_id_bits(previous),
                semantic_id_bits(semantic_id)
            );
        }
    }
}

pub(crate) fn build_surface_index(
    source: &'static str,
) -> HashMap<&'static str, SemanticId> {
    let rows = parse_rows(source);
    let mut index = HashMap::new();
    for row in rows {
        for surface in row.surfaces.iter().map(|surface| surface.name) {
            insert_surface_mapping(&mut index, surface, row.semantic_id);
        }
    }
    index
}

pub(crate) fn build_admitted_surface_index(
    source: &'static str,
) -> HashMap<&'static str, SemanticId> {
    // Historical API name retained while callers migrate. In status-free sr/2,
    // every non-empty surface is simply present and therefore routable.
    build_surface_index(source)
}

fn live_rows() -> &'static [SemanticRow] {
    static ROWS: OnceLock<Vec<SemanticRow>> = OnceLock::new();
    ROWS.get_or_init(|| {
        let rows = parse_rows(SEMANTIC_REGISTRY);
        assert_contiguous_byte_axis(&rows);
        rows
    })
}

fn admitted_surface_index() -> &'static HashMap<&'static str, SemanticId> {
    static INDEX: OnceLock<HashMap<&'static str, SemanticId>> = OnceLock::new();
    INDEX.get_or_init(|| {
        let _ = live_rows();
        build_admitted_surface_index(SEMANTIC_REGISTRY)
    })
}

pub(crate) fn admitted_semantic_id_for_surface(name: &str) -> Option<SemanticId> {
    admitted_surface_index().get(name).copied()
}

fn surface_index() -> &'static HashMap<&'static str, SemanticId> {
    static INDEX: OnceLock<HashMap<&'static str, SemanticId>> = OnceLock::new();
    INDEX.get_or_init(|| {
        let _ = live_rows();
        build_surface_index(SEMANTIC_REGISTRY)
    })
}

fn stable_surfaces_from_index(
    index: &HashMap<&'static str, SemanticId>,
    semantic_id: SemanticId,
) -> Vec<&'static str> {
    let mut surfaces = index
        .iter()
        .filter_map(|(surface, mapped_id)| (*mapped_id == semantic_id).then_some(*surface))
        .collect::<Vec<_>>();
    surfaces.sort_unstable();
    surfaces
}

fn admitted_surfaces_from_rows(
    rows: &[SemanticRow],
    semantic_id: SemanticId,
) -> Vec<&'static str> {
    let mut surfaces = rows
        .iter()
        .find(|row| row.semantic_id == semantic_id)
        .into_iter()
        .flat_map(|row| row.surfaces.iter().map(|surface| surface.name))
        .collect::<Vec<_>>();
    surfaces.sort_unstable();
    surfaces
}

pub(crate) fn semantic_id_for_surface(name: &str) -> Option<SemanticId> {
    surface_index().get(name).copied()
}

#[cfg(test)]
pub(crate) fn stable_surfaces_for_semantic_id_from_source(
    source: &'static str,
    semantic_id: SemanticId,
) -> Vec<&'static str> {
    stable_surfaces_from_index(&build_surface_index(source), semantic_id)
}

#[cfg(test)]
pub(crate) fn admitted_surfaces_for_semantic_id_from_source(
    source: &'static str,
    semantic_id: SemanticId,
) -> Vec<&'static str> {
    admitted_surfaces_from_rows(&parse_rows(source), semantic_id)
}

pub(crate) fn stable_surfaces_for_semantic_id(
    semantic_id: SemanticId,
) -> Vec<&'static str> {
    stable_surfaces_from_index(surface_index(), semantic_id)
}

/// Historical API name retained while callers migrate.
/// In status-free sr/2 every non-empty spelling is directly routable; () is absence.
pub(crate) fn admitted_surfaces_for_semantic_id(
    semantic_id: SemanticId,
) -> Vec<&'static str> {
    admitted_surfaces_from_rows(live_rows(), semantic_id)
}

pub(crate) fn admitted_surfaces_with_namespace_for_semantic_id(
    semantic_id: SemanticId,
) -> Vec<(&'static str, &'static str)> {
    let mut surfaces = live_rows()
        .iter()
        .find(|row| row.semantic_id == semantic_id)
        .into_iter()
        .flat_map(|row| row.surfaces.iter().map(|s| (s.namespace, s.name)))
        .collect::<Vec<_>>();
    surfaces.sort_unstable();
    surfaces
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn registry_projection_is_status_free_and_empty_list_means_absence() {
        const SYNTHETIC: &str =
            "(\"00101010\" (en comet) (uk ()) (ukr meteor) (sa ()) (sym +))";
        let parsed = parse_rows(SYNTHETIC);
        assert_eq!(parsed.len(), 1);
        assert_eq!(parsed[0].semantic_id, 42);
        assert_eq!(
            parsed[0].surfaces,
            vec![
                SemanticSurface { namespace: "en", name: "comet" },
                SemanticSurface { namespace: "ukr", name: "meteor" },
                SemanticSurface { namespace: "sym", name: "+" },
            ]
        );
    }

    #[test]
    #[should_panic(expected = "expected (namespace spelling) or (namespace ())")]
    fn status_tokens_are_rejected_by_sr2() {
        let _ = parse_rows(
            "(\"00101010\" (en comet stable) (uk ()) (ukr ()) (sa ()) (sym ()))"
        );
    }

    #[test]
    fn machine_sid_bit_spelling_is_not_a_lisp_surface() {
        const SYNTHETIC: &str =
            "(\"00101010\" (en comet) (uk ()) (ukr meteor) (sa ()) (sym ()))";
        let direct = build_surface_index(SYNTHETIC);
        let admitted = build_admitted_surface_index(SYNTHETIC);
        assert_eq!(direct.get("comet"), Some(&42));
        assert_eq!(direct.get("meteor"), Some(&42));
        assert_eq!(direct.get("00101010"), None);
        assert_eq!(admitted.get("00101010"), None);
    }

    #[test]
    fn peer_namespaces_may_repeat_one_spelling_for_the_same_identity() {
        const SYNTHETIC: &str =
            "(\"00101010\" (en comet) (uk comet) (ukr comet) (sa ()) (sym ()))";
        let direct = build_surface_index(SYNTHETIC);
        assert_eq!(direct.get("comet"), Some(&42));
    }

    #[test]
    fn every_present_surface_is_constructively_selected_by_semantic_id() {
        const SYNTHETIC: &str =
            "(\"00101010\" (en ()) (uk comet) (ukr ()) (sa asteroid) (sym +))";
        let index = build_surface_index(SYNTHETIC);
        assert_eq!(
            stable_surfaces_from_index(&index, 42),
            vec!["+", "asteroid", "comet"]
        );
        assert!(stable_surfaces_from_index(&index, 99).is_empty());
    }

    #[test]
    fn live_registry_is_one_contiguous_byte_axis_starting_at_canon_zero() {
        let rows = parse_rows(SEMANTIC_REGISTRY);
        assert_contiguous_byte_axis(&rows);
        assert_eq!(rows.len(), 168);
        assert_eq!(rows[0].semantic_id, 0);
        assert!(rows[0].surfaces.is_empty(), "Canon 0 is ground, not a surface spelling");
        assert_eq!(rows.last().map(|row| row.semantic_id), Some(167));
    }

    #[test]
    fn public_reverse_projection_preserves_identity_across_present_surfaces() {
        for surface in admitted_surfaces_for_semantic_id(15) {
            assert_eq!(
                crate::semantic_registry_export::semantic_id_for_admitted_surface(surface),
                Some(15)
            );
        }
        assert_eq!(
            crate::semantic_registry_export::semantic_id_for_admitted_surface("not-a-surface"),
            None
        );
    }

    #[test]
    #[should_panic(expected = "semantic registry surface must be unique")]
    fn duplicate_surface_is_rejected_deterministically() {
        const CONFLICTING: &str =
            "(\"00000001\" (en collision) (uk ()) (ukr ()) (sa ()) (sym ()))\n\
             (\"00000010\" (en ()) (uk collision) (ukr ()) (sa ()) (sym ()))";
        let _ = build_surface_index(CONFLICTING);
    }

    #[test]
    fn unrelated_rows_are_projected_without_assigning_evaluator_meaning() {
        assert_eq!(semantic_id_for_surface("+"), Some(12));
    }

    #[test]
    fn surfaces_with_namespace_match_present_names_and_keep_namespace() {
        let with_namespace = admitted_surfaces_with_namespace_for_semantic_id(1);
        let names_only = admitted_surfaces_for_semantic_id(1);
        assert_eq!(with_namespace.len(), names_only.len());
        assert!(with_namespace.contains(&("en", "quote")));
        assert!(with_namespace.contains(&("uk", "як-є")));
        assert!(with_namespace.contains(&("sym", "'")));
    }
}
