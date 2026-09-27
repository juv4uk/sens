//! Параметри замикання за номером слота (`ExprKind::Local`) не змінюють
//! семантики: кожна програма тут має ту саму відповідь, що й при пошуку за
//! іменем. Випадки підібрано там, де розв'язувач міг би помилитися.

use sens::{eval_program, Session};

fn run(source: &str) -> String {
    let mut session = Session::default();
    eval_program(source, &mut session)
        .unwrap_or_else(|error| panic!("{source}: {error}"))
        .value
        .to_string()
}

#[test]
fn parameter_inside_quote_stays_data() {
    assert_eq!(run("((00001000 (x) (00000001 x)) 5)"), "x");
    assert_eq!(run("((00001000 (x) (00000001 (x x))) 5)"), "(x x)");
}

#[test]
fn cond_expected_result_is_data_not_a_parameter() {
    // Очікуваний результат — дані: символ x, а не значення параметра x.
    assert_eq!(run("((00001000 (x) (00000111 ((00000001 x) x 1))) 5)"), "1");
}

#[test]
fn nested_closure_captures_outer_parameters() {
    assert_eq!(run("(((00001000 (x) (00001000 (y) (00001100 x y))) 3) 4)"), "7");
    assert_eq!(
        run("((((00001000 (a) (00001000 (b) (00001000 (c) (00001101 (00001100 a b) c)))) 10) 20) 5)"),
        "25"
    );
}

#[test]
fn eval_in_inner_frame_shadows_outer_parameter() {
    // Внутрішній кадр отримує x через eval — пошук за іменем знаходить його
    // раніше за параметр зовнішньої lambda.
    assert_eq!(
        run("((00001000 (x) ((00001000 () (01001101 (00000001 (00001011 x 9))) x))) 1)"),
        "9"
    );
}

#[test]
fn def_in_inner_frame_shadows_outer_parameter() {
    assert_eq!(run("((00001000 (x) ((00001000 () (00001011 x 9) x))) 1)"), "9");
}

#[test]
fn def_of_own_parameter_updates_it() {
    assert_eq!(run("((00001000 (x) (00001011 x 5) x) 1)"), "5");
}

#[test]
fn parameter_shadows_a_global_name() {
    assert_eq!(run("(00001011 y 1) ((00001000 (y) y) 2)"), "2");
    assert_eq!(run("(00001011 y 1) ((00001000 (z) y) 2)"), "1");
}

#[test]
fn rest_parameter_is_a_slot() {
    assert_eq!(run("((00001000 (a . r) r) 1 2 3)"), "(2 3)");
    assert_eq!(run("((00001000 r r) 1 2)"), "(1 2)");
}

#[test]
fn deep_tail_recursion_through_slots_stays_off_the_stack() {
    assert_eq!(
        run("(00001011 down (00001000 (n acc) (00000111 ((00000011 n 0) acc) \
             (t (down (00001101 n 1) (00001100 acc 1)))))) (down 100000 0)"),
        "100000"
    );
}
