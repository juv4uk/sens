//! Лише механічна тотожність доменної ширини. Мовну арифметику перевіряє SENS.
use sens::{parse_exact_domain_source, DomainIdentity, ExprKind};

#[test]
fn точні_d5_і_d8_з_однаковим_payload_не_тотожні() {
    let d5 = parse_exact_domain_source("01010").expect("D5");
    let d8 = parse_exact_domain_source("00001010").expect("D8");
    assert!(matches!(&d5[0].kind, ExprKind::DomainIdentity(DomainIdentity::D5(_))));
    assert!(matches!(&d8[0].kind, ExprKind::DomainIdentity(DomainIdentity::D8(_))));
    assert_ne!(d5[0].kind, d8[0].kind, "ширина є частиною тотожності");
}
