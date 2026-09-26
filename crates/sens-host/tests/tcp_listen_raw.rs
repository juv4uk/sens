use sens::{eval_program, load_core_library, Session};
use sens_host::install;
use std::net::TcpStream;
use std::thread;
use std::time::Duration;

#[test]
fn tcp_listen_raw_binds_the_explicit_address() {
    install();
    let port = std::net::TcpListener::bind("127.0.0.1:0")
        .unwrap()
        .local_addr()
        .unwrap()
        .port();

    let server = thread::spawn(move || {
        let mut session = Session::default();
        load_core_library(&mut session).unwrap();
        let source = format!(
            r#"
            (def listener (tcp-listen-raw "127.0.0.1" {port}))
            (def connection (tcp-accept listener))
            (tcp-close connection)
            "#
        );
        eval_program(&source, &mut session).unwrap();
    });

    let mut connected = None;
    for _ in 0..20 {
        match TcpStream::connect(("127.0.0.1", port)) {
            Ok(stream) => {
                connected = Some(stream);
                break;
            }
            Err(_) => thread::sleep(Duration::from_millis(50)),
        }
    }
    drop(connected.expect("tcp-listen-raw should bind the requested loopback address"));
    server.join().unwrap();
}
