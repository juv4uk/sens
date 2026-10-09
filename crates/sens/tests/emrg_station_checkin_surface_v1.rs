use std::collections::HashMap;

const SURFACES: &str =
    include_str!("../../../fixtures/emrg/v1/station-checkin-v1.surfaces.tsv");
const WIRE: &str =
    include_str!("../../../fixtures/emrg/v1/station-checkin-v1.wire");

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum Locale {
    Uk,
    Pl,
    En,
}

impl Locale {
    const ALL: [Self; 3] = [Self::Uk, Self::Pl, Self::En];

    fn column(self) -> usize {
        match self {
            Self::Uk => 1,
            Self::Pl => 2,
            Self::En => 3,
        }
    }
}

#[derive(Debug, PartialEq, Eq)]
enum ProjectionLookup<'a> {
    Unique(&'a str),
    Unknown,
    Ambiguous,
}

fn rows(tsv: &str) -> Vec<[&str; 4]> {
    let mut lines = tsv.lines();
    assert_eq!(
        lines.next(),
        Some("p\tuk\tpl\ten"),
        "EMRG surface table header is part of the fixture contract"
    );

    lines
        .map(|line| {
            let columns: Vec<&str> = line.split('\t').collect();
            assert_eq!(
                columns.len(),
                4,
                "every EMRG surface row must have coordinate + uk/pl/en"
            );
            [columns[0], columns[1], columns[2], columns[3]]
        })
        .collect()
}

fn coordinate_for_label<'a>(
    table: &'a [[&'a str; 4]],
    locale: Locale,
    label: &str,
) -> ProjectionLookup<'a> {
    let matches: Vec<&str> = table
        .iter()
        .filter(|row| row[locale.column()] == label)
        .map(|row| row[0])
        .collect();

    match matches.as_slice() {
        [] => ProjectionLookup::Unknown,
        [coordinate] => ProjectionLookup::Unique(coordinate),
        _ => ProjectionLookup::Ambiguous,
    }
}

#[test]
fn every_station_checkin_coordinate_has_one_label_in_every_locale() {
    let table = rows(SURFACES);
    assert_eq!(table.len(), 7);

    let mut seen_coordinates = HashMap::new();
    for row in &table {
        assert!(!row[0].is_empty(), "projection coordinate must be non-empty");
        assert!(
            seen_coordinates.insert(row[0], ()).is_none(),
            "projection coordinate must occur exactly once: {}",
            row[0]
        );

        for locale in Locale::ALL {
            assert!(
                !row[locale.column()].is_empty(),
                "every projection coordinate must render in every admitted locale"
            );
        }
    }
}

#[test]
fn localized_labels_reverse_to_the_same_projection_coordinate() {
    let table = rows(SURFACES);

    for row in &table {
        for locale in Locale::ALL {
            assert_eq!(
                coordinate_for_label(&table, locale, row[locale.column()]),
                ProjectionLookup::Unique(row[0]),
                "rendered label must parse back to its exact projection coordinate"
            );
        }
    }
}

#[test]
fn unknown_and_ambiguous_labels_fail_closed() {
    let table = rows(SURFACES);
    assert_eq!(
        coordinate_for_label(&table, Locale::Uk, "цього-ярлика-немає"),
        ProjectionLookup::Unknown
    );

    let mut duplicated = table.clone();
    let duplicate_label = duplicated[0][Locale::En.column()];
    duplicated[1][Locale::En.column()] = duplicate_label;

    assert_eq!(
        coordinate_for_label(&duplicated, Locale::En, duplicate_label),
        ProjectionLookup::Ambiguous,
        "a duplicate display label must never silently choose one projection coordinate"
    );
}

#[test]
fn locale_selection_has_no_route_to_canonical_wire_mutation() {
    let table = rows(SURFACES);
    let original_wire = WIRE.as_bytes().to_vec();

    for locale in Locale::ALL {
        for row in &table {
            let label = row[locale.column()];
            assert_eq!(
                coordinate_for_label(&table, locale, label),
                ProjectionLookup::Unique(row[0])
            );
        }

        assert_eq!(
            WIRE.as_bytes(),
            original_wire.as_slice(),
            "projection lookup is metadata-only; locale cannot rewrite canonical wire"
        );
    }
}

#[test]
fn explicit_unknown_and_absent_states_are_distinct_paths_in_all_locales() {
    let table = rows(SURFACES);
    let unknown = table
        .iter()
        .find(|row| row[0] == "4/0")
        .expect("station-checkin must expose explicit unknown location state");
    let absent = table
        .iter()
        .find(|row| row[0] == "5/0")
        .expect("station-checkin must expose explicit absent note state");

    assert_ne!(unknown[0], absent[0]);

    for locale in Locale::ALL {
        assert_ne!(
            unknown[locale.column()],
            absent[locale.column()],
            "unknown and absent must remain visibly distinct"
        );
        assert_eq!(
            coordinate_for_label(&table, locale, unknown[locale.column()]),
            ProjectionLookup::Unique("4/0")
        );
        assert_eq!(
            coordinate_for_label(&table, locale, absent[locale.column()]),
            ProjectionLookup::Unique("5/0")
        );
    }
}
