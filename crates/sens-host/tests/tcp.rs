//! TCP capability and language-owned read-semantics integration tests.
//! TCP integration tests use real sockets and separate sessions per endpoint.

use sens::{
    eval_program, load_core_library, load_tcp_library, ErrorKind, Exactness, Session, Value,
};
use sens_host::install;
use std::io::{Read, Write};
use std::net::{TcpListener, TcpStream};
use std::thread;

fn tcp_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).unwrap();
    load_tcp_library(&mut session).unwrap();
    session
}

fn eval_client_with_retry(
    source: &str,
    session: &mut Session,
) -> Result<sens::EvalResult, sens::LanguageError> {
    let mut last_error = None;
    for attempt in 0..20 {
        if attempt > 0 {
            thread::sleep(std::time::Duration::from_millis(100));
        }
        match eval_program(source, session) {
            Ok(result) => return Ok(result),
            Err(error) if error.message.contains("tcp-connect:") => last_error = Some(error),
            Err(error) => return Err(error),
        }
    }
    Err(last_error.expect("at least one attempt should have run"))
}

fn free_port() -> u16 {
    TcpListener::bind("127.0.0.1:0")
        .expect("binding to port 0 should succeed")
        .local_addr()
        .expect("a bound listener should have a local address")
        .port()
}

fn load_knowledge(session: &mut Session) {
    load_core_library(session).unwrap();
    load_tcp_library(session).unwrap();
    eval_program(include_str!("../../../lib/unify.lisp"), session).unwrap();
    eval_program(include_str!("../../../lib/reason.lisp"), session).unwrap();
    eval_program(include_str!("../../../lib/forward.lisp"), session).unwrap();
    eval_program(include_str!("../../../lib/knowledge.lisp"), session).unwrap();
}

#[test]
fn client_and_server_exchange_one_message_each_way() {
    install();
    let port = free_port();

    let server = thread::spawn(move || {
        let mut session = tcp_session();
        let source = format!(
            r#"
            (def listener (tcp-listen {port}))
            (def conn (tcp-accept listener))
            (def request (tcp-read conn))
            (tcp-write conn (string-append "echo: " request))
            (tcp-close conn)
            request
            "#
        );
        eval_program(&source, &mut session)
            .expect("server-side program should evaluate without error")
            .value
            .to_string()
    });

    thread::sleep(std::time::Duration::from_millis(200));

    let mut client_session = tcp_session();
    let client_source = format!(
        r#"
        (def conn (tcp-connect "127.0.0.1" {port}))
        (tcp-write conn "hello from client")
        (def reply (tcp-read conn))
        (tcp-close conn)
        reply
        "#
    );
    let client_result = eval_client_with_retry(&client_source, &mut client_session)
        .expect("client-side program should evaluate without error");

    assert_eq!(
        client_result.value,
        Value::String("echo: hello from client".into())
    );
    assert_eq!(
        server.join().expect("server thread should not panic"),
        "\"hello from client\""
    );
}

#[test]
fn send_knowledge_package_transmits_one_canonical_expression_then_eof() {
    install();
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let port = listener.local_addr().unwrap().port();
    let server = thread::spawn(move || {
        let (mut stream, _) = listener.accept().unwrap();
        let mut text = String::new();
        stream.read_to_string(&mut text).unwrap();
        text
    });
    let mut session = Session::default();
    load_knowledge(&mut session);
    let source = format!(
        r#"
        (def connection (tcp-connect "127.0.0.1" {port}))
        (send-knowledge-package connection (quote exchange)
          (quote (((planet earth)) ((has-mass (var x)) (planet (var x))))))
        "#
    );
    eval_program(&source, &mut session).unwrap();
    assert_eq!(
        server.join().unwrap(),
        "((format . my-lisp-knowledge) (version 0 1) (module . exchange) (clauses ((planet earth)) ((has-mass (var x)) (planet (var x)))))"
    );
}

