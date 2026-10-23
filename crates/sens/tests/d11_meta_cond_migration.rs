//! D11 00001010011 — закон виявлення двопольової гілки COND.
//! Усі рішення ухвалює власний MetaEval, що виконується мовою SENS.
//! Дослідна координата — не прямий машинний D11 opcode.

mod common;

use sens::{eval_program, load_core_library, Session};

#[test]
fn d11_двопольова_умовна_гілка_досяжна_і_не_плутається_з_трипольовою() {
    let mut session = Session::bare();
    load_core_library(&mut session).expect("завантажити ядро SENS");
    common::load_meta_evaluator_library(&mut session).expect("завантажити живий MetaEval");

    for (case, source, expected) in [
        ("порожньо", "(має-перехідну-гілку-за-умовою? (як-є ()))", false),
        ("лише-атом", "(має-перехідну-гілку-за-умовою? (як-є (шум)))", false),
        ("одне-поле", "(має-перехідну-гілку-за-умовою? (як-є ((запит))))", false),
        ("два-поля", "(має-перехідну-гілку-за-умовою? (як-є ((запит дія))))", true),
        ("три-поля", "(має-перехідну-гілку-за-умовою? (як-є ((запит відповідь дія))))", false),
        ("три-перед-двома", "(має-перехідну-гілку-за-умовою? (як-є ((запит відповідь дія) (інший дія))))", true),
        ("два-перед-трьома", "(має-перехідну-гілку-за-умовою? (як-є ((інший дія) (запит відповідь дія))))", true),
        ("атом-перед-двома", "(має-перехідну-гілку-за-умовою? (як-є (шум (запит дія))))", true),
        ("атом-після-трьох", "(має-перехідну-гілку-за-умовою? (як-є ((запит відповідь дія) шум)))", false),
        ("одне-перед-двома", "(має-перехідну-гілку-за-умовою? (як-є ((шум) (запит дія))))", true),
    ] {
        let observed = eval_program(source, &mut session)
            .unwrap_or_else(|error| {
                panic!("test_id=D11-META-COND-{case} layer=SENS input={source} actual_error={error}")
            })
            .value;
        assert_eq!(
            observed.as_predicate_bit(),
            Some(expected),
            "test_id=D11-META-COND-{case} layer=SENS input={source} expected=D1:{expected} actual={observed}"
        );
    }
}
