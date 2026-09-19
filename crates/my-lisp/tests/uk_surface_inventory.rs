use my_lisp::{language_items, parse, LanguageItemKind, CORE_LIBRARY_SOURCE};
use std::collections::BTreeSet;

const INVENTORY: &str = include_str!("../../../lib/surface/uk-inventory.lisp");
const SEMANTIC_REGISTRY: &str = include_str!("../../../lib/surface/semantic-registry.lisp");

fn names_after(source: &str, marker: &str) -> BTreeSet<String> {
    let start = source.find(marker).expect("inventory marker must exist") + marker.len();
    let rest = &source[start..];
    let end = rest.find("))").expect("inventory group must close");
    rest[..end]
        .split_whitespace()
        .map(|word| word.trim_matches(|c| c == '(' || c == ')'))
        .filter(|word| !word.is_empty())
        .map(str::to_owned)
        .collect()
}

fn semantic_registry_surface_names() -> BTreeSet<String> {
    SEMANTIC_REGISTRY
        .split('(')
        .filter_map(|fragment| {
            let tuple = fragment.split(')').next()?;
            let fields = tuple.split_whitespace().collect::<Vec<_>>();
            let [_surface, name] = fields.as_slice() else {
                return None;
            };
            if *name != "()" {
                Some(name.trim_matches('"').to_owned())
            } else {
                None
            }
        })
        .collect()
}

fn core_definition_names() -> BTreeSet<String> {
    CORE_LIBRARY_SOURCE
        .lines()
        .filter_map(|line| {
            let line = line.trim_start();
            line.strip_prefix("(defmacro ")
                .or_else(|| line.strip_prefix("(def "))
                .and_then(|rest| rest.split_whitespace().next())
                .map(|name| name.trim_matches(|c| c == '(' || c == ')').to_owned())
        })
        .collect()
}

#[test]
fn inventory_is_valid_my_lisp_data() {
    let forms = parse(INVENTORY).expect("Ukrainian surface inventory must parse");
    assert_eq!(forms.len(), 1);
}

#[test]
fn every_discoverable_runtime_item_is_classified() {
    let root_builtins = names_after(INVENTORY, "(root-builtins");
    let registry_names = semantic_registry_surface_names();
    let live_builtins = language_items()
        .into_iter()
        .filter(|item| item.kind == LanguageItemKind::Builtin)
        .map(|item| item.name)
        .collect::<BTreeSet<_>>();

    assert!(
        root_builtins.is_subset(&live_builtins),
        "legacy inventory contains root builtins no longer discoverable: {:?}",
        root_builtins.difference(&live_builtins).collect::<Vec<_>>()
    );

    let mut classified_builtins = root_builtins.clone();
    classified_builtins.extend(registry_names.iter().cloned());
    assert!(
        live_builtins.is_subset(&classified_builtins),
        "runtime builtin bindings are absent from both legacy inventory and semantic registry: {:?}",
        live_builtins
            .difference(&classified_builtins)
            .collect::<Vec<_>>()
    );

    let mut classified = root_builtins;
    classified.extend(registry_names);
    classified.extend(names_after(INVENTORY, "(canon"));
    classified.extend(names_after(INVENTORY, "(necessary-forms"));
    classified.extend(names_after(INVENTORY, "(language-macros"));
    classified.extend(names_after(INVENTORY, "(compatibility-forms"));
    let discoverable = language_items()
        .into_iter()
        .map(|item| item.name)
        .collect::<BTreeSet<_>>();
    assert!(
        discoverable.is_subset(&classified),
        "unclassified discoverable names: {:?}",
        discoverable.difference(&classified).collect::<Vec<_>>()
    );
}

#[test]
fn every_core_definition_is_public_or_explicitly_internal() {
    let public = names_after(INVENTORY, "(core-library");
    let second = INVENTORY
        .rfind("(core-library")
        .expect("internal core marker");
    let internal = names_after(&INVENTORY[second..], "(core-library");
    let classified = public.union(&internal).cloned().collect::<BTreeSet<_>>();
    assert_eq!(core_definition_names(), classified);
    assert!(public.is_disjoint(&internal));
}

#[test]
fn every_question_mark_public_name_is_classified_as_a_predicate() {
    let predicates = names_after(INVENTORY, "(public-predicates");
    let mut public = names_after(INVENTORY, "(root-builtins");
    public.extend(names_after(INVENTORY, "(core-library"));
    for name in public.into_iter().filter(|name| name.ends_with('?')) {
        assert!(
            predicates.contains(&name),
            "question-mark public name {name} must be classified as a predicate"
        );
    }
}

#[test]
fn symbolic_sugar_is_an_explicit_subset_of_the_public_surface() {
    let marker = INVENTORY
        .rfind("(symbolic-sugar")
        .expect("symbolic sugar group must exist");
    let sugar = names_after(&INVENTORY[marker..], "(symbolic-sugar");
    let mut public = names_after(INVENTORY, "(root-builtins");
    public.extend(names_after(INVENTORY, "(core-library"));
    assert!(sugar.is_subset(&public));
}
