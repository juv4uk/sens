use sens::{eval_program, Session};

fn eval(source: &str) -> String {
    let mut session = Session::default();
    eval_program(source, &mut session)
        .expect("timing witness must evaluate")
        .value
        .to_string()
}

#[test]
fn evaluation_time_transformer_observes_same_frame_redefinition_after_function_definition() {
    let value = eval(
        r#"
        (визначити перетворювач-фази
          (макрос
            (функція ()
              (як-є (як-є OLD)))))

        (визначити викликати-пізніше
          (функція ()
            (перетворювач-фази)))

        (визначити перетворювач-фази
          (макрос
            (функція ()
              (як-є (як-є NEW)))))

        (викликати-пізніше)
        "#,
    );

    assert_eq!(
        value, "НОВЕ",
        "current SENS expands the transformer call when викликати-пізніше is evaluated,          so the same-frame transformer redefinition is visible"
    );
}

#[test]
fn evaluation_time_transformer_still_executes_generated_form_in_calling_environment() {
    let value = eval(
        r#"
        (визначити видати-імя-викликача
          (макрос
            (функція ()
              (як-є імя-викликача))))

        ((функція (імя-викликача)
           (видати-імя-викликача))
         73)
        "#,
    );

    assert_eq!(value, "73");
}
