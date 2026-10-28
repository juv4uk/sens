//! Durable event journal + node identity, per the M0.1 scope in
//! docs/swarm-mesh-v2.md: append-first, ack-after, restart-safe.

use crate::sexpr::{parse, Sexp};
use std::fs::{self, File, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::path::{Path, PathBuf};

fn invalid_data(message: impl Into<String>) -> std::io::Error {
    std::io::Error::new(std::io::ErrorKind::InvalidData, message.into())
}

#[derive(Debug, Clone)]
pub struct Event {
    pub node: String,
    /// Durable identity lifetime this event was issued under. `None` for
    /// legacy events written before M1.1a (and for events from pre-M1.1a
    /// peers); those keep the old `(node, seq)` dedup semantics.
    pub incarnation: Option<String>,
    pub seq: u64,
    pub lamport: u64,
    pub typ: String,
    pub payload: Sexp,
}

impl Event {
    pub fn id(&self) -> String {
        match &self.incarnation {
            Some(inc) => format!("{}:{}:{}", self.node, inc, self.seq),
            None => format!("{}:{}", self.node, self.seq),
        }
    }

    pub fn to_sexp(&self) -> Sexp {
        // Flat shape, same as pre-M1.1a: (event (id ..) (node ..) [(incarnation ..)] (seq ..) ...).
        let mut fields = vec![
            Sexp::list(vec![Sexp::atom("id"), Sexp::atom(self.id())]),
            Sexp::list(vec![Sexp::atom("node"), Sexp::atom(&self.node)]),
        ];
        if let Some(inc) = &self.incarnation {
            fields.push(Sexp::list(vec![Sexp::atom("incarnation"), Sexp::atom(inc)]));
        }
        fields.push(Sexp::list(vec![
            Sexp::atom("seq"),
            Sexp::atom(self.seq.to_string()),
        ]));
        fields.push(Sexp::list(vec![
            Sexp::atom("lamport"),
            Sexp::atom(self.lamport.to_string()),
        ]));
        fields.push(Sexp::list(vec![Sexp::atom("type"), Sexp::atom(&self.typ)]));
        fields.push(Sexp::list(vec![
            Sexp::atom("payload"),
            self.payload.clone(),
        ]));
        Sexp::list(std::iter::once(Sexp::atom("event")).chain(fields).collect())
    }

    pub fn from_sexp(s: &Sexp) -> Result<Event, String> {
        if s.head() != Some("event") {
            return Err("expected event form".to_string());
        }
        let node = s
            .field_atom("node")
            .ok_or("event missing node")?
            .to_string();
        // "-" is the legacy-namespace sentinel in sync-hello v2 maps; a
        // peer sending `(incarnation -)` would alias it (review finding
        // F2), so reject it at parse time.
        let incarnation = match s.field_atom("incarnation") {
            Some("-") => return Err("invalid incarnation `-`".to_string()),
            Some(inc) => Some(inc.to_string()),
            None => None,
        };
        let seq: u64 = s
            .field_atom("seq")
            .ok_or("event missing seq")?
            .parse()
            .map_err(|_| "event seq not a number".to_string())?;
        let lamport: u64 = s
            .field_atom("lamport")
            .ok_or("event missing lamport")?
            .parse()
            .map_err(|_| "event lamport not a number".to_string())?;
        let typ = s
            .field_atom("type")
            .ok_or("event missing type")?
            .to_string();
        let payload = s
            .field("payload")
            .and_then(|f| f.first())
            .cloned()
            .unwrap_or(Sexp::List(vec![]));
        Ok(Event {
            node,
            incarnation,
            seq,
            lamport,
            typ,
            payload,
        })
    }
}

/// Stable node-id + restart-counting epoch + durable incarnation id,
/// persisted at `<data-dir>/node.lisp`.
///
/// Identity model (M1.1a):
/// - `node_id` — logical actor name, stable across lifetimes;
/// - `incarnation` — opaque id generated once when the identity store is
///   first created. Survives normal restarts; a LOST data-dir produces a
///   NEW incarnation under the same node-id, so old and new event streams
///   never collide even though both restart their seq at 1;
/// - `epoch` — process-restart counter *within* one incarnation.
pub struct Identity {
    pub node_id: String,
    pub epoch: u64,
    pub incarnation: String,
}

/// Generates an opaque incarnation id. Post-review (finding F4): 8 bytes
/// from the OS entropy pool via /dev/urandom, hex-encoded — no
/// deterministic-hash reasoning burden. Falls back to a time/pid hash only
/// if /dev/urandom is unreadable (non-Linux/testing environments).
pub fn fresh_incarnation() -> String {
    use std::io::Read;
    if let Ok(mut f) = std::fs::File::open("/dev/urandom") {
        let mut buf = [0u8; 8];
        if f.read_exact(&mut buf).is_ok() {
            return buf.iter().map(|b| format!("{b:02x}")).collect();
        }
    }
    // Fallback (non-Linux/testing): time + pid hash.
    use std::collections::hash_map::DefaultHasher;
    use std::hash::{Hash, Hasher};
    let mut h = DefaultHasher::new();
    std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_nanos())
        .unwrap_or(0)
        .hash(&mut h);
    std::process::id().hash(&mut h);
    format!("{:016x}", h.finish())
}

