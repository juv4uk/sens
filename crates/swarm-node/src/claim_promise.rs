//! Durable local claim-vote promises.
//!
//! A YES vote is a safety decision, not ordinary replicated task history.  The
//! voter therefore keeps its promise in a small local store and publishes that
//! store before the YES can leave the process.  One task has at most one live
//! record: a higher generation replaces the older fence; time alone never does.

use crate::sexpr::{parse, Sexp};
use std::collections::BTreeMap;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};

fn invalid_data(message: impl Into<String>) -> std::io::Error {
    std::io::Error::new(std::io::ErrorKind::InvalidData, message.into())
}

fn invalid_input(message: impl Into<String>) -> std::io::Error {
    std::io::Error::new(std::io::ErrorKind::InvalidInput, message.into())
}

#[derive(Debug, Clone, PartialEq, Eq)]
struct Promise {
    generation: u64,
    proposer: String,
}

/// Local, crash-recoverable single-vote fence at
/// `<data-dir>/claim-promises.lisp`.
pub struct ClaimPromiseStore {
    path: PathBuf,
    promises: BTreeMap<String, Promise>,
}

impl ClaimPromiseStore {
    pub fn open(data_dir: &Path) -> std::io::Result<Self> {
        fs::create_dir_all(data_dir)?;
        let path = data_dir.join("claim-promises.lisp");
        let promises = if path.exists() {
            Self::decode(&path, &fs::read_to_string(&path)?)?
        } else {
            BTreeMap::new()
        };
        Ok(Self { path, promises })
    }

    /// Reserve this voter's YES for `(task, generation, proposer)`.
    ///
    /// The durable snapshot is published before `Ok(true)` is returned.  A
    /// repeated request from the same proposer is idempotent.  A competing
    /// proposer at the same (or an older) generation is refused forever; an
    /// observed/proposed higher generation safely supersedes the old fence.
    pub fn acquire(
        &mut self,
        task: &str,
        generation: u64,
        proposer: &str,
    ) -> std::io::Result<bool> {
        self.acquire_with_before_publish(task, generation, proposer, |_| Ok(()))
    }

    fn acquire_with_before_publish<F>(
        &mut self,
        task: &str,
        generation: u64,
        proposer: &str,
        before_publish: F,
    ) -> std::io::Result<bool>
    where
        F: FnOnce(&Path) -> std::io::Result<()>,
    {
        if task.is_empty() {
            return Err(invalid_input("claim promise task must not be empty"));
        }
        if proposer.is_empty() {
            return Err(invalid_input("claim promise proposer must not be empty"));
        }
        if generation == 0 {
            return Err(invalid_input("claim promise generation must be positive"));
        }

        if let Some(existing) = self.promises.get(task) {
            if generation < existing.generation {
                return Ok(false);
            }
            if generation == existing.generation {
                return Ok(existing.proposer == proposer);
            }
        }

        let mut next = self.promises.clone();
        next.insert(
            task.to_string(),
            Promise {
                generation,
                proposer: proposer.to_string(),
            },
        );

        self.persist_snapshot(&next, before_publish)?;
        // No fallible operation follows the atomic rename above.  If this
        // process dies between rename and this assignment, restart reloads the
        // already-published snapshot; if assignment runs, memory and disk agree.
        self.promises = next;
        Ok(true)
    }

    fn persist_snapshot<F>(
        &self,
        promises: &BTreeMap<String, Promise>,
        before_publish: F,
    ) -> std::io::Result<()>
    where
        F: FnOnce(&Path) -> std::io::Result<()>,
    {
        let temp_path = self.path.with_extension("my.tmp");
        match fs::remove_file(&temp_path) {
            Ok(()) => {}
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {}
            Err(error) => return Err(error),
        }

        let result = (|| {
            let mut temp = OpenOptions::new()
                .create_new(true)
                .write(true)
                .open(&temp_path)?;
            writeln!(temp, "{}", Self::encode(promises))?;
            temp.sync_all()?;
            before_publish(&temp_path)?;
            fs::rename(&temp_path, &self.path)?;
            Ok(())
        })();

        if result.is_err() {
            let _ = fs::remove_file(&temp_path);
        }
        result
    }

