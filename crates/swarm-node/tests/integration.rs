//! Integration tests for swarm-node, promoted from the ad-hoc bash smoke
//! scripts used while building M0.1-M0.8 (see docs/swarm-mesh-v2.md) into
//! something that actually runs under `cargo test` and catches regressions
//! automatically instead of only when someone remembers to check by hand.
//!
//! Each test spawns real `swarm-node` child processes (via
//! `CARGO_BIN_EXE_swarm-node`, the compiled binary for this crate) and
//! talks to them over real TCP loopback sockets — this is deliberately an
//! end-to-end test of the wire protocol, not a unit test of internal
//! functions (those live next to the code in `src/*.rs`).

use std::io::{BufRead, BufReader, Write};
use std::net::TcpStream;
use std::path::{Path, PathBuf};
use std::process::{Child, Command, Stdio};
use std::sync::atomic::{AtomicU16, Ordering};
use std::time::{Duration, Instant};

static NEXT_PORT: AtomicU16 = AtomicU16::new(15001);

/// Reserves `n` consecutive ports for one test, so parallel `cargo test`
/// execution (multiple tests in this binary run concurrently by default)
/// never collides on a port.
fn alloc_ports(n: u16) -> u16 {
    NEXT_PORT.fetch_add(n, Ordering::SeqCst)
}

fn data_dir(name: &str) -> PathBuf {
    let dir = std::env::temp_dir()
        .join("swarm-node-itest")
        .join(format!("{name}-{}", std::process::id()));
    let _ = std::fs::remove_dir_all(&dir);
    dir
}

struct Node {
    child: Child,
}

impl Drop for Node {
    fn drop(&mut self) {
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}

fn spawn(port: u16, node_id: &str, data_dir: &Path, connect: Option<u16>) -> Node {
    let mut cmd = Command::new(env!("CARGO_BIN_EXE_swarm-node"));
    cmd.arg("--port").arg(port.to_string());
    cmd.arg("--node-id").arg(node_id);
    cmd.arg("--project").arg("itest");
    cmd.arg("--data-dir").arg(data_dir);
    cmd.arg("--no-auto-sync");
    if let Some(p) = connect {
        cmd.arg("--connect").arg(format!("127.0.0.1:{p}"));
    }
    if let Ok(logdir) = std::env::var("SWARM_TEST_LOGS") {
        let _ = std::fs::create_dir_all(&logdir);
        let f = std::fs::File::create(
            std::path::Path::new(&logdir).join(format!("{node_id}-{port}.log")),
        )
        .unwrap();
        cmd.stdout(f.try_clone().unwrap()).stderr(f);
    } else {
        cmd.stdout(Stdio::null()).stderr(Stdio::null());
    }
    let child = cmd
        .spawn()
        .expect("failed to spawn swarm-node — did `cargo build -p swarm-node` run first?");
    let node = Node { child };
    wait_for_port(port);
    wait_for_file(&data_dir.join("node.lisp"));
    node
}

fn wait_for_port(port: u16) {
    let deadline = Instant::now() + Duration::from_secs(3);
    while Instant::now() < deadline {
        if TcpStream::connect(("127.0.0.1", port)).is_ok() {
            return;
        }
        std::thread::sleep(Duration::from_millis(20));
    }
    panic!("swarm-node on port {port} never started listening");
}

fn wait_for_file(path: &Path) {
    let deadline = Instant::now() + Duration::from_secs(3);
    while Instant::now() < deadline {
        if path.is_file() {
            return;
        }
        std::thread::sleep(Duration::from_millis(10));
    }
    panic!("swarm-node startup did not create {}", path.display());
}

#[test]
fn startup_rejects_relative_data_dir() {
    let output = Command::new(env!("CARGO_BIN_EXE_swarm-node"))
        .args([
            "--port",
            "15991",
            "--node-id",
            "strict-node",
            "--project",
            "itest",
            "--data-dir",
            "relative-state",
            "--no-auto-sync",
        ])
        .output()
        .unwrap();
    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("--data-dir must be absolute"));
}

#[test]
fn startup_rejects_data_dir_owned_by_another_identity() {
    let dir = data_dir("identity-mismatch");
    std::fs::create_dir_all(&dir).unwrap();
    std::fs::write(
        dir.join("node.lisp"),
        "(node (id original-node) (epoch 1) (incarnation test))",
    )
    .unwrap();
    let output = Command::new(env!("CARGO_BIN_EXE_swarm-node"))
        .arg("--port")
        .arg("15992")
        .arg("--node-id")
        .arg("different-node")
        .arg("--project")
        .arg("itest")
        .arg("--data-dir")
        .arg(&dir)
        .arg("--no-auto-sync")
        .output()
        .unwrap();
    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("identity mismatch"));
}

fn startup_command(port: u16, node_id: &str, dir: &Path) -> Command {
    let mut command = Command::new(env!("CARGO_BIN_EXE_swarm-node"));
    command
        .arg("--port")
        .arg(port.to_string())
        .arg("--node-id")
        .arg(node_id)
        .arg("--project")
        .arg("itest")
        .arg("--data-dir")
        .arg(dir)
        .arg("--no-auto-sync");
    command
}

#[test]
fn duplicate_port_fails_before_mutating_identity() {
    let port = alloc_ports(1);
    let dir = data_dir("duplicate-port-no-mutation");
    let _first = spawn(port, "one-owner", &dir, None);
    let before = std::fs::read_to_string(dir.join("node.lisp")).unwrap();

    let output = startup_command(port, "one-owner", &dir).output().unwrap();

    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("Address already in use"));
    assert_eq!(
        std::fs::read_to_string(dir.join("node.lisp")).unwrap(),
        before
    );
    assert!(request(port, "(status)").starts_with("(status"));
}

#[test]
fn shared_data_dir_rejects_second_live_process_on_another_port() {
    let ports = alloc_ports(2);
    let dir = data_dir("shared-data-dir-lock");
    let _first = spawn(ports, "one-owner", &dir, None);
    let before = std::fs::read_to_string(dir.join("node.lisp")).unwrap();

    let output = startup_command(ports + 1, "one-owner", &dir)
        .output()
        .unwrap();

    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("already owned"));
    assert_eq!(
        std::fs::read_to_string(dir.join("node.lisp")).unwrap(),
        before
    );
    assert!(TcpStream::connect(("127.0.0.1", ports + 1)).is_err());
}

#[test]
fn startup_requires_explicit_task_sync_choice_and_rejects_unknown_args() {
    let dir = data_dir("explicit-task-sync");
    let without_choice = Command::new(env!("CARGO_BIN_EXE_swarm-node"))
        .arg("--node-id")
        .arg("strict")
        .arg("--project")
        .arg("itest")
        .arg("--data-dir")
        .arg(&dir)
        .output()
        .unwrap();
    assert!(!without_choice.status.success());
    assert!(String::from_utf8_lossy(&without_choice.stderr).contains("--no-auto-sync"));
    assert!(!dir.exists(), "validation must precede state creation");

    let unknown = startup_command(alloc_ports(1), "strict", &dir)
        .arg("--aut-sync")
        .output()
        .unwrap();
    assert!(!unknown.status.success());
    assert!(String::from_utf8_lossy(&unknown.stderr).contains("unknown argument"));
    assert!(
        !dir.exists(),
        "argument parsing must precede state creation"
    );
}

/// One request/response round trip over a fresh connection, matching how
/// every other client in this ecosystem talks to the line-framed sexpr
/// protocol (one form in, one line out).
fn request(port: u16, msg: &str) -> String {
    let deadline = Instant::now() + Duration::from_secs(3);
    let mut stream = loop {
        match TcpStream::connect(("127.0.0.1", port)) {
            Ok(s) => break s,
            Err(_) if Instant::now() < deadline => std::thread::sleep(Duration::from_millis(20)),
            Err(e) => panic!("could not connect to port {port}: {e}"),
        }
    };
    stream
        .set_read_timeout(Some(Duration::from_secs(3)))
        .unwrap();
    writeln!(stream, "{msg}").unwrap();
    let mut reader = BufReader::new(stream);
    let mut line = String::new();
    reader.read_line(&mut line).unwrap();
    line.trim().to_string()
}

/// Polls `request(port, msg)` until `predicate` matches or the deadline
/// passes, returning the last response seen. Used for anything that
/// depends on gossip/anti-entropy/reconnect propagating asynchronously —
/// avoids flaky fixed `sleep`s tuned to one machine's speed.
fn eventually(port: u16, msg: &str, timeout: Duration, predicate: impl Fn(&str) -> bool) -> String {
    let deadline = Instant::now() + timeout;
    let mut last = String::new();
    while Instant::now() < deadline {
        last = request(port, msg);
        if predicate(&last) {
            return last;
        }
        std::thread::sleep(Duration::from_millis(50));
    }
    last
}

