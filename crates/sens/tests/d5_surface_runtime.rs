//! End-to-end witnesses for #3354 exact-domain D5 surface routing.

use sens::{eval_program, Session};

#[test]
fn d5_uk_and_sanskrit_plus_execute_through_ratified_d5() {
    for source in ["(додати 2 3)", "(yoga 2 3)"] {
        let mut session = Session::default();
        let result = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("D5 PLUS surface must execute: {source}: {error}"));
        assert_eq!(result.value.to_string(), "5");
    }
}

#[test]
fn d5_depth3_selector_surface_executes_selector_law() {
    for surface in ["перше-від-решти-від-першого", "ādi-śeṣa-ādi"] {
        let source = format!("({surface} (як-є ((1 2) (3 4))))");
        let mut session = Session::default();
        let result = eval_program(&source, &mut session)
            .unwrap_or_else(|error| panic!("D5 CADAR surface must execute: {source}: {error}"));
        assert_eq!(result.value.to_string(), "2");
    }
}
