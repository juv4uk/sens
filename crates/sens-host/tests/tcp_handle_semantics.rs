use sens::{eval_program, load_tcp_library, Session};
use sens_host::install;
use std::any::Any;
use std::cell::RefCell;
use std::io::{Read, Write};
use std::net::{Shutdown, TcpListener, TcpStream};
use std::rc::Rc;
use std::thread;

fn tcp_session() -> Session {
    install();
    let mut session = Session::default();
    sens::load_core_library(&mut session).unwrap();
    load_tcp_library(&mut session).unwrap();
    session
}

#[test]
fn listener_handles_expose_only_class_and_identity() {
    // Port 0 asks the OS for a fresh ephemeral listener each time, avoiding
    // the race inherent in probing a free port and then reopening it later.
    let source = r#"
        (def a (tcp-listen-on "127.0.0.1" 0))
        (def b (tcp-listen-on "127.0.0.1" 0))
        (list (eq? a a) (eq? a b) a b)
    "#;

    let value = eval_program(source, &mut tcp_session())
        .expect("two listener handles should be ordinary opaque runtime values")
        .value;

    assert_eq!(
        value.to_string(),
        "((1) (0) <tcp-listener> <tcp-listener>)",
        "listener observables are pointer identity plus resource class, not std::net details"
    );
}

#[test]
fn connection_handle_keeps_identity_and_display_across_close() {
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let port = listener.local_addr().unwrap().port();
    let server = thread::spawn(move || {
        let (stream, _) = listener.accept().expect("client should connect");
        drop(stream);
    });

    let source = format!(
        r#"
        (def c (tcp-connect "127.0.0.1" {port}))
        (def same (eq? c c))
        (tcp-close c)
        (list same c)
        "#
    );
    let value = eval_program(&source, &mut tcp_session())
        .expect("connection identity remains meaningful after lifecycle operation")
        .value;

    assert_eq!(value.to_string(), "((1) <tcp-connection>)");
    server.join().expect("server thread should finish");
}

#[test]
fn rc_dyn_any_is_a_viable_opaque_tcp_payload_experiment() {
    // This is deliberately test-only. It falsifies the claim that concrete
    // std::net types must be visible to the core Value representation in order
    // to preserve the current host mechanism. The host can retain the exact
    // concrete payload behind Rc<dyn Any>, recover it locally, and keep Rc
    // identity unchanged.
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let port = listener.local_addr().unwrap().port();
    let listener_handle: Rc<dyn Any> = Rc::new(listener);
    let listener_alias = Rc::clone(&listener_handle);
    assert!(Rc::ptr_eq(&listener_handle, &listener_alias));

    let peer = thread::spawn(move || {
        let mut stream = TcpStream::connect(("127.0.0.1", port)).expect("peer connects");
        stream.write_all(b"x").expect("peer writes request byte");
        let mut reply = [0u8; 1];
        stream.read_exact(&mut reply).expect("peer reads reply byte");
        assert_eq!(reply, *b"y");
    });

    let listener = listener_handle
        .as_ref()
        .downcast_ref::<TcpListener>()
        .expect("host recovers listener payload");
    let (stream, _) = listener.accept().expect("opaque listener accepts");

    let connection_handle: Rc<dyn Any> = Rc::new(RefCell::new(stream));
    let connection_alias = Rc::clone(&connection_handle);
    assert!(Rc::ptr_eq(&connection_handle, &connection_alias));

    let connection = connection_handle
        .as_ref()
        .downcast_ref::<RefCell<TcpStream>>()
        .expect("host recovers connection payload");
    let mut request = [0u8; 1];
    connection
        .borrow_mut()
        .read_exact(&mut request)
        .expect("host reads through opaque payload");
    assert_eq!(request, *b"x");
    connection
        .borrow_mut()
        .write_all(b"y")
        .expect("host writes through opaque payload");
    connection
        .borrow()
        .shutdown(Shutdown::Both)
        .expect("host closes through opaque payload");

    peer.join().expect("peer thread finishes");
}