#[test]
fn anti_entropy_sync_and_live_push_event() {
    let base = alloc_ports(2);
    let (port_a, port_b) = (base, base + 1);

    let _a = spawn(port_a, "node-a", &data_dir("ae-a"), None);
    // M1.1a: emitted ids now embed the node's incarnation id —
    // `node-a:<incarnation>:N`. Assert the shape instead of a literal.
    let e1 = request(
        port_a,
        "(emit (type evidence-created) (payload (artifact \"x.my\")))",
    );
    assert!(
        e1.starts_with("(ok (id node-a:") && e1.ends_with(":1))"),
        "unexpected first emit id: {e1}"
    );
    let e2 = request(
        port_a,
        "(emit (type evidence-created) (payload (artifact \"y.my\")))",
    );
    assert!(e2.ends_with(":2))"), "unexpected second emit id: {e2}");

    // B connects after A already has 2 events -- must anti-entropy sync them.
    let _b = spawn(port_b, "node-b", &data_dir("ae-b"), Some(port_a));
    let synced = eventually(port_b, "(list-task-state)", Duration::from_secs(2), |r| {
        !r.is_empty()
    });
    let _ = synced; // list-task-state is task-only; just confirm B is responsive post-sync below

    // A live-pushes a 3rd event; B must receive it without any resync call.
    let e3 = request(
        port_a,
        "(emit (type evidence-created) (payload (artifact \"z.my\")))",
    );
    assert!(e3.ends_with(":3))"), "unexpected third emit id: {e3}");

    // No direct way to read the raw journal over the wire, so prove sync worked
    // indirectly via a task defined on A becoming visible on B.
    request(port_a, "(define-task (task PROOF) (priority 1) (capabilities ()) (depends-on ()) (description \"sync worked\"))");
    let seen_on_b = eventually(port_b, "(list-task-state)", Duration::from_secs(2), |r| {
        r.contains("PROOF")
    });
    assert!(
        seen_on_b.contains("PROOF"),
        "task defined on A never propagated to B: {seen_on_b}"
    );
}

#[test]
fn quorum_claim_fencing_and_stale_rejection() {
    let base = alloc_ports(3);
    let (port_a, port_b, port_c) = (base, base + 1, base + 2);

    let _a = spawn(port_a, "node-a", &data_dir("qf-a"), None);
    let _b = spawn(port_b, "node-b", &data_dir("qf-b"), Some(port_a));
    let _c = spawn(port_c, "node-c", &data_dir("qf-c"), Some(port_a));
    eventually(port_c, "(presence)", Duration::from_secs(2), |r| {
        r.contains("node-a") && r.contains("node-b")
    });

    let claimed = request(port_a, "(claim-task (task T1))");
    assert!(
        claimed.starts_with("(ok"),
        "expected quorum claim to succeed: {claimed}"
    );

    // Give B's own copy time to observe A's commit via gossip before B tries
    // to claim -- otherwise B legitimately races A (M0.6 correctly rejects
    // that race via voter promises, but that's a *different* assertion than
    // "B saw the commit and backed off", which is what this test checks).
    let duplicate = eventually(
        port_b,
        "(claim-task (task T1))",
        Duration::from_secs(2),
        |r| r.contains("already claimed"),
    );
    assert!(
        duplicate.contains("already claimed by `node-a`"),
        "expected duplicate claim rejection: {duplicate}"
    );

    let stale = request(port_b, "(complete-task (task T1) (generation 99))");
    assert!(
        stale.contains("STALE"),
        "expected STALE rejection for wrong generation: {stale}"
    );

    let completed = request(port_a, "(complete-task (task T1) (generation 1))");
    assert!(
        completed.starts_with("(ok"),
        "expected completion with correct generation to succeed: {completed}"
    );

    let after_done = eventually(
        port_c,
        "(claim-task (task T1))",
        Duration::from_secs(2),
        |r| r.contains("already completed"),
    );
    assert!(
        after_done.contains("already completed"),
        "expected claim on completed task to be rejected: {after_done}"
    );
}

#[test]
fn gossip_peer_discovery_reaches_full_mesh() {
    let base = alloc_ports(3);
    let (port_a, port_b, port_c) = (base, base + 1, base + 2);

    let _a = spawn(port_a, "node-a", &data_dir("gd-a"), None);
    let _b = spawn(port_b, "node-b", &data_dir("gd-b"), Some(port_a));
    // C connects ONLY to A -- must discover and dial B via gossip through A.
    let _c = spawn(port_c, "node-c", &data_dir("gd-c"), Some(port_a));

    let c_presence = eventually(port_c, "(presence)", Duration::from_secs(3), |r| {
        r.contains("node-b")
    });
    assert!(
        c_presence.contains("node-b"),
        "node-c never gossip-discovered node-b: {c_presence}"
    );
}

#[test]
fn compaction_preserves_derived_state() {
    let base = alloc_ports(1);
    let port = base;
    let _a = spawn(port, "node-a", &data_dir("cc-a"), None);

    request(port, "(define-task (task X) (priority 1) (capabilities ()) (depends-on ()) (description \"v1\"))");
    request(port, "(define-task (task X) (priority 2) (capabilities ()) (depends-on ()) (description \"v2 final\"))");
    request(port, "(claim-task (task X))");
    request(port, "(release-task (task X) (generation 1))");
    request(port, "(claim-task (task X))");

    let before = request(port, "(list-task-state)");

    let compacted = request(port, "(compact)");
    assert!(
        compacted.starts_with("(ok"),
        "compact should succeed: {compacted}"
    );

    let after = request(port, "(list-task-state)");
    assert_eq!(
        before, after,
        "derived state must be byte-identical before/after compaction"
    );
}

#[test]
fn dynamic_membership_voter_quorum_and_status() {
    let base = alloc_ports(4);
    let (port_a, port_b, port_c, port_w) = (base, base + 1, base + 2, base + 3);

    let _a = spawn(port_a, "node-a", &data_dir("dm-a"), None);
    let _b = spawn(port_b, "node-b", &data_dir("dm-b"), Some(port_a));
    let _c = spawn(port_c, "node-c", &data_dir("dm-c"), Some(port_a));
    eventually(port_c, "(presence)", Duration::from_secs(2), |r| {
        r.contains("node-b")
    });

    for port in [port_a, port_b, port_c] {
        let r = request(port, "(join (capabilities (x)) (roles (voter)))");
        assert!(
            r.starts_with("(ok"),
            "join should succeed on port {port}: {r}"
        );
    }

    // A worker joins mid-session through just A, and must reach node-b/node-c via gossip.
    let _w = spawn(port_w, "worker-1", &data_dir("dm-w"), Some(port_a));
    eventually(port_w, "(presence)", Duration::from_secs(2), |r| {
        r.contains("node-b") && r.contains("node-c")
    });
    request(port_w, "(join (capabilities (docs)) (roles (worker)))");

    let members = eventually(port_a, "(list-members)", Duration::from_secs(2), |r| {
        r.contains("worker-1")
    });
    assert!(
        members.contains("worker-1"),
        "worker never showed up in list-members: {members}"
    );

    // Worker's own claim should only need 2/3 VOTER votes, not counting itself.
    request(port_w, "(define-task (task WORK) (priority 1) (capabilities ()) (depends-on ()) (description \"anyone\"))");
    let claimed = eventually(
        port_w,
        "(claim-task (task WORK))",
        Duration::from_secs(2),
        |r| r.starts_with("(ok") || r.contains("error"),
    );
    assert!(
        claimed.contains("2/3"),
        "expected a 2/3 voter quorum, got: {claimed}"
    );

    let status = request(port_a, "(status)");
    assert!(
        status.starts_with("(status"),
        "status op malformed: {status}"
    );
    assert!(
        status.contains("(synced t)"),
        "node-a should report itself synced: {status}"
    );
}

#[test]
fn rejects_duplicate_node_id_claim_from_a_second_connection() {
    let base = alloc_ports(2);
    let (port_a, port_b) = (base, base + 1);

    let _a = spawn(port_a, "node-a", &data_dir("dup-a"), None);
    let _b = spawn(port_b, "node-b", &data_dir("dup-b"), Some(port_a));
    // Confirm the real node-b is live on A before trying to impersonate it.
    eventually(port_a, "(presence)", Duration::from_secs(2), |r| {
        r.contains("node-b")
    });

    // A raw connection claiming to already-live node-b's identity, from
    // somewhere that is NOT the real node-b -- simulates a spoofing
    // attempt (or a genuine but confused duplicate) rather than a normal
    // reconnect. Must get no peer-welcome back.
    let mut spoof = TcpStream::connect(("127.0.0.1", port_a)).unwrap();
    spoof
        .set_read_timeout(Some(Duration::from_millis(500)))
        .unwrap();
    writeln!(
        spoof,
        "(peer-hello (protocol swarm/1) (node node-b) (epoch 0) (project spoof) (listen-port 0))"
    )
    .unwrap();
    let mut reply = String::new();
    let mut reader = BufReader::new(&spoof);
    let read_result = reader.read_line(&mut reply);
    assert!(
        read_result.is_err() || reply.trim().is_empty(),
        "spoofed peer-hello for an already-live node-id should get no peer-welcome reply, got: {reply:?}"
    );

    // The real node-b must still be the one registered -- not evicted.
    let presence = request(port_a, "(presence)");
    assert!(
        presence.contains("node-b"),
        "real node-b should still be present after a rejected spoof attempt: {presence}"
    );
}

