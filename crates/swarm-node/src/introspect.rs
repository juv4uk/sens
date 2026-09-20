//! Membership / introspection surface for swarm-node: presence, status,
//! delivery-status, metrics, join/leave/evict, compact, list-members.
//!
//! Extracted verbatim from `main.rs` (issue #577, SWARM-NODE-DECOMPOSITION-1,
//! slice 2). Pure move under the #299 substrate policy: no behavior change;
//! visibility widened to `pub(crate)` only, on exactly the referenced items.

use crate::{Node, broadcast_event, send, task_state_sexp};
use crate::journal::{Event};
use crate::sexpr::{Sexp};
use crate::compact;
use crate::state;
use crate::log::{log_info as info};
use std::net::TcpStream;
use std::sync::Arc;
use std::time::Instant;

/// Local client op: `(presence)`. Derived live from currently-open
/// connections rather than the event log — unlike claims and evidence,
/// "is this node up right now" is inherently ephemeral and shouldn't
/// survive a restart as a stale fact, so it deliberately isn't durable.
pub(crate) fn handle_presence(node: &Arc<Node>, stream: &mut TcpStream) {
    send(stream, &presence_sexp(node));
}

fn presence_sexp(node: &Arc<Node>) -> Sexp {
    let mut ids: Vec<String> = node
        .peers
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner())
        .keys()
        .cloned()
        .collect();
    ids.push(node.identity.node_id.clone());
    ids.sort();
    Sexp::list(vec![
        Sexp::atom("presence"),
        Sexp::list(ids.into_iter().map(Sexp::atom).collect()),
    ])
}

/// Local client op: `(status)`. One round trip instead of three —
/// `presence` + `list-members` + `list-task-state` bundled together, for
/// whoever's checking swarm health (a human, or an agent deciding what to
/// do next) without stitching three separate replies together by hand.
pub(crate) fn handle_status(node: &Arc<Node>, stream: &mut TcpStream) {
    let presence = presence_sexp(node);

    let journal = node
        .journal
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner());
    let members = state::membership(&journal);
    let mut member_ids: Vec<&String> = members.keys().collect();
    member_ids.sort();
    let members_sexp = Sexp::list(vec![
        Sexp::atom("members"),
        Sexp::list(
            member_ids
                .into_iter()
                .map(|id| {
                    let m = &members[id];
                    Sexp::list(vec![
                        Sexp::list(vec![Sexp::atom("node"), Sexp::atom(id)]),
                        Sexp::list(vec![
                            Sexp::atom("present"),
                            Sexp::atom(if m.present { "t" } else { "nil" }),
                        ]),
                        Sexp::list(vec![
                            Sexp::atom("roles"),
                            Sexp::list(m.roles.iter().map(Sexp::atom).collect()),
                        ]),
                        Sexp::list(vec![
                            Sexp::atom("capabilities"),
                            Sexp::list(m.capabilities.iter().map(Sexp::atom).collect()),
                        ]),
                    ])
                })
                .collect(),
        ),
    ]);
    let tasks_sexp = Sexp::list(vec![
        Sexp::atom("task-states"),
        Sexp::list(
            state::all_task_ids(&journal)
                .iter()
                .map(|task| task_state_sexp(task, &state::task_state(&journal, task)))
                .collect(),
        ),
    ]);
    drop(journal);

    send(
        stream,
        &Sexp::list(vec![
            Sexp::atom("status"),
            Sexp::list(vec![Sexp::atom("node"), Sexp::atom(&node.identity.node_id)]),
            Sexp::list(vec![
                Sexp::atom("epoch"),
                Sexp::atom(node.identity.epoch.to_string()),
            ]),
            Sexp::list(vec![
                Sexp::atom("synced"),
                Sexp::atom(if node.synced() { "t" } else { "nil" }),
            ]),
            presence,
            members_sexp,
            tasks_sexp,
        ]),
    );
}

