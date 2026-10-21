//! Реальний SENS evaluator: UNIFY outcomes без жодних host-імітацій.
//! Перевіряємо окремо невдачу, порожню успішну підстановку і вкладене термо.
use sens::{
    eval_parsed_expressions, eval_core_library_source,
    eval_pinned_reasoning_source, parse_mixed_exact_domain, Session,
};

fn session() -> Session {
    let mut session = Session::default();
    eval_core_library_source(include_str!("../../../lib/core.lisp"), &mut session
    ).expect("точнодоменне ядро");
    eval_pinned_reasoning_source(
        "lib/unify.lisp", include_str!("../../../lib/unify.lisp"), &mut session
    ).expect("реальне Lisp-owned ядро уніфікації");
    let forms = parse_mixed_exact_domain(include_str!("../../../lib/unify-observe.lisp"))
        .expect("обидва D4-визначення повинні читатися точно");
    eval_parsed_expressions(&forms, &mut session)
        .expect("виконуваний observer має завантажитися");
    session
}

fn observe(session: &mut Session, query: &str) -> String {
    let forms = parse_mixed_exact_domain(query).expect("припустимий D3/D4 запит");
    eval_parsed_expressions(&forms, session)
        .unwrap_or_else(|e| panic!("живий observer не виконав {query}: {e:?}"))
        .value.to_string()
}

#[test]
fn empty_success_and_real_failure_are_distinct_data() {
    let mut session = session();
    assert_eq!(
        observe(&mut session,
            "(спостерігати-уніфікацію (як-є radio) (як-є radio) (як-є ()))"),
        "(unified ())"
    );
    assert_eq!(
        observe(&mut session,
            "(спостерігати-уніфікацію (як-є radio) (як-є antenna) (як-є ()))"),
        "(unification-failure radio antenna ())"
    );
}

#[test]
fn helper_distinguishes_fail_atom_other_atom_and_compound_substitution() {
    let mut session = session();
    for (source, expected) in [
        ("(уніфікація-спостереження-стан (як-є fail) (як-є radio) (як-є antenna) (як-є ()))",
         "(unification-failure radio antenna ())"),
        ("(уніфікація-спостереження-стан (як-є ()) (як-є radio) (як-є radio) (як-є ()))",
         "(unified ())"),
        ("(уніфікація-спостереження-стан (як-є ready) (як-є radio) (як-є radio) (як-є ()))",
         "(unified ready)"),
        ("(уніфікація-спостереження-стан (як-є ((x . radio))) (як-є radio) (як-є radio) (як-є ()))",
         "(unified ((x . radio)))"),
    ] {
        assert_eq!(observe(&mut session, source), expected, "{source}");
    }
}
