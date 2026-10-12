//! Відділення історичної восьмибітної сумісності від поточних доменів.
//! Зовнішня інтеграція компілює бібліотеку без cfg(test)-залежностей
//! інших зайнятих агентами модулів. Не є свідком виклику функції D8.

use sens::{
    Bit3, Bit8, Bit9, Bija3, CoreD8, CoreD9, DomainIdentity,
    PresentationLanguage, Value, render_value_for_presentation,
};

#[test]
fn w8_invoke_ne_staie_d8_round_za_spilnymy_bitamy() {
    let old = Value::Sid(sens::sens!(10101000));
    let exact = Value::DomainIdentity(DomainIdentity::D8(
        CoreD8::from_word(Bit8::new(0b10101000).unwrap()),
    ));

    assert_eq!(old.to_string(), exact.to_string());
    assert_eq!(old.to_string(), "10101000");
    let old_uk = render_value_for_presentation(&old, PresentationLanguage::Ukrainian);
    let current_uk = render_value_for_presentation(&exact, PresentationLanguage::Ukrainian);
    assert!(old_uk.starts_with("#<сумісний W8:10101000 "), "{old_uk}");
    assert_eq!(current_uk, "#<домен D8:10101000>");
    assert_ne!(old_uk, current_uk);
    // Жодного автоматичного права виконання через вісім однакових бітів.
    assert_eq!(exact.as_domain_identity().unwrap().width(), 8);
    assert!(old.as_domain_identity().is_none());
}

#[test]
fn istorichnyi_quote_maie_lyshe_dovedenu_d3_proiektsiiu() {
    let old = Value::Sid(sens::sens!(00000001));
    let exact = Value::DomainIdentity(DomainIdentity::D3(
        Bija3::from_word(Bit3::new(0b001).unwrap()),
    ));
    assert_eq!(
        render_value_for_presentation(&old, PresentationLanguage::Ukrainian),
        render_value_for_presentation(&exact, PresentationLanguage::Ukrainian),
    );
    // Доведена людська проєкція — не зміна історичного wire.
    assert_eq!(old.to_string(), "00000001");
    assert_eq!(exact.to_string(), "001");
}

#[test]
fn d9_bez_runtime_surface_ne_vtrachaie_shyrynu_u_ukrainskomu_podanni() {
    let d9 = Value::DomainIdentity(DomainIdentity::D9(
        CoreD9::from_word(Bit9::new(0b100000001).unwrap()),
    ));
    assert_eq!(
        render_value_for_presentation(&d9, PresentationLanguage::Ukrainian),
        "#<домен D9:100000001>",
    );
    assert_eq!(
        render_value_for_presentation(&d9, PresentationLanguage::Canonical),
        "100000001",
    );
}