#[test]
fn protocol_read_drains_tcp_chunks_until_eof() {
    install();
    let port = free_port();
    let server = thread::spawn(move || {
        let mut session = Session::default();
        load_knowledge(&mut session);
        session
            .environment
            .define("порт", Value::Number(port as f64, Exactness::Exact));
        let source = format!(
            r#"
            (визначити слухач (протокол-передавання-сире-слухання "127.0.0.1" порт))
            (визначити підключення (tcp-accept слухач))
            (протокол-передавання-сире-читання підключення)
            "#
        );
        eval_program(&source, &mut session)
            .unwrap_or_else(|error| panic!("TCP reader failed: {error}"))
            .value
            .to_string()
    });
    let payload = b"((format . my-lisp-knowledge) (version 0 1) (module . exchange) (clauses . (((planet earth)) ((has-mass (var x)) (planet (var x))))))";
    let deadline = std::time::Instant::now() + std::time::Duration::from_secs(5);
    let mut stream = loop {
        match TcpStream::connect(("127.0.0.1", port)) {
            Ok(stream) => break stream,
            Err(error) => {
                assert!(
                    !server.is_finished(),
                    "TCP reader exited before accepting TCP (last connect error: {error})"
                );
                assert!(
                    std::time::Instant::now() < deadline,
                    "TCP reader did not open listener within 5s (last connect error: {error})"
                );
                thread::sleep(std::time::Duration::from_millis(50));
            }
        }
    };
    for chunk in payload.chunks(17) {
        stream.write_all(chunk).unwrap();
    }
    drop(stream);
    let expected = Value::list(
        payload
            .iter()
            .map(|byte| Value::Number(*byte as f64, Exactness::Exact)),
    );
    assert_eq!(server.join().unwrap(), expected.to_string());
}

#[test]
fn framed_exchange_returns_an_accepted_receipt_to_the_sender() {
    install();
    let port = free_port();
    let server = thread::spawn(move || {
        let mut session = Session::default();
        load_knowledge(&mut session);
        let source = format!(
            r#"
            (def listener (tcp-listen {port}))
            (def connection (tcp-accept listener))
            (accept-knowledge-exchange connection)
            "#
        );
        eval_program(&source, &mut session)
            .unwrap()
            .value
            .to_string()
    });
    let mut client = Session::default();
    load_knowledge(&mut client);
    let source = format!(
        r#"
        (def connection (tcp-connect "127.0.0.1" {port}))
        (exchange-knowledge-package connection (quote exchange) (quote (((planet earth)))))
        "#
    );
    let receipt = eval_client_with_retry(&source, &mut client).unwrap();
    assert_eq!(
        receipt.value.to_string(),
        "(accepted (module exchange) (knowledge (((planet earth)))))"
    );
    assert_eq!(server.join().unwrap(), receipt.value.to_string());
}

#[test]
fn framed_exchange_returns_conflict_and_does_not_install_the_new_fact() {
    install();
    let port = free_port();
    let server = thread::spawn(move || {
        let mut session = Session::default();
        load_knowledge(&mut session);
        let source = format!(
            r#"
            (defmodule exchange (quote (((not? (planet pluto))))))
            (def listener (tcp-listen {port}))
            (def connection (tcp-accept listener))
            (def decision (accept-knowledge-exchange connection))
            (list (car decision) (reason-in (quote exchange) (quote (planet pluto))))
            "#
        );
        eval_program(&source, &mut session)
            .unwrap()
            .value
            .to_string()
    });
    let mut client = Session::default();
    load_knowledge(&mut client);
    let source = format!(
        r#"
        (def connection (tcp-connect "127.0.0.1" {port}))
        (exchange-knowledge-package connection (quote exchange) (quote (((planet pluto)))))
        "#
    );
    let receipt = eval_client_with_retry(&source, &mut client).unwrap();
    assert_eq!(
        receipt.value.to_string().split_whitespace().next(),
        Some("(conflict")
    );
    assert_eq!(server.join().unwrap(), "(conflict ())");
}

