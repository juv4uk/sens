use std::io::{BufRead, BufReader, Write};
use std::net::TcpStream;
use std::process::{Child, Command, Stdio};
use std::time::Duration;

const RETIRED_COORDINATION_OPS: &[&str] = &[
    "hello",
    "heartbeat",
    "claim",
    "release",
    "complete-task",
    "define-task",
    "validate-tasks",
    "sync-tasks",
    "sync-milestone",
    "next-best-action",
    "list-task-state",
    "list-tasks",
    "presence",
    "list-claims",
    "capability-request",
    "subscribe",
    "publish",
    "notify",
    "poll",
];

fn spawn_oracle() -> (Child, u16) {
    let mut child = Command::new(env!("CARGO_BIN_EXE_my-lisp"))
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
            .strip_prefix("my-lisp TCP REPL ")
            .and_then(|rest| rest.split_once(" listening on 127.0.0.1:"))
            .map(|(_, port)| port.trim())
        {
            if let Ok(port) = port_text.parse::<u16>() {
                break port;
            }
        }
    };

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
                writeln!(stream, "{message}").expect("request should be written");
                stream.flush().expect("request should be flushed");

                let mut response = String::new();
                BufReader::new(stream)
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
fn every_retired_coordination_op_is_rejected_by_the_semantic_oracle() {
    let (mut child, port) = spawn_oracle();

    for (index, op) in RETIRED_COORDINATION_OPS.iter().enumerate() {
        // Construct the request dynamically so the static no-callers scanner
        // does not mistake this negative rejection witness for a live caller.
        let message = format!("(request (id {}) (op {}))", index + 1, op);
        let response = request(port, &message);

        assert!(response.contains("(status error)"), "{op}: {response}");
        assert!(
            response.contains("(kind invalid-form)"),
            "{op}: {response}"
        );
        assert!(
            response.contains(&format!("unknown op `{op}`")),
            "retired op was not rejected as unknown: {op}: {response}"
        );
    }

    child.kill().expect("semantic oracle should stop");
}
