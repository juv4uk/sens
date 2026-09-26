use std::io::{BufRead, BufReader, Write};
use std::net::TcpStream;
use std::process::{Child, Command, Stdio};
use std::time::Duration;

fn spawn_oracle() -> (Child, u16) {
    let mut child = Command::new(env!("CARGO_BIN_EXE_sens"))
        .args(["--tcp=0", "--protocol=sexpr"])
        .stderr(Stdio::piped())
        .stdout(Stdio::null())
        .spawn()
        .expect("semantic oracle binary should start");

    let stderr = child.stderr.take().expect("stderr should be piped");
    let mut reader = BufReader::new(stderr);
    let deadline = std::time::Instant::now() + Duration::from_secs(5);
    let mut diagnostics = Vec::new();

    let port = loop {
        assert!(
            std::time::Instant::now() < deadline,
            "semantic oracle did not announce a listening port within 5s; stderr={diagnostics:?}"
        );

        let mut line = String::new();
        let bytes = reader
            .read_line(&mut line)
            .expect("oracle stderr should be readable");
        if bytes == 0 {
            panic!("semantic oracle exited before announcing a listening port; stderr={diagnostics:?}");
        }

        diagnostics.push(line.trim_end().to_string());
        if let Some(port_text) = line
            .strip_prefix("sens TCP REPL ")
            .and_then(|rest| rest.split_once(" listening on 127.0.0.1:"))
            .map(|(_, port)| port.trim())
        {
            if let Ok(port) = port_text.parse::<u16>() {
                break port;
            }
        }
    };

    // The oracle writes request diagnostics to stderr. Keep draining the pipe
    // after reading the banner so a full pipe cannot block the child.
    std::thread::spawn(move || {
        let mut reader = reader;
        let _ = std::io::copy(&mut reader, &mut std::io::sink());
    });

    (child, port)
}

fn request(port: u16, message: &str) -> String {
    let mut last_error = None;
    for _ in 0..40 {
        match TcpStream::connect(("127.0.0.1", port)) {
            Ok(mut stream) => {
                stream
                    .set_read_timeout(Some(Duration::from_secs(3)))
                    .expect("read timeout should be set");
                stream
                    .write_all(format!("{message}\n").as_bytes())
                    .expect("request should be written");
                stream.flush().expect("request should be flushed");

                let mut response = String::new();
                let mut reader = BufReader::new(stream);
                reader
                    .read_line(&mut response)
                    .expect("one response frame should be readable");
                if !response.trim().is_empty() {
                    return response;
                }
            }
            Err(error) => last_error = Some(error),
        }
        std::thread::sleep(Duration::from_millis(50));
    }
    panic!("semantic oracle did not answer: {last_error:?}");
}

#[test]
fn semantic_oracle_surface_survives_coordination_removal() {
    let (mut child, port) = spawn_oracle();

    let contract = request(port, "(request (id 1) (op contract-version))");
    assert!(contract.contains("(status ok)"), "{contract}");
    assert!(contract.contains("(contract-version"), "{contract}");

    let eval = request(
        port,
        r#"(request (id 2) (op eval) (source "(+ 1 2)"))"#,
    );
    assert!(eval.contains("(status ok)"), "{eval}");
    assert!(eval.contains("(value 3)"), "{eval}");

    let parse = request(
        port,
        r#"(request (id 3) (op parse) (source "(+ 1 2)"))"#,
    );
    assert!(parse.contains("(status ok)"), "{parse}");
    assert!(parse.contains("(value (+ 1 2))"), "{parse}");

    let diagnose = request(
        port,
        r#"(request (id 4) (op diagnose) (source "(car 1)"))"#,
    );
    assert!(diagnose.contains("(status error)"), "{diagnose}");
    assert!(diagnose.contains("(kind type-error)"), "{diagnose}");

    // Each request is a new TCP connection. A definition made in one semantic
    // session must remain invisible to the next connection after C5 cleanup.
    let _ = request(
        port,
        r#"(request (id 5) (op eval) (source "(def c5-private 999)"))"#,
    );
    let isolated = request(
        port,
        r#"(request (id 6) (op eval) (source "c5-private"))"#,
    );
    assert!(isolated.contains("(status error)"), "{isolated}");
    assert!(isolated.contains("unknown-symbol"), "{isolated}");

    child.kill().expect("semantic oracle should stop");
}
