//! Перевірки чинного доменного подання та доказового переносу D3.
//! Зовнішня інтеграція компілює бібліотеку без cfg(test)-залежностей
//! інших зайнятих агентами модулів. Не є свідком виклику функції D8.

use sens::{
    render_value_for_presentation, Bija3, Bit3, Bit9, CoreD9, DomainIdentity, PresentationLanguage,
    Value,
};

#[test]
fn exact_d3_quote_projects_through_the_current_ukrainian_surface() {
    let exact = Value::DomainIdentity(DomainIdentity::D3(Bija3::from_word(
        Bit3::new(0b001).unwrap(),
    )));
    assert_eq!(
        render_value_for_presentation(&exact, PresentationLanguage::Ukrainian),
        "як-є",
    );
    assert_eq!(exact.to_string(), "001");
}

#[test]
fn d9_bez_runtime_surface_ne_vtrachaie_shyrynu_u_ukrainskomu_podanni() {
    let d9 = Value::DomainIdentity(DomainIdentity::D9(CoreD9::from_word(
        Bit9::new(0b100000001).unwrap(),
    )));
    assert_eq!(
        render_value_for_presentation(&d9, PresentationLanguage::Ukrainian),
        "#<домен D9:100000001>",
    );
    assert_eq!(
        render_value_for_presentation(&d9, PresentationLanguage::Canonical),
        "100000001",
    );
}