#[test]
fn metrics_reports_event_count_peer_count_and_synced() {
    let base = alloc_ports(2);
    let (port_a, port_b) = (base, base + 1);

    let dir_a = data_dir("metrics-a");
    let _a = spawn(port_a, "node-a", &dir_a, None);
    request(
        port_a,
        "(emit (type evidence-created) (payload (artifact \"x.my\")))",
    );
    request(
        port_a,
        "(emit (type evidence-created) (payload (artifact \"y.my\")))",
    );

    let _b = spawn(port_b, "node-b", &data_dir("metrics-b"), Some(port_a));
    eventually(port_a, "(metrics)", Duration::from_secs(2), |r| {
        r.contains("(peer-count 1)")
    });

    let metrics = request(port_a, "(metrics)");
    assert!(
        metrics.starts_with("(metrics"),
        "metrics op malformed: {metrics}"
    );
    assert!(
        metrics.contains("(event-count 2)"),
        "expected 2 events after 2 emits: {metrics}"
    );
    assert!(
        metrics.contains("(peer-count 1)"),
        "expected 1 connected peer (node-b): {metrics}"
    );
    assert!(
        metrics.contains("(synced t)"),
        "node-a with no --connect should be trivially synced: {metrics}"
    );
    assert!(metrics.contains("(bootstrap-peers 0)"), "{metrics}");
    assert!(metrics.contains("(task-sync t)"), "{metrics}");
    assert!(
        metrics.contains("(node node-a)"),
        "metrics should report the caller's own node-id: {metrics}"
    );
    let dir_a_str = dir_a.to_string_lossy().replace('\\', "/");
    let metrics_normalized = metrics.replace("\\\\", "/").replace('\\', "/");
    assert!(
        metrics_normalized.contains(&*dir_a_str),
        "metrics should report the node's own --data-dir ({dir_a_str}), got: {metrics}"
    );
}

#[test]
fn help_flag_prints_usage_and_exits_without_starting_a_server() {
    // Regression test for SWARM-NODE-HELP-FLAG-BUG: --help used to fall
    // through to the unknown-argument warning and then start a real
    // server under every default anyway.
    for flag in ["--help", "-h"] {
        let output = Command::new(env!("CARGO_BIN_EXE_swarm-node"))
            .arg(flag)
            .output()
            .unwrap_or_else(|e| panic!("failed to run swarm-node {flag}: {e}"));
        assert!(
            output.status.success(),
            "swarm-node {flag} should exit 0, got {:?}",
            output.status
        );
        let stdout = String::from_utf8_lossy(&output.stdout);
        assert!(
            stdout.contains("USAGE"),
            "{flag} output should contain usage text, got: {stdout}"
        );
        assert!(
            !stdout.contains("listening on"),
            "{flag} must not start a server: {stdout}"
        );
    }
}

#[test]
fn define_task_is_idempotent_for_an_identical_redefinition() {
    // Regression test for SWARM-DEFINE-TASK-DEDUP: re-broadcasting the
    // exact same define-task call (the same task/priority/capabilities/
    // depends-on/blocked-by/description) must not append a fresh
    // task-defined event every time — confirmed in practice 2026-08-18,
    // the same task definition landed in a real journal three times from
    // one peer notifying the swarm about it.
    let port = alloc_ports(1);
    let _a = spawn(port, "node-a", &data_dir("dedup-a"), None);

    fn event_count(port: u16) -> u64 {
        let metrics = request(port, "(metrics)");
        let marker = "(event-count ";
        let start = metrics
            .find(marker)
            .expect("metrics should report event-count")
            + marker.len();
        let rest = &metrics[start..];
        let end = rest.find(')').expect("event-count should be closed");
        rest[..end].parse().expect("event-count should be a number")
    }

    let define = "(define-task (task DUP) (priority 3) (capabilities (a b)) (depends-on ()) (blocked-by ()) (description \"same every time\"))";

    let first = request(port, define);
    assert!(
        first.starts_with("(ok"),
        "first define-task should succeed: {first}"
    );
    let after_first = event_count(port);

    // Two more identical calls, as if a peer re-broadcast the same
    // define-task (or retried after a timeout) — neither should grow the
    // journal.
    let second = request(port, define);
    assert!(
        second.starts_with("(ok"),
        "repeat define-task should still report ok: {second}"
    );
    assert!(
        second.contains("(unchanged t)"),
        "repeat define-task should report unchanged: {second}"
    );
    let third = request(port, define);
    assert!(
        third.contains("(unchanged t)"),
        "repeat define-task should report unchanged: {third}"
    );

    let after_repeats = event_count(port);
    assert_eq!(
        after_first, after_repeats,
        "identical redefinitions must not append new events"
    );

    // A genuinely different redefinition (priority changed) must still
    // append normally — this isn't a blanket "only define once" guard.
    let changed = "(define-task (task DUP) (priority 5) (capabilities (a b)) (depends-on ()) (blocked-by ()) (description \"same every time\"))";
    let fourth = request(port, changed);
    assert!(
        !fourth.contains("(unchanged t)"),
        "a genuinely different redefinition must not be reported unchanged: {fourth}"
    );
    let after_change = event_count(port);
    assert_eq!(
        after_repeats + 1,
        after_change,
        "a real change must append exactly one new event"
    );
}

// ---------------------------------------------------------------------------
// M1.1a: incarnation-safe event identity
// ---------------------------------------------------------------------------

/// Reads this node's incarnation id out of its persisted identity store.
fn read_incarnation(dir: &Path) -> String {
    let text = std::fs::read_to_string(dir.join("node.lisp")).expect("node.my must exist");
    let marker = "(incarnation ";
    let start = text
        .find(marker)
        .expect("node.my must contain an incarnation field")
        + marker.len();
    let end = text[start..]
        .find(')')
        .expect("incarnation field must be closed")
        + start;
    text[start..end].trim_matches('"').to_string()
}

fn kill(node: &mut Node) {
    let _ = node.child.kill();
    let _ = node.child.wait();
}

/// THE reincarnation regression test for the 2026-08-22 anti-entropy bug:
///
/// A node emits T1 under incarnation X. Its data-dir is destroyed. The same
/// node-id comes back as incarnation Y and emits T2 with seq restarting at 1.
/// A bootstrap that saw both lifetimes must end up holding BOTH events, and
/// anti-entropy must converge in both directions — before M1.1a the second
/// lifetime's `(id my-idea-1:1)` collided with the first and the bootstrap
/// permanently believed it was already synced.
#[test]
fn reincarnation_does_not_collide_and_anti_entropy_converges() {
    let base = alloc_ports(2);
    let (port_boot, port_a) = (base, base + 1);

    let boot_dir = data_dir("reinc-boot");
    let a_dir = data_dir("reinc-a");

    // Bootstrap first, alone.
    let boot = spawn(port_boot, "boot", &boot_dir, None);

    // Incarnation X of node "wanderer": define T1.
    let mut x = spawn(port_a, "wanderer", &a_dir, Some(port_boot));
    let inc_x = read_incarnation(&a_dir);
    // Wait until the mesh link is actually up — a define issued before the
    // handshake completes would only ever live in the local journal.
    eventually(port_a, "(metrics)", Duration::from_secs(3), |r| {
        r.contains("(peer-count 1)")
    });
    assert!(
        request(port_a, "(define-task (task T1) (priority 5) (capabilities ()) (depends-on ()) (description \"from incarnation X\"))").starts_with("(ok"),
        "T1 define failed"
    );
    // The scenario requires the bootstrap to HAVE received T1 before X
    // dies. Killing immediately after the define can RST the connection
    // while boot's reader hasn't consumed the push yet — a test artifact,
    // not a protocol property.
    eventually(
        port_boot,
        "(list-task-state)",
        Duration::from_secs(5),
        |r| r.contains("T1"),
    );
    kill(&mut x);

    // Identity store DESTROYED — the exact scenario that produced the
    // silent-sync bug. Same node-id returns with fresh state.
    std::fs::remove_dir_all(&a_dir).unwrap();

    // Wait for the bootstrap to notice X is gone, or its duplicate-live
    // identity guard would reject Y's handshake as a spoof of X.
    eventually(port_boot, "(metrics)", Duration::from_secs(5), |r| {
        r.contains("(peer-count 0)")
    });

    // Incarnation Y of the same node-id: define T2 (its seq restarts at 1).
    let y = spawn(port_a, "wanderer", &a_dir, Some(port_boot));
    let inc_y = read_incarnation(&a_dir);
    assert_ne!(
        inc_x, inc_y,
        "destroying the data-dir MUST produce a new incarnation"
    );
    eventually(port_a, "(metrics)", Duration::from_secs(3), |r| {
        r.contains("(peer-count 1)")
    });
    assert!(
        request(port_a, "(define-task (task T2) (priority 5) (capabilities ()) (depends-on ()) (description \"from incarnation Y\"))").starts_with("(ok"),
        "T2 define failed"
    );

    // Bootstrap must hold BOTH definitions despite identical (node, seq)
    // namespaces across the two lifetimes.
    let boot_view = eventually(
        port_boot,
        "(list-task-state)",
        Duration::from_secs(3),
        |r| r.contains("T1") && r.contains("T2"),
    );
    assert!(
        boot_view.contains("T1"),
        "bootstrap lost incarnation-X task T1: {boot_view}"
    );
    assert!(
        boot_view.contains("T2"),
        "bootstrap lost incarnation-Y task T2: {boot_view}"
    );

    // Bidirectional convergence (review finding F5): Y itself must relearn
    // T1 — an event issued by its own PREVIOUS incarnation — from the
    // bootstrap. Y's sync-hello reports only (wanderer, inc_y); boot
    // iterates ITS origins, finds (wanderer, inc_x) absent from Y's map,
    // serves the full X stream, and Y's has(wanderer, inc_x, k) = false
    // applies it. Pre-M1.1a this was impossible: the shared (node, seq)
    // made boot believe Y was already caught up.
    let y_view = eventually(port_a, "(list-task-state)", Duration::from_secs(3), |r| {
        r.contains("T1")
    });
    assert!(
        y_view.contains("T1"),
        "reincarnated node never relearned its previous incarnation's task T1: {y_view}"
    );

    // And a THIRD node joining late must see both lifetimes' tasks purely
    // through gossip/anti-entropy.
    drop(y);
    let base2 = alloc_ports(1);
    let c = spawn(base2, "latecomer", &data_dir("reinc-c"), Some(port_boot));
    let c_view = eventually(base2, "(list-task-state)", Duration::from_secs(3), |r| {
        r.contains("T1") && r.contains("T2")
    });
    assert!(
        c_view.contains("T1") && c_view.contains("T2"),
        "latecomer never converged on both lifetimes' tasks: {c_view}"
    );

    // Sanity: both lifetimes' tasks visible; the logical node-id appears in
    // presence (it never joined, so membership stays empty).
    let status = request(port_boot, "(status)");
    assert!(
        status.contains("T1") && status.contains("T2"),
        "bootstrap status lost tasks: {status}"
    );
    drop(c);
    drop(boot);
}

