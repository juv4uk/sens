//! tcp_repl.rs - the line-based TCP REPL (plain `expr\n` in, value out),
//! served on 127.0.0.1 only. The semantic sexpr/oracle protocol lives in
//! swarm.rs. Moved verbatim from main.rs (2026-08-22 mechanical split).

use sens::{
    eval_parsed_expressions_incremental, load_process_library, parse, Environment, Session,
};
use std::io::{self, BufRead, BufReader, Write};
use std::net::{Ipv4Addr, TcpListener, TcpStream};
use std::process;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::{Duration, Instant};


const MAX_TCP_REPL_LINE_BYTES: usize = 256 * 1024;
const TCP_REPL_FRAME_DEADLINE: Duration = Duration::from_secs(5);
const MAX_TCP_REPL_CONNECTIONS: usize = 4;
// A separate worker must accommodate the same deep SENS recursion as Oracle.
const TCP_REPL_WORKER_STACK_BYTES: usize = 256 * 1024 * 1024;

/// A bounded, RAII-owned TCP worker slot: always released on exit or panic.
struct LineConnectionSlot {
    active: Arc<AtomicUsize>,
}

impl LineConnectionSlot {
    fn acquire(active: &Arc<AtomicUsize>, limit: usize) -> Option<Self> {
        let mut count = active.load(Ordering::Acquire);
        while count < limit {
            match active.compare_exchange_weak(count, count + 1, Ordering::AcqRel, Ordering::Acquire) {
                Ok(_) => return Some(Self { active: Arc::clone(active) }),
                Err(current) => count = current,
            }
        }
        None
    }
}

impl Drop for LineConnectionSlot {
    fn drop(&mut self) {
        self.active.fetch_sub(1, Ordering::AcqRel);
    }
}

/// Обмежене читання одного кадру. Ліміт у байтах включає LF.
/// Прострочення, перевищення ліміту або некоректний UTF-8 закривають
/// саме з'єднання, а не вимагають дочитувати решту ворожого кадру.
/// EOF із непорожнім фрагментом зберігає попередній контракт read_line.
fn read_bounded_tcp_line(
    reader: &mut BufReader<TcpStream>,
    max_bytes: usize,
    budget: Duration,
) -> io::Result<Option<String>> {
    let deadline = Instant::now() + budget;
    let mut bytes = Vec::with_capacity(max_bytes.min(4096));

    loop {
        // Тайм-аут окремого read не може продовжувати загальний дедлайн:
        // клієнт, що передає по байту, не отримує нових п'яти секунд.
        let remaining = deadline
            .checked_duration_since(Instant::now())
            .filter(|duration| !duration.is_zero())
            .ok_or_else(|| io::Error::new(io::ErrorKind::TimedOut, "TCP frame deadline exceeded"))?;
        reader.get_ref().set_read_timeout(Some(remaining))?;

        let chunk = reader.fill_buf()?;
        if chunk.is_empty() {
            return if bytes.is_empty() {
                Ok(None)
            } else {
                String::from_utf8(bytes)
                    .map(Some)
                    .map_err(|_| io::Error::new(io::ErrorKind::InvalidData, "TCP frame is not UTF-8"))
            };
        }

        let newline = chunk.iter().position(|byte| *byte == b'\n');
        let take = newline.map_or(chunk.len(), |index| index + 1);
        if take > max_bytes.saturating_sub(bytes.len()) {
            return Err(io::Error::new(
                io::ErrorKind::InvalidData,
                "TCP frame exceeds byte limit",
            ));
        }
        bytes.extend_from_slice(&chunk[..take]);
        reader.consume(take);

        if newline.is_some() {
            return String::from_utf8(bytes)
                .map(Some)
                .map_err(|_| io::Error::new(io::ErrorKind::InvalidData, "TCP frame is not UTF-8"));
        }
    }
}

