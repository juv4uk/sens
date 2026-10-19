//! Реальне виконання SENS REPL після завантаження чинного core/meta-eval.
//! Незаконні атомарні хвости не мають виглядати як кінець списку.
use sens::{eval_parsed_expressions, eval_program, load_core_library, load_meta_evaluator_library, parse_mixed_exact_domain, Session};

fn repl_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).expect("current Core4 must load");
    load_meta_evaluator_library(&mut session).expect("SENS meta-evaluator must load");
    let source = include_str!("../../../lib/repl-core.lisp");
    let forms = parse_mixed_exact_domain(source).expect("SENS REPL reader");
    eval_parsed_expressions(&forms, &mut session).expect("SENS REPL definitions must evaluate");
    session
}

#[test]
fn repl_bit_and_label_comparisons_reject_improper_tails() {
    let mut session = repl_session();
    for (source, expected) in [
        ("(репл-біти-збігаються? (як-є ()) \"\")", true),
        ("(репл-біти-збігаються? (як-є зайве) \"\")", false),
        ("(репл-біти-збігаються? (як-є (зайве)) \"\")", false),
        ("(репл-мітки-черги? (як-є ()) (як-є ()))", true),
        ("(репл-мітки-черги? (як-є зайве) (як-є ()))", false),
        ("(репл-мітки-черги? (як-є (зайве)) (як-є ()))", false),
    ] {
        let result = eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("SENS REPL failed on {source}: {error:?}"))
            .value;
        assert_eq!(result.as_predicate_bit(), Some(expected), "{source}: {result}");
    }
}
