use sens::{eval_program, ErrorKind, Session};
use sens_host::install;

#[test]
fn tcp_connect_failure_has_stable_operation_prefix_without_pinning_os_tail() {
    install();
    let mut session = Session::default();

    let error = eval_program("(tcp-connect \"127.0.0.1\" 0)", &mut session)
        .expect_err("connecting to TCP port 0 must fail");

    assert_eq!(error.kind, ErrorKind::InvalidForm);
    assert!(
        error.message.starts_with("tcp-connect:"),
        "host failure must preserve stable operation identity before platform detail: {}",
        error.message
    );
}