/// `--tcp` / `--tcp=PORT` — a REPL reachable over TCP instead of stdio, for
/// other local processes (e.g. a cross-session tool) to eval expressions
/// against without shelling out to the CLI per call. Bound to
/// `127.0.0.1` only — never `0.0.0.0` — since there is no authentication:
/// anything that can reach this port can eval arbitrary sens, including
/// `process-run` if `--allow-process` was also passed. Loopback-only keeps
/// that blast radius to "processes already running as this user on this
/// machine", matching what the stdio REPL already allows.
/// Each connection gets its own fresh `Session` (core.lisp reloaded from
/// scratch) rather than sharing one across every caller — tried the shared
/// version first, and it let one connection's `def` (accidental or not)
/// corrupt every other caller's environment with no way to trace it back.
/// `Environment` clones cheaply (`Rc<RefCell<Frame>>`) but that's exactly
/// the problem: a clone shares the underlying frame, it doesn't fork it,
/// so cloning an existing `Session` would not have fixed this — a genuinely
/// new `Environment::root()` per connection is what isolates state.
/// State does NOT persist across reconnects within the same connection is
/// fine (a single connection's lines share state, same as one REPL
/// session), but two different connections never see each other's `def`s.
/// Every expression is still logged to stderr with its peer address, for
/// the same accountability reason the isolation itself was added for.
pub(crate) fn run_tcp_repl(port: u16, allowed: &[String]) {
    let listener = match TcpListener::bind((Ipv4Addr::LOCALHOST, port)) {
        Ok(listener) => listener,
        Err(err) => {
            eprintln!("Error: could not bind TCP REPL to 127.0.0.1:{port}: {err}");
            process::exit(1);
        }
    };
    let actual_port = listener.local_addr().map(|a| a.port()).unwrap_or(port);
    println!(
        "sens TCP REPL v{} listening on 127.0.0.1:{actual_port}",
        env!("CARGO_PKG_VERSION")
    );

    // Sessions are independent and concurrent. One client that keeps
    // submitting valid lines must not monopolize the entire accept loop.
    // Allocate a bounded worker slot BEFORE reserving its large stack.
    let active = Arc::new(AtomicUsize::new(0));
    let allowed = Arc::new(allowed.to_vec());
    for stream in listener.incoming() {
        let stream = match stream {
            Ok(stream) => stream,
            Err(error) => {
                eprintln!("TCP REPL: accept failed: {error}");
                continue;
            }
        };
        let Some(slot) = LineConnectionSlot::acquire(&active, MAX_TCP_REPL_CONNECTIONS) else {
            eprintln!("TCP REPL: maximum {MAX_TCP_REPL_CONNECTIONS} sessions reached");
            let _ = stream.shutdown(std::net::Shutdown::Both);
            continue;
        };
        let allowed = Arc::clone(&allowed);
        if let Err(error) = thread::Builder::new()
            .stack_size(TCP_REPL_WORKER_STACK_BYTES)
            .spawn(move || {
                let _slot = slot;
                handle_tcp_line_connection(stream, allowed.as_slice());
            })
        {
            // Failed spawning drops the closure and releases the slot.
            eprintln!("TCP REPL: cannot spawn session worker: {error}");
        }
    }
}

