//! Нативна регресія нових українських циклічних зсувів D3/D4.
//! Рівно ті самі Lisp-байти перевіряються в SENS, не Python/JSON-оракулом.
use sens::{eval_program, parse_mixed_exact_domain, Session};

const SOURCE: &str = include_str!("../../../lib/list-rotate-inverse-general.lisp");

#[test]
fn rotate_left_right_inverse_runs_32_laws_in_real_sens() {
    parse_mixed_exact_domain(SOURCE).expect("test_id=ukr-rotate layer=reader expected=valid-lisp");
    let mut session = Session::default();
    let result = eval_program(SOURCE, &mut session)
        .expect("test_id=ukr-rotate layer=SENS expected=32-laws-D1-true");
    let mut truth_session = Session::default();
    let truth = eval_program("(атом? (як-є ()))", &mut truth_session)
        .expect("test_id=ukr-rotate layer=D1 expected=true");
    assert_eq!(
        result.value, truth.value,
        "test_id=ukr-rotate layer=SENS expected=D1-true actual=nontrue"
    );
}

#[test]
fn wrong_right_rotation_rejects_inverse_law_in_real_sens() {
    const CORRECT: &str = "(сполучити (останній-для-зсуву елементи)";
    const WRONG: &str = "(сполучити (перше елементи)";
    assert_eq!(
        SOURCE.matches(CORRECT).count(), 1,
        "test_id=ukr-rotate layer=mutation expected=one-site"
    );
    let mutant = SOURCE.replacen(CORRECT, WRONG, 1);
    parse_mixed_exact_domain(&mutant)
        .expect("test_id=ukr-rotate layer=reader expected=valid-mutant");
    let mut session = Session::default();
    let actual = eval_program(&mutant, &mut session);
    let mut truth_session = Session::default();
    let truth = eval_program("(атом? (як-є ()))", &mut truth_session)
        .expect("test_id=ukr-rotate layer=D1 expected=true");
    match actual {
        Ok(value) => assert_ne!(
            value.value, truth.value,
            "test_id=ukr-rotate layer=SENS expected=mutant-rejected actual=D1-true"
        ),
        Err(_semantic_rejection) => {
            // Помилка живого SENS-виконання допустима для хибного закону.
        }
    }
}