    fn encode(promises: &BTreeMap<String, Promise>) -> String {
        let mut items = vec![Sexp::atom("claim-promises/1")];
        items.extend(promises.iter().map(|(task, promise)| {
            Sexp::list(vec![
                Sexp::atom("promise"),
                Sexp::list(vec![Sexp::atom("task"), Sexp::string(task)]),
                Sexp::list(vec![
                    Sexp::atom("generation"),
                    Sexp::atom(promise.generation.to_string()),
                ]),
                Sexp::list(vec![
                    Sexp::atom("proposer"),
                    Sexp::string(&promise.proposer),
                ]),
            ])
        }));
        Sexp::list(items).to_text()
    }

    fn decode(path: &Path, text: &str) -> std::io::Result<BTreeMap<String, Promise>> {
        let canonical = text.trim();
        if canonical.is_empty() {
            return Err(invalid_data(format!(
                "invalid claim promise store {}: empty file",
                path.display()
            )));
        }
        let parsed = parse(canonical).map_err(|error| {
            invalid_data(format!(
                "invalid claim promise store {}: {error}",
                path.display()
            ))
        })?;
        // `sexpr::parse` intentionally reads one expression.  This file is
        // fully owned by swarm-node, so requiring its canonical rendering also
        // rejects a valid prefix followed by ignored/trailing garbage.
        if parsed.to_text() != canonical {
            return Err(invalid_data(format!(
                "invalid claim promise store {}: non-canonical or trailing data",
                path.display()
            )));
        }

        let Sexp::List(items) = parsed else {
            return Err(invalid_data(format!(
                "invalid claim promise store {}: expected list",
                path.display()
            )));
        };
        if !matches!(items.first(), Some(Sexp::Atom(head)) if head == "claim-promises/1") {
            return Err(invalid_data(format!(
                "invalid claim promise store {}: unsupported or missing version",
                path.display()
            )));
        }

        let mut promises = BTreeMap::new();
        for entry in &items[1..] {
            if entry.head() != Some("promise") {
                return Err(invalid_data(format!(
                    "invalid claim promise store {}: expected promise entry",
                    path.display()
                )));
            }
            let task = entry.field_atom("task").ok_or_else(|| {
                invalid_data(format!(
                    "invalid claim promise store {}: promise missing task",
                    path.display()
                ))
            })?;
            let proposer = entry.field_atom("proposer").ok_or_else(|| {
                invalid_data(format!(
                    "invalid claim promise store {}: promise missing proposer",
                    path.display()
                ))
            })?;
            let generation = entry
                .field_atom("generation")
                .ok_or_else(|| {
                    invalid_data(format!(
                        "invalid claim promise store {}: promise missing generation",
                        path.display()
                    ))
                })?
                .parse::<u64>()
                .map_err(|_| {
                    invalid_data(format!(
                        "invalid claim promise store {}: generation is not a number",
                        path.display()
                    ))
                })?;
            if task.is_empty() || proposer.is_empty() || generation == 0 {
                return Err(invalid_data(format!(
                    "invalid claim promise store {}: empty identity or zero generation",
                    path.display()
                )));
            }
            if promises
                .insert(
                    task.to_string(),
                    Promise {
                        generation,
                        proposer: proposer.to_string(),
                    },
                )
                .is_some()
            {
                return Err(invalid_data(format!(
                    "invalid claim promise store {}: duplicate task `{task}`",
                    path.display()
                )));
            }
        }
        Ok(promises)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn test_dir(label: &str) -> PathBuf {
        let nonce = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .expect("clock should be after Unix epoch")
            .as_nanos();
        std::env::temp_dir().join(format!(
            "swarm-claim-promises-{label}-{}-{nonce}",
            std::process::id()
        ))
    }

    #[test]
    fn restart_preserves_single_vote_fence_and_same_proposer_is_idempotent() {
        let dir = test_dir("restart");
        let mut store = ClaimPromiseStore::open(&dir).unwrap();
        assert!(store.acquire("TASK-1", 1, "proposer-a").unwrap());
        drop(store);

        let mut restarted = ClaimPromiseStore::open(&dir).unwrap();
        assert!(
            !restarted.acquire("TASK-1", 1, "proposer-b").unwrap(),
            "restart must not erase a YES already promised to another proposer"
        );
        assert!(
            restarted.acquire("TASK-1", 1, "proposer-a").unwrap(),
            "redelivery of the same proposal is idempotent"
        );
        let _ = fs::remove_dir_all(dir);
    }

    #[test]
    fn higher_generation_makes_progress_without_time_based_repromise() {
        let dir = test_dir("next-generation");
        let mut store = ClaimPromiseStore::open(&dir).unwrap();
        assert!(store.acquire("TASK-1", 7, "proposer-a").unwrap());
        assert!(!store.acquire("TASK-1", 7, "proposer-b").unwrap());
        assert!(store.acquire("TASK-1", 8, "proposer-b").unwrap());
        assert!(!store.acquire("TASK-1", 7, "proposer-a").unwrap());

        drop(store);
        let mut restarted = ClaimPromiseStore::open(&dir).unwrap();
        assert!(!restarted.acquire("TASK-1", 8, "proposer-c").unwrap());
        assert!(restarted.acquire("TASK-1", 9, "proposer-c").unwrap());
        let _ = fs::remove_dir_all(dir);
    }

    #[test]
    fn persistence_failure_cannot_emit_a_yes_or_mutate_memory() {
        let dir = test_dir("publish-failure");
        let mut store = ClaimPromiseStore::open(&dir).unwrap();
        assert!(store.acquire("TASK-1", 1, "proposer-a").unwrap());
        let before = fs::read(dir.join("claim-promises.lisp")).unwrap();

        let error = store
            .acquire_with_before_publish("TASK-2", 1, "proposer-b", |temp| {
                assert!(temp.exists());
                Err(std::io::Error::other("injected failure before publish"))
            })
            .expect_err("pre-publish failure must fail closed");
        assert_eq!(error.kind(), std::io::ErrorKind::Other);
        assert_eq!(fs::read(dir.join("claim-promises.lisp")).unwrap(), before);

        // If memory had been mutated despite the failed publication, this
        // competing proposal would be rejected.  It must still be free.
        assert!(store.acquire("TASK-2", 1, "proposer-c").unwrap());
        let _ = fs::remove_dir_all(dir);
    }

    #[test]
    fn corrupt_store_fails_closed_instead_of_forgetting_promises() {
        let dir = test_dir("corrupt");
        fs::create_dir_all(&dir).unwrap();
        let path = dir.join("claim-promises.lisp");
        let before = b"(claim-promises/1 (promise (task \"T\") (generation 1)";
        fs::write(&path, before).unwrap();

        let error = ClaimPromiseStore::open(&dir)
            .err()
            .expect("corrupt safety state must stop startup");
        assert_eq!(error.kind(), std::io::ErrorKind::InvalidData);
        assert_eq!(fs::read(&path).unwrap(), before);
        let _ = fs::remove_dir_all(dir);
    }

    #[test]
    fn stale_partial_temp_file_is_never_authority() {
        let dir = test_dir("stale-temp");
        let mut store = ClaimPromiseStore::open(&dir).unwrap();
        assert!(store.acquire("TASK-1", 1, "proposer-a").unwrap());
        drop(store);

        fs::write(
            dir.join("claim-promises.lisp.tmp"),
            "(claim-promises/1 (promise",
        )
        .unwrap();

        let mut restarted = ClaimPromiseStore::open(&dir).unwrap();
        assert!(!restarted.acquire("TASK-1", 1, "proposer-b").unwrap());
        let _ = fs::remove_dir_all(dir);
    }
}