/// Local client op: `(delivery-status)`. The explicit answer to "did my
/// push-event actually reach the mesh" that this protocol never had
/// before -- see `Node::pending_acks`'s doc comment. `pending` is every
/// write awaiting an ack right now (bounded implicitly by `ACK_TIMEOUT`
/// -- nothing sits here longer than that before the sweep moves it to
/// `recent-failures` or an ack removes it); `recent-failures` is the
/// bounded diagnostic ring of deliveries that timed out unacked.
pub(crate) fn handle_delivery_status(node: &Arc<Node>, stream: &mut TcpStream) {
    let now = Instant::now();
    let pending: Vec<Sexp> = node
        .pending_acks
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner())
        .iter()
        .map(|((peer_id, event_id), sent_at)| {
            Sexp::list(vec![
                Sexp::list(vec![Sexp::atom("peer"), Sexp::atom(peer_id)]),
                Sexp::list(vec![Sexp::atom("event"), Sexp::atom(event_id)]),
                Sexp::list(vec![
                    Sexp::atom("age-ms"),
                    Sexp::atom(now.duration_since(*sent_at).as_millis().to_string()),
                ]),
            ])
        })
        .collect();
    let failures: Vec<Sexp> = node
        .recent_delivery_failures
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner())
        .iter()
        .map(|(peer_id, event_id, reason)| {
            Sexp::list(vec![
                Sexp::list(vec![Sexp::atom("peer"), Sexp::atom(peer_id)]),
                Sexp::list(vec![Sexp::atom("event"), Sexp::atom(event_id)]),
                Sexp::list(vec![Sexp::atom("reason"), Sexp::atom(reason)]),
            ])
        })
        .collect();
    let (queued_len, queued): (usize, Vec<Sexp>) = {
        let rq = node
            .retry_queue
            .lock()
            .unwrap_or_else(|poisoned| poisoned.into_inner());
        let count = rq.len();
        let list = rq
            .entries()
            .into_iter()
            .map(|(peer_id, event_id)| {
                Sexp::list(vec![
                    Sexp::list(vec![Sexp::atom("peer"), Sexp::atom(peer_id)]),
                    Sexp::list(vec![Sexp::atom("event"), Sexp::atom(event_id)]),
                ])
            })
            .collect();
        (count, list)
    };
    send(
        stream,
        &Sexp::list(vec![
            Sexp::atom("delivery-status"),
            Sexp::list(vec![Sexp::atom("pending"), Sexp::list(pending)]),
            Sexp::list(vec![Sexp::atom("recent-failures"), Sexp::list(failures)]),
            Sexp::list(vec![
                Sexp::atom("queued-retries"),
                Sexp::list(vec![
                    Sexp::list(vec![
                        Sexp::atom("count"),
                        Sexp::atom(queued_len.to_string()),
                    ]),
                    Sexp::list(vec![Sexp::atom("entries"), Sexp::list(queued)]),
                ]),
            ]),
        ]),
    );
}

/// Local client op: `(metrics)`. A handful of small, fixed fields meant
/// to be polled repeatedly and diffed/graphed over time (e.g. by
/// `SWARM-STATUS-DASHBOARD`) — deliberately lighter than `(status)`,
/// which re-serializes the full task/member list on every call and gets
/// more expensive as the swarm grows. No new derived-state computation
/// beyond what `(status)`/`(presence)` already do; this just bundles the
/// cheap scalar facts on their own.
pub(crate) fn handle_metrics(node: &Arc<Node>, stream: &mut TcpStream) {
    let journal = node
        .journal
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner());
    let event_count = journal.events.len();
    // Report the *directory* the operator passed as --data-dir, not the
    // events.log file path itself — that's what a `--data-dir <this>` on
    // a restart actually needs (SWARM-NODE-DATA-DIR-DISCOVERY: this
    // replaces having to `find / -name events.log` blind when a running
    // node's --data-dir was never recorded anywhere).
    let data_dir = journal
        .path()
        .parent()
        .map(|p| p.display().to_string())
        .unwrap_or_else(|| journal.path().display().to_string());
    drop(journal);
    let peer_count = node
        .peers
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner())
        .len();
    let uptime_secs = node.started_at.elapsed().as_secs();
    let bootstrap_peers = node.bootstrap_expected;
    let synced_peers = node.caught_up_with.lock().unwrap().len();
    let auto_sync_paths = node.auto_sync_paths.lock().unwrap().len();
    let task_syncs_completed = node.auto_sync_snapshots.lock().unwrap().len();

    send(
        stream,
        &Sexp::list(vec![
            Sexp::atom("metrics"),
            Sexp::list(vec![Sexp::atom("node"), Sexp::atom(&node.identity.node_id)]),
            Sexp::list(vec![
                Sexp::atom("epoch"),
                Sexp::atom(node.identity.epoch.to_string()),
            ]),
            Sexp::list(vec![
                Sexp::atom("uptime-secs"),
                Sexp::atom(uptime_secs.to_string()),
            ]),
            Sexp::list(vec![
                Sexp::atom("event-count"),
                Sexp::atom(event_count.to_string()),
            ]),
            Sexp::list(vec![
                Sexp::atom("peer-count"),
                Sexp::atom(peer_count.to_string()),
            ]),
            Sexp::list(vec![
                Sexp::atom("synced"),
                Sexp::atom(if node.synced() { "t" } else { "nil" }),
            ]),
            Sexp::list(vec![
                Sexp::atom("bootstrap-peers"),
                Sexp::atom(bootstrap_peers.to_string()),
            ]),
            Sexp::list(vec![
                Sexp::atom("synced-peers"),
                Sexp::atom(synced_peers.to_string()),
            ]),
            Sexp::list(vec![
                Sexp::atom("task-sync"),
                Sexp::atom(if auto_sync_paths == task_syncs_completed {
                    "t"
                } else {
                    "nil"
                }),
            ]),
            Sexp::list(vec![Sexp::atom("data-dir"), Sexp::string(data_dir)]),
        ]),
    );
}

