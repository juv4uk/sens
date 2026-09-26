use sens::{eval_program, Session};

#[test]
fn process_run_raw_preserves_non_utf8_stdout_and_stderr() {
    sens_host::install();
    let mut session = Session::default();

    let source = r#"
        (process-run-raw
          "python3"
          (quote ("-c"
                   "import sys; sys.stdout.buffer.write(bytes([255,65])); sys.stderr.buffer.write(bytes([254]))")))
    "#;

    let result = eval_program(source, &mut session).expect("raw process observation should succeed");
    assert_eq!(
        result.value.to_string(),
        "(process-result 0 (255 65) (254))"
    );
}
