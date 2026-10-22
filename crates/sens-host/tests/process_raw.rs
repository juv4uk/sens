use sens::{eval_program, Session};

#[test]
fn process_run_raw_preserves_non_utf8_stdout_and_stderr() {
    sens_host::install();
    let mut session = Session::default();

    let source = r#"
        (процес-запустити-сирий
          "sh"
          (як-є ("-c" "printf '\\377A'; printf '\\376' >&2")))
    "#;

    let result =
        eval_program(source, &mut session).expect("raw process observation should succeed");
    let sens::Value::Pair(tag) = &result.value else {
        panic!("result list");
    };
    let sens::Value::Pair(status) = &tag.tail else {
        panic!("status field");
    };
    let mut streams = &status.tail;
    while let sens::Value::Pair(stream) = streams {
        let mut bytes = &stream.head;
        while let sens::Value::Pair(byte) = bytes {
            assert!(matches!(&byte.head, sens::Value::BinaryNumber(number)
                if number.numeric_domain_width() == Some(24)));
            bytes = &byte.tail;
        }
        assert!(matches!(bytes, sens::Value::Nil));
        streams = &stream.tail;
    }
    assert!(matches!(streams, sens::Value::Nil));
    assert_eq!(
        result.value.to_string(),
        "(process-result 0 (255 65) (254))"
    );
}