fn handle_tcp_line_connection(stream: TcpStream, allowed: &[String]) {
    let peer = stream
        .peer_addr()
        .map(|a| a.to_string())
        .unwrap_or_else(|_| "?".into());
    eprintln!("TCP REPL: connection from {peer}");

    // TCP is an unauthenticated entry point, not the trusted local
    // Lisp-machine profile. Empty means deny all; a supplied list is exact.
    let environment = Environment::untrusted_tcp(allowed.to_vec());
    let mut session = Session { environment };

    // The TCP REPL uses the same canonical physical bootstrap as the
    // local CLI. No Rust-held Core4 Lisp source is passed into this runtime.
    if let Err(error) = sens::load_core_library(&mut session) {
        eprintln!(
            "TCP REPL: Core4 T5M bootstrap failed: {}",
            error.render("<Core4 T5M bootstrap>")
        );
        return;
    }
    if let Err(error) = sens::load_time_library(&mut session) {
        eprintln!(
            "TCP REPL: T5M time bootstrap failed: {}",
            error.render("<T5M time bootstrap>")
        );
        return;
    }
    if let Err(error) = load_process_library(&mut session) {
        eprintln!(
            "TCP REPL: process library bootstrap failed: {}",
            error.render("<T5M process bootstrap>")
        );
        return;
    }

    // Apply finite resource budgets after Core4/time/process bootstrap.
    session.environment.activate_untrusted_runtime_limits();

    // Обмежуємо і запис: клієнт, що перестав читати відповіді,
    // не повинен тримати сервер у нескінченному write.
    if let Err(error) = stream.set_write_timeout(Some(Duration::from_secs(5))) {
        eprintln!("TCP REPL: {peer} cannot set write timeout: {error}");
        return;
    }
    // BufReader володіє socket; зайвого дублювання handle не потрібно.
    let mut reader = BufReader::new(stream);
    loop {
        match read_bounded_tcp_line(
            &mut reader,
            MAX_TCP_REPL_LINE_BYTES,
            TCP_REPL_FRAME_DEADLINE,
        ) {
            Ok(None) => break,
            Ok(Some(line)) => {
                let trimmed = line.trim();
                if trimmed.is_empty() {
                    continue;
                }
                eprintln!("TCP REPL: {peer} > {trimmed}");
                let response = match parse(trimmed) {
                    Ok(ast) => match eval_parsed_expressions_incremental(&ast, &mut session) {
                        Ok(result) => {
                            let mut out = String::new();
                            for line in result.output {
                                out.push_str(&line);
                                out.push('\n');
                            }
                            out.push_str(&result.value.to_string());
                            out
                        }
                        Err(e) => format!("Error: {}", e.render(trimmed)),
                    },
                    Err(e) => format!("Parse error: {}", e.render(trimmed)),
                };
                if writeln!(reader.get_mut(), "{response}").is_err() {
                    break;
                }
            }
            Err(error) => {
                eprintln!("TCP REPL: {peer} rejected input: {error}");
                break;
            }
        }
    }
    eprintln!("TCP REPL: {peer} disconnected");
}



#[cfg(test)]
mod tests {
    use super::*;
    use std::net::Shutdown;
    use std::io::Write;

    fn connected_streams() -> (TcpStream, TcpStream) {
        let listener = TcpListener::bind((Ipv4Addr::LOCALHOST, 0)).unwrap();
        let sender = TcpStream::connect(listener.local_addr().unwrap()).unwrap();
        let (receiver, _) = listener.accept().unwrap();
        (sender, receiver)
    }

    #[test]
    fn tcp_repl_frame_worker_slots_are_bounded_and_released_on_panic() {
        let active = Arc::new(AtomicUsize::new(0));
        let first = LineConnectionSlot::acquire(&active, 2).expect("first session");
        let second = LineConnectionSlot::acquire(&active, 2).expect("second session");
        assert!(LineConnectionSlot::acquire(&active, 2).is_none());
        drop(first);
        let third = LineConnectionSlot::acquire(&active, 2).expect("released slot");
        drop(second);
        drop(third);
        assert_eq!(active.load(Ordering::Acquire), 0);

        let outcome = std::panic::catch_unwind({
            let active = Arc::clone(&active);
            move || {
                let _slot = LineConnectionSlot::acquire(&active, 2).expect("worker slot");
                panic!("simulated session failure");
            }
        });
        assert!(outcome.is_err());
        assert_eq!(active.load(Ordering::Acquire), 0);
    }