pub fn load_or_init_identity(data_dir: &Path, node_id: &str) -> std::io::Result<Identity> {
    fs::create_dir_all(data_dir)?;
    let path = data_dir.join("node.lisp");
    let (epoch, stored_incarnation) = if path.exists() {
        let text = fs::read_to_string(&path)?;
        let parsed = parse(&text)
            .map_err(|e| invalid_data(format!("invalid node identity {}: {e}", path.display())))?;
        if parsed.head() != Some("node") {
            return Err(invalid_data(format!(
                "invalid node identity {}: expected node form",
                path.display()
            )));
        }
        let stored_id = parsed.field_atom("id").ok_or_else(|| {
            invalid_data(format!(
                "invalid node identity {}: missing id",
                path.display()
            ))
        })?;
        if stored_id != node_id {
            return Err(std::io::Error::new(
                std::io::ErrorKind::InvalidInput,
                format!(
                    "data-dir identity mismatch: stored node-id `{stored_id}`, requested `{node_id}`"
                ),
            ));
        }
        let stored_epoch = parsed.field_atom("epoch").ok_or_else(|| {
            invalid_data(format!(
                "invalid node identity {}: missing epoch",
                path.display()
            ))
        })?;
        let epoch = stored_epoch.parse::<u64>().map_err(|_| {
            invalid_data(format!(
                "invalid node identity {}: epoch is not a number",
                path.display()
            ))
        })?;
        let e = epoch.checked_add(1).ok_or_else(|| {
            invalid_data(format!(
                "invalid node identity {}: epoch overflow",
                path.display()
            ))
        })?;
        // A pre-M1.1a node.lisp has no incarnation: generate one now and
        // persist it — this upgrade keeps the journal's legacy events
        // (incarnation-less) distinct from everything this process will
        // emit from here on. If an incarnation field is present, however,
        // it must be a real atom/string rather than malformed data.
        let inc = if parsed.field("incarnation").is_some() {
            let value = parsed.field_atom("incarnation").ok_or_else(|| {
                invalid_data(format!(
                    "invalid node identity {}: malformed incarnation",
                    path.display()
                ))
            })?;
            if value.is_empty() || value == "-" {
                return Err(invalid_data(format!(
                    "invalid node identity {}: invalid incarnation `{value}`",
                    path.display()
                )));
            }
            value.to_string()
        } else {
            fresh_incarnation()
        };
        (e, inc)
    } else {
        (0, fresh_incarnation())
    };
    let doc = Sexp::list(vec![
        Sexp::atom("node"),
        Sexp::list(vec![Sexp::atom("id"), Sexp::atom(node_id)]),
        Sexp::list(vec![Sexp::atom("epoch"), Sexp::atom(epoch.to_string())]),
        Sexp::list(vec![
            Sexp::atom("incarnation"),
            Sexp::atom(&stored_incarnation),
        ]),
    ]);
    fs::write(&path, doc.to_text())?;
    Ok(Identity {
        node_id: node_id.to_string(),
        epoch,
        incarnation: stored_incarnation,
    })
}

/// Append-only durable log at `<data-dir>/events.log`, one event per line.
pub struct Journal {
    path: PathBuf,
    file: File,
    pub events: Vec<Event>,
}

