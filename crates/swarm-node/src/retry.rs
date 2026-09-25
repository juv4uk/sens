//! Durable per-peer push-event retry queue (`SWARM-PUSH-EVENT-RETRY-QUEUE`).
//!
//! `broadcast_event` / `sweep_timed_out_acks` are where a `push-event` to a
//! peer is decided to have failed (socket write error, or write succeeded
//! but no `event-ack` arrived inside `ACK_TIMEOUT`). Before this module those
//! failures were only dropped into `recent_delivery_failures`, a *bounded,
//! in-memory, observability-only* ring -- honest but non-recovering. The real
//! mesh (see `runs/2026-09-04-seed-connection-instability/`) showed 99-160
//! such losses in 45 minutes while the seed link cycled, so a durable
//! redelivery path is now warranted.
//!
//! This queue stores only `(peer_id, event_id)` pairs in a small persisted
//! file (`<data-dir>/retry-queue.lisp`). The full event payload is *not*
//! duplicated here: it is re-read from the durable journal to which the
//! event was already appended (journal = authoritative event store). If a
//! queued event has since been compacted out of the journal, the entry is
//! dropped at drain time -- the event is legitimately gone and redelivery is
//! impossible anyway.
//!
//! Redelivery is safe and idempotent because `handle_push_event` on the
//! receiver dedups via `Journal::has()` and acks duplicates without
//! re-appending. Entries are keyed `(peer_id, event_id)` to avoid unbounded
//! growth if a peer never returns.
//!
//! The file is rewritten (atomically, temp + rename) on each change rather
//! than append-logged with tombstones, because the set is small and bounded
//! and simplicity beats append-complexity here; the rewrite happens at most
//! once per heartbeat sweep anyway.

use crate::sexpr::{parse, Sexp};
use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};

/// Hard cap on distinct `(peer_id, event_id)` entries awaiting redelivery.
/// Guards a permanently-absent peer from growing the file without bound.
const RETRY_CAP: usize = 2000;

#[derive(Debug)]
pub struct RetryQueue {
    /// `(peer_id, event_id)` awaiting redelivery, in insertion order.
    pending: Vec<(String, String)>,
    path: PathBuf,
}

impl RetryQueue {
    /// Opens the queue persisted at `data_dir/retry-queue.lisp`, creating an
    /// empty in-memory queue if the file is absent or unreadable (a corrupt
    /// queue must not take the node down -- it only affects retries).
    pub fn open(data_dir: &Path) -> RetryQueue {
        let path = data_dir.join("retry-queue.lisp");
        let pending = match fs::read_to_string(&path) {
            Ok(text) => Self::parse_entries(&text),
            Err(_) => Vec::new(),
        };
        RetryQueue { pending, path }
    }

    fn parse_entries(text: &str) -> Vec<(String, String)> {
        let Ok(root) = parse(text) else {
            return Vec::new();
        };
        let Sexp::List(items) = root else {
            return Vec::new();
        };
        let mut out = Vec::new();
        for item in items.iter().filter_map(|i| match i {
            Sexp::List(inner) if matches!(inner.first(), Some(Sexp::Atom(h)) if h == "entry") => {
                Some(inner)
            }
            _ => None,
        }) {
            let peer = item.iter().find_map(|f| f.field_atom("peer")).map(String::from);
            let ev = item
                .iter()
                .find_map(|f| f.field_atom("event-id"))
                .map(String::from);
            if let (Some(peer), Some(ev)) = (peer, ev) {
                out.push((peer, ev));
            }
        }
        out
    }

    /// Records `(peer_id, event_id)` for later redelivery if not already
    /// queued, persisting the update. Bounded by `RETRY_CAP` (dropping the
    /// oldest entries first when over capacity).
    pub fn push(&mut self, peer_id: &str, event_id: &str) {
        if self.pending.iter().any(|(p, e)| p == peer_id && e == event_id) {
            return;
        }
        self.pending.push((peer_id.to_string(), event_id.to_string()));
        while self.pending.len() > RETRY_CAP {
            self.pending.remove(0);
        }
        let _ = self.save();
    }

    /// Removes and returns every queued `(peer_id, event_id)` for `peer_id`,
    /// persisting the update. The caller re-reads each event's payload from
    /// the journal and re-pushes it on the freshly reconnected stream.
    pub fn take_for(&mut self, peer_id: &str) -> Vec<(String, String)> {
        if !self.pending.iter().any(|(p, _)| p == peer_id) {
            return Vec::new();
        }
        let mut taken = Vec::new();
        let mut remaining = Vec::with_capacity(self.pending.len());
        for (p, e) in self.pending.drain(..) {
            if p == peer_id {
                taken.push((p, e));
            } else {
                remaining.push((p, e));
            }
        }
        self.pending = remaining;
        let _ = self.save();
        taken
    }

