use sens::{
    eval_parsed_expressions, parse_mixed_exact_domain_machine_source,
    ExprKind, Session,
};

const PATH: &str = "lib/machine/admission/x86-64.lisp";
const SOURCE: &str = include_str!("../../../lib/machine/admission/x86-64.lisp");

fn predicate(source: &str) -> bool {
    let forms = parse_mixed_exact_domain_machine_source(PATH, source)
        .expect("джерело машинного допуску має точні D3-голови");
    let mut session = Session::default();
    let result = eval_parsed_expressions(&forms, &mut session)
        .expect("структурний ATOM має відповідати ратифікованому D1");
    result.value.as_predicate_bit()
        .expect("D3 ATOM зобов'язаний повертати лише D1 так або ні")
}

#[test]
fn shorter_quoted_singleton_preserves_observable_d1_no() {
    let original = "(010 (001 (00000000)))";
    let current = "(010 (001 (000)))";
    assert!(!predicate(original), "історичний цитований одноелементний список не атом");
    assert_eq!(predicate(original), predicate(current), "заміна не може змінити D1 відповідь");
    assert!(!predicate(current));

    // Якщо видалити саме елемент, буде порожній список — це інша семантика.
    assert!(predicate("(010 (001 ()))"), "негативний свідок: ATOM від порожнього списку є D1 так");
}

#[test]
fn admission_source_has_exactly_27_short_inert_payloads_and_no_old_d8_sentinel() {
    assert_eq!(SOURCE.matches("(атом? (як-є (000)))").count(), 27,
        "усі 27 відмов тепер явно обчислюють D1:NO у SENS");
    assert!(!SOURCE.contains("(010 (001 (000)))"),
        "неповернений старий бітовий call head у виконуваному Lisp");
    assert!(!SOURCE.contains("(00000000)"),
        "історична восьмибітна позначка не повинна повертатися");
    assert!(SOURCE.contains("(значення-у-текст значення)"),
        "реальний український D8 WRITE-TO-STRING мусить залишитися виконуваним");
    assert!(!SOURCE.contains("(11110100 value)"),
        "застарілу D8 викличну голову не можна повертати замість поверхні");

    let expressions = parse_mixed_exact_domain_machine_source(PATH, SOURCE)
        .expect("увесь admission-файл має проходити суворий машинний reader");
    assert_eq!(expressions.len(), 20, "чинні D4 помічники зберігають усі механізми допуску");
    // Тепер чинний D8 подає 7 як "7", а не історичний #q2:7/1.
    assert!(SOURCE.contains("(визначити машина-допуск-цифра?"));
    assert!(SOURCE.contains("(визначити машина-допуск-цифри?"));
    assert!(SOURCE.contains("(визначити машина-допуск-текст-точне-ціле?"));
    assert!(!SOURCE.contains("((функція"),
        "невикличні анонімні D5 value-call не мають повертатися в допуск");
    for definition in &expressions {
        let ExprKind::List(list) = &definition.kind else {
            panic!("верхні визначення повинні лишатися списками")
        };
        assert!(list.len() >= 3, "верхнє визначення повинно лишатися цілісним");
    }
}

#[test]
fn quote_payload_remains_data_and_cannot_be_relabelled_as_callable_d8() {
    let form = parse_mixed_exact_domain_machine_source(
        PATH, "(010 (001 (000)))",
    ).expect("читач із точними ширинами");
    let ExprKind::List(atom) = &form[0].kind else { panic!("ATOM") };
    let ExprKind::List(quoted) = &atom[1].kind else { panic!("QUOTE") };
    assert!(matches!(&quoted[0].kind, ExprKind::DomainIdentity(id)
        if id.width() == 3 && id.packed_bits() == 0b001));
    let ExprKind::List(singleton) = &quoted[1].kind else { panic!("цитовані дані") };
    assert_eq!(singleton.len(), 1);
    assert!(!matches!(&singleton[0].kind, ExprKind::DomainIdentity(_)),
        "цитований бінарний datum не набуває права виконання D3/D8");
}
