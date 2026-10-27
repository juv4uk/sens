//! Лише механіка читача D1. Семантичні вердикти COND/істини належать SENS.
//! Rust не встановлює таблицю істинності D1.

use sens::{parse, parse_canonical_binary, DomainIdentity, Exactness, ExprKind};

#[test]
fn reader_recognizes_explicit_d1_projection_and_canonical_width() {
    for (source, exact) in [("#d1:0", "0"), ("#d1:1", "1")] {
        let parsed = parse(source).expect("typed D1 projection");
        assert!(matches!(
            parsed[0].kind,
            ExprKind::DomainIdentity(DomainIdentity::D1(_))
        ));
        let canonical = parse_canonical_binary(exact).expect("canonical one-bit source");
        assert_eq!(canonical.len(), 1, "canonical frame count");
    }
}

#[test]
fn historical_bare_numerals_remain_distinct_parser_nodes() {
    for source in ["0", "1"] {
        let ast = parse(source).expect("historical number reader");
        assert!(matches!(ast[0].kind, ExprKind::Number(_, Exactness::Exact)));
    }
}

#[test]
fn malformed_d1_projections_fail_in_reader() {
    for source in [
        "#d1:", "#d1:00", "#d1:01", "#d1:10", "#d1:2", "#d1:-1",
        "#d1:1x", "#d1:000", "#d1:YES",
    ] {
        assert!(parse(source).is_err(), "must reject {source}");
    }
    assert!(parse_canonical_binary("#d1:1").is_err());
}
