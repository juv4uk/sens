//! #1391: логіка відповідей Core4 (контракт core4-predicate-answer-scale/3).
//! Відповідь — список двійкових бітів; лінія істинності
//! 0 < 00 < … < 0000000 < () < 1111111 < … < 11 < 1.
//! Тут лінію рахує Rust незалежно від Lisp, а функції мови мають
//! давати на ній мінімум (AND) і максимум (OR) для всіх 225 пар.

use sens::{eval_program, load_core_library, Session};

fn session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("core library should load");
    session
}

fn eval(session: &mut Session, source: &str) -> String {
    eval_program(source, session)
        .unwrap_or_else(|error| panic!("{source}: {error:?}"))
        .value
        .to_string()
}

/// Усі 15 відповідей у порядку лінії істинності.
fn truth_line() -> Vec<Vec<u8>> {
    let mut line: Vec<Vec<u8>> = (1..=7).map(|width| vec![0; width]).collect();
    line.push(Vec::new());
    line.extend((1..=7).rev().map(|width| vec![1; width]));
    line
}

/// Запис відповіді так, як її друкує мова: (0 0), (1), ().
fn spell(answer: &[u8]) -> String {
    let bits: Vec<String> = answer.iter().map(u8::to_string).collect();
    format!("({})", bits.join(" "))
}

fn quoted(answer: &[u8]) -> String {
    format!("(00000001 {})", spell(answer))
}

#[test]
fn and_is_meet_and_or_is_join_on_the_truth_line() {
    let line = truth_line();
    let mut session = session();
    for (i, a) in line.iter().enumerate() {
        for (j, b) in line.iter().enumerate() {
            let meet = &line[i.min(j)];
            let join = &line[i.max(j)];
            let and = eval(&mut session, &format!("(answer-and {} {})", quoted(a), quoted(b)));
            let or = eval(&mut session, &format!("(answer-or {} {})", quoted(a), quoted(b)));
            assert_eq!(and, spell(meet), "AND {} {}", spell(a), spell(b));
            assert_eq!(or, spell(join), "OR {} {}", spell(a), spell(b));
        }
    }
}

#[test]
fn not_mirrors_the_line_and_fixes_only_the_empty_answer() {
    let line = truth_line();
    let mut session = session();
    for (i, a) in line.iter().enumerate() {
        let mirrored = &line[line.len() - 1 - i];
        let not = eval(&mut session, &format!("(answer-not {})", quoted(a)));
        assert_eq!(not, spell(mirrored), "NOT {}", spell(a));
    }
}

#[test]
fn weakening_appends_the_same_bit_and_seven_bits_converge_to_empty() {
    let mut session = session();
    for bit in [0u8, 1] {
        for width in 1..=6 {
            let answer = vec![bit; width];
            let weaker = vec![bit; width + 1];
            let got = eval(&mut session, &format!("(answer-weaken {})", quoted(&answer)));
            assert_eq!(got, spell(&weaker));
        }
        let weakest = vec![bit; 7];
        let got = eval(&mut session, &format!("(answer-weaken {})", quoted(&weakest)));
        assert_eq!(got, "()");
    }
    assert_eq!(eval(&mut session, "(answer-weaken (00000001 ()))"), "()");
}

#[test]
fn atom_answer_treats_the_empty_list_as_unknown() {
    let mut session = session();
    assert_eq!(eval(&mut session, "(answer-atom (00000001 x))"), "(1)");
    assert_eq!(eval(&mut session, "(answer-atom 42)"), "(1)");
    assert_eq!(eval(&mut session, "(answer-atom (00000001 (a b)))"), "(0)");
    assert_eq!(eval(&mut session, "(answer-atom (00000001 ()))"), "()");
}

#[test]
fn eq_answer_is_grade_one_on_atoms() {
    let mut session = session();
    assert_eq!(eval(&mut session, "(answer-eq (00000001 a) (00000001 a))"), "(1)");
    assert_eq!(eval(&mut session, "(answer-eq (00000001 a) (00000001 b))"), "(0)");
    assert_eq!(eval(&mut session, "(answer-eq 7 7)"), "(1)");
}

#[test]
fn ukrainian_names_reach_the_same_functions() {
    let mut session = session();
    assert_eq!(
        eval(&mut session, "(відповідь-і (00000001 (1 1)) (00000001 (0)))"),
        "(0)"
    );
    assert_eq!(eval(&mut session, "(відповідь-атом (00000001 ()))"), "()");
}
