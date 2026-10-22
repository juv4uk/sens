//! D11: одноразове розіменування як визначена SENS-композиція, не новий примітив.
//! Відмінність від рекурсивного пройти перевіряє справжній eval_program SENS.

use sens::{eval_program, Session};

#[test]
fn d11_розвязати_один_раз_не_підмінює_рекурсивне_проходження() {
    let mut session = Session::default();
    eval_program(include_str!("../../../lib/core.lisp"), &mut session)
        .expect("завантажити чинне ядро SENS");
    eval_program(include_str!("../../../lib/unify.lisp"), &mut session)
        .expect("завантажити живі правила уніфікації SENS");

    eval_program(
        r#"
        (визначити один-змінний (логічна-змінна (як-є х)))
        (визначити другий-змінний (логічна-змінна (як-є у)))
        (визначити звязування
          (розширити-підстановку один-змінний другий-змінний
            (розширити-підстановку другий-змінний (як-є готово) (як-є ()))))
        "#,
        &mut session,
    )
    .expect("створити два послідовні бібліотечні зв'язування");

    for (case, source, expected) in [
        (
            "один-крок",
            "(розв'язати-один-раз один-змінний звязування)",
            "(var у)",
        ),
        (
            "повне-проходження",
            "(пройти один-змінний звязування)",
            "готово",
        ),
        (
            "атом-не-змінюється",
            "(розв'язати-один-раз (як-є атом) звязування)",
            "атом",
        ),
        (
            "не-знайдено",
            "(розв'язати-один-раз (логічна-змінна (як-є немає)) звязування)",
            "(var немає)",
        ),
    ] {
        let observed = eval_program(source, &mut session)
            .unwrap_or_else(|error| {
                panic!(
                    "test_id=D11-UNIFY-ONCE-{case} layer=SENS source={source} actual_error={error}"
                )
            })
            .value
            .to_string();
        assert_eq!(
            observed, expected,
            "test_id=D11-UNIFY-ONCE-{case} layer=SENS source={source} expected={expected} actual={observed}"
        );
    }
}