    #[test]
    fn tcp_repl_frame_worker_slots_are_atomic_under_contention() {
        let active = Arc::new(AtomicUsize::new(0));
        let begin = Arc::new(std::sync::Barrier::new(17));
        let release = Arc::new(std::sync::Barrier::new(17));
        let mut joins = Vec::new();
        for _ in 0..16 {
            let active = Arc::clone(&active);
            let begin = Arc::clone(&begin);
            let release = Arc::clone(&release);
            joins.push(thread::spawn(move || {
                begin.wait();
                let slot = LineConnectionSlot::acquire(&active, 4);
                release.wait();
                slot.is_some()
            }));
        }
        begin.wait();
        release.wait();
        let admitted = joins.into_iter().map(|join| join.join().unwrap()).filter(|ok| *ok).count();
        assert!(admitted <= 4);
        assert_eq!(active.load(Ordering::Acquire), 0);
    }

    #[test]
    fn tcp_repl_frame_preserves_crlf_and_following_frame() {
        let (mut sender, receiver) = connected_streams();
        sender.write_all(b"(a)\r\n(b)\n").unwrap();
        let mut reader = BufReader::new(receiver);
        assert_eq!(
            read_bounded_tcp_line(&mut reader, 5, Duration::from_secs(1)).unwrap(),
            Some("(a)\r\n".into())
        );
        assert_eq!(
            read_bounded_tcp_line(&mut reader, 5, Duration::from_secs(1)).unwrap(),
            Some("(b)\n".into())
        );
    }

    #[test]
    fn tcp_repl_frame_rejects_oversize_without_waiting_for_lf() {
        let (mut sender, receiver) = connected_streams();
        sender.write_all(b"12345").unwrap();
        // Keep the socket open: the fifth byte must fail without LF or EOF.
        let mut reader = BufReader::new(receiver);
        let error = read_bounded_tcp_line(&mut reader, 4, Duration::from_secs(1))
            .unwrap_err();
        assert_eq!(error.kind(), io::ErrorKind::InvalidData);
    }

    #[test]
    fn tcp_repl_frame_exact_boundary_and_multibyte_utf8() {
        let (mut sender, receiver) = connected_streams();
        sender.write_all("é\n".as_bytes()).unwrap(); // two UTF-8 bytes plus LF
        let mut reader = BufReader::new(receiver);
        assert_eq!(
            read_bounded_tcp_line(&mut reader, 3, Duration::from_secs(1)).unwrap(),
            Some("é\n".into())
        );
    }

    #[test]
    fn tcp_repl_frame_rejects_invalid_utf8() {
        let (mut sender, receiver) = connected_streams();
        sender.write_all(b"\xff\n").unwrap();
        let mut reader = BufReader::new(receiver);
        let error = read_bounded_tcp_line(&mut reader, 3, Duration::from_secs(1))
            .unwrap_err();
        assert_eq!(error.kind(), io::ErrorKind::InvalidData);
    }

    #[test]
    fn tcp_repl_frame_retains_partial_eof_compatibility() {
        let (mut sender, receiver) = connected_streams();
        sender.write_all(b"abc").unwrap();
        sender.shutdown(Shutdown::Write).unwrap();
        let mut reader = BufReader::new(receiver);
        assert_eq!(
            read_bounded_tcp_line(&mut reader, 3, Duration::from_secs(1)).unwrap(),
            Some("abc".into())
        );
        assert_eq!(
            read_bounded_tcp_line(&mut reader, 3, Duration::from_secs(1)).unwrap(),
            None
        );
    }

    #[test]
    fn tcp_repl_frame_idle_peer_has_bounded_deadline() {
        let (_sender, receiver) = connected_streams();
        let mut reader = BufReader::new(receiver);
        let error = read_bounded_tcp_line(&mut reader, 16, Duration::from_millis(100))
            .unwrap_err();
        assert!(matches!(
            error.kind(),
            io::ErrorKind::TimedOut | io::ErrorKind::WouldBlock
        ));
    }
}
