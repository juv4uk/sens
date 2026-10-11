//! CLI argument surface for swarm-node: `Args`, argv parsing, startup
//! validation, and usage text.
//!
//! Extracted verbatim from `main.rs` (issue #577, SWARM-NODE-DECOMPOSITION-1,
//! slice 1). Pure move under the #299 substrate policy: no behavior change;
//! visibility widened to `pub(crate)` only.

use std::path::PathBuf;

pub(crate) struct Args {
    pub(crate) port: u16,
    pub(crate) node_id: String,
    pub(crate) project: String,
    pub(crate) data_dir: PathBuf,
    pub(crate) connect: Vec<String>,
    /// Interface to listen on. Defaults to `127.0.0.1` (unchanged,
    /// localhost-only behavior) so existing single-machine setups keep
    /// working exactly as before; pass `0.0.0.0` (or a specific interface
    /// IP, e.g. a Tailscale address) to accept connections from other
    /// machines. Not validated/firewalled by swarm-node itself — whatever
    /// network the bind address is reachable from is who can talk to this
    /// node, so this is a deliberate, explicit opt-in, not a new default.
    pub(crate) bind: String,
    /// What this node tells peers to dial back to reach it. `bind`,
    /// `advertise`, and the observed source IP of an inbound connection
    /// are three genuinely different things: where a process listens,
    /// what it claims others should use, and what one specific peer
    /// happened to see a connection arrive from. This used to not exist
    /// -- gossip inferred a peer's dialable address purely from the
    /// observed source IP, on the assumption that direct-routing overlays
    /// like Tailscale never rewrite addresses in transit, so observed ==
    /// dialable. That's only true for the direct hop that made the
    /// observation; it breaks across a second hop. Confirmed live
    /// 2026-09-01: a node bound to `127.0.0.1` (loopback-only) that dials
    /// *out* to a remote seed necessarily does so from its real interface
    /// address (the OS has no other choice), so the seed correctly
    /// observes it there -- but that address is not where the node is
    /// actually listening, and gossiping it onward sent other same-machine
    /// peers to dial a port nothing was bound to, making them silently
    /// unreachable from each other despite being on the same box. `None`
    /// (no explicit `--advertise-host`) resolves to `bind` itself, which
    /// covers both "loopback-only, advertise loopback" and "bound
    /// directly to my real IP, advertise that same IP." A wildcard
    /// `--bind 0.0.0.0` has no single correct default and requires
    /// `--advertise-host` explicitly (see `validate_startup_args`).
    pub(crate) advertise_host: Option<String>,
    /// M1.2 auto-sync: absolute paths to `tasks.my` files to periodically
    /// re-read and import into the task registry (same format as
    /// `(sync-tasks)`). Each path is re-read every `AUTO_SYNC_INTERVAL`;
    /// file parse/IO errors are logged and skipped without crashing the
    /// node or clearing already-imported facts.
    pub(crate) auto_sync: Vec<PathBuf>,
    /// An explicit opt-out is required for protocol-only/test nodes. This
    /// prevents a typo in `--auto-sync` from silently starting an empty task
    /// projection.
    pub(crate) no_auto_sync: bool,
}

pub(crate) fn invalid_arg(message: impl Into<String>) -> std::io::Error {
    std::io::Error::new(std::io::ErrorKind::InvalidInput, message.into())
}

pub(crate) fn parse_args() -> std::io::Result<Args> {
    let mut port = 9101u16;
    let mut node_id = "node-1".to_string();
    let mut project = "unknown".to_string();
    let mut data_dir = PathBuf::from(".swarm-node");
    let mut connect = Vec::new();
    let mut bind = "127.0.0.1".to_string();
    let mut advertise_host = None;
    let mut auto_sync = Vec::new();
    let mut no_auto_sync = false;
    let mut seen = HashSet::new();

    let mut it = std::env::args().skip(1);
    while let Some(arg) = it.next() {
        match arg.as_str() {
            "--help" | "-h" => print_usage_and_exit(),
            "--port" => {
                if !seen.insert("--port") {
                    return Err(invalid_arg("duplicate --port"));
                }
                let value = it
                    .next()
                    .ok_or_else(|| invalid_arg("--port requires a value"))?;
                port = value
                    .parse()
                    .map_err(|_| invalid_arg("--port requires a valid u16"))?;
            }
            "--node-id" => {
                if !seen.insert("--node-id") {
                    return Err(invalid_arg("duplicate --node-id"));
                }
                node_id = it
                    .next()
                    .ok_or_else(|| invalid_arg("--node-id requires a value"))?;
            }
            "--project" => {
                if !seen.insert("--project") {
                    return Err(invalid_arg("duplicate --project"));
                }
                project = it
                    .next()
                    .ok_or_else(|| invalid_arg("--project requires a value"))?;
            }
            "--data-dir" => {
                if !seen.insert("--data-dir") {
                    return Err(invalid_arg("duplicate --data-dir"));
                }
                data_dir = PathBuf::from(
                    it.next()
                        .ok_or_else(|| invalid_arg("--data-dir requires a value"))?,
                );
            }
            "--bind" => {
                if !seen.insert("--bind") {
                    return Err(invalid_arg("duplicate --bind"));
                }
                bind = it
                    .next()
                    .ok_or_else(|| invalid_arg("--bind requires a value"))?;
            }
            "--advertise-host" => {
                if !seen.insert("--advertise-host") {
                    return Err(invalid_arg("duplicate --advertise-host"));
                }
                advertise_host = Some(
                    it.next()
                        .ok_or_else(|| invalid_arg("--advertise-host requires a value"))?,
                );
            }
            "--connect" => {
                connect.push(
                    it.next()
                        .ok_or_else(|| invalid_arg("--connect requires a value"))?,
                );
            }
            "--auto-sync" => {
                let path = PathBuf::from(
                    it.next()
                        .ok_or_else(|| invalid_arg("--auto-sync requires a value"))?,
                );
                if !path.is_absolute() {
                    return Err(invalid_arg("--auto-sync requires an absolute path"));
                }
                auto_sync.push(path);
            }
            "--no-auto-sync" => {
                if no_auto_sync {
                    return Err(invalid_arg("duplicate --no-auto-sync"));
                }
                no_auto_sync = true;
            }
            other => return Err(invalid_arg(format!("unknown argument `{other}`"))),
        }
    }
    Ok(Args {
        port,
        node_id,
        project,
        data_dir,
        connect,
        bind,
        advertise_host,
        auto_sync,
        no_auto_sync,
    })
}