/// Local client op: `(join (capabilities (a b)) (roles (worker)))`.
/// Declares this agent's capabilities/roles as an `agent-joined` fact — a
/// durable, replicated statement of "I am part of this swarm and here is
/// what I can do", independent of any one connection. Roles default to
/// `(worker)` when omitted; only a node with an explicit `voter` role
/// counts toward `claim-task` quorum (see `handle_claim_task`).
pub(crate) fn handle_join(node: &Arc<Node>, msg: &Sexp, stream: &mut TcpStream) {
    let capabilities = msg
        .field("capabilities")
        .and_then(|f| f.first())
        .cloned()
        .unwrap_or(Sexp::List(vec![]));
    let roles = msg
        .field("roles")
        .and_then(|f| f.first())
        .cloned()
        .unwrap_or(Sexp::List(vec![Sexp::atom("worker")]));
    let payload = Sexp::list(vec![
        Sexp::list(vec![Sexp::atom("node"), Sexp::atom(&node.identity.node_id)]),
        Sexp::list(vec![
            Sexp::atom("epoch"),
            Sexp::atom(node.identity.epoch.to_string()),
        ]),
        Sexp::list(vec![Sexp::atom("capabilities"), capabilities]),
        Sexp::list(vec![Sexp::atom("roles"), roles]),
    ]);
    let lamport = node.tick_lamport(0);
    let mut journal = node
        .journal
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner());
    let seq = journal.next_seq(&node.identity.node_id, Some(&node.identity.incarnation));
    let event = Event {
        node: node.identity.node_id.clone(),
        incarnation: Some(node.identity.incarnation.clone()),
        seq,
        lamport,
        typ: "agent-joined".to_string(),
        payload,
    };
    match journal.append(event.clone()) {
        Ok(()) => {
            drop(journal);
            send(
                stream,
                &Sexp::list(vec![
                    Sexp::atom("ok"),
                    Sexp::list(vec![Sexp::atom("node"), Sexp::atom(&node.identity.node_id)]),
                ]),
            );
            broadcast_event(node, &event, None);
        }
        Err(e) => send(
            stream,
            &Sexp::list(vec![
                Sexp::atom("error"),
                Sexp::string(format!("journal append failed: {e}")),
            ]),
        ),
    }
}

/// Local client op: `(leave)`. Records `agent-left` — membership history is
/// kept, not erased, matching the immutable-facts philosophy; `present`
/// just flips to false in the derived view.
pub(crate) fn handle_leave(node: &Arc<Node>, stream: &mut TcpStream) {
    let payload = Sexp::list(vec![
        Sexp::list(vec![Sexp::atom("node"), Sexp::atom(&node.identity.node_id)]),
        Sexp::list(vec![
            Sexp::atom("epoch"),
            Sexp::atom(node.identity.epoch.to_string()),
        ]),
    ]);
    let lamport = node.tick_lamport(0);
    let mut journal = node
        .journal
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner());
    let seq = journal.next_seq(&node.identity.node_id, Some(&node.identity.incarnation));
    let event = Event {
        node: node.identity.node_id.clone(),
        incarnation: Some(node.identity.incarnation.clone()),
        seq,
        lamport,
        typ: "agent-left".to_string(),
        payload,
    };
    match journal.append(event.clone()) {
        Ok(()) => {
            drop(journal);
            send(
                stream,
                &Sexp::list(vec![
                    Sexp::atom("ok"),
                    Sexp::list(vec![Sexp::atom("node"), Sexp::atom(&node.identity.node_id)]),
                ]),
            );
            broadcast_event(node, &event, None);
        }
        Err(e) => send(
            stream,
            &Sexp::list(vec![
                Sexp::atom("error"),
                Sexp::string(format!("journal append failed: {e}")),
            ]),
        ),
    }
}

