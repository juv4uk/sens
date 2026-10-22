//! Focused M0.6 safety witness: two real proposers race the same task in a
//! three-node mesh. At most one ownership commit may succeed, and the mesh
//! must converge on that one holder. This is deliberately separate from the
//! sequential duplicate-claim assertion in `integration.rs`.
//!
//! This witness originally falsified M0.6 on exact-head CI
//! 0438477ea2d5fffbd68f351cc93cd1b3e4be80aa, where both proposers committed
//! `RACE-0` at generation 1 with 2/3 votes. It is now an ordinary regression
//! gate for #35 and must never be weakened to eventual last-writer convergence.

use std::fs;
use std::io::{BufRead, BufReader, Write};
use std::net::{TcpListener, TcpStream};
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::{Arc, Barrier};
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

struct Node {
    child: Child,
    log: PathBuf,
}

impl Drop for Node {
    fn drop(&mut self) {
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}

fn test_root() -> PathBuf {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("clock should be after Unix epoch")
        .as_nanos();
    std::env::temp_dir().join(format!("swarm-claim-race-{}-{nonce}", std::process::id()))
}

fn reserve_ports(count: usize) -> Vec<u16> {
    let listeners: Vec<TcpListener> = (0..count)
        .map(|_| TcpListener::bind(("127.0.0.1", 0)).expect("ephemeral port reservation"))
        .collect();
    let ports = listeners
        .iter()
        .map(|listener| listener.local_addr().unwrap().port())
        .collect();
    drop(listeners);
    ports
}

fn spawn(port: u16, node_id: &str, data_dir: &Path, connect: Option<u16>) -> Node {
    fs::create_dir_all(data_dir).unwrap();
    let log = data_dir.join("process.log");
    let log_file = fs::File::create(&log).unwrap();
    let mut command = Command::new(env!("CARGO_BIN_EXE_swarm-node"));
    command
        .arg("--port")
        .arg(port.to_string())
        .arg("--node-id")
        .arg(node_id)
        .arg("--project")
        .arg("claim-race")
        .arg("--data-dir")
        .arg(data_dir)
        .arg("--no-auto-sync")
        .stdout(Stdio::from(log_file.try_clone().unwrap()))
        .stderr(Stdio::from(log_file));
    if let Some(peer) = connect {
        command.arg("--connect").arg(format!("127.0.0.1:{peer}"));
    }
    let child = command.spawn().expect("spawn swarm-node");
    let node = Node { child, log };
    wait_for_start(port, data_dir, &node.log);
    node
}

fn wait_for_start(port: u16, data_dir: &Path, log: &Path) {
    let deadline = Instant::now() + Duration::from_secs(3);
    while Instant::now() < deadline {
        if data_dir.join("node.lisp").is_file() && TcpStream::connect(("127.0.0.1", port)).is_ok() {
            return;
        }
        std::thread::sleep(Duration::from_millis(20));
    }
    let diagnostics = fs::read_to_string(log).unwrap_or_default();
    panic!("node {port} did not start; process log:\n{diagnostics}");
}

fn request(port: u16, message: &str) -> String {
    let mut stream = TcpStream::connect(("127.0.0.1", port)).unwrap();
    stream
        .set_read_timeout(Some(Duration::from_secs(3)))
        .unwrap();
    writeln!(stream, "{message}").unwrap();
    let mut line = String::new();
    BufReader::new(stream).read_line(&mut line).unwrap();
    line.trim().to_string()
}

fn eventually(
    port: u16,
    message: &str,
    timeout: Duration,
    predicate: impl Fn(&str) -> bool,
) -> String {
    let deadline = Instant::now() + timeout;
    let mut last = String::new();
    while Instant::now() < deadline {
        last = request(port, message);
        if predicate(&last) {
            return last;
        }
        std::thread::sleep(Duration::from_millis(40));
    }
    last
}

#[test]
fn simultaneous_claims_commit_exactly_one_owner_and_converge() {
    let root = test_root();
    let ports = reserve_ports(3);
    let (port_a, port_b, port_c) = (ports[0], ports[1], ports[2]);

    let _a = spawn(port_a, "race-a", &root.join("a"), None);
    let _b = spawn(port_b, "race-b", &root.join("b"), Some(port_a));
    let _c = spawn(port_c, "race-c", &root.join("c"), Some(port_a));

    for (port, peer_1, peer_2) in [
        (port_a, "race-b", "race-c"),
        (port_b, "race-a", "race-c"),
        (port_c, "race-a", "race-b"),
    ] {
        let presence = eventually(port, "(presence)", Duration::from_secs(3), |response| {
            response.contains(peer_1) && response.contains(peer_2)
        });
        assert!(
            presence.contains(peer_1) && presence.contains(peer_2),
            "mesh did not converge before race on port {port}: {presence}"
        );
    }

    // Repeat with distinct task ids so prior voting promises cannot affect a
    // later trial. The barrier releases both client requests together; the
    // protocol itself decides which proposal gets the shared majority vote.
    for trial in 0..3 {
        let task = format!("RACE-{trial}");
        let barrier = Arc::new(Barrier::new(3));

        let a_barrier = Arc::clone(&barrier);
        let a_task = task.clone();
        let a = std::thread::spawn(move || {
            a_barrier.wait();
            request(port_a, &format!("(claim-task (task {a_task}))"))
        });

        let b_barrier = Arc::clone(&barrier);
        let b_task = task.clone();
        let b = std::thread::spawn(move || {
            b_barrier.wait();
            request(port_b, &format!("(claim-task (task {b_task}))"))
        });

        barrier.wait();
        let response_a = a.join().expect("claim thread A");
        let response_b = b.join().expect("claim thread B");
        let success_count =
            usize::from(response_a.starts_with("(ok")) + usize::from(response_b.starts_with("(ok"));

        assert_eq!(
            success_count, 1,
            "simultaneous proposals must produce exactly one commit, never split-brain or zero durable owner; A={response_a}; B={response_b}"
        );

        let expected_holder = if response_a.starts_with("(ok") {
            "race-a"
        } else {
            "race-b"
        };
        let state = eventually(
            port_c,
            "(list-task-state)",
            Duration::from_secs(3),
            |response| response.contains(&task) && response.contains(expected_holder),
        );
        assert!(
            state.contains(&task) && state.contains(expected_holder),
            "third node did not converge on the sole winner {expected_holder}: {state}"
        );
        let other = if expected_holder == "race-a" {
            "race-b"
        } else {
            "race-a"
        };
        let task_fragment = state
            .split(&task)
            .nth(1)
            .unwrap_or("")
            .split("(task ")
            .next()
            .unwrap_or("");
        assert!(
            !task_fragment.contains(other),
            "same task appears to expose both owners after convergence: {state}"
        );
    }

    let _ = fs::remove_dir_all(root);
}
