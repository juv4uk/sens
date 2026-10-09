use sens::{eval_program, ErrorKind, Session};

fn session_with_language_canon() -> Session {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/canon.lisp"), &mut session)
        .expect("lib/canon.my must bootstrap as executable semantics");
    session
}

#[test]
fn historical_canon_surface_cannot_be_rebound() {
    let mut session = session_with_language_canon();
    let error = eval_program("(def car (lambda (x) (quote зламано)))", &mut session)
        .expect_err("Contract 6.0 must reject rebinding the historical Canon spelling");
    assert_eq!(error.kind, ErrorKind::InvalidForm);

    let result = eval_program("(перше (сполучити 1 2))", &mut session)
        .expect("failed rebinding must leave the immutable Canon identity intact");
    assert_eq!(result.value.to_string(), "1");
}

#[test]
fn ukrainian_and_sanskrit_surfaces_are_reserved_spellings_of_one_semantics() {
    let mut session = session_with_language_canon();

    for source in [
        "(def перше (lambda (x) (quote локально)))",
        "(def ādi (lambda (x) (quote sthānika)))",
    ] {
        let error = eval_program(source, &mut session)
            .expect_err("every human Canon spelling must be reserved under Contract 6.0");
        assert_eq!(error.kind, ErrorKind::InvalidForm, "source: {source}");
    }

    let ukrainian = eval_program("(перше (сполучити 1 2))", &mut session)
        .expect("Ukrainian Canon surface must remain available");
    let sanskrit = eval_program("(ādi (saṃyuj 1 2))", &mut session)
        .expect("Sanskrit Canon surface must remain available");
    assert_eq!(ukrainian.value.to_string(), "1");
    assert_eq!(sanskrit.value.to_string(), "1");
}

#[test]
fn canon_zero_is_stated_by_the_language_as_the_empty_list_itself() {
    let mut session = session_with_language_canon();
    let result = eval_program("canon-empty-list", &mut session)
        .expect("language canon should expose its Canon 0 witness");
    assert_eq!(result.value.to_string(), "()");
}
