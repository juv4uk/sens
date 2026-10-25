//! Живі закони незмінної асоціативної мапи — виконання справжнім SENS.
//! Імена, D1-предикати та D3-пари належать lib/persistent-map.lisp.
//! Історичні AVL/англійські def/cond/t не є чинною семантикою мапи.

use sens::{eval_pinned_reasoning_source, eval_program, load_core_library, Session, Value};

fn map_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("фізичний Core4 SENS із Zig T5M");
    eval_pinned_reasoning_source(
        "lib/persistent-map.lisp",
        include_str!("../../../lib/persistent-map.lisp"),
        &mut session,
    )
    .expect("чинні українські Lisp-визначення мапи");
    session
}

fn observe(session: &mut Session, source: &str) -> Value {
    eval_program(source, session)
        .unwrap_or_else(|error| panic!("SENS eval failed on {source}: {error}"))
        .value
}

#[test]
fn порожня_мапа_не_повертає_вигаданих_значень() {
    let mut session = map_session();
    assert_eq!(observe(&mut session, "(мапа-порожній)").to_string(), "()");
    assert_eq!(
        observe(&mut session, "(мапа-отримати (як-є a) (мапа-порожній))").to_string(),
        "()"
    );
    assert_eq!(
        observe(&mut session, "(мапа-містить? (як-є a) (мапа-порожній))").as_predicate_bit(),
        Some(false),
    );
}

#[test]
fn вставлення_та_пошук_виконуються_українським_lisp() {
    let mut session = map_session();
    let m = "(мапа-вставити (як-є a) (як-є v) (мапа-порожній))";
    let get = format!("(мапа-отримати (як-є a) {m})");
    assert_eq!(observe(&mut session, &get).to_string(), "(v)");
    let contains = format!("(мапа-містить? (як-є a) {m})");
    assert_eq!(
        observe(&mut session, &contains).as_predicate_bit(),
        Some(true)
    );
    let absent = format!("(мапа-містить? (як-є b) {m})");
    assert_eq!(
        observe(&mut session, &absent).as_predicate_bit(),
        Some(false)
    );
}

#[test]
fn відсутність_не_дорівнює_записаному_nil() {
    let mut session = map_session();
    let m = "(мапа-вставити (як-є a) (як-є ()) (мапа-порожній))";
    assert_eq!(
        observe(&mut session, &format!("(мапа-отримати (як-є a) {m})")).to_string(),
        "(())"
    );
    assert_eq!(
        observe(&mut session, &format!("(мапа-отримати (як-є b) {m})")).to_string(),
        "()"
    );
}

#[test]
fn рівний_ключ_замінює_значення_без_дублікатів() {
    let mut session = map_session();
    let m = "(мапа-вставити (як-є a) (як-є new)
                 (мапа-вставити (як-є a) (як-є old) (мапа-порожній)))";
    assert_eq!(
        observe(&mut session, &format!("(мапа-отримати (як-є a) {m})")).to_string(),
        "(new)"
    );
    assert_eq!(
        observe(&mut session, &format!("(мапа-список {m})")).to_string(),
        "((a . new))"
    );
}

#[test]
fn нова_мапа_зберігає_стару_і_порядок_пар() {
    let mut session = map_session();
    let original = "(мапа-вставити (як-є b) (як-є bee) (мапа-порожній))";
    let updated = format!("(мапа-вставити (як-є a) (як-є aye) {original})");
    assert_eq!(
        observe(&mut session, &format!("(мапа-список {original})")).to_string(),
        "((b . bee))"
    );
    assert_eq!(
        observe(&mut session, &format!("(мапа-список {updated})")).to_string(),
        "((b . bee) (a . aye))"
    );
}

#[test]
fn старий_викличний_так_не_є_виконуваним_d1() {
    let mut session = map_session();
    // Негативну семантику перевіряє сам SENS; переклад тексту помилки
    // не є її частиною і не повинен ламати робочий тест.
    eval_program("(так (як-є помилка))", &mut session)
        .expect_err("історичний голий так не є D3-умовою чи функцією");
}
