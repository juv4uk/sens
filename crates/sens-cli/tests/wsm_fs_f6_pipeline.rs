use std::io::Write;
use std::process::{Command, Stdio};

#[test]
fn producer_records_are_reconstructed_by_the_physical_f6_consumer() {
    let produced = Command::new(env!("CARGO_BIN_EXE_wsm-fs-record-producer"))
        .output()
        .expect("start F6 producer");
    assert!(
        produced.status.success(),
        "producer failed: {}",
        String::from_utf8_lossy(&produced.stderr)
    );
    assert_eq!(
        produced
            .stdout
            .iter()
            .filter(|&&byte| byte == b'\n')
            .count(),
        2,
        "producer must emit two records"
    );

    let mut consumer = Command::new(env!("CARGO_BIN_EXE_wsm-fs-record-consumer"))
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("start F6 consumer");
    consumer
        .stdin
        .take()
        .expect("consumer stdin")
        .write_all(&produced.stdout)
        .expect("send producer records");
    let consumed = consumer.wait_with_output().expect("wait for F6 consumer");
    assert!(
        consumed.status.success(),
        "consumer failed: {}",
        String::from_utf8_lossy(&consumed.stderr)
    );
    assert!(String::from_utf8_lossy(&consumed.stdout).contains("f6-semantic-consumer-ok records=2"));
}

#[test]
fn physical_f6_consumer_rejects_malformed_record_envelopes() {
    let mut consumer = Command::new(env!("CARGO_BIN_EXE_wsm-fs-record-consumer"))
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("start F6 consumer");
    consumer
        .stdin
        .take()
        .expect("consumer stdin")
        .write_all(b"()\n()\n")
        .expect("send malformed records");
    let rejected = consumer.wait_with_output().expect("wait for F6 consumer");
    assert!(
        !rejected.status.success(),
        "malformed envelopes were accepted"
    );
    assert!(
        String::from_utf8_lossy(&rejected.stderr).contains("root reconstruction rejected"),
        "unexpected rejection: {}",
        String::from_utf8_lossy(&rejected.stderr)
    );
}