/// M1.3 hygiene (SWARM-NODE-PRESENCE-HYGIENE): `(evict (node <id>))`
/// records an `agent-left` fact ON BEHALF of a member that is gone and
/// can no longer leave for itself (dead incarnation, wiped data-dir).
/// Same immutable-facts semantics as `leave`: history kept, derived
/// presence flips false. Also shuts down any live-looking connection
/// held by that id (zombie sockets from fast restarts). Trust model
/// identical to every other op: the plane assumes a trusted network;
/// crypto identity remains M1.3 proper work.
pub(crate) fn handle_evict(node: &Arc<Node>, msg: &Sexp, stream: &mut TcpStream) {
    let Some(target) = msg.field_atom("node") else {
        send(
            stream,
            &Sexp::list(vec![
                Sexp::atom("error"),
                Sexp::string("evict requires a `node` field"),
            ]),
        );
        return;
    };
    if target == node.identity.node_id {
        send(
            stream,
            &Sexp::list(vec![
                Sexp::atom("error"),
                Sexp::string("use (leave) to remove yourself"),
            ]),
        );
        return;
    }
    let payload = Sexp::list(vec![Sexp::list(vec![
        Sexp::atom("node"),
        Sexp::atom(target),
    ])]);
    let lamport = node.tick_lamport(0);
    let mut journal = node
        .journal
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner());
    let seq = journal.next_seq(&node.identity.node_id, Some(&node.identity.incarnation));
    let event = Event {
        node: node.identity.node_id.clone(),
        incarnation: Some(node.identity.incarnation.clone()),
        seq,
        lamport,
        typ: "agent-left".to_string(),
        payload,
    };
    match journal.append(event.clone()) {
        Ok(()) => {
            drop(journal);
            if let Some(zombie) = node
                .peers
                .lock()
                .unwrap_or_else(|poisoned| poisoned.into_inner())
                .remove(target)
            {
                let _ = zombie.shutdown(std::net::Shutdown::Both);
            }
            send(
                stream,
                &Sexp::list(vec![
                    Sexp::atom("ok"),
                    Sexp::list(vec![Sexp::atom("evicted"), Sexp::atom(target)]),
                ]),
            );
            broadcast_event(node, &event, None);
        }
        Err(e) => send(
            stream,
            &Sexp::list(vec![
                Sexp::atom("error"),
                Sexp::string(format!("journal append failed: {e}")),
            ]),
        ),
    }
}

/// Local client op: `(compact)`. Rewrites this node's own on-disk journal
/// to the minimal set of facts that reproduces the current derived state —
/// see `compact.rs` for the safety argument for why this can't corrupt any
/// peer's view even though it changes what's on disk. Broadcasts nothing:
/// peers only ever pull via `sync-hello`/`sync-events`, and after
/// compaction that path already serves the smaller equivalent set.
pub(crate) fn handle_compact(node: &Arc<Node>, stream: &mut TcpStream) {
    let mut journal = node
        .journal
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner());
    match compact::compact(
        &mut journal,
        &node.identity.node_id,
        &node.identity.incarnation,
    ) {
        Ok((before, after)) => {
            drop(journal);
            info!("swarm-node: compacted journal {before} -> {after} events");
            send(
                stream,
                &Sexp::list(vec![
                    Sexp::atom("ok"),
                    Sexp::list(vec![Sexp::atom("before"), Sexp::atom(before.to_string())]),
                    Sexp::list(vec![Sexp::atom("after"), Sexp::atom(after.to_string())]),
                ]),
            );
        }
        Err(e) => {
            drop(journal);
            send(
                stream,
                &Sexp::list(vec![
                    Sexp::atom("error"),
                    Sexp::string(format!("compaction failed: {e}")),
                ]),
            );
        }
    }
}

pub(crate) fn handle_list_members(node: &Arc<Node>, stream: &mut TcpStream) {
    let journal = node
        .journal
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner());
    let members = state::membership(&journal);
    drop(journal);
    let mut ids: Vec<&String> = members.keys().collect();
    ids.sort();
    let entries: Vec<Sexp> = ids
        .into_iter()
        .map(|id| {
            let m = &members[id];
            Sexp::list(vec![
                Sexp::list(vec![Sexp::atom("node"), Sexp::atom(id)]),
                Sexp::list(vec![
                    Sexp::atom("present"),
                    Sexp::atom(if m.present { "t" } else { "nil" }),
                ]),
                Sexp::list(vec![
                    Sexp::atom("roles"),
                    Sexp::list(m.roles.iter().map(Sexp::atom).collect()),
                ]),
                Sexp::list(vec![
                    Sexp::atom("capabilities"),
                    Sexp::list(m.capabilities.iter().map(Sexp::atom).collect()),
                ]),
            ])
        })
        .collect();
    send(
        stream,
        &Sexp::list(vec![Sexp::atom("members"), Sexp::list(entries)]),
    );
}