pub(crate) fn validate_startup_args(args: &Args) -> std::io::Result<()> {
    let invalid = |message: &str| std::io::Error::new(std::io::ErrorKind::InvalidInput, message);
    if args.node_id == "node-1" {
        return Err(invalid(
            "refusing implicit node-id `node-1`; pass an explicit stable --node-id",
        ));
    }
    if args.project == "unknown" {
        return Err(invalid(
            "refusing implicit project `unknown`; pass an explicit --project",
        ));
    }
    if !args.data_dir.is_absolute() {
        return Err(invalid(
            "--data-dir must be absolute so restart cannot create a second identity tree",
        ));
    }
    if args.bind == "0.0.0.0" && args.advertise_host.is_none() {
        return Err(invalid(
            "a wildcard --bind 0.0.0.0 has no single correct dial-back address; pass --advertise-host explicitly",
        ));
    }
    if args.auto_sync.is_empty() && !args.no_auto_sync {
        return Err(invalid(
            "pass at least one --auto-sync tasks.my path, or explicitly pass --no-auto-sync",
        ));
    }
    if !args.auto_sync.is_empty() && args.no_auto_sync {
        return Err(invalid(
            "--auto-sync and --no-auto-sync are mutually exclusive",
        ));
    }
    for path in &args.auto_sync {
        if !path.is_file() {
            return Err(invalid(
                "every --auto-sync path must name an existing tasks.my file",
            ));
        }
    }
    Ok(())
}

/// `--help`/`-h` must exit before touching the network or filesystem at
/// all — the bug this fixes (`SWARM-NODE-HELP-FLAG-BUG`) was that an
/// unrecognized-looking `--help` fell through to `other => warn!(...)`
/// and then the process kept going and actually started a real node
/// under every default (relative `.swarm-node` data-dir, port 9101,
/// node-id `node-1`) — confirmed live: running `--help` while port 9101
/// was already in use crashed with `AddrInUse` instead of showing help,
/// and with the port free it would have silently joined/started a real
/// node under those defaults instead.
fn print_usage_and_exit() -> ! {
    println!(
        "swarm-node — P2P coordination-plane node (see docs/swarm-mesh-v2.md)\n\
         \n\
         USAGE:\n\
         \x20\x20swarm-node [OPTIONS]\n\
         \n\
         OPTIONS:\n\
         \x20\x20--port <PORT>          Listen port (default: 9101)\n\
         \x20\x20--node-id <ID>         Stable node identity (required; placeholder node-1 is refused)\n\
         \x20\x20--project <NAME>       Project label (required; placeholder unknown is refused)\n\
         \x20\x20--data-dir <PATH>      Absolute journal/identity directory (required; relative state\n\
         \x20\x20                       is refused so restart cannot create a second identity tree)\n\
         \x20\x20--bind <ADDRESS>       Interface to listen on (default: 127.0.0.1, localhost-only;\n\
         \x20\x20                       pass 0.0.0.0 or a specific interface IP for cross-machine use)\n\
         \x20\x20--advertise-host <HOST> What this node tells peers to dial back to reach it (default:\n\
         \x20\x20                       the --bind value itself; required if --bind is 0.0.0.0, since\n\
         \x20\x20                       a wildcard bind has no single correct dial-back address)\n\
         \x20\x20--connect <HOST:PORT>  Bootstrap peer to dial on startup (repeatable; one is enough,\n\
         \x20\x20                       gossip discovers the rest of the mesh)\n\
         \x20\x20--auto-sync <PATH>     Absolute path to a tasks.my file to periodically re-read and\n\
         \x20\x20                       import into the task registry (repeatable; same format as\n\
         \x20\x20                       (sync-tasks); interval is ~30 s, override via\n\
         \x20\x20                       SWARM_AUTO_SYNC_INTERVAL_MS)\n\
         \x20\x20--no-auto-sync         Explicit opt-out for protocol-only or isolated test nodes\n\
         \x20\x20--help, -h             Show this message and exit\n\
         \n\
         See docs/swarm-mesh-v2.md's onboarding checklist for a full first-join walkthrough."
    );
    std::process::exit(0);
}