impl Journal {
    pub fn open(data_dir: &Path) -> std::io::Result<Journal> {
        fs::create_dir_all(data_dir)?;
        let path = data_dir.join("events.log");
        let mut events = Vec::new();
        if path.exists() {
            let reader = BufReader::new(File::open(&path)?);
            for (index, line) in reader.lines().enumerate() {
                let line = line?;
                if line.trim().is_empty() {
                    continue;
                }
                let line_number = index + 1;
                let sexp = parse(&line).map_err(|e| {
                    invalid_data(format!(
                        "invalid journal {} line {line_number}: {e}",
                        path.display()
                    ))
                })?;
                let ev = Event::from_sexp(&sexp).map_err(|e| {
                    invalid_data(format!(
                        "invalid journal {} line {line_number}: {e}",
                        path.display()
                    ))
                })?;
                events.push(ev);
            }
        }
        let file = OpenOptions::new().create(true).append(true).open(&path)?;
        Ok(Journal { path, file, events })
    }

    /// Persists `event` to disk (fsync'd) before it is considered committed —
    /// callers must only ACK/broadcast after this returns Ok.
    pub fn append(&mut self, event: Event) -> std::io::Result<()> {
        let line = event.to_sexp().to_text();
        writeln!(self.file, "{line}")?;
        self.file.sync_data()?;
        self.events.push(event);
        Ok(())
    }

    /// Wholesale-replaces the on-disk log and in-memory event list — used
    /// by compaction (`compact.rs`) to swap the full history for a smaller
    /// equivalent set. Callers are responsible for the replacement events
    /// being derivation-equivalent to what they replace. Publication is
    /// transactional: the live journal is never truncated in place.
    pub fn replace_all(&mut self, new_events: Vec<Event>) -> std::io::Result<()> {
        self.replace_all_with_before_publish(new_events, |_| Ok(()))
    }

    /// Transactional implementation with a deterministic fault-injection
    /// seam immediately before the atomic publish point. Any error before
    /// `rename` leaves both the live file and `self.events` unchanged.
    fn replace_all_with_before_publish<F>(
        &mut self,
        new_events: Vec<Event>,
        before_publish: F,
    ) -> std::io::Result<()>
    where
        F: FnOnce(&Path) -> std::io::Result<()>,
    {
        let temp_path = self.path.with_extension("log.tmp");

        match fs::remove_file(&temp_path) {
            Ok(()) => {}
            Err(err) if err.kind() == std::io::ErrorKind::NotFound => {}
            Err(err) => return Err(err),
        }

        let result = (|| {
            let mut temp_file = OpenOptions::new()
                .create_new(true)
                .write(true)
                .open(&temp_path)?;
            for ev in &new_events {
                writeln!(temp_file, "{}", ev.to_sexp().to_text())?;
            }
            temp_file.sync_all()?;

            before_publish(&temp_path)?;

            // Open the future append handle before publication so there is no
            // fallible reopen step after the atomic rename. The handle keeps
            // referring to the same file once that file becomes `events.log`.
            let append_file = OpenOptions::new().append(true).open(&temp_path)?;
            fs::rename(&temp_path, &self.path)?;

            self.file = append_file;
            self.events = new_events;
            Ok(())
        })();

        if result.is_err() {
            let _ = fs::remove_file(&temp_path);
        }
        result
    }

    pub fn has(&self, node: &str, incarnation: Option<&str>, seq: u64) -> bool {
        self.events
            .iter()
            .any(|e| e.node == node && e.incarnation.as_deref() == incarnation && e.seq == seq)
    }

    pub fn last_seq(&self, node: &str, incarnation: Option<&str>) -> u64 {
        self.events
            .iter()
            .filter(|e| e.node == node && e.incarnation.as_deref() == incarnation)
            .map(|e| e.seq)
            .max()
            .unwrap_or(0)
    }

    pub fn next_seq(&self, node: &str, incarnation: Option<&str>) -> u64 {
        self.last_seq(node, incarnation) + 1
    }

    pub fn max_lamport(&self) -> u64 {
        self.events.iter().map(|e| e.lamport).max().unwrap_or(0)
    }

    pub fn events_after(&self, node: &str, incarnation: Option<&str>, seq: u64) -> Vec<&Event> {
        self.events
            .iter()
            .filter(|e| e.node == node && e.incarnation.as_deref() == incarnation && e.seq > seq)
            .collect()
    }

    /// All distinct `(node, incarnation)` origins present in the journal.
    /// Legacy events (no incarnation) report `None`.
    pub fn all_origins(&self) -> Vec<(String, Option<String>)> {
        let mut origins: Vec<(String, Option<String>)> = self
            .events
            .iter()
            .map(|e| (e.node.clone(), e.incarnation.clone()))
            .collect();
        origins.sort();
        origins.dedup();
        origins
    }

    pub fn path(&self) -> &Path {
        &self.path
    }
}