    /// Removes a single `(peer_id, event_id)` if queued, persisting the
    /// update. Used when the peer confirms the delivery (an `event-ack`):
    /// a confirmed event no longer needs redelivery, so a queued copy can
    /// be dropped instead of lingering until the next reconnect.
    pub fn remove(&mut self, peer_id: &str, event_id: &str) {
        let before = self.pending.len();
        self.pending
            .retain(|(p, e)| !(p == peer_id && e == event_id));
        if self.pending.len() != before {
            let _ = self.save();
        }
    }

    /// Number of entries currently queued (observability).
    pub fn len(&self) -> usize {
        self.pending.len()
    }

    /// Snapshot of every queued `(peer_id, event_id)` for observability.
    pub fn entries(&self) -> Vec<(String, String)> {
        self.pending.clone()
    }

    fn to_sexp(&self) -> Sexp {
        let mut items: Vec<Sexp> = vec![Sexp::atom("retry-queue")];
        for (peer, ev) in &self.pending {
            items.push(Sexp::list(vec![
                Sexp::atom("entry"),
                Sexp::list(vec![
                    Sexp::list(vec![Sexp::atom("peer"), Sexp::atom(peer)]),
                    Sexp::list(vec![Sexp::atom("event-id"), Sexp::atom(ev)]),
                ]),
            ]));
        }
        Sexp::list(items)
    }

    /// Atomically persists the queue: write to a temp file then rename over
    /// the target, so a crash mid-write never leaves a half-written queue.
    fn save(&self) -> std::io::Result<()> {
        if let Some(parent) = self.path.parent() {
            fs::create_dir_all(parent)?;
        }
        let tmp = self.path.with_extension("my.tmp");
        let text = format!("{}\n", self.to_sexp().to_text());
        {
            let mut f = fs::File::create(&tmp)?;
            f.write_all(text.as_bytes())?;
            f.sync_all()?;
        }
        fs::rename(&tmp, &self.path)?;
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    fn tmpdir(tag: &str) -> PathBuf {
        let dir = std::env::temp_dir().join(format!("swarm-retry-{}-{}", tag, std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(&dir).unwrap();
        dir
    }

    #[test]
    fn push_dedups_and_take_for_scopes_by_peer() {
        let dir = tmpdir("dedup");
        let mut q = RetryQueue::open(&dir);
        q.push("peer-a", "e1");
        q.push("peer-a", "e1"); // duplicate -> ignored
        q.push("peer-a", "e2");
        q.push("peer-b", "e1");
        assert_eq!(q.len(), 3);

        let a = q.take_for("peer-a");
        // insertion order preserved, only peer-a's entries taken
        let ids: Vec<&String> = a.iter().map(|(_, e)| e).collect();
        assert_eq!(ids, vec!["e1", "e2"]);
        assert_eq!(q.len(), 1, "peer-b entry remains");

        let b = q.take_for("peer-b");
        assert_eq!(b[0].1, "e1");
        assert_eq!(q.len(), 0);
        fs::remove_dir_all(&dir).unwrap();
    }

    #[test]
    fn survives_restart_via_persisted_file() {
        let dir = tmpdir("persist");
        {
            let mut q = RetryQueue::open(&dir);
            q.push("seed", "n1:inc:7");
            q.push("node-x", "n1:inc:8");
        }
        // Fresh queue from the same dir must recover both entries.
        let mut q = RetryQueue::open(&dir);
        assert_eq!(q.len(), 2);
        let x = q.take_for("node-x");
        assert_eq!(x[0].1, "n1:inc:8");
        // The file also round-trips through the sexp parser.
        let text = fs::read_to_string(dir.join("retry-queue.lisp")).unwrap();
        assert!(text.contains("retry-queue"));
        fs::remove_dir_all(&dir).unwrap();
    }

    #[test]
    fn remove_clears_only_the_matching_entry() {
        let dir = tmpdir("remove");
        let mut q = RetryQueue::open(&dir);
        q.push("peer-a", "e1");
        q.push("peer-a", "e2");
        q.push("peer-b", "e1");
        q.remove("peer-a", "e1");
        assert_eq!(q.len(), 2);
        // Reopening the persisted file reflects the removal.
        let q2 = RetryQueue::open(&dir);
        assert_eq!(q2.len(), 2);
        assert!(
            !q2.entries().iter().any(|(p, e)| p == "peer-a" && e == "e1"),
            "removed entry must not survive reload"
        );
        fs::remove_dir_all(&dir).unwrap();
    }

    #[test]
    fn corrupt_file_degrades_to_empty() {
        let dir = tmpdir("corrupt");
        fs::write(dir.join("retry-queue.lisp"), "((not? valid sexp").unwrap();
        let q = RetryQueue::open(&dir);
        assert_eq!(q.len(), 0);
        fs::remove_dir_all(&dir).unwrap();
    }
}
