//! Фізичний Core3 завантажується через Zig; тестовий frontend перетворює
//! українське ім'я на точні D7 клітини перед зверненням до бекенду.
use sens::{
    encode_text7, eval_parsed_expressions, parse_canonical_binary, CoreProfile, Session,
    Text7Layout,
};

#[test]
fn core3_physical_bootstrap_preserves_executor_order_and_current_ukrainian_binding() {
    let mut session = Session::default();
    sens::load_core3_library(&mut session).expect("Core3 library load");
    assert_eq!(
        session.environment.selected_core_profile(),
        Some(CoreProfile::Core3)
    );
    let name = encode_text7("ядро3-виконавці", Text7Layout::Uk).unwrap();
    let lookup = frame(name.cells());
    let forms = parse_canonical_binary(&lookup).unwrap();
    let actual = eval_parsed_expressions(&forms, &mut session)
        .expect("точний D7 binder чинної української назви має бути визначений")
        .value;

    // Незалежний очікуваний список — точні англійські D7 координати
    // чинного протоколу, не старі викличні голови й не аліаси SID8.
    let expected_items =
        ["common-lisp", "prolog", "clips", "datalog"].map(|name| frame(name.as_bytes()));
    let expected_words = format!("10 001 00 10 {} 01 01", expected_items.join(" 00 "));
    let expected_forms = parse_canonical_binary(&expected_words).unwrap();
    let expected = eval_parsed_expressions(&expected_forms, &mut session)
        .unwrap()
        .value;
    assert_eq!(
        actual, expected,
        "порядок, кожна клітина й довжина списку мають зберегтися"
    );
}

fn frame(cells: &[u8]) -> String {
    let words = cells
        .iter()
        .map(|cell| format!("{cell:07b}"))
        .collect::<Vec<_>>();
    format!("10 {} 01", words.join(" 00 "))
}
