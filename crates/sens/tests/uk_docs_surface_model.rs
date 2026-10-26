const README: &str = include_str!("../../../README.md");
const UKRAINIAN_API: &str = include_str!("../../../docs/ukrainian-api.md");
const DOCS_INDEX: &str = include_str!("../../../lib/surface/uk-docs.lisp");

#[test]
fn readme_explains_the_two_ukrainian_surfaces() {
    for required in [
        "`ук` — коротка, інтуїтивно зрозуміла українська поверхня",
        "`укр` — повна українська поверхня",
        "docs/generated/function-table.md",
    ] {
        assert!(
            README.contains(required),
            "README missing Ukrainian surface contract: {required}"
        );
    }
}

#[test]
fn ukrainian_api_distinguishes_surface_names_from_function_meaning() {
    for required in [
        "`ук` — коротке ім'я",
        "`укр` — повне ім'я",
        "точних доменних",
        "generated/function-table.md",
    ] {
        assert!(
            UKRAINIAN_API.contains(required),
            "docs/ukrainian-api.md missing ук/укр documentation rule: {required}"
        );
    }
}

#[test]
fn machine_docs_index_states_that_registry_owns_surface_spellings() {
    for required in [
        "«укр»",
        "lib/domains/d1..d10.lisp",
        "опис",
    ] {
        assert!(
            DOCS_INDEX.contains(required),
            "lib/surface/uk-docs.lisp missing authority note: {required}"
        );
    }
}

fn documented_ids() -> Vec<String> {
    DOCS_INDEX
        .lines()
        .filter_map(|line| {
            let mut fields = line.trim_start().strip_prefix("(doc ")?.split_whitespace();
            fields.next()?; // category
            let identity = fields.next()?;
            let (domain, bits) = identity.split_once(':')?;
            let width = domain.strip_prefix('D')?.parse::<usize>().ok()?;
            ((1..=10).contains(&width)
                &&
                && bits.len() == width
                && bits.bytes().all(|bit| matches!(bit, b'0' | b'1')))
                .then(|| identity.to_string())
        })
        .collect()
}

#[test]
fn every_documented_identity_shows_uk_ukr_and_one_behavior_description() {
    let (_, reference_and_tail) = UKRAINIAN_API
        .split_once("## Повний довідник")
        .expect("Ukrainian API must contain the detailed reference section");
    let (reference, _) = reference_and_tail
        .split_once("## Межа довідника")
        .expect("Ukrainian API detailed reference must end before the boundary section");

    assert!(
        reference.contains("| Домен | `ук` | `укр` | Виклик | Тип | Що робить | Основа |"),
        "detailed Ukrainian API must expose ук and укр side by side"
    );

    let ids = documented_ids();
    assert!(
        !ids.is_empty(),
        "machine docs index must document semantic identities"
    );

    let rows = reference
        .lines()
        .filter(|line| {
            line.starts_with("| `")
                && line.chars().filter(|character| *character == '|').count() == 8
        })
        .collect::<Vec<_>>();
    assert_eq!(
        rows.len(),
        ids.len(),
        "detailed reference must contain exactly one row per exact domain identity"
    );

    for id in ids {
        let marker = format!("| `{id}` |");
        let count = rows.iter().filter(|row| row.starts_with(&marker)).count();
        assert_eq!(
            count, 1,
            "exact {id} must appear exactly once in the detailed ук/укр reference"
        );
    }

    for required_row_fragment in [
        "| `D9:110011100` | `рядок-порожній?` | `рядок-порожній?` |",
        "| `D10:0011110110` | `монотонний-наносекунди` | `монотонний-наносекунди` |",
    ] {
        assert!(
            reference.contains(required_row_fragment),
            "detailed reference missing representative ук/укр row: {required_row_fragment}"
        );
    }
}
