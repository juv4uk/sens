use sens::{eval_program, load_core_library, load_tcp_library, Session, Value};
use sens_host::install;
use std::io::Read;
use std::net::TcpListener;
use std::thread;

fn tcp_session() -> Session {
    let mut session = Session::default();
    load_core_library(&mut session).unwrap();
    load_tcp_library(&mut session).unwrap();
    session
}

#[test]
fn tcp_write_raw_preserves_arbitrary_wire_bytes() {
    install();
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let port = listener.local_addr().unwrap().port();
    let server = thread::spawn(move || {
        let (mut stream, _) = listener.accept().unwrap();
        let mut bytes = Vec::new();
        stream.read_to_end(&mut bytes).unwrap();
        bytes
    });

    let mut session = tcp_session();
    let source = format!(
        r#"
        (def c (tcp-connect "127.0.0.1" {port}))
        (tcp-write-raw c (quote (255 0 65 128)))
        (tcp-close c)
        "#
    );
    eval_program(&source, &mut session).unwrap();

    assert_eq!(server.join().unwrap(), vec![255, 0, 65, 128]);
}

#[test]
fn language_owned_tcp_write_encodes_unicode_before_raw_transport() {
    install();
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let port = listener.local_addr().unwrap().port();
    let server = thread::spawn(move || {
        let (mut stream, _) = listener.accept().unwrap();
        let mut bytes = Vec::new();
        stream.read_to_end(&mut bytes).unwrap();
        bytes
    });

    let mut session = tcp_session();
    let source = format!(
        r#"
        (def c (tcp-connect "127.0.0.1" {port}))
        (def written (tcp-write-via-raw c "Привіт €😀"))
        (tcp-close c)
        written
        "#
    );
    let result = eval_program(&source, &mut session).unwrap();
    assert_eq!(result.value, Value::String("Привіт €😀".into()));
    assert_eq!(server.join().unwrap(), "Привіт €😀".as_bytes());
}
