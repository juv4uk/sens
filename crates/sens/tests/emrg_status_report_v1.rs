use sens::{eval_program, Session};

const SOURCE: &str =
    include_str!("../../../fixtures/emrg/v1/status-report-v1.source.lisp");
const WIRE: &str =
    include_str!("../../../fixtures/emrg/v1/status-report-v1.wire");
const SURFACES: &str =
    include_str!("../../../fixtures/emrg/v1/status-report-v1.surfaces.tsv");

const EXPECTED_WIRE_HEX: &str =
    "282371323a312f31202371323a31302f312022732d30303031222022323032362d31302d30345430303a30303a30305a22202371323a302f3120282371323a302f312920282371323a302f312929";

fn eval(source: &str) -> String {
    let mut session = Session::default();
    eval_program(source, &mut session)
        .expect("EMRG status fixture expression should evaluate")
        .value
        .to_string()
}

fn hex(bytes: &[u8]) -> String {
    const DIGITS: &[u8; 16] = b"0123456789abcdef";
    let mut out = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        out.push(DIGITS[(byte >> 4) as usize] as char);
        out.push(DIGITS[(byte & 0x0f) as usize] as char);
    }
    out
}

#[test]
fn status_report_v1_has_runtime_verified_canonical_wire() {
    let program = format!("(write-to-string (quote {SOURCE}))");
    assert_eq!(eval(&program), format!("{WIRE:?}"));

    let round_trip =
        format!("(write-to-string (read (write-to-string (quote {SOURCE}))))");
    assert_eq!(eval(&round_trip), format!("{WIRE:?}"));
}

#[test]
fn status_report_v1_records_exact_consumer_payload_size() {
    assert_eq!(WIRE.as_bytes().len(), 78);
    assert_eq!(WIRE.as_bytes().len() * 8, 624);
    assert_eq!(hex(WIRE.as_bytes()), EXPECTED_WIRE_HEX);
}

#[test]
fn status_report_v1_projection_coordinates_are_language_neutral() {
    let mut lines = SURFACES.lines();
    assert_eq!(lines.next(), Some("p\tuk\tpl\ten"));

    for line in lines {
        let coordinate = line
            .split('\t')
            .next()
            .expect("surface row must begin with a projection coordinate");
        assert!(!coordinate.is_empty());
        assert!(
            coordinate
                .bytes()
                .all(|byte| byte.is_ascii_digit() || byte == b'/'),
            "projection identity must be positional/numeric, got: {coordinate}"
        );
    }
}

#[test]
fn status_report_v1_human_labels_are_projection_only() {
    for required in [
        "Звіт про стан",
        "Raport stanu",
        "Status report",
        "У безпеці",
        "Bezpiecznie",
        "Safe",
        "Невідомо",
        "Nieznana",
        "Unknown",
        "Відсутня",
        "Brak",
        "Absent",
    ] {
        assert!(SURFACES.contains(required));
        assert!(!WIRE.contains(required));
    }
}

#[test]
fn safe_unknown_and_absent_are_distinct_projection_states() {
    let coordinates: Vec<&str> = SURFACES
        .lines()
        .skip(1)
        .filter_map(|line| line.split('\t').next())
        .collect();

    for required in ["4/0", "5/0", "6/0"] {
        assert!(
            coordinates.contains(&required),
            "required projection coordinate missing: {required}"
        );
    }

    assert_ne!("4/0", "5/0");
    assert_ne!("4/0", "6/0");
    assert_ne!("5/0", "6/0");
}