#[test]
fn tcp_read_returns_an_empty_string_on_a_closed_connection() {
    install();
    let port = free_port();

    let server = thread::spawn(move || {
        let mut session = tcp_session();
        let source = format!(
            r#"
            (def listener (tcp-listen {port}))
            (def conn (tcp-accept listener))
            (tcp-close conn)
            "#
        );
        eval_program(&source, &mut session)
            .expect("server-side program should evaluate without error");
    });

    thread::sleep(std::time::Duration::from_millis(200));

    let mut client_session = tcp_session();
    let client_source = format!(
        r#"
        (def conn (tcp-connect "127.0.0.1" {port}))
        (tcp-read conn)
        "#
    );
    let result = eval_client_with_retry(&client_source, &mut client_session)
        .expect("reading a closed connection should return an empty string, not error");
    assert_eq!(result.value, Value::String("".into()));

    server.join().expect("server thread should not panic");
}

#[test]
fn tcp_connect_to_a_closed_port_fails_named_not_silently() {
    install();
    let port = free_port();
    let mut session = tcp_session();
    session
        .environment
        .define("порт", Value::Number(port as f64, Exactness::Exact));
    let source = r#"(tcp-connect "127.0.0.1" порт)"#;
    let error = eval_program(&source, &mut session)
        .expect_err("connecting to a port nothing listens on must fail named, not hang or panic");
    assert_eq!(error.kind, ErrorKind::InvalidForm);
    assert!(error.message.contains("tcp-connect: failed to connect"));
}

#[test]
fn tcp_connect_rejects_a_non_string_host() {
    install();
    let error = eval_program("(tcp-connect 42 8099)", &mut tcp_session())
        .expect_err("a non-string host must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn tcp_connect_rejects_an_out_of_range_port() {
    install();
    let error = eval_program(r#"(tcp-connect "127.0.0.1" 99999)"#, &mut tcp_session())
        .expect_err("a port past 65535 must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn tcp_read_rejects_a_non_connection_argument() {
    install();
    let error = eval_program(
        r#"(протокол-передавання-читати "not a connection")"#,
        &mut tcp_session(),
    )
    .expect_err("a non-connection argument must fail named, not panic");
    assert_eq!(error.kind, ErrorKind::Type);
}

#[test]
fn tcp_raw_read_preserves_non_utf8_bytes_and_public_read_rejects_them_in_lisp() {
    install();
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let port = listener.local_addr().unwrap().port();

    let server = thread::spawn(move || {
        let (mut stream, _) = listener.accept().unwrap();
        stream.write_all(&[255]).unwrap();
    });

    let mut raw_session = tcp_session();
    let raw = eval_program(
        &format!(r#"(def c (tcp-connect "127.0.0.1" {port})) (tcp-read-raw c)"#),
        &mut raw_session,
    )
    .unwrap();
    assert_eq!(raw.value.to_string(), "(255)");
    server.join().unwrap();

    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let port = listener.local_addr().unwrap().port();
    let server = thread::spawn(move || {
        let (mut stream, _) = listener.accept().unwrap();
        stream.write_all(&[255]).unwrap();
    });
    let mut text_session = tcp_session();
    let interpreted = eval_program(
        &format!(r#"(def c (tcp-connect "127.0.0.1" {port})) (tcp-read c)"#),
        &mut text_session,
    )
    .unwrap();
    assert_eq!(interpreted.value.to_string(), "(rejected invalid-utf8)");
    server.join().unwrap();
}

#[test]
fn tcp_write_returns_its_content_argument_unchanged() {
    install();
    let port = free_port();
    let server = thread::spawn(move || {
        let mut session = tcp_session();
        let source = format!(
            r#"
            (def listener (tcp-listen {port}))
            (def conn (tcp-accept listener))
            (tcp-read conn)
            (tcp-close conn)
            "#
        );
        eval_program(&source, &mut session)
            .expect("server-side program should evaluate without error");
    });

    thread::sleep(std::time::Duration::from_millis(200));

    let mut client_session = tcp_session();
    let client_source = format!(
        r#"
        (def conn (tcp-connect "127.0.0.1" {port}))
        (def written (tcp-write conn "payload"))
        (tcp-close conn)
        written
        "#
    );
    let result = eval_client_with_retry(&client_source, &mut client_session)
        .expect("client-side program should evaluate without error");
    assert_eq!(result.value, Value::String("payload".into()));

    server.join().expect("server thread should not panic");
}
