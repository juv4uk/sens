//! Чинний український інвентар є виконуваною SENS-програмою, не плоским
//! списком старих SID8/Function8. Перевіряємо його живим evaluator SENS.
use sens::{eval_program, load_core_library, parse, ExprKind, Session};
use std::collections::BTreeSet;

const CORE_LIBRARY_SOURCE: &str = include_str!("../../../lib/core4.lisp");

const INVENTORY: &str = include_str!("../../../lib/surface/uk-inventory.lisp");

fn session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("завантажити справжню українську Core4");
    session
}

#[test]
fn інвентар_укр_є_справжньою_sens_програмою_а_не_sid8_списком() {
    let forms = parse(INVENTORY).expect("прочитати виконуваний український інвентар");
    assert_eq!(forms.len(), 3, "два визначення та один живий закон");
    for (index, form) in forms.iter().enumerate() {
        let ExprKind::List(parts) = &form.kind else {
            panic!("top-level {index}: очікувалася SENS-форма");
        };
        let ExprKind::Symbol(head) = &parts[0].kind else {
            panic!("top-level {index}: історична кодова голова не є українською проєкцією");
        };
        assert_eq!(
            head.as_ref(),
            if index < 2 { "визначити" } else { "за-умовою" },
            "top-level {index}: чинна українська голова"
        );
    }
}

#[test]
fn інвентар_укр_реально_виконується_мовою_та_повертає_точні_дані() {
    let actual = eval_program(INVENTORY, &mut session())
        .expect("закон та вкладений негативний контроль виконує сам SENS").value;
    let expected = eval_program(
        "(як-є (uk-inventory (визначити функція за-умовою тотожне? як-є перше решта список)))",
        &mut session(),
    ).expect("поточне цитоване значення").value;
    assert_eq!(actual, expected, "живе виконання не повинно підмінятися інвентарним лічильником");
}

#[test]
fn неправильна_структура_в_інвентарі_дійсно_провалює_sens_закон() {
    let old = "(список (як-є (неприпустиме-вкладення)))";
    let changed = "(список (як-є неприпустиме-вкладення))";
    assert!(INVENTORY.contains(old), "негативний свідок мусить залишатися в джерелі");
    let mutated = INVENTORY.replacen(old, changed, 1);
    assert!(
        eval_program(&mutated, &mut session()).is_err(),
        "незаконний список більше не може маскуватися зеленим тестом"
    );
}

#[test]
fn чинна_core4_визначає_українські_імена_а_не_sid8_координати() {
    let forms = parse(CORE_LIBRARY_SOURCE).expect("Core4 читається SENS");
    let names: BTreeSet<String> = forms.iter().filter_map(|form| {
        let ExprKind::List(parts) = &form.kind else { return None };
        let [head, name, ..] = parts.as_ref() else { return None };
        if !matches!(&head.kind, ExprKind::Symbol(word) if word.as_ref() == "визначити") {
            return None;
        }
        let ExprKind::Symbol(name) = &name.kind else { return None };
        Some(name.to_string())
    }).collect();
    for required in ["тотожність", "двійковий", "список", "друге", "четверте"] {
        assert!(names.contains(required), "відсутнє чинне визначення Core4: {required}");
    }
}