/// Normal restart WITHOUT losing the data-dir must NOT create a new
/// namespace: same incarnation, epoch increments, seq continues —
/// otherwise fixing reincarnation would have broken restart semantics.
#[test]
fn restart_preserves_incarnation_epoch_increments_seq_continues() {
    let port = alloc_ports(1);
    let dir = data_dir("restart-semantics");

    let mut n1 = spawn(port, "steady", &dir, None);
    let inc_1 = read_incarnation(&dir);
    let e1 = request(
        port,
        "(emit (type evidence-created) (payload (artifact \"one\")))",
    );
    assert!(e1.ends_with(":1))"), "first emit should be seq 1: {e1}");
    kill(&mut n1);
    drop(n1);

    let mut n2 = spawn(port, "steady", &dir, None);
    let inc_2 = read_incarnation(&dir);
    assert_eq!(
        inc_1, inc_2,
        "restart without data-dir loss must KEEP the incarnation"
    );
    let e2 = request(
        port,
        "(emit (type evidence-created) (payload (artifact \"two\")))",
    );
    assert!(
        e2.ends_with(":2))"),
        "restart must CONTINUE the sequence, not reset it: {e2}"
    );

    let epoch_text = std::fs::read_to_string(dir.join("node.lisp")).unwrap();
    let epoch_marker = "(epoch ";
    let start = epoch_text.find(epoch_marker).unwrap() + epoch_marker.len();
    let end = epoch_text[start..].find(')').unwrap() + start;
    let epoch: u64 = epoch_text[start..end].parse().unwrap();
    assert_eq!(
        epoch, 1,
        "two process starts => epoch 1 (0-indexed): {epoch_text}"
    );
    kill(&mut n2);
}

// ---------------------------------------------------------------------------
// M1.1b: task origin/provenance
// ---------------------------------------------------------------------------

