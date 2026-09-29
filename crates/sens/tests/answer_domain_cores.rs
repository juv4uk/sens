//! #1663 — спільна фістура домену відповіді для ядер Core1–Core4.
//!
//! Один закон, одна фікстура, чотири профілі: так — 1, ні — 0.
//! Джерело — `tests/fixtures/answer-domain-cores-v1.lisp`; Rust лише
//! виконує вирази й переносить фактичні відповіді, як спостерігач #217
//! робить для control-dispatch.
//!
//! Закон перевіряється як ЗНАЧЕННЯ (1 або 0), незалежно від того, чи сповнене
//! воно списком бітів (1)/(0), чи скаляром 1/0. Носій — окрема вимір: він
//! асертиться лише там, де ратифікований договіром проєкцій.
//!
//! Ідентифікація функцій — лише кодами СЕНС: основа тотожності — вісім бітів,
//! назва поверхні не є тотожністю.
//!
//! Межі цього зрізу (чесно, без прикрас):
//!   * ядро 2 відповідає t/() на іменованій поверхні, але на кодах СЕНС уже
//!     відповідає бітами; проекція назад на t/() усунена окремим кроком;
//!   * ядро 1 не має публічного runtime-завантажувача в цьому крейте
//!     (лише `lib/core1.lisp` та `tests/fixtures/core1-s0-witness.lisp`),
//!     тому для нього закон поки не перевіряється взагалі — це UNRESOLVED,
//!     а не «перевірено й пройдено».

use sens::{
    eval_program, load_core2_library, load_core3_library, load_core_library, parse, CoreProfile,
    Expr, ExprKind, Session,
};

#[derive(Clone, Debug)]
struct Row {
    id: String,
    expr: String,
    expected: String,
    carrier: Option<String>,
    status: String,
    cores: Vec<u8>,
}

impl Row {
    /// Закон: значення відповіді належить домену {так, ні}.
    fn law_holds(&self, answer: &str) -> bool {
        match self.expected.as_str() {
            "1" => matches!(answer, "1" | "(1)"),
            "0" => matches!(answer, "0" | "(0)"),
            _ => true,
        }
    }
}

fn alist<'a>(entries: &'a [Expr], key: &str) -> Option<&'a Expr> {
    entries
        .iter()
        .find_map(|entry| {
            let ExprKind::Pair(key_expr, value) = &entry.kind else { return None; };
            let ExprKind::Symbol(name) = &key_expr.kind else { return None; };
            (&**name == key).then_some(value)
        })
        .map(|value| &**value)
}

fn alist_str<'a>(entries: &'a [Expr], key: &str) -> Option<&'a str> {
    match &alist(entries, key)?.kind {
        ExprKind::String(value) => Some(value.as_ref()),
        _ => None,
    }
}

fn alist_cores(entries: &[Expr], key: &str) -> Option<Vec<u8>> {
    let ExprKind::List(items) = &alist(entries, key)?.kind else { return None; };
    items
        .iter()
        .map(|item| match &item.kind {
            ExprKind::Number(value, _) => Some(*value as u8),
            _ => None,
        })
        .collect()
}

fn rows() -> Vec<Row> {
    let source = include_str!("../../../tests/fixtures/answer-domain-cores-v1.lisp");
    parse(source)
        .expect("answer-domain-cores-v1.lisp must parse")
        .into_iter()
        .filter_map(|form| {
            let ExprKind::List(entries) = &form.kind else { return None; };
            Some(Row {
                id: alist_str(entries, "ід")?.to_string(),
                expr: alist_str(entries, "вираз")?.to_string(),
                expected: alist_str(entries, "очікуване")?.to_string(),
                carrier: alist_str(entries, "носій").map(str::to_string),
                status: alist_str(entries, "статус")?.to_string(),
                cores: alist_cores(entries, "ядра")?,
            })
        })
        .collect()
}

fn core4_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core4 library should load");
    assert_eq!(session.environment.selected_core_profile(), Some(CoreProfile::Core4));
    session
}

fn core3_session() -> Session {
    let mut session = Session::default();
    load_core3_library(&mut session).expect("core3 library should load");
    assert_eq!(session.environment.selected_core_profile(), Some(CoreProfile::Core3));
    session
}

fn core2_session() -> Session {
    let mut session = Session::default();
    load_core2_library(&mut session).expect("core2 library should load");
    assert_eq!(session.environment.selected_core_profile(), Some(CoreProfile::Core2));
    session
}

fn actual(session: &mut Session, expr: &str) -> String {
    match eval_program(expr, session) {
        Ok(result) => result.value.to_string(),
        Err(error) => format!("(помилка {:?})", error.kind),
    }
}

/// Кожен ряд спільний для чотирьох ядер — інакше це вже не спільна фікстура.
#[test]
fn every_shared_row_covers_all_four_cores() {
    let shared = rows();
    assert!(!shared.is_empty(), "спільна фікстура домену відповіді не порожня");
    for row in &shared {
        assert!(
            (1..=4).all(|core| row.cores.contains(&core)),
            "ряд {} має бути спільним для ядер 1–4, а не лише для {:?}",
            row.id,
            row.cores
        );
    }
}

/// Фактична відповідь кожного доступного ядра на кожен спільний ряд.
/// Це доказова таблиця, а не прикраса: вона показує і збіги, і розбіжності.
#[test]
fn shared_rows_report_the_actual_answer_of_every_available_core() {
    let mut core4 = core4_session();
    let mut core3 = core3_session();
    let mut core2 = core2_session();

    let mut table = String::new();
    for row in rows() {
        let answer4 = actual(&mut core4, &row.expr);
        let answer3 = actual(&mut core3, &row.expr);
        let answer2 = actual(&mut core2, &row.expr);
        let verdict = if row.law_holds(&answer4) && row.law_holds(&answer3) && row.law_holds(&answer2) {
            "закон"
        } else {
            "ПОРУШЕНО"
        };
        table.push_str(&format!(
            "{:<34} {:<16} | 4: {:<6} 3: {:<6} 2: {:<6} {}\n",
            row.expr, row.status, answer4, answer3, answer2, verdict
        ));
    }
    println!("#1663 спільна доменна таблиця відповіді\n{table}");
}

/// Спільний закон діє на кодах СЕНС вже на ядрах 2, 3 і 4.
#[test]
fn shared_law_holds_on_every_core_that_can_be_loaded() {
    let violations: Vec<String> = rows()
        .iter()
        .filter(|row| row.status == "спільний")
        .flat_map(|row| {
            [("ядро 4", core4_session()), ("ядро 3", core3_session()), ("ядро 2", core2_session())]
                .into_iter()
                .filter_map(move |(label, mut session)| {
                    let answer = actual(&mut session, &row.expr);
                    (!row.law_holds(&answer))
                        .then(|| format!("{label}: {} дав {answer} замість {}", row.expr, row.expected))
                })
        })
        .collect();

    assert!(
        violations.is_empty(),
        "спільний закон домену відповіді порушено:\n{}",
        violations.join("\n")
    );
}

/// Носій асертиться лише там, де він ратифікований.
#[test]
fn ratified_carrier_is_a_list_of_bits() {
    let mut core4 = core4_session();
    for row in rows().iter().filter(|row| row.status == "спільний") {
        let carrier = row
            .carrier
            .as_ref()
            .expect("ряд «спільний» має ратифікований носій");
        let answer = actual(&mut core4, &row.expr);
        assert_eq!(answer, *carrier, "носій відповіді розбігвся для {}", row.expr);
    }
}
