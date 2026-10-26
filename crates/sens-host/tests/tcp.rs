//! TCP capability and language-owned read-semantics integration tests.
//! TCP integration tests use real sockets and separate sessions per endpoint.

use sens::{
    eval_program, load_core_library, load_tcp_library, ErrorKind, Exactness, Session, Value,
};
use sens_host::install;
use std::io::{Read, Write};
use std::net::{Shutdown, TcpListener, TcpStream};
use std::thread;

fn tcp_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).unwrap();
    load_tcp_library(&mut session).unwrap();
    session
}

fn free_port() -> u16 {
    TcpListener::bind("127.0.0.1:0")
        .expect("binding to port 0 should succeed")
        .local_addr()
        .expect("a bound listener should have a local address")
        .port()
}

fn tcp_session_with_port(port: u16) -> Session {
    let session = tcp_session();
    session
        .environment
        .define("порт", Value::Number(port as f64, Exactness::Exact));
    session
}

#[test]
fn raw_tcp_client_reads_peer_bytes_and_writes_a_response() {
    install();
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let port = listener.local_addr().unwrap().port();
    let server = thread::spawn(move || {
        let (mut stream, _) = listener.accept().unwrap();
        stream.write_all(b"ok").unwrap();
        stream.shutdown(Shutdown::Write).unwrap();
        let mut received = Vec::new();
        stream.read_to_end(&mut received).unwrap();
        received
    });

    let mut session = tcp_session_with_port(port);
    session.environment.define(
        "дані",
        Value::list([104, 105].map(|byte| Value::Number(byte as f64, Exactness::Exact))),
    );
    let result = eval_program(
        r#"
        (визначити підключення (tcp-connect "127.0.0.1" порт))
        (визначити відповідь (протокол-передавання-сире-читання підключення))
        (визначити записане (протокол-передавання-сирий-запис підключення дані))
        (tcp-close підключення)
        (список відповідь записане)
        "#,
        &mut session,
    )
    .unwrap();
    assert_eq!(result.value.to_string(), "((111 107) (104 105))");
    assert_eq!(server.join().unwrap(), b"hi");
}

#[test]
fn raw_tcp_server_receives_one_byte_from_peer() {
    install();
    let port = free_port();
    let server = thread::spawn(move || {
        let mut session = tcp_session_with_port(port);
        let source = r#"
            (визначити слухач (протокол-передавання-сире-слухання "127.0.0.1" порт))
            (визначити підключення (tcp-accept слухач))
            (протокол-передавання-сире-читання підключення)
            "#;
        eval_program(source, &mut session)
            .unwrap_or_else(|error| panic!("TCP reader failed: {error}"))
            .value
            .to_string()
    });
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
    stream.write_all(b"x").unwrap();
    drop(stream);
    assert_eq!(server.join().unwrap(), "(120)");
}

#[test]
fn text_read_returns_an_empty_string_on_a_closed_connection() {
    install();
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let port = listener.local_addr().unwrap().port();
    let server = thread::spawn(move || {
        let (stream, _) = listener.accept().unwrap();
        drop(stream);
    });
    let result = eval_program(
        r#"
        (визначити підключення (tcp-connect "127.0.0.1" порт))
        (визначити текст (протокол-передавання-читати підключення))
        (tcp-close підключення)
        текст
        "#,
        &mut tcp_session_with_port(port),
    )
    .expect("reading a closed connection should return an empty string, not error");
    assert_eq!(result.value, Value::String("".into()));
    server.join().unwrap();
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
fn raw_read_preserves_non_utf8_bytes_and_public_read_rejects_them() {
    install();
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let port = listener.local_addr().unwrap().port();

    let server = thread::spawn(move || {
        let (mut stream, _) = listener.accept().unwrap();
        stream.write_all(&[255]).unwrap();
    });

    let mut raw_session = tcp_session();
    raw_session
        .environment
        .define("порт", Value::Number(port as f64, Exactness::Exact));
    let raw = eval_program(
        r#"(визначити підключення (tcp-connect "127.0.0.1" порт)) (протокол-передавання-сире-читання підключення)"#,
        &mut raw_session,
    )
    .unwrap_or_else(|error| panic!("raw TCP read failed: {error}"));
    assert_eq!(raw.value.to_string(), "(255)");
    server.join().unwrap();

    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let port = listener.local_addr().unwrap().port();
    let server = thread::spawn(move || {
        let (mut stream, _) = listener.accept().unwrap();
        stream.write_all(&[255]).unwrap();
    });
    let mut text_session = tcp_session();
    text_session
        .environment
        .define("порт", Value::Number(port as f64, Exactness::Exact));
    let interpreted = eval_program(
        r#"(визначити підключення (tcp-connect "127.0.0.1" порт)) (протокол-передавання-читати підключення)"#,
        &mut text_session,
    )
    .unwrap_or_else(|error| panic!("public TCP text reader failed: {error}"));
    assert_eq!(interpreted.value.to_string(), "(rejected invalid-utf8)");
    server.join().unwrap();
}

#[test]
fn public_text_writer_sends_utf8_and_returns_the_input_text() {
    install();
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let port = listener.local_addr().unwrap().port();
    let server = thread::spawn(move || {
        let (mut stream, _) = listener.accept().unwrap();
        let mut bytes = Vec::new();
        stream.read_to_end(&mut bytes).unwrap();
        bytes
    });
    let source = r#"
        (визначити підключення (tcp-connect "127.0.0.1" порт))
        (визначити записане (протокол-передавання-записати підключення "payload"))
        (tcp-close підключення)
        записане
    "#;
    let result = eval_program(source, &mut tcp_session_with_port(port))
        .unwrap_or_else(|error| panic!("public TCP text writer failed: {error}"));
    assert_eq!(result.value, Value::String("payload".into()));
    assert_eq!(server.join().unwrap(), b"payload");
}