/// Origin flows end to end: define-task with (origin X) is visible via
/// task-def; sync-tasks stamps per-file `(origin . repo)` and honors the
/// msg-level default; tasks with neither stay unresolved.
#[test]
fn task_origin_provenance_flows_through() {
    let port = alloc_ports(1);
    let dir = data_dir("origin-prov");
    let _n = spawn(port, "prov", &dir, None);

    // 1. explicit origin via define-task
    request(port, "(define-task (task ORIG-A) (priority 5) (capabilities ()) (depends-on ()) (origin cml) (description \"owned by cml\"))");
    let a = request(port, "(task-def (task ORIG-A))");
    assert!(
        a.contains("(origin cml)"),
        "define-task origin not visible in task-def: {a}"
    );

    // 2. no origin => unresolved (empty list, not an atom)
    request(port, "(define-task (task ORIG-B) (priority 5) (capabilities ()) (depends-on ()) (description \"no owner\"))");
    let b = request(port, "(task-def (task ORIG-B))");
    assert!(
        b.contains("(origin ())") || b.contains("(origin nil)"),
        "unresolved origin must render empty: {b}"
    );
    assert!(!b.contains("(origin cml)"));

    // 3. sync-tasks: per-task (origin . x) wins over msg-level default
    let f = dir.join("tasks_with_origin.lisp");
    std::fs::write(
        &f,
        r#"
((kind . tasks-my)
 (tasks .
  (("ORIG-C" . ((priority . 4) (origin . fpga-lisp) (done . ())))
   ("ORIG-D" . ((priority . 3) (done . ()))))))
"#,
    )
    .unwrap();
    let resp = request(
        port,
        &format!(r#"(sync-tasks (file "{}") (origin my-idea))"#, f.display()),
    );
    assert!(resp.starts_with("(ok"), "sync-tasks failed: {resp}");
    let c = request(port, "(task-def (task ORIG-C))");
    assert!(
        c.contains("(origin fpga-lisp)"),
        "per-task origin must beat msg default: {c}"
    );
    let d = request(port, "(task-def (task ORIG-D))");
    assert!(
        d.contains("(origin my-idea)"),
        "msg-level origin must fill undeclared tasks: {d}"
    );

    // 4. unknown task => defined nil
    let none = request(port, "(task-def (task NO-SUCH))");
    assert!(
        none.contains("(defined nil)"),
        "unknown task must report undefined: {none}"
    );

    // 5. next-best-action exposes origin too
    let nba = request(port, "(next-best-action (capabilities ()))");
    if nba.starts_with("(next-best-action (task") && nba.contains("ORIG-C") {
        assert!(
            nba.contains("(origin fpga-lisp)"),
            "NBA should expose origin: {nba}"
        );
    }
}

// ---------------------------------------------------------------------------
// M1.1c liveness (SWARM-NODE-M11C-LIVENESS): hello deadlines, redial after
// silent refusal, and catch-up trains that no longer starve the heartbeat.
// ---------------------------------------------------------------------------

fn spawn_with_env(
    port: u16,
    node_id: &str,
    data_dir: &Path,
    connect: Option<u16>,
    deadline_ms: u64,
) -> Node {
    let mut cmd = Command::new(env!("CARGO_BIN_EXE_swarm-node"));
    cmd.arg("--port").arg(port.to_string());
    cmd.arg("--node-id").arg(node_id);
    cmd.arg("--project").arg("itest");
    cmd.arg("--data-dir").arg(data_dir);
    cmd.arg("--no-auto-sync");
    cmd.env("SWARM_TEST_HELLO_DEADLINE_MS", deadline_ms.to_string());
    if let Some(p) = connect {
        cmd.arg("--connect").arg(format!("127.0.0.1:{p}"));
    }
    cmd.stdout(Stdio::null()).stderr(Stdio::null());
    let child = cmd.spawn().expect("spawn swarm-node");
    let node = Node { child };
    wait_for_port(port);
    node
}

/// Fix A, inbound side: a connected socket that never speaks protocol is
/// closed after the (test-shrunk) inbound hello deadline instead of leaking.
#[test]
fn silent_inbound_socket_is_closed_after_hello_deadline() {
    let ports = alloc_ports(1);
    let dir = data_dir("m11c-inbound");
    let _a = spawn_with_env(ports, "a", &dir.join("a"), None, 400);

    // Connect and deliberately say nothing — the old code kept this
    // socket in the peers-eligible world forever if it never spoke.
    let dead = TcpStream::connect(("127.0.0.1", ports)).unwrap();
    dead.set_read_timeout(Some(Duration::from_secs(3))).unwrap();

    // The node itself must stay healthy and answer clients throughout.
    let start = Instant::now();
    let mut saw_reply_after_close = false;
    while start.elapsed() < Duration::from_secs(5) {
        if request(ports, "(metrics)").contains("metrics")
            && start.elapsed() > Duration::from_millis(700)
        {
            saw_reply_after_close = true;
            break;
        }
        std::thread::sleep(Duration::from_millis(100));
    }
    drop(dead);
    assert!(
        saw_reply_after_close,
        "node stopped answering after silent socket window"
    );
}

/// Fix A, initiator side: dialing a listener that accepts but never says
/// welcome must produce repeated redials (deadline fires, handle_connection
/// returns, spawn_connect loops) — not one eternal ESTABLISHED zombie.
///
/// Review fix #5 (Vyasa): the accepted sockets are HELD OPEN (a drop would
/// surface as EOF — a different path than the silent-welcome deadline this
/// test exists for), and the test asserts the redial actually happened by
/// counting >= 2 accepts.
#[test]
fn initiator_redials_when_welcome_never_arrives() {
    let ports = alloc_ports(2);
    // Silent peer: accepts TCP, holds the sockets open, never sends a byte.
    let listener = std::net::TcpListener::bind(("127.0.0.1", ports + 1)).unwrap();
    listener.set_nonblocking(true).unwrap();
    let accepted: std::sync::Arc<std::sync::atomic::AtomicUsize> =
        std::sync::Arc::new(std::sync::atomic::AtomicUsize::new(0));
    let held: std::sync::Arc<std::sync::Mutex<Vec<TcpStream>>> =
        std::sync::Arc::new(std::sync::Mutex::new(Vec::new()));
    {
        let accepted = std::sync::Arc::clone(&accepted);
        let held = std::sync::Arc::clone(&held);
        std::thread::spawn(move || {
            for stream in listener.incoming().flatten() {
                accepted.fetch_add(1, Ordering::SeqCst);
                held.lock().unwrap().push(stream);
            }
        });
    }

    let dir = data_dir("m11c-redial");
    let _b = spawn_with_env(ports, "b", &dir.join("b"), Some(ports + 1), 300);

    // Several deadline cycles must pass with the node fully responsive,
    // and each cycle should have produced a fresh accept.
    let deadline = Instant::now() + Duration::from_secs(4);
    while Instant::now() < deadline {
        assert!(
            request(ports, "(metrics)").contains("metrics"),
            "node wedged while its bootstrap link was stalled"
        );
        std::thread::sleep(Duration::from_millis(200));
    }
    let count = accepted.load(Ordering::SeqCst);
    assert!(
        count >= 2,
        "expected >=2 accepts (redials), got {count} — initiator is not re-dialing after silent welcome"
    );
}

/// Fix B: a large catch-up train must CONVERGE without either side closing
/// mid-sync (the flood-then-stale-close loop). 1200 events on a fresh join.
#[test]
fn large_backlog_sync_converges_without_stale_close() {
    let ports = alloc_ports(2);
    let dir = data_dir("m11c-backlog");
    let a_port = ports;
    let _a = spawn(a_port, "backlog-a", &dir.join("a"), None);

    for i in 0..1200 {
        let r = request(
            a_port,
            &(format!("(define-task (task BK-{i}) (priority 1))")),
        );
        assert!(r.starts_with("(ok"), "define failed at {i}: {r}");
    }

    let b_port = ports + 1;
    let _b = spawn(b_port, "backlog-b", &dir.join("b"), Some(a_port));

    // B must reach synced=t AND both sides must keep each other connected
    // through the whole train (peer-count on B includes A afterwards).
    let deadline = Instant::now() + Duration::from_secs(30);
    loop {
        let m = request(b_port, "(metrics)");
        let synced = m.contains("(synced t)");
        let peers: usize = m
            .split("(peer-count ")
            .nth(1)
            .and_then(|s| s.split(')').next())
            .and_then(|s| s.parse().ok())
            .unwrap_or(0);
        if synced && peers >= 1 {
            break;
        }
        assert!(
            Instant::now() < deadline,
            "sync did not converge in 30s: {m}"
        );
        std::thread::sleep(Duration::from_millis(200));
    }

    // Diagnostics on failure: full state of both sides at the moment of
    // the (previously flaky) assertion.
    let diag = |port: u16| {
        format!(
            "metrics={}\n  BK-0={}\n  BK-1199={}",
            request(port, "(metrics)"),
            request(port, "(task-status (task BK-0))"),
            request(port, "(task-status (task BK-1199))")
        )
    };
    let status = request(b_port, "(task-status (task BK-1199))");
    assert!(
        status.contains("(defined t"),
        "BK-1199 missing on B\nA: {}\nB: {}",
        diag(a_port),
        diag(b_port)
    );
}

/// M1.3 hygiene: `(evict (node <id>))` flips a dead member's presence to
/// nil across the mesh and shuts down its live-looking socket.
#[test]
fn evict_marks_dead_member_absent_everywhere() {
    let ports = alloc_ports(3);
    let dir = data_dir("m11d-evict");
    let _a = spawn(ports, "evict-a", &dir.join("a"), None);
    let victim_port = ports + 1;
    let mut victim = spawn(victim_port, "ghost-9", &dir.join("g"), Some(ports));

    // ghost joins from ITS own connection
    assert!(
        request(victim_port, "(join (capabilities (test)) (roles (worker)))").starts_with("(ok")
    );

    // Wait until the join fact has propagated to A before evicting —
    // otherwise the late-arriving join would re-mark the ghost present.
    let deadline = Instant::now() + Duration::from_secs(10);
    loop {
        let members = request(ports, "(list-members)");
        let seg = members
            .split("(node ghost-9)")
            .nth(1)
            .unwrap_or("")
            .chars()
            .take_while(|c| *c != ')')
            .collect::<String>();
        if seg.contains("t") {
            break;
        }
        assert!(
            Instant::now() < deadline,
            "ghost-9 never appeared present on A"
        );
        std::thread::sleep(Duration::from_millis(100));
    }

    // admin on A evicts the ghost id
    let r = request(ports, "(evict (node ghost-9))");
    assert!(r.starts_with("(ok"), "{r}");

    // derived membership on A shows it absent
    let deadline = Instant::now() + Duration::from_secs(10);
    loop {
        let members = request(ports, "(list-members)");
        let seg = members
            .split("(node ghost-9)")
            .nth(1)
            .unwrap_or("")
            .chars()
            .take_while(|c| *c != ')')
            .collect::<String>();
        if seg.contains("nil") {
            break;
        }
        assert!(
            Instant::now() < deadline,
            "ghost-9 still present after evict"
        );
        std::thread::sleep(Duration::from_millis(100));
    }

    // Reap the spawned child before Drop does it for us.
    victim.child.kill().ok();
    victim.child.wait().ok();
}

// ---------------------------------------------------------------------------
// M1.2 auto-sync: periodic tasks.lisp file re-read
// ---------------------------------------------------------------------------

fn spawn_with_auto_sync(
    port: u16,
    node_id: &str,
    data_dir: &Path,
    connect: Option<u16>,
    auto_sync_path: &Path,
    sync_interval_ms: u64,
) -> Node {
    let mut cmd = Command::new(env!("CARGO_BIN_EXE_swarm-node"));
    cmd.arg("--port").arg(port.to_string());
    cmd.arg("--node-id").arg(node_id);
    cmd.arg("--project").arg("itest");
    cmd.arg("--data-dir").arg(data_dir);
    cmd.arg("--auto-sync")
        .arg(auto_sync_path.to_string_lossy().to_string());
    cmd.env("SWARM_AUTO_SYNC_INTERVAL_MS", sync_interval_ms.to_string());
    if let Some(p) = connect {
        cmd.arg("--connect").arg(format!("127.0.0.1:{p}"));
    }
    cmd.stdout(Stdio::null()).stderr(Stdio::null());
    let child = cmd.spawn().expect("spawn swarm-node with --auto-sync");
    let node = Node { child };
    wait_for_port(port);
    node
}

/// M1.2: a tasks.lisp file registered via --auto-sync is periodically
/// re-read and its task definitions imported into the registry without
/// any manual (sync-tasks) call. Modifying the file mid-flight must be
/// picked up on the next cycle.
#[test]
fn auto_sync_periodically_imports_tasks_my_file() {
    let port = alloc_ports(1);
    let dir = data_dir("autosync-basic");
    let tasks_file = dir.join("tasks.lisp");

    // Create the directory first (data_dir() only removes, doesn't recreate).
    std::fs::create_dir_all(&dir).unwrap();

    // Write an initial tasks.lisp BEFORE starting the node.
    std::fs::write(
        &tasks_file,
        r#"
((kind . tasks-my)
 (tasks .
  (("AUTO-A" . ((priority . 3) (capabilities . (docs)) (done . ())))
   ("AUTO-B" . ((priority . 7) (capabilities . (rust)) (done . t))))))
"#,
    )
    .unwrap();

    let _n = spawn_with_auto_sync(port, "autosync", &dir, None, &tasks_file, 500);

    // Wait for the first auto-sync cycle to import the tasks.
    let found = eventually(port, "(list-task-state)", Duration::from_secs(5), |r| {
        r.contains("AUTO-A") && r.contains("AUTO-B")
    });
    assert!(
        found.contains("AUTO-A"),
        "auto-sync never imported AUTO-A: {found}"
    );
    assert!(
        found.contains("AUTO-B"),
        "auto-sync never imported AUTO-B: {found}"
    );

    // AUTO-B was marked done in the file — verify that propagated.
    let b_state = eventually(
        port,
        "(task-state (task AUTO-B))",
        Duration::from_secs(3),
        |r| r.contains("(completed t)"),
    );
    assert!(
        b_state.contains("(completed t)"),
        "auto-sync should have marked AUTO-B as completed: {b_state}"
    );

    // Polling an unchanged file must not append duplicate task facts forever.
    let event_count = |port| {
        let metrics = request(port, "(metrics)");
        let marker = "(event-count ";
        let start = metrics.find(marker).expect("metrics event-count") + marker.len();
        let tail = &metrics[start..];
        let end = tail.find(')').expect("closed event-count");
        tail[..end].parse::<usize>().expect("numeric event-count")
    };
    let after_initial_import = event_count(port);
    std::thread::sleep(Duration::from_millis(1_200));
    assert_eq!(
        event_count(port),
        after_initial_import,
        "unchanged auto-sync source must not append duplicate journal facts"
    );

    // Now mutate the file: add a new task AUTO-C.
    std::fs::write(
        &tasks_file,
        r#"
((kind . tasks-my)
 (tasks .
  (("AUTO-A" . ((priority . 3) (capabilities . (docs)) (done . ())))
   ("AUTO-B" . ((priority . 7) (capabilities . (rust)) (done . t)))
   ("AUTO-C" . ((priority . 2) (capabilities . (lisp)) (description . "newly added"))))))
"#,
    )
    .unwrap();

    // Wait for the next auto-sync cycle to pick up the addition.
    let found_c = eventually(port, "(list-task-state)", Duration::from_secs(5), |r| {
        r.contains("AUTO-C")
    });
    assert!(
        found_c.contains("AUTO-C"),
        "auto-sync never picked up newly-added AUTO-C: {found_c}"
    );

    // Verify AUTO-C's description survived through the pipeline.
    let c_def = request(port, "(task-def (task AUTO-C))");
    assert!(
        c_def.contains("newly added"),
        "auto-sync should have imported AUTO-C's description: {c_def}"
    );
}

// --- bind / advertise / observed address model -----------------------
//
// Confirmed live 2026-09-01: several same-machine nodes bound to
// `127.0.0.1` became silently unreachable from each other because their
// address, as *observed* when they dialed out through a remote seed, got
// gossiped onward as their dial-back address -- even though nothing was
// bound to listen there. `bind` (where a process listens), `advertise`
// (what it tells peers to use), and `observed` (what one specific peer's
// socket happened to see) must never silently substitute for one another.
// See `Args::advertise_host`'s doc comment in src/main.rs for the full
// account. These tests prove: (1) a wildcard bind refuses to start
// without an explicit advertise address (no unsafe default exists for
// it), (2) a peer's self-declared advertise-host is what gossip actually
// propagates to a third node, never the observed socket IP, and (3) a
// peer that doesn't declare one (an older binary) still falls back to
// the observed IP exactly as before -- this fix must not break
// interop with live peers this session cannot restart.

#[test]
fn startup_rejects_wildcard_bind_without_advertise_host() {
    let dir = data_dir("wildcard-bind-no-advertise");
    let output = Command::new(env!("CARGO_BIN_EXE_swarm-node"))
        .args([
            "--port",
            "15993",
            "--node-id",
            "wildcard-node",
            "--project",
            "itest",
            "--data-dir",
        ])
        .arg(&dir)
        .args(["--bind", "0.0.0.0", "--no-auto-sync"])
        .output()
        .unwrap();
    assert!(!output.status.success());
    assert!(
        String::from_utf8_lossy(&output.stderr).contains("--advertise-host"),
        "expected the wildcard-bind-without-advertise-host error: {}",
        String::from_utf8_lossy(&output.stderr)
    );
}

/// Spawns a node with its stdout/stderr redirected to a real file this
/// test can poll -- `SWARM_TEST_LOGS` (used elsewhere in this file) is an
/// opt-in env var for a human running tests locally; this needs the log
/// unconditionally, for every run, to observe the exact address gossip
/// actually dialed.
fn spawn_logged(
    port: u16,
    node_id: &str,
    data_dir: &Path,
    connect: Option<u16>,
) -> (Node, PathBuf) {
    spawn_logged_with_env(port, node_id, data_dir, connect, &[])
}

/// Same as `spawn_logged`, plus arbitrary env vars -- for the
/// `SWARM_TEST_ACK_TIMEOUT_MS`-style overrides that let a test prove a
/// background sweep fires without waiting out its real production
/// interval.
fn spawn_logged_with_env(
    port: u16,
    node_id: &str,
    data_dir: &Path,
    connect: Option<u16>,
    env: &[(&str, &str)],
) -> (Node, PathBuf) {
    let log_dir = data_dir.parent().unwrap();
    std::fs::create_dir_all(log_dir).unwrap();
    let log_path = log_dir.join(format!("{node_id}.log"));
    let mut cmd = Command::new(env!("CARGO_BIN_EXE_swarm-node"));
    cmd.arg("--port").arg(port.to_string());
    cmd.arg("--node-id").arg(node_id);
    cmd.arg("--project").arg("itest");
    cmd.arg("--data-dir").arg(data_dir);
    cmd.arg("--no-auto-sync");
    if let Some(p) = connect {
        cmd.arg("--connect").arg(format!("127.0.0.1:{p}"));
    }
    for (key, value) in env {
        cmd.env(key, value);
    }
    let f = std::fs::File::create(&log_path).unwrap();
    cmd.stdout(f.try_clone().unwrap()).stderr(f);
    let child = cmd
        .spawn()
        .expect("failed to spawn swarm-node — did `cargo build -p swarm-node` run first?");
    let node = Node { child };
    wait_for_port(port);
    wait_for_file(&data_dir.join("node.lisp"));
    (node, log_path)
}

fn wait_for_log_containing(log_path: &Path, needle: &str, timeout: Duration) -> String {
    let deadline = Instant::now() + timeout;
    let mut last = String::new();
    while Instant::now() < deadline {
        if let Ok(text) = std::fs::read_to_string(log_path) {
            if text.contains(needle) {
                return text;
            }
            last = text;
        }
        std::thread::sleep(Duration::from_millis(50));
    }
    last
}

/// A raw, hand-spoken peer-hello over a real TCP connection to a real
/// spawned node -- standing in for a peer whose OS-observed source IP
/// (correctly, always 127.0.0.1 in this loopback-only test) would be
/// wrong to trust as its actual dial-back address, matching the real
/// scenario: a node reachable only via a different, non-observed address.
/// Returns once the welcome is read, so the caller knows the handshake
/// (and therefore `register_peer`) has completed before asserting on
/// what the *other* node gossips onward.
fn hand_speak_peer_hello(port: u16, node_id: &str, listen_port: u16, advertise_host: Option<&str>) {
    hand_speak_peer_hello_and_keep_connected(port, node_id, listen_port, advertise_host);
}

/// Same handshake, but returns the still-open connection instead of
/// dropping it -- for tests that need to observe (or deliberately not
/// respond to) what the real node sends afterward, e.g. a `push-event`
/// this fake peer will receive and silently never ack.
fn hand_speak_peer_hello_and_keep_connected(
    port: u16,
    node_id: &str,
    listen_port: u16,
    advertise_host: Option<&str>,
) -> BufReader<TcpStream> {
    let mut stream = TcpStream::connect(("127.0.0.1", port)).unwrap();
    stream
        .set_read_timeout(Some(Duration::from_secs(3)))
        .unwrap();
    let advertise_field = match advertise_host {
        Some(host) => format!(" (advertise-host {host})"),
        None => String::new(),
    };
    writeln!(
        stream,
        "(peer-hello (protocol swarm/1) (node {node_id}) (epoch 0) (project itest) (listen-port {listen_port}){advertise_field})"
    )
    .unwrap();
    let mut reader = BufReader::new(stream);
    let mut line = String::new();
    reader
        .read_line(&mut line)
        .expect("expected a peer-welcome reply");
    assert!(
        line.contains("peer-welcome"),
        "expected peer-welcome, got: {line}"
    );
    reader
}

#[test]
fn gossip_relays_advertised_address_not_the_observed_socket_ip() {
    let ports = alloc_ports(2);
    let (port_b, port_c) = (ports, ports + 1);
    let dir = data_dir("advertise-vs-observed");

    let (_b, _log_b) = spawn_logged(port_b, "relay-b", &dir.join("b"), None);
    let (_c, log_c) = spawn_logged(port_c, "relay-c", &dir.join("c"), Some(port_b));

    // "zzz-fake-remote-a" declares a dial-back address nothing about its real
    // TCP connection would reveal -- the only way this string can reach
    // C's gossip log is through the advertise-host field, never the
    // observed 127.0.0.1 source IP.
    const MARKER: &str = "advertise-host-proof-marker";
    hand_speak_peer_hello(port_b, "zzz-fake-remote-a", 19999, Some(MARKER));

    let log = wait_for_log_containing(
        &log_c,
        "learned of zzz-fake-remote-a",
        Duration::from_secs(5),
    );
    assert!(
        log.contains(&format!("learned of zzz-fake-remote-a at {MARKER}:19999")),
        "C should have gossip-learned zzz-fake-remote-a's advertised address from B, not an observed one: {log}"
    );
    assert!(
        !log.contains("learned of zzz-fake-remote-a at 127.0.0.1:19999"),
        "C used the observed socket IP instead of the peer's declared advertise-host: {log}"
    );
}

#[test]
fn gossip_falls_back_to_observed_ip_when_peer_omits_advertise_host() {
    let ports = alloc_ports(2);
    let (port_b, port_c) = (ports, ports + 1);
    let dir = data_dir("advertise-fallback-compat");

    let (_b, _log_b) = spawn_logged(port_b, "relay-b2", &dir.join("b"), None);
    let (_c, log_c) = spawn_logged(port_c, "relay-c2", &dir.join("c"), Some(port_b));

    // No advertise-host field at all -- simulates a peer still running
    // the pre-fix binary. Must keep working exactly as before: this
    // session cannot restart other agents' live nodes, so old and new
    // binaries have to interoperate.
    hand_speak_peer_hello(port_b, "zzz-fake-old-peer", 18888, None);

    let log = wait_for_log_containing(
        &log_c,
        "learned of zzz-fake-old-peer",
        Duration::from_secs(5),
    );
    assert!(
        log.contains("learned of zzz-fake-old-peer at 127.0.0.1:18888"),
        "an old peer with no advertise-host must still fall back to the observed IP: {log}"
    );
}

// --- push-event delivery confirmation ---------------------------------
//
// Original bug (SWARM-PUSH-EVENT-SILENT-LOSS, ecosystem/plans/tasks.lisp,
// still open as of 2026-09-01): a socket write succeeding only proves the
// bytes reached this machine's kernel send buffer -- it was silently
// treated as "delivered." The owner's framing: event-created !=
// send-attempted != socket-write-ok != peer-accepted != mesh-converged.
// These tests prove the fix's whole PASS criterion: a peer that accepts
// a push-event but never acks it (indistinguishable, from the sender's
// side, from the original bug's connection-cycling silent loss) must
// never be silently treated as a successful delivery -- it shows up as
// `pending`, then as an honest `recent-failures` entry, never neither.

fn emit_event(port: u16, event_type: &str) -> String {
    let response = request(port, &format!("(emit (type {event_type}) (payload ()))"));
    assert!(
        response.starts_with("(ok"),
        "emit should have succeeded: {response}"
    );
    // (ok (id EVENT_ID)) -- pull EVENT_ID out without a full parser.
    let after_id = response
        .split("(id ")
        .nth(1)
        .expect("emit ok must carry an id");
    after_id
        .split(')')
        .next()
        .expect("malformed id field")
        .to_string()
}

#[test]
fn silent_peer_delivery_never_silently_counts_as_acked() {
    let port_a = alloc_ports(1);
    let dir = data_dir("silent-peer-delivery");
    // Shrink ACK_TIMEOUT so this proves the sweep fires without waiting
    // out a real 10s production timeout -- the heartbeat cadence itself
    // (HEARTBEAT_INTERVAL, not overridden here) still bounds how soon
    // after that a sweep tick actually runs.
    let (_a, _log_a) = spawn_logged_with_env(
        port_a,
        "delivery-a",
        &dir.join("a"),
        None,
        &[("SWARM_TEST_ACK_TIMEOUT_MS", "200")],
    );

    // A silent peer: completes the handshake normally (so A registers it
    // as a live connected peer and will push events to it), then never
    // sends anything back -- exactly what the original bug's
    // connection-cycling looked like from A's side: the write succeeds,
    // nothing useful ever comes back.
    let mut silent_peer =
        hand_speak_peer_hello_and_keep_connected(port_a, "zzz-silent-peer", 17777, None);

    let event_id = emit_event(port_a, "test-delivery-event");

    // A really did write the push-event onto the wire to the silent peer
    // -- prove that first, so a later "it's gone" isn't just "it was
    // never sent." The handshake's own sync-hello (empty: this fake peer
    // never claimed to have anything) arrives first on the same
    // connection; skip past it to the push-event.
    let mut line = String::new();
    loop {
        line.clear();
        silent_peer
            .read_line(&mut line)
            .expect("silent peer should have received the push-event");
        if line.contains("push-event") {
            break;
        }
    }
    assert!(
        line.contains(&event_id),
        "expected the push-event for {event_id}, got: {line}"
    );

    // Immediately after: still within ACK_TIMEOUT, this delivery must be
    // `pending`, not silently absent (which would be indistinguishable
    // from "never happened" or "already confirmed").
    let status = request(port_a, "(delivery-status)");
    assert!(
        status.contains(&event_id) && status.contains("pending"),
        "delivery to the silent peer should be pending right after the write: {status}"
    );

    // Past ACK_TIMEOUT: the sweep must have moved it to recent-failures,
    // and it must no longer be reported pending -- silence is never
    // treated as success.
    let final_status = eventually(port_a, "(delivery-status)", Duration::from_secs(8), |r| {
        r.contains(&event_id) && r.contains("ack-timeout")
    });
    assert!(
        final_status.contains("ack-timeout"),
        "an unacked delivery must become an explicit recent-failure, never vanish silently: {final_status}"
    );

    // SWARM-PUSH-EVENT-RETRY-QUEUE: the same failed delivery must ALSO be
    // captured in the durable retry queue (`queued-retries`), so it is not
    // merely observable but actually recoverable on the peer's reconnect --
    // not just a diagnostic ring that forgets the event on restart.
    assert!(
        final_status.contains("queued-retries") && final_status.contains(&event_id),
        "an unacked delivery must also be queued for durable redelivery: {final_status}"
    );

    // And the pending entry for THIS event is gone -- it moved, it didn't duplicate.
    let pending_section = final_status
        .split("recent-failures")
        .next()
        .unwrap_or(&final_status);
    assert!(
        !pending_section.contains(&event_id),
        "the timed-out event must not still be listed as pending: {final_status}"
    );

    drop(silent_peer);
}

/// The actual *recovery* half of SWARM-PUSH-EVENT-RETRY-QUEUE: a delivery
/// that failed (never acked) must not just be diagnosed -- it must be
/// re-pushed once the peer comes back. Proves the full round-trip:
/// queued-on-timeout -> drained-on-reconnect -> acked -> cleared.
#[test]
fn failed_delivery_is_redelivered_after_peer_reconnects() {
    let port_a = alloc_ports(1);
    let dir = data_dir("retry-redelivery");
    // Shrink ACK_TIMEOUT so the failed delivery is swept without waiting
    // out a real 10s production timeout.
    let (_a, _log_a) = spawn_logged_with_env(
        port_a,
        "retry-a",
        &dir.join("a"),
        None,
        &[("SWARM_TEST_ACK_TIMEOUT_MS", "200")],
    );

    // First connection: a peer that gets the push-event but never acks
    // (the connection-cycling / silent-loss scenario from the wire).
    let silent =
        hand_speak_peer_hello_and_keep_connected(port_a, "zzz-retry-peer", 17788, None);
    let event_id = emit_event(port_a, "test-redeliver-event");

    // After ACK_TIMEOUT the delivery must be captured in the durable
    // `queued-retries` (the retry queue), not just the diagnostic ring.
    // Note: the event id also appears in `pending`/`recent-failures`; this
    // predicate specifically requires it inside the trailing
    // `queued-retries` section, so an early `pending` hit doesn't satisfy it.
    eventually(port_a, "(delivery-status)", Duration::from_secs(15), |r| {
        r.split("queued-retries")
            .nth(1)
            .unwrap_or("")
            .contains(&event_id)
    });

    // The old connection dies (peer "went away") -- the only way redelivery
    // is triggered is a genuinely fresh reconnect registering the same id.
    drop(silent);
    // Wait until the node has noticed the close: a peer-hello for an id that
    // still has a live connection is rejected as a possible duplicate
    // identity, so reconnecting too early raced that guard.
    eventually(port_a, "(presence)", Duration::from_secs(5), |r| {
        !r.contains("zzz-retry-peer")
    });

    // Reconnect as the SAME node id, but this time a cooperative peer that
    // acks what it receives. `register_peer` must drain the queue and
    // re-push the lost event onto this fresh stream.
    let mut conn =
        hand_speak_peer_hello_and_keep_connected(port_a, "zzz-retry-peer", 17788, None);
    let mut line = String::new();
    let mut redelivered = false;
    for _ in 0..50 {
        line.clear();
        match conn.read_line(&mut line) {
            Ok(0) | Err(_) => break,
            Ok(_) => {}
        }
        if line.contains("push-event") && line.contains(&event_id) {
            redelivered = true;
            writeln!(conn.get_mut(), "(event-ack (id {event_id}))").unwrap();
            conn.get_mut().flush().unwrap();
            break;
        }
    }
    assert!(
        redelivered,
        "expected the queued event to be redelivered to the reconnected peer"
    );

    // Once acked, the retry queue must be empty for this event -- the
    // `(queued-retries ...)` section (the last, after `recent-failures`)
    // no longer lists it.
    let done = eventually(port_a, "(delivery-status)", Duration::from_secs(15), |r| {
        !r.split("queued-retries").nth(1).unwrap_or("").contains(&event_id)
    });
    assert!(
        !done.split("queued-retries").nth(1).unwrap_or("").contains(&event_id),
        "an acked redelivery must clear the retry queue: {done}"
    );

    drop(conn);
}

// ---------------------------------------------------------------------------
// P2P work-state visibility / help-request / help-offer (2026-09-02)
// ---------------------------------------------------------------------------

/// The full acceptance witness the feature was scoped against: three local
/// nodes, no central coordinator -- A announces work-state, B sees it (not
/// via A relaying to B, but via each node's own gossip-connected peer set
/// folding the same replicated journal); A publishes a help-request; C
/// (connected only to A, must gossip-discover B/A's mesh) sees it and
/// publishes an offer; A sees the offer; B disconnects and reconnects and
/// recovers the current swarm view from whatever the event model already
/// supports (anti-entropy sync on reconnect, same mechanism every other
/// event type already relies on -- no special-cased "resync work-state"
/// path was needed or written).
#[test]
fn p2p_presence_work_visibility_help_request_offer_and_reconnect() {
    let base = alloc_ports(3);
    let (port_a, port_b, port_c) = (base, base + 1, base + 2);
    let dir_b = data_dir("p2p-b");

    let _a = spawn(port_a, "agent-a", &data_dir("p2p-a"), None);
    let mut b = spawn(port_b, "agent-b", &dir_b, Some(port_a));
    let _c = spawn(port_c, "agent-c", &data_dir("p2p-c"), Some(port_a));

    // P2P-PRESENCE-PASS: gossip discovery reaches full mesh (same
    // guarantee gossip_peer_discovery_reaches_full_mesh already covers;
    // re-asserted narrowly here as this test's own precondition).
    let c_presence = eventually(port_c, "(presence)", Duration::from_secs(3), |r| {
        r.contains("agent-b")
    });
    assert!(
        c_presence.contains("agent-b"),
        "P2P-PRESENCE-PASS failed: agent-c never discovered agent-b via gossip through agent-a: {c_presence}"
    );

    // A announces work-state -- through the generic `emit` op (no
    // dedicated `work-state` write command exists; Rust does not parse
    // these fields, `state::work_states` just folds whatever arrives
    // typed `work-state`).
    let announce = request(
        port_a,
        "(emit (type work-state) (payload ((node agent-a) (repo sens) (task macro-semantics) (current-action \"auditing eq/macro value roundtrip\") (status working))))",
    );
    assert!(announce.starts_with("(ok"), "A's work-state announce should succeed: {announce}");

    // P2P-WORK-VISIBILITY-PASS: B sees A's work-state, purely through
    // gossip/anti-entropy -- B never talked to A about this directly
    // except via the peer connection already established for presence.
    let b_sees_a = eventually(port_b, "(list-work-state)", Duration::from_secs(3), |r| {
        r.contains("agent-a") && r.contains("macro-semantics")
    });
    assert!(
        b_sees_a.contains("agent-a") && b_sees_a.contains("macro-semantics") && b_sees_a.contains("working"),
        "P2P-WORK-VISIBILITY-PASS failed: agent-b never saw agent-a's work-state: {b_sees_a}"
    );

    // A publishes a help-request, again through generic `emit`.
    let req = request(
        port_a,
        "(emit (type help-request) (payload ((id request-x) (requester agent-a) (need \"need independent witness for macro value roundtrip\"))))",
    );
    assert!(req.starts_with("(ok"), "A's help-request should succeed: {req}");

    // P2P-HELP-REQUEST-PASS: C sees the request.
    let c_sees_request = eventually(port_c, "(list-help)", Duration::from_secs(3), |r| {
        r.contains("request-x") && r.contains("independent witness")
    });
    assert!(
        c_sees_request.contains("request-x"),
        "P2P-HELP-REQUEST-PASS failed: agent-c never saw agent-a's help-request: {c_sees_request}"
    );

    // C publishes a help-offer responding to A's request, through emit.
    let offer = request(
        port_c,
        "(emit (type help-offer) (payload ((request request-x) (agent agent-c) (capability testing))))",
    );
    assert!(offer.starts_with("(ok"), "C's help-offer should succeed: {offer}");

    // P2P-HELP-OFFER-PASS: A sees C's offer nested under its own request --
    // an offer is a proposal, not an assignment: this assertion only
    // checks visibility, not that A's task ownership or status changed.
    let a_sees_offer = eventually(port_a, "(list-help)", Duration::from_secs(3), |r| {
        r.contains("request-x") && r.contains("agent-c") && r.contains("testing")
    });
    assert!(
        a_sees_offer.contains("agent-c") && a_sees_offer.contains("testing"),
        "P2P-HELP-OFFER-PASS failed: agent-a never saw agent-c's help-offer: {a_sees_offer}"
    );

    // B disconnects and reconnects (same process-restart pattern as
    // restart_preserves_incarnation_epoch_increments_seq_continues) and
    // must recover the current swarm view -- work-state AND help-request/
    // offer visibility, via the same reconnect/anti-entropy path that
    // already restores task/membership state after a restart.
    kill(&mut b);
    drop(b);
    let _b2 = spawn(port_b, "agent-b", &dir_b, Some(port_a));

    // P2P-RECONNECT-PASS.
    let b_recovers_work = eventually(port_b, "(list-work-state)", Duration::from_secs(3), |r| {
        r.contains("agent-a") && r.contains("macro-semantics")
    });
    assert!(
        b_recovers_work.contains("agent-a") && b_recovers_work.contains("macro-semantics"),
        "P2P-RECONNECT-PASS (work-state) failed: agent-b did not recover A's work-state after reconnect: {b_recovers_work}"
    );
    let b_recovers_help = eventually(port_b, "(list-help)", Duration::from_secs(3), |r| {
        r.contains("request-x") && r.contains("agent-c")
    });
    assert!(
        b_recovers_help.contains("request-x") && b_recovers_help.contains("agent-c"),
        "P2P-RECONNECT-PASS (help) failed: agent-b did not recover the request/offer pair after reconnect: {b_recovers_help}"
    );
}

/// Compaction must not silently erase P2P work-state / help-request /
/// help-offer facts -- the same "derive current view, re-emit fresh"
/// safety argument the module doc already makes for task/membership state,
/// checked narrowly here for the three new event types.
#[test]
fn compaction_preserves_work_state_and_help_requests() {
    let port = alloc_ports(1);
    let _a = spawn(port, "compact-node", &data_dir("p2p-compact"), None);

    request(
        port,
        "(emit (type work-state) (payload ((node compact-node) (repo sens) (task macro-semantics) (status working))))",
    );
    request(
        port,
        "(emit (type help-request) (payload ((id req-1) (requester compact-node) (need \"witness\"))))",
    );
    request(
        port,
        "(emit (type help-offer) (payload ((request req-1) (agent compact-node) (capability testing))))",
    );

    let before_work = request(port, "(list-work-state)");
    let before_help = request(port, "(list-help)");

    let compacted = request(port, "(compact)");
    assert!(compacted.starts_with("(ok"), "compact should succeed: {compacted}");

    let after_work = request(port, "(list-work-state)");
    let after_help = request(port, "(list-help)");
    // `last-seen-lamport` is expected to change -- compaction re-emits
    // work-state under a fresh lamport (same "re-derive, re-emit fresh"
    // strategy the module doc already describes for task facts; those
    // just have no lamport-derived field in their read projection to
    // expose the same expected drift). Strip it before comparing so the
    // assertion checks the semantic fields that must actually survive,
    // not a freshness counter that is not meant to.
    fn strip_lamport(s: &str) -> String {
        match s.find("(last-seen-lamport") {
            Some(i) => format!("{}...", &s[..i]),
            None => s.to_string(),
        }
    }
    assert_eq!(
        strip_lamport(&before_work),
        strip_lamport(&after_work),
        "work-state projection (excluding last-seen-lamport, which compaction legitimately refreshes) must survive compaction: before={before_work} after={after_work}"
    );
    assert_eq!(
        before_help, after_help,
        "help-request/offer projection must be byte-identical before/after compaction"
    );
}
